import json, re
from datetime import date
from collections import Counter
import requests
from bs4 import BeautifulSoup

USERNAME = 'venky10008'
URL = f'https://github.com/users/{USERNAME}/contributions'
headers = {'User-Agent': 'venky10008-profile-readme/1.0'}
resp = requests.get(URL, headers=headers, timeout=30)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, 'html.parser')

days=[]
for el in soup.select('[data-date][data-level]'):
    d=el.get('data-date')
    level=el.get('data-level')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d or ''):
        try:
            count_text = el.get('aria-label','')
            m=re.search(r'(\d+) contribution', count_text)
            count=int(m.group(1)) if m else 0
            days.append({'date': d, 'level': int(level or 0), 'count': count})
        except ValueError:
            pass

days=sorted({x['date']:x for x in days}.values(), key=lambda x:x['date'])
if not days:
    raise RuntimeError('No contribution cells found; GitHub HTML format may have changed.')
counts=[x['count'] for x in days]
nonzero=[x for x in days if x['count']>0]
cur=0
for x in reversed(days):
    if x['count']>0: cur+=1
    else: break
best=max(days, key=lambda x:x['count'])
# longest streak
longest=run=0
prev=None
for x in days:
    if x['count']>0:
        if prev and (date.fromisoformat(x['date'])-date.fromisoformat(prev)).days==1: run+=1
        else: run=1
        longest=max(longest,run)
        prev=x['date']
    else:
        run=0; prev=None
monthly=Counter(x['date'][:7] for x in nonzero)
summary={
    'username': USERNAME,
    'days': days,
    'total_contributions': sum(counts),
    'current_streak': cur,
    'longest_streak': longest,
    'best_day': best,
    'months': dict(monthly),
}
with open('data/contributions.json','w',encoding='utf-8') as f:
    json.dump(summary,f,indent=2)
print(f"Fetched {len(days)} days; {summary['total_contributions']} contributions")
