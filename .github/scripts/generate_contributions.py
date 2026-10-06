#!/usr/bin/env python3
"""Generate assets/contributions.svg — a GitHub-style contribution matrix.

The card is pure SVG + SMIL (no JavaScript, no external requests), so it
animates safely inside a README <img>:
  * a neon comet (bloom trail + gradient core + white-hot line with a glowing
    head orb) sweeps the serpentine route through every cell,
  * a soft light band periodically scans across the grid,
  * a light streak zips across the header divider.
"""
import json
import os
import random
import urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get('GITHUB_TOKEN')
LOGIN = os.environ.get('GITHUB_USER_NAME') or os.environ.get('GITHUB_REPOSITORY_OWNER')
OUT = os.environ.get('OUTPUT_PATH', 'assets/contributions.svg')
SAMPLE = os.environ.get('SAMPLE_DATA', '')

# ---- layout ------------------------------------------------------------
CELL, SIZE, RADIUS = 15, 11, 4
LEFT, TOP = 92, 86
ROWS, MAX_WEEKS = 7, 53
WIDTH = LEFT + MAX_WEEKS * CELL + 60   # 947
HEIGHT = 290
LEGEND_Y, FOOTER_Y = 227, 264

# ---- animation timing --------------------------------------------------
SWEEP_DUR = '12s'    # comet over the whole matrix
STREAK_DUR = '3.6s'  # light streak across the header divider
SCAN_DUR = '6.5s'    # light band across the grid

# ---- palette -----------------------------------------------------------
LEVELS = {
    'NONE': '#111827',
    'FIRST_QUARTILE': '#0e4429',
    'SECOND_QUARTILE': '#006d32',
    'THIRD_QUARTILE': '#26a641',
    'FOURTH_QUARTILE': '#39d353',
}
FOOTER_LIVE = 'REFRESHED DAILY BY GITHUB ACTIONS · SOURCE: GITHUB GRAPHQL API'
FOOTER_SAMPLE = 'SAMPLE DATA · REAL HISTORY ARRIVES WITH THE FIRST GITHUB ACTIONS RUN'


def level_for(count):
    if count <= 0:
        return 'NONE'
    if count <= 2:
        return 'FIRST_QUARTILE'
    if count <= 5:
        return 'SECOND_QUARTILE'
    if count <= 9:
        return 'THIRD_QUARTILE'
    return 'FOURTH_QUARTILE'


