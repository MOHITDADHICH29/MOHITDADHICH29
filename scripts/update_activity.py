#!/usr/bin/env python3
"""Builds assets/heatmap.svg and assets/stats.svg from real GitHub contribution data.
Usage: python3 scripts/update_activity.py [username]   (no packages needed)"""
import re, sys, html, datetime, urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "MOHITDADHICH29"
OUT = Path(__file__).resolve().parent.parent / "assets"
SANS = "'Segoe UI', Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"
NS = 'xmlns="http://www.w3.org/2000/svg"'
LEVEL = {0: "#2A121C", 1: "#5B1A35", 2: "#8F2A57", 3: "#C77B9B", 4: "#E5B5C7"}

def fetch():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-activity-script"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

def parse(page):
    cells = re.findall(r'<td[^>]*?data-date="([^"]+)"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', page)
    tips = dict(re.findall(r'<tool-tip[^>]*?for="([^"]+)"[^>]*>([^<]+)</tool-tip>', page))
    days = []
    for date, cid, lvl in cells:
        row, col = map(int, cid.replace("contribution-day-component-", "").split("-"))
        m = re.match(r"(\d+) contribution", tips.get(cid, ""))
        days.append(dict(date=datetime.date.fromisoformat(date), row=row, col=col,
                         level=int(lvl), count=int(m.group(1)) if m else 0))
    if not days:
        raise SystemExit("No contribution data found; leaving existing files untouched.")
    return sorted(days, key=lambda d: d["date"])

def heatmap(days, total):
    cs, gap, x0, y0 = 16, 4, 56, 62
    ncols = max(d["col"] for d in days) + 1
    W = x0 + ncols * (cs + gap) + 24
    H = y0 + 7 * (cs + gap) + 58
    body, last_month = "", None
    for c in range(ncols):
        first = min((d for d in days if d["col"] == c), key=lambda d: d["date"])
        if first["date"].month != last_month and first["date"].day <= 21:
            body += f'<text x="{x0 + c*(cs+gap)}" y="{y0-12}" font-family="{SANS}" font-size="12" fill="#C77B9B">{first["date"].strftime("%b")}</text>'
            last_month = first["date"].month
    for lab, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        body += f'<text x="{x0-12}" y="{y0 + r*(cs+gap) + 12}" text-anchor="end" font-family="{SANS}" font-size="12" fill="#C77B9B">{lab}</text>'
    for d in days:
        x, y = x0 + d["col"]*(cs+gap), y0 + d["row"]*(cs+gap)
        extra = ""
        if d["level"] >= 3:
            extra = '<animate attributeName="opacity" values="1;0.6;1" dur="3.5s" repeatCount="indefinite"/>'
        body += (f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" rx="3" fill="{LEVEL[d["level"]]}">'
                 f'<title>{d["count"]} contributions on {d["date"].isoformat()}</title>{extra}</rect>')
    ly = y0 + 7*(cs+gap) + 24
    body += f'<text x="{x0}" y="{ly+12}" font-family="{SANS}" font-size="12" fill="#C77B9B">Less</text>'
    for i in range(5):
        body += f'<rect x="{x0+40+i*(cs+4)}" y="{ly}" width="{cs}" height="{cs}" rx="3" fill="{LEVEL[i]}"/>'
    body += f'<text x="{x0+40+5*(cs+4)+6}" y="{ly+12}" font-family="{SANS}" font-size="12" fill="#C77B9B">More</text>'
    body += (f'<text x="{W-24}" y="{ly+12}" text-anchor="end" font-family="{SERIF}" font-style="italic" font-size="13" fill="#E5B5C7">'
             f'{total} contributions in the last year</text>')
    return (f'<svg {NS} viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub contribution heatmap, {total} contributions in the last year">'
            f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="#190B12" stroke="#C77B9B" stroke-opacity="0.3"/>{body}</svg>')

def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    today = datetime.date.today()
    cur = 0
    for d in reversed(days):
        if d["date"] > today: continue
        if d["count"] > 0: cur += 1
        elif d["date"] == today: continue   # today may not be over yet
        else: break
    return longest, cur

def stats(days, total):
    active = sum(1 for d in days if d["count"] > 0)
    longest, cur = streaks(days)
    tiles = [(str(total), "contributions, last year"), (str(active), "active days"),
             (str(longest), "day longest streak"), (str(cur), "day current streak")]
    tw_, gap = 282, 24
    body = ""
    for i, (num, lab) in enumerate(tiles):
        x = i * (tw_ + gap)
        body += (f'<rect x="{x+1}" y="1" width="{tw_-2}" height="108" rx="14" fill="#190B12" stroke="#C77B9B" stroke-opacity="0.3"/>'
                 f'<rect x="{x+1}" y="26" width="4" height="52" rx="2" fill="#C77B9B"/>'
                 f'<text x="{x+30}" y="68" font-family="{SERIF}" font-size="44" fill="#E5B5C7">{num}</text>'
                 f'<text x="{x+30}" y="92" font-family="{SANS}" font-size="13" fill="#C77B9B">{html.escape(lab)}</text>')
    body += (f'<text x="1200" y="134" text-anchor="end" font-family="{SANS}" font-size="11" fill="#C77B9B" fill-opacity="0.8">'
             f'updated {datetime.date.today().isoformat()}</text>')
    return f'<svg {NS} viewBox="0 0 1200 142" width="1200" height="142" role="img" aria-label="GitHub activity summary">{body}</svg>'

if __name__ == "__main__":
    days = parse(fetch())
    total = sum(d["count"] for d in days)
    OUT.mkdir(exist_ok=True)
    (OUT / "heatmap.svg").write_text(heatmap(days, total), encoding="utf-8")
    (OUT / "stats.svg").write_text(stats(days, total), encoding="utf-8")
    print(f"Wrote heatmap.svg and stats.svg for {USER}: {total} contributions")
