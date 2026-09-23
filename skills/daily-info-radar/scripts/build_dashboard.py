"""Validate reviewed radar data, archive immutable editions, and build offline HTML.

Python 3.10+, standard library only. This does not fetch news or call an LLM.
"""
import argparse
import copy
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

SKILL=Path(__file__).resolve().parents[1]
LAYERS={1:'新闻与原始材料',2:'GitHub',3:'Hacker News',4:'Product Hunt',5:'Reddit'}
COMPONENTS={'原始性':{0,15,30},'支持程度':{0,15,30},'独立复核':{0,10,20},'时间与口径':{0,10,20}}

def require(condition,message):
    if not condition:
        raise ValueError(message)

def validate(raw):
    d=copy.deepcopy(raw)
    require(isinstance(d,dict),'Input must be an object')
    for key in ('edition','report_date','timezone','completed_at','cutoff_at','research_window','sources','items'):
        require(key in d,f'Missing {key}')
    require(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}',d['edition']) is not None,'Unsafe edition name')
    day=date.fromisoformat(d['report_date'])
    require(day.isoformat()==d['report_date'],'Date must be YYYY-MM-DD')
    for k in ('completed_at','cutoff_at'):
        require(datetime.fromisoformat(d[k]).tzinfo is not None,k+' needs timezone offset')
    if 'window_start' in d or 'window_end' in d:
        from window import resolve_window
        expected=resolve_window(d['report_date'],d['timezone'])
        for k in ('window_start','window_end'):
            require(d.get(k)==expected[k],f'{k} must match the target calendar day')
    source_ids=set()
    for s in d['sources']:
        require(s.get('id') and s['id'] not in source_ids,'Duplicate/missing source id')
        source_ids.add(s['id'])
        for k in ('name','status','retrieved_during'):
            require(k in s,'Source missing '+k)
        require(s['status'] in {'成功','部分成功','无法获取','失败','未尝试'},'Invalid source status')
        require(s.get('url') is None or re.match(r'^https?://',s['url']),'Source URL must be HTTP(S)')
    require(isinstance(d['items'],list) and len(d['items'])>0,'No verified items: save a failure log, retain last successful edition')
    ids=set()
    for item in d['items']:
        for k in ('id','event_id','layer','title','summary','value','angle','unknown','source_ids','topic','freshness','claims'):
            require(k in item,'Item missing '+k)
        require(item['id'] not in ids,'Duplicate item id');ids.add(item['id'])
        require(item['layer'] in LAYERS,'Layer must be 1..5')
        require(item['topic'] in ('AI/科技','金融/商业'),'Unsupported topic')
        require(isinstance(item['unknown'],list),'unknown must be a list')
        require(item['source_ids'] and set(item['source_ids'])<=source_ids,'Broken item source reference')
        require(item['claims'],'Missing claim evidence')
        for c in item['claims']:
            for k in ('text','kind','R','components','source_ids','boundary'):
                require(k in c,'Claim missing '+k)
            require(c['source_ids'] and set(c['source_ids'])<=source_ids,'Broken claim source reference')
            if c['R'] is None:
                require(c['components'] is None,'Unscored claim must have null components')
            else:
                require(isinstance(c['components'],dict) and set(c['components'])==set(COMPONENTS),'Wrong components')
                require(all(type(v) is int and v in COMPONENTS[k] for k,v in c['components'].items()),'Invalid scoring band')
                require(type(c['R']) is int and c['R']==sum(c['components'].values()),'R does not equal component sum')
    d.setdefault('top',[]);require(len(d['top'])<=3,'At most three priorities')
    require(all(t['id'] in ids for t in d['top']),'Priority references nonexistent item')
    for k in ('research_log','limitations','candidates'):
        d.setdefault(k,[])
    d.setdefault('horizon_note','参考 Horizon 的汇集、分流和去重；R 为本项目证据完整度规则，不是事实概率。')
    d['counts']={'items':len(d['items']),'events':len({i['event_id'] for i in d['items']}),
                 'by_layer':{str(n):sum(i['layer']==n for i in d['items']) for n in LAYERS}}
    if any(n!=5 for n in d['counts']['by_layer'].values()):
        require(bool(d['limitations']),'Non-target counts require a disclosed limitation')
    return d