def fetch_calendar():
    if not TOKEN or not LOGIN:
        raise SystemExit('GITHUB_TOKEN and GITHUB_USER_NAME are required')
    query = '''
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount contributionLevel } }
      }
    }
  }
}
'''
    payload = json.dumps({'query': query, 'variables': {'login': LOGIN}}).encode()
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=payload,
        headers={
            'Authorization': f'bearer {TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'Venky10008-profile-contributions',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get('errors'):
        raise SystemExit(json.dumps(data['errors']))
    return data['data']['user']['contributionsCollection']['contributionCalendar']


def sample_calendar():
    """Deterministic sample year used for local previews when no token exists."""
    rng = random.Random(10008)
    today = datetime.now(timezone.utc).date()
    end = today + timedelta(days=(5 - today.weekday()) % 7)   # Saturday of this week
    start = end - timedelta(days=MAX_WEEKS * 7 - 1)           # 371 days back (Sunday)
    days, total, i = [], 0, 0
    d = start
    while d <= end:
        progress = i / (MAX_WEEKS * 7)
        weekend = d.weekday() >= 5
        active_p = (0.40 + 0.45 * progress) if weekend else (0.68 + 0.27 * progress)
        count = 0
        if rng.random() < active_p:
            count = rng.randint(1, 6 if weekend else 16)
        total += count
        days.append({'date': d.isoformat(),
                     'contributionCount': count,
                     'contributionLevel': level_for(count)})
        d += timedelta(days=1)
        i += 1
    weeks = [{'contributionDays': days[j:j + ROWS]} for j in range(0, len(days), ROWS)]
    return {'totalContributions': total, 'weeks': weeks}

def build_svg(calendar):
    weeks = calendar['weeks'][-MAX_WEEKS:]
    cols = len(weeks)
    grid_right = LEFT + cols * CELL
    total = calendar['totalContributions']

    # Contribution cells.
    rects = []
    for x, w in enumerate(weeks):
        for y, day in enumerate(w['contributionDays']):
            px, py = LEFT + x * CELL, TOP + y * CELL
            fill = LEVELS.get(day['contributionLevel'], LEVELS['NONE'])
            rects.append(
                f'<rect x="{px}" y="{py}" width="{SIZE}" height="{SIZE}" '
                f'rx="{RADIUS}" fill="{fill}"/>'
            )

    # Serpentine route through every cell so the comet visits the whole year.
    pts = []
    for x in range(cols):
        ys = range(ROWS) if x % 2 == 0 else range(ROWS - 1, -1, -1)
        for y in ys:
            pts.append((LEFT + x * CELL + SIZE / 2, TOP + y * CELL + SIZE / 2))
    path_d = 'M ' + ' L '.join(f'{px},{py}' for px, py in pts)

    # Exact polyline length: vertical runs inside columns + horizontal links.
    route_len = (ROWS - 1) * CELL * cols + CELL * (cols - 1)

    # Month labels above the grid (first week is usually a partial month).
    month_labels, seen = [], set()
    for x, w in enumerate(weeks):
        if x == 0 or not w['contributionDays']:
            continue
        month = datetime.strptime(w['contributionDays'][0]['date'], '%Y-%m-%d').strftime('%b')
        if month not in seen:
            month_labels.append(f'<text x="{LEFT + x * CELL}" y="76" class="month">{month}</text>')
            seen.add(month)

    # The comet: three stacked strokes whose leading edges stay aligned with
    # the head orb — soft bloom, gradient core, white-hot line.
    trails = []
    for length, width, opacity, color, filt in (
        (430, 13, .22, 'url(#comet)', ' filter="url(#bloom)"'),
        (240, 5, .7, 'url(#comet)', ''),
        (110, 2, .95, '#ffffff', ''),
    ):
        trails.append(
            f'<path d="{path_d}" stroke="{color}" stroke-width="{width}" '
            f'stroke-opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round" '
            f'fill="none" stroke-dasharray="{length} {route_len - length}"{filt}>'
            f'<animate attributeName="stroke-dashoffset" from="{length}" '
            f'to="{length - route_len}" dur="{SWEEP_DUR}" repeatCount="indefinite"/>'
            f'</path>'
        )

    # Light streak zipping across the header divider (soft under + bright core).
    line_len = WIDTH - 48
    streaks = []
    for width, opacity in ((7, .16), (2, .9)):
        streaks.append(
            f'<path d="M24 58H{WIDTH - 24}" stroke="#cfe8ff" stroke-width="{width}" '
            f'stroke-opacity="{opacity}" stroke-linecap="round" fill="none" '
            f'stroke-dasharray="130 {line_len - 130}">'
            f'<animate attributeName="stroke-dashoffset" from="{line_len}" to="0" '
            f'dur="{STREAK_DUR}" repeatCount="indefinite"/>'
            f'</path>'
        )

    # Soft light band sweeping across the grid (clipped to the matrix area).
    scan = (
        f'<g clip-path="url(#gridClip)">'
        f'<rect x="{LEFT - 170}" y="{TOP - 6}" width="150" height="{ROWS * CELL + 4}" '
        f'fill="url(#scan)" opacity=".3">'
        f'<animate attributeName="x" from="{LEFT - 170}" to="{grid_right + 20}" '
        f'dur="{SCAN_DUR}" repeatCount="indefinite"/>'
        f'</rect></g>'
    )

    all_days = [d for w in weeks for d in w['contributionDays']]
    last_date = (datetime.strptime(all_days[-1]['date'], '%Y-%m-%d').strftime('%d %b %Y')
                 if all_days else '—')
    footer_left = FOOTER_SAMPLE if SAMPLE else FOOTER_LIVE

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#070b16"/><stop offset="1" stop-color="#0b1224"/></linearGradient>
  <linearGradient id="line" gradientUnits="userSpaceOnUse" x1="24" y1="58" x2="{WIDTH - 24}" y2="58"><stop stop-color="#247bff"/><stop offset="1" stop-color="#ff354f"/></linearGradient>
  <linearGradient id="comet" gradientUnits="userSpaceOnUse" x1="{LEFT}" y1="0" x2="{grid_right}" y2="0"><stop stop-color="#22d3ee"/><stop offset=".33" stop-color="#7c5cff"/><stop offset=".66" stop-color="#ff3d8b"/><stop offset="1" stop-color="#ffb020"/></linearGradient>
  <linearGradient id="routeGrad" gradientUnits="userSpaceOnUse" x1="{LEFT}" y1="0" x2="{grid_right}" y2="0"><stop stop-color="#247bff"/><stop offset=".5" stop-color="#8b5cf6"/><stop offset="1" stop-color="#ff354f"/></linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#ffffff" stop-opacity="0"/><stop offset=".5" stop-color="#bfe3ff" stop-opacity=".55"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
  <filter id="bloom" x="-15%" y="-40%" width="130%" height="180%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="bloomCircle" x="-90%" y="-90%" width="280%" height="280%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="gridClip"><rect x="{LEFT - 6}" y="{TOP - 6}" width="{cols * CELL + 6}" height="{ROWS * CELL + 4}" rx="10"/></clipPath>
  <style>
    .title{{font:700 22px Arial,sans-serif;letter-spacing:1.6px;fill:#f8fafc}}
    .sub{{font:500 12px Arial,sans-serif;letter-spacing:1.1px;fill:#8fa3bf}}
    .month{{font:500 10px Arial,sans-serif;fill:#73859d}}
    .day{{font:500 10px Arial,sans-serif;fill:#73859d}}
    .stat{{font:700 16px Arial,sans-serif;fill:#f8fafc}}
    .foot{{font:500 10px Arial,sans-serif;letter-spacing:.8px;fill:#5f7189}}
  </style>
</defs>
<rect x="2" y="2" width="{WIDTH - 4}" height="{HEIGHT - 4}" rx="22" fill="url(#bg)" stroke="#1b2b46"/>
<text x="28" y="32" class="title">CONTRIBUTION MATRIX</text>
<text x="28" y="49" class="sub">LIVE FROM GITHUB · AUTO-REFRESHED DAILY</text>
<text x="{WIDTH - 28}" y="31" class="stat" text-anchor="end">{total:,} contributions</text>
<path d="M24 58H{WIDTH - 24}" stroke="url(#line)" stroke-opacity=".7"/>
{''.join(streaks)}
{''.join(month_labels)}
<text x="34" y="{TOP + 24}" class="day">Mon</text><text x="34" y="{TOP + 54}" class="day">Wed</text><text x="34" y="{TOP + 84}" class="day">Fri</text>
{''.join(rects)}
{scan}
<path id="route" d="{path_d}" stroke="url(#routeGrad)" stroke-opacity=".3" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
{''.join(trails)}
<g>
  <circle r="9" fill="url(#comet)" opacity=".45" filter="url(#bloomCircle)"/>
  <circle r="5" fill="url(#comet)"/>
  <circle r="2.4" fill="#ffffff"/>
  <animateMotion dur="{SWEEP_DUR}" repeatCount="indefinite"><mpath href="#route" xlink:href="#route"/></animateMotion>
</g>
<text x="{LEFT}" y="{LEGEND_Y}" class="sub">LOW</text>
<rect x="{LEFT + 34}" y="{LEGEND_Y - 9}" width="11" height="11" rx="4" fill="#111827"/><rect x="{LEFT + 51}" y="{LEGEND_Y - 9}" width="11" height="11" rx="4" fill="#0e4429"/><rect x="{LEFT + 68}" y="{LEGEND_Y - 9}" width="11" height="11" rx="4" fill="#006d32"/><rect x="{LEFT + 85}" y="{LEGEND_Y - 9}" width="11" height="11" rx="4" fill="#26a641"/><rect x="{LEFT + 102}" y="{LEGEND_Y - 9}" width="11" height="11" rx="4" fill="#39d353"/>
<text x="{LEFT + 124}" y="{LEGEND_Y}" class="sub">HIGH</text>
<text x="{WIDTH - 28}" y="{LEGEND_Y}" class="sub" text-anchor="end">COMET SWEEP · ACTIVE</text>
<text x="{LEFT}" y="{FOOTER_Y}" class="foot">{footer_left}</text>
<text x="{WIDTH - 28}" y="{FOOTER_Y}" class="foot" text-anchor="end">LAST SYNC · {last_date}</text>
</svg>'''
    return svg


def main():
    calendar = sample_calendar() if SAMPLE else fetch_calendar()
    svg = build_svg(calendar)
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(svg)
    who = LOGIN or 'sample'
    print(f'Wrote {OUT} for {who} ({calendar["totalContributions"]} contributions)')


if __name__ == '__main__':
    main()



