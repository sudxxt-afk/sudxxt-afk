import json, os, textwrap, urllib.request
from html import escape

USER = "sudxxt-afk"
PINS = ["SPEAR-GUARD", "mudex", "kudexgram", "hyprland-quickshell-rice", "url-shortener", "kudexcut_bot"]
LANG_COLORS = {"Python": "#3572A5", "TypeScript": "#3178c6", "Go": "#00ADD8", "Lua": "#6c7bff",
               "Shell": "#89e051", "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#a78bfa", "Dockerfile": "#384d54"}
BG, BORDER, TITLE, TEXT, MUTED, ACCENT = "#0d1117", "#30363d", "#a78bfa", "#e6edf3", "#8b949e", "#22d3ee"
FONT = "font-family=\"'JetBrains Mono','Fira Code',ui-monospace,monospace\""


def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def frame(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c3aed"/>'
            f'<stop offset="1" stop-color="{ACCENT}"/></linearGradient></defs>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
            f'<rect x="0" y="0" width="4" height="{h}" rx="2" fill="url(#g)"/>{body}</svg>')


def pin(repo):
    d = api(f"/repos/{USER}/{repo}")
    lines = textwrap.wrap(d.get("description") or "No description", 48)[:2]
    desc = "".join(f'<text x="22" y="{58 + i*17}" fill="{MUTED}" font-size="12" {FONT}>{escape(l)}</text>' for i, l in enumerate(lines))
    lang = d.get("language")
    foot = ""
    if lang:
        foot += (f'<circle cx="26" cy="108" r="5" fill="{LANG_COLORS.get(lang, MUTED)}"/>'
                 f'<text x="38" y="112" fill="{TEXT}" font-size="12" {FONT}>{escape(lang)}</text>')
    foot += f'<text x="190" y="112" fill="{TEXT}" font-size="12" {FONT}>★ {d["stargazers_count"]}   ⑂ {d["forks_count"]}</text>'
    body = (f'<text x="22" y="33" fill="{TITLE}" font-size="15" font-weight="700" {FONT}>◆ {escape(repo)}</text>' + desc + foot)
    open(f"assets/pin-{repo}.svg", "w").write(frame(400, 126, body))


def stats():
    u = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    langs = {}
    for r in own:
        for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[k] = langs.get(k, 0) + v
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:6]
    rows = [("Public repos", u["public_repos"]), ("Stars", stars), ("Followers", u["followers"])]
    body = f'<text x="22" y="34" fill="{TITLE}" font-size="16" font-weight="700" {FONT}>◆ stats</text>'
    for i, (k, v) in enumerate(rows):
        y = 66 + i * 26
        body += (f'<text x="22" y="{y}" fill="{MUTED}" font-size="13" {FONT}>{k}</text>'
                 f'<text x="190" y="{y}" fill="{ACCENT}" font-size="14" font-weight="700" text-anchor="end" {FONT}>{v}</text>')
    body += f'<text x="250" y="34" fill="{TITLE}" font-size="16" font-weight="700" {FONT}>◆ languages</text>'
    x, bar = 250, ""
    for k, v in top:
        w = max(2, 228 * v / total)
        bar += f'<rect x="{x:.1f}" y="48" width="{w:.1f}" height="8" fill="{LANG_COLORS.get(k, MUTED)}"/>'
        x += w
    body += f'<clipPath id="c"><rect x="250" y="48" width="228" height="8" rx="4"/></clipPath><g clip-path="url(#c)">{bar}</g>'
    for i, (k, v) in enumerate(top):
        cx, cy = 256 + (i % 2) * 116, 78 + (i // 2) * 22
        body += (f'<circle cx="{cx}" cy="{cy-4}" r="4.5" fill="{LANG_COLORS.get(k, MUTED)}"/>'
                 f'<text x="{cx+11}" y="{cy}" fill="{TEXT}" font-size="12" {FONT}>{escape(k)} {100*v/total:.0f}%</text>')
    open("assets/stats.svg", "w").write(frame(500, 160, body))


for r in PINS:
    pin(r)
stats()