def write_atomic(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
        f.write(text);tmp=Path(f.name)
    os.replace(tmp,path)

def jdump(value):
    return json.dumps(value,ensure_ascii=False,indent=2)+'\n'

def md(s):
    return str(s or '').replace('|','\\|').replace('\r','').replace('\n',' ')

def report(d):
    sources={s['id']:s for s in d['sources']}
    def links(ids):
        return '；'.join(f"[{md(sources[i]['name'])}]({sources[i]['url']})" if sources[i].get('url') else md(sources[i]['name']) for i in ids)
    lines=[f"# 每日信息雷达 · {d['report_date']}",'',f"版号：{d['edition']}；完成：{d['completed_at']}；时区：{d['timezone']}",'',
           d['research_window'],'',f"{d['counts']['items']}条信息 / {d['counts']['events']}个独立主题",'','## 来源获取情况','',
           '| 来源 | 状态 | 获取时间 | 说明 |','|---|---|---|---|']
    for s in d['sources']:
        lines.append(f"| {links([s['id']])} | {md(s['status'])} | {md(s['retrieved_during'])} | {md(s.get('note'))} |")
    lines+=['','## 证据评分','', 'R=原始性(0/15/30)+支持程度(0/15/30)+独立复核(0/10/20)+时间口径(0/10/20)。不是事实概率；没有效果验证就不评分。', '',d['horizon_note'],'',
            '## 覆盖与限制','']+['- '+s for s in d['research_log']+d['limitations']]
    for n,name in LAYERS.items():
        lines+=['',f"## {n}. {name} · {d['counts']['by_layer'][str(n)]}条",'']
        for x in (x for x in d['items'] if x['layer']==n):
            lines += [f"### {x['title']}",'',f"- **发生了什么：** {x['summary']}",f"- **价值：** {x['value']}",f"- **研究角度：** {x['angle']}",
                      f"- **时间：** {x['freshness']}；发布：{x.get('published_at') or '未取得'}；核验：{x.get('verified_at') or d['cutoff_at']}",
                      f"- **原始来源：** {links(x['source_ids'])}",'- **待核实：** '+'；'.join(x['unknown'])]
            lines += [f'- **{k}：** {v}' for k,v in (x.get('detail') or {}).items()]
            for c in x['claims']:
                score='不评分' if c['R'] is None else 'R '+str(c['R'])+'（'+' + '.join(k+str(v) for k,v in c['components'].items())+'）'
                lines += [f"- **{c['kind']} · {score}：** {c['text']} {c['boundary']} {links(c['source_ids'])}"]
            lines += [f"- 关联事件：`{x['event_id']}`",'']
    lines+=['## 最值得继续研究','']
    for n,t in enumerate(d['top'],1):
        x=next(x for x in d['items'] if x['id']==t['id']);lines += [f"{n}. **{x['title']}**：{t['reason']}"]
    return '\n'.join(lines)+'\n'

def render(editions,base,bundle=False):
    # 'full' aliases the newest actual edition. Other keys are stable edition IDs.
    mapping={}
    for n,d in enumerate(editions):
        item=copy.deepcopy(d)
        if bundle:
            item['report_path']='report.md';item['data_path']='data.json'
        else:
            folder=base/'daily'/d['report_date']
            item['report_path']=os.path.relpath(folder/(d['edition']+'.md'),render.output_dir).replace(os.sep,'/')
            item['data_path']=os.path.relpath(folder/(d['edition']+'.json'),render.output_dir).replace(os.sep,'/')
        mapping['full' if n==0 else d['edition']]=item
    payload=json.dumps(mapping,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return (SKILL/'assets/dashboard.html').read_text(encoding='utf-8').replace('__RADAR_DATA__',payload)

def build(raw,root):
    d=validate(raw);root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    lock=root/'.build.lock'
    try:
        handle=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        raise ValueError('Another build is active (.build.lock). Inspect before removing a stale lock.')
    try:
        os.close(handle)
        day=root/'daily'/d['report_date'];edition=d['edition'];data_path=day/(edition+'.json')
        if data_path.exists():
            require(json.loads(data_path.read_text(encoding='utf-8'))==d,'Edition exists with different content. Use a new revision edition.')
        else:
            write_atomic(data_path,jdump(d))
        text=report(d);write_atomic(day/(edition+'.md'),text)
        write_atomic(day/(edition+'-sources.json'),jdump(d['sources']))
        write_atomic(day/(edition+'-candidates.json'),jdump(d['candidates']))
        archive=[]
        for file in (root/'daily').glob('*/*.json'):
            if file.name.endswith(('-sources.json','-candidates.json')):
                continue
            doc=json.loads(file.read_text(encoding='utf-8'))
            if isinstance(doc,dict) and 'edition' in doc:
                archive.append(validate(doc))
        archive.sort(key=lambda x:(x['report_date'],datetime.fromisoformat(x['completed_at'])),reverse=True)
        render.output_dir=root;write_atomic(root/'index.html',render(archive,root))
        same_day=[a for a in archive if a['report_date']==d['report_date']]
        render.output_dir=day;write_atomic(day/'index.html',render(same_day,root))
        write_atomic(day/(edition+'.html'),render([d],root))
        write_atomic(root/'archive-manifest.json',jdump([{'edition':a['edition'],'date':a['report_date'],'items':a['counts']['items'],'completed_at':a['completed_at']} for a in archive]))
        downloads=root/'downloads';downloads.mkdir(exist_ok=True);zip_path=downloads/(edition+'-offline.zip')
        with tempfile.NamedTemporaryFile(dir=downloads,delete=False,suffix='.zip') as f:
            tempzip=Path(f.name)
        with zipfile.ZipFile(tempzip,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('index.html',render([d],root,bundle=True))
            z.writestr('report.md',text);z.writestr('data.json',jdump(d));z.writestr('sources.json',jdump(d['sources']));z.writestr('candidates.json',jdump(d['candidates']))
            z.writestr('README.txt','解压后双击 index.html。断网可读正文和证据摘要；原文外链需要网络。\n收藏和已读仅存浏览器。\n')
        os.replace(tempzip,zip_path)
        return {'index':str(root/'index.html'),'report':str(day/(edition+'.md')),'offline_zip':str(zip_path),'counts':d['counts']}
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output-root',required=True)
    a=p.parse_args();raw=json.loads(Path(a.input).read_text(encoding='utf-8-sig'))
    print(jdump(build(raw,a.output_root)))
