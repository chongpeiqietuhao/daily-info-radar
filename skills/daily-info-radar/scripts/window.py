"""Resolve yesterday as a calendar day in the requested timezone."""
import argparse
import json
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def resolve_window(target=None, timezone_name='Asia/Shanghai', now=None):
    try:
        tz=ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name!='Asia/Shanghai':
            raise ValueError('Timezone data missing. Install tzdata or use Asia/Shanghai.')
        tz=timezone(timedelta(hours=8), name='Asia/Shanghai')
    clock=datetime.fromisoformat(now) if now else datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError('--now must include a timezone offset')
    day=date.fromisoformat(target) if target else clock.astimezone(tz).date()-timedelta(days=1)
    start=datetime.combine(day,time.min,tzinfo=tz)
    end=datetime.combine(day+timedelta(days=1),time.min,tzinfo=tz)
    return {'report_date':day.isoformat(),'timezone':timezone_name,'window_start':start.isoformat(),
            'window_end':end.isoformat(),'boundary':'start inclusive; end exclusive'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--date');p.add_argument('--timezone',default='Asia/Shanghai');p.add_argument('--now')
    a=p.parse_args();print(json.dumps(resolve_window(a.date,a.timezone,a.now),ensure_ascii=False,indent=2))
