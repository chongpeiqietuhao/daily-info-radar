import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/daily-info-radar/scripts'))
from build_dashboard import build, validate
from window import resolve_window

def sample():
    # Explicit synthetic fixture, never displayed in a real user's daily archive.
    return {'edition':'2026-01-01-test','report_date':'2026-01-01','timezone':'Asia/Shanghai',
        'completed_at':'2026-01-02T10:00:00+08:00','cutoff_at':'2026-01-02T10:00:00+08:00','research_window':'合成测试，不是真实新闻',
        'sources':[{'id':'s','name':'测试','url':'https://example.com','layer':1,'status':'成功','retrieved_during':'测试'}],
        'items':[{'id':'i','event_id':'e','layer':1,'title':'测试 </script> <b>','summary':'test','value':'test','angle':'test',
                  'unknown':['test'],'source_ids':['s'],'topic':'AI/科技','freshness':'测试','claims':[
                      {'text':'test','kind':'当事方主张','R':55,'components':{'原始性':30,'支持程度':15,'独立复核':0,'时间与口径':10},'source_ids':['s'],'boundary':'test'}]}],
        'top':[{'id':'i','reason':'test'}],'limitations':['仅一个合成条目用于测试']}

class RadarTests(unittest.TestCase):
    def test_timezone_midnight_and_month(self):
        self.assertEqual(resolve_window(now='2026-09-23T01:59:59+00:00')['report_date'],'2026-09-22')
        self.assertEqual(resolve_window(now='2026-03-01T10:00:00+08:00')['report_date'],'2026-02-28')
        self.assertEqual(resolve_window(now='2026-01-01T10:00:00+08:00')['report_date'],'2025-12-31')
    def test_bad_scores_and_references(self):
        d=sample();d['items'][0]['claims'][0]['R']=99
        with self.assertRaises(ValueError):validate(d)
        d=sample();d['items'][0]['source_ids']=['missing']
        with self.assertRaises(ValueError):validate(d)
    def test_real_estate_layer_is_supported(self):
        d=sample();d['items'][0]['layer']=6;d['items'][0]['topic']='地产';d['sources'][0]['layer']=6
        self.assertEqual(validate(d)['counts']['by_layer']['6'],1)
    def test_path_traversal_and_window(self):
        d=sample();d['edition']='../oops'
        with self.assertRaises(ValueError):validate(d)
        d=sample();d.update(window_start='2026-01-01T08:00:00+08:00',window_end='2026-01-02T08:00:00+08:00')
        with self.assertRaises(ValueError):validate(d)
    def test_archive_idempotence_and_escaping(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);d=sample();build(d,root);build(d,root)
            text=(root/'index.html').read_text(encoding='utf-8')
            self.assertIn('\\u003c/script\\u003e',text)
            changed=copy.deepcopy(d);changed['items'][0]['title']='changed'
            with self.assertRaises(ValueError):build(changed,root)
            self.assertFalse((root/'.build.lock').exists())
            changed['edition']='2026-01-01-r2';changed['completed_at']='2026-01-02T11:00:00+08:00';build(changed,root)
            tomorrow=copy.deepcopy(d);tomorrow.update(edition='2026-01-02-test',report_date='2026-01-02');build(tomorrow,root)
            self.assertEqual(len(json.loads((root/'archive-manifest.json').read_text(encoding='utf-8'))),3)
            with zipfile.ZipFile(root/'downloads/2026-01-02-test-offline.zip') as z:
                self.assertEqual(set(z.namelist()),{'index.html','report.md','data.json','sources.json','candidates.json','README.txt'})
                self.assertIn('"report_path": "report.md"',z.read('index.html').decode('utf-8'))

if __name__=='__main__':unittest.main()
