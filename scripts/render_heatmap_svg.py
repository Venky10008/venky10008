import json, math
from datetime import date, timedelta

with open('data/contributions.json',encoding='utf-8') as f: data=json.load(f)
days={x['date']:x for x in data.get('days', [])}
if not days:
    # Keep the profile valid before the first GitHub Actions run.
    end=date.today()
    start=end-timedelta(days=364)
    cur=start
    while cur<=end:
        days[cur.isoformat()]={'date':cur.isoformat(),'level':0,'count':0}
        cur += timedelta(days=1)
else:
    end=max(date.fromisoformat(k) for k in days)
start=end-timedelta(days=364)
# align to Sunday before start and Saturday after end
start=start-timedelta(days=(start.weekday()+1)%7)
end=end+timedelta(days=(5-end.weekday())%7+1)
weeks=[]; cur=start
while cur<=end:
    week=[]
    for i in range(7):
        d=cur+timedelta(days=i); x=days.get(d.isoformat(),{'level':0,'count':0})
        week.append((d,x))
    weeks.append(week); cur+=timedelta(days=7)

cell=12; gap=4; left=44; top=38; cols=len(weeks); rows=7
width=left+cols*(cell+gap)+20; height=top+rows*(cell+gap)+54
palette=['#161b22','#0e4429','#006d32','#26a641','#39d353','#69f0a0']
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
     '<rect width="100%" height="100%" rx="12" fill="#0d1117"/>',
     '<text x="18" y="22" fill="#f0f6fc" font-family="monospace" font-size="13">github@venky10008 ~ $ contributions --live</text>']
for r,label in enumerate(['Sun','Mon','Tue','Wed','Thu','Fri','Sat']):
    if r in (1,3,5): svg.append(f'<text x="8" y="{top+r*(cell+gap)+10}" fill="#8b949e" font-family="monospace" font-size="9">{label}</text>')
for c,week in enumerate(weeks):
    for r,(d,x) in enumerate(week):
        xx=left+c*(cell+gap); yy=top+r*(cell+gap); lvl=max(0,min(5,int(x.get('level',0))))
        delay=(c*0.018+r*0.012)
        svg.append(f'<rect x="{xx}" y="{yy}" width="{cell}" height="{cell}" rx="3" fill="{palette[lvl]}"><animate attributeName="opacity" from="0" to="1" dur="0.35s" begin="{delay:.3f}s" fill="freeze"/></rect>')

stats=f"{data['total_contributions']:,} contributions  ·  current streak: {data['current_streak']}  ·  longest: {data['longest_streak']}"
svg.append(f'<text x="18" y="{height-18}" fill="#8b949e" font-family="monospace" font-size="10">{stats}</text>')
svg.append(f'<text x="{width-165}" y="{height-18}" fill="#8b949e" font-family="monospace" font-size="9">Less  ■ ■ ■ ■ ■  More</text>')
svg.append('</svg>')
open('contrib-heatmap.svg','w',encoding='utf-8').write('\n'.join(svg))
print('Rendered contrib-heatmap.svg')
