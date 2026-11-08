"""Render the profile's SVG assets (hero, project cards, stats, footer) from live GitHub data."""
import base64, json, os, textwrap, urllib.request
from html import escape
from pathlib import Path

USER = "sudxxt-afk"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"

# Featured repos must stay public: cards link to them and GITHUB_TOKEN can't see private ones.
PROJECTS = [
    ("SPEAR-GUARD", "Anti-spear-phishing platform. Six engines score every email: SPF/DKIM/DMARC, language pressure, sender behaviour, URLs. Real-time threat dashboard.", ["FastAPI", "Celery", "Postgres", "TypeScript"]),
    ("mudex", "Neon terminal music player in pure Go. Live FFT visualizer, album art in any terminal without Kitty/Sixel, 15 ms cold start.", ["Go", "Bubble Tea", "FFT"]),
    ("dstu_assistant", "Study assistant bot: odd/even week timetable, lecture notes synced to Obsidian, deadlines and a morning brief.", ["FastAPI", "aiogram", "Vue", "Docker"]),
    ("kudexcut_bot", "Trim videos right inside Telegram: Mini App with a range slider, FFmpeg worker queue, files wiped after every job.", ["Mini App", "FastAPI", "Redis", "FFmpeg"]),
    ("vpn-free", "Control plane for free VPN subscriptions: node ingestion and Xray health checks, per-device tokens, Telegram bot onboarding.", ["aiogram", "FastAPI", "Xray", "TypeScript"]),
    ("think-asta", "Agency website with its own CMS and admin panel. Server components, Prisma models, Tailwind 4.", ["Next.js 15", "Prisma", "Postgres"]),
]

BG, PANEL, BORDER = "#0d1117", "#111723", "#262d3a"
TEXT, SOFT, MUTED, DIM = "#e6edf3", "#c9d1d9", "#8b949e", "#6e7681"
VIOLET, VIOLET_DEEP, CYAN, GREEN = "#58a6ff", "#1f6feb", "#58a6ff", "#3fb950"
CH = 0.6  # JetBrains Mono advance width, in em

STAR = "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"
PLANE = "M.989 8 .064 2.68a1.342 1.342 0 0 1 1.85-1.462l13.402 5.744a1.13 1.13 0 0 1 0 2.076L1.913 14.782a1.343 1.343 0 0 1-1.85-1.463L.99 8Zm.603-5.288L2.38 7.25h4.87a.75.75 0 0 1 0 1.5H2.38l-.788 4.538L13.929 8Z"
MAIL = "M1.75 2h12.5c.966 0 1.75.784 1.75 1.75v8.5A1.75 1.75 0 0 1 14.25 14H1.75A1.75 1.75 0 0 1 0 12.25v-8.5C0 2.784.784 2 1.75 2ZM1.5 12.251c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25V5.809L8.38 9.397a.75.75 0 0 1-.76 0L1.5 5.809v6.442Zm13-8.181v-.32a.25.25 0 0 0-.25-.25H1.75a.25.25 0 0 0-.25.25v.32L8 7.88Z"
GITHUB = "M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"
BUTTONS = [
    ("telegram", "Telegram", "@defibrilla_tor", CYAN, PLANE),
    ("email", "Email", "sudxxt@gmail.com", VIOLET, MAIL),
    ("github", "Repositories", "browse all", TEXT, GITHUB),
]
REPO = "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]


def font_css():
    css = ""
    for name, weight in [("Regular", 400), ("Medium", 500), ("ExtraBold", 800)]:
        b64 = base64.b64encode((ROOT / "fonts" / f"jbm-{name}.woff2").read_bytes()).decode()
        css += f"@font-face{{font-family:J;font-weight:{weight};src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
    return css + "text{font-family:J,ui-monospace,SFMono-Regular,Menlo,monospace}"


FONTS = font_css()


def svg(w, h, body, defs="", css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">'
            f"<style>{FONTS}{css}</style><defs>{defs}</defs>{body}</svg>")


def text(x, y, s, size, fill, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def width(s, size):
    return len(s) * size * CH


def chip(x, y, label, size=11.0, color=SOFT, dot=None):
    pad = 9
    w = width(label, size) + pad * 2 + (12 if dot else 0)
    h = size + 11
    out = f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="#ffffff08" stroke="{BORDER}"/>'
    tx = x + pad
    if dot:
        out += f'<circle cx="{tx + 3.5:.1f}" cy="{y + h / 2}" r="3.5" fill="{dot}"/>'
        tx += 12
    out += text(f"{tx:.1f}", f"{y + h / 2 + size * 0.36:.1f}", label, size, color, 500)
    return out, w


def frame_defs(w, h, gid):
    return ""


def frame(w, h, gid):
    r = f'x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14"'
    return f'<rect {r} fill="{PANEL}" stroke="{BORDER}"/>'


def hero(commits):
    W, H = 860, 300
    body = f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
    x = 36
    body += text(x - 2, 96, "kudesnik", 56, TEXT, 800, extra='letter-spacing="-1"')
    body += text(x, 132, "Python backend developer, Russia", 15, SOFT, 500)
    body += text(x, 166, "Telegram bots and the FastAPI", 13, MUTED)
    body += text(x, 186, "services behind them.", 13, MUTED)
    cx = x
    for label in ["FastAPI", "aiogram", "PostgreSQL", "Redis", "Docker"]:
        c, w = chip(cx, 214, label)
        body += c
        cx += w + 7
    body += text(x, 266, f"{commits} commits in the last 12 months", 12, DIM)
    body += terminal(452, 32, 372, 236, commits)
    return svg(W, H, body)


def terminal(tx, ty, tw, th, commits):
    size, lh, cw = 12.5, 22, 12.5 * CH
    out = (f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="12" fill="{BG}" fill-opacity=".88" stroke="{BORDER}"/>'
           f'<path d="M{tx} {ty + 30}h{tw}" stroke="{BORDER}"/>')
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        out += f'<circle cx="{tx + 18 + i * 17}" cy="{ty + 15}" r="5" fill="{c}"/>'
    out += text(tx + tw / 2, ty + 19.5, "kudesnik@fedora: ~", 11, DIM, anchor="middle")

    script = [
        ("whoami", "python backend developer", SOFT),
        ("cat stack.txt", "fastapi  aiogram  postgres  redis  docker", SOFT),
        ("git log --since=1.year --oneline | wc -l", str(commits), SOFT),
        ("ls ~/projects", "SPEAR-GUARD  mudex  kudexcut_bot  vpn-free", SOFT),
    ]
    x0, y = tx + 16, ty + 30 + 26
    cmd_x = x0 + 2 * cw
    t = 0.6
    for n, (cmd, result, color) in enumerate(script):
        dur = len(cmd) * 0.055
        widths = ";".join(f"{i * cw:.1f}" for i in range(len(cmd) + 1))
        xs = ";".join(f"{cmd_x + i * cw:.1f}" for i in range(len(cmd) + 1))
        out += (f'<clipPath id="c{n}"><rect x="{cmd_x:.1f}" y="{y - 14}" height="20" width="0">'
                f'<animate attributeName="width" values="{widths}" calcMode="discrete" begin="{t + .3:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>')
        out += (f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                + text(x0, y, "$", size, VIOLET, 800) + "</g>")
        out += text(f"{cmd_x:.1f}", y, cmd, size, TEXT, extra=f'clip-path="url(#c{n})"')
        # caret that rides along while the command is typed
        out += (f'<rect x="{cmd_x:.1f}" y="{y - 11}" width="{cw:.1f}" height="14" fill="{SOFT}" opacity="0">'
                f'<set attributeName="opacity" to=".85" begin="{t:.2f}s"/>'
                f'<animate attributeName="x" values="{xs}" calcMode="discrete" begin="{t + .3:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{t + .3 + dur + .15:.2f}s" fill="freeze"/></rect>')
        t += 0.3 + dur + 0.25
        y += lh
        out += (f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                + text(x0, y, result, size, color, 500) + "</g>")
        t += 0.45
        y += lh
    out += (f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
            + text(x0, y, "$", size, VIOLET, 800)
            + f'<rect x="{cmd_x:.1f}" y="{y - 11}" width="{cw:.1f}" height="14" fill="{SOFT}">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect></g>')
    return out


def project(repo, desc, tags, info):
    W, H = 420, 176
    body = frame(W, H, "p")
    body += f'<g transform="translate(22 21)"><path d="{REPO}" fill="{VIOLET}"/></g>'
    body += text(46, 34, repo, 16, TEXT, 800)
    stars = str(info["stargazerCount"])
    sx = W - 22 - width(stars, 12)
    body += f'<g transform="translate({sx - 19:.1f} 23) scale(.8125)"><path d="{STAR}" fill="{MUTED}"/></g>'
    body += text(W - 22, 34, stars, 12, MUTED, 500, anchor="end")
    for i, line in enumerate(textwrap.wrap(desc, 50)[:3]):
        body += text(22, 66 + i * 19, line, 12, MUTED)
    lang = info["primaryLanguage"]
    labels = ([lang["name"]] if lang else []) + [t for t in tags if not lang or t != lang["name"]]
    cx = 22
    for i, label in enumerate(labels):
        first = i == 0 and lang
        c, w = chip(cx, 136, label, 10.5, SOFT if first else MUTED, dot=(lang["color"] or MUTED) if first else None)
        if cx + w > W - 22:
            break
        body += c
        cx += w + 6
    return svg(W, H, body, frame_defs(W, H, "p"))


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current, i = 0, len(counts) - 1
    if counts and counts[i] == 0:
        i -= 1  # today may simply not have commits yet
    while i >= 0 and counts[i]:
        current, i = current + 1, i - 1
    return current, longest


def smooth(points, floor):
    d = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0, p1, p2 = points[max(i - 1, 0)], points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        # clamp control points so the curve never dips below the baseline
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(floor, p1[1] + (p2[1] - p0[1]) / 6))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(floor, p2[1] - (p3[1] - p1[1]) / 6))
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def stats(user, langs):
    W, H = 860, 300
    cal = user["contributionsCollection"]["contributionCalendar"]
    current, longest = streaks([d for wk in cal["weeks"] for d in wk["contributionDays"]])
    defs = frame_defs(W, H, "s") + (
        f'<linearGradient id="area" x1="0" y1="130" x2="0" y2="262" gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="{VIOLET_DEEP}" stop-opacity=".25"/><stop offset="1" stop-color="{VIOLET_DEEP}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="line" x1="26" y1="0" x2="520" y2="0" gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="{VIOLET_DEEP}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>'
        f'<linearGradient id="num" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{TEXT}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>')
    css = ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}@keyframes pulse{0%{transform:scale(1);opacity:.8}100%{transform:scale(3.4);opacity:0}}"
    body = frame(W, H, "s")

    kpis = [
        ("CONTRIBUTIONS · 1Y", cal["totalContributions"], ""),
        ("CURRENT STREAK", current, "day" if current == 1 else "days"),
        ("LONGEST STREAK", longest, "day" if longest == 1 else "days"),
        ("PUBLIC REPOS", user["repositories"]["totalCount"], ""),
    ]
    tile_w = (W - 52 - 3 * 14) / 4
    for i, (label, value, unit) in enumerate(kpis):
        x = 26 + i * (tile_w + 14)
        body += f'<rect x="{x:.1f}" y="24" width="{tile_w:.1f}" height="76" rx="10" fill="#ffffff06" stroke="{BORDER}"/>'
        body += text(f"{x + 16:.1f}", 48, label, 10, DIM, 500, extra='letter-spacing="1.2"')
        body += text(f"{x + 16:.1f}", 84, str(value), 28, TEXT, 800)
        if unit:
            body += text(f"{x + 22 + width(str(value), 28):.1f}", 84, unit, 12, MUTED, 500)

    weeks = [sum(d["contributionCount"] for d in wk["contributionDays"]) for wk in cal["weeks"]][-52:]
    x0, x1, y0, y1 = 26, 512, 146, 262
    peak = max(weeks) or 1
    pts = [(x0 + i * (x1 - x0) / (len(weeks) - 1), y1 - (v / peak) * (y1 - y0)) for i, v in enumerate(weeks)]
    line = smooth(pts, y1)
    body += text(x0, 130, "WEEKLY CONTRIBUTIONS · 52 WEEKS", 10, DIM, 500, extra='letter-spacing="1.2"')
    body += text(x1, 130, f"peak {peak}/wk", 10, DIM, 500, anchor="end")
    for gy in (y0, (y0 + y1) / 2, y1):
        body += f'<path d="M{x0} {gy}H{x1}" stroke="{BORDER}" stroke-dasharray="2 4"/>'
    body += (f'<path d="{line}L{x1} {y1}L{x0} {y1}Z" fill="url(#area)"/>'
             f'<path d="{line}" stroke="{VIOLET}" stroke-width="2.2" stroke-linecap="round"/>')
    lx, ly = pts[-1]
    body += f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{VIOLET}"/>'

    lx0, lw = 548, W - 26 - 548
    body += text(lx0, 130, "LANGUAGES · PUBLIC REPOS", 10, DIM, 500, extra='letter-spacing="1.2"')
    total = sum(s for _, s, _ in langs) or 1
    body += f'<clipPath id="bar"><rect x="{lx0}" y="146" width="{lw}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">'
    bx = lx0
    for _, size, color in langs:
        seg = lw * size / total
        body += f'<rect x="{bx:.1f}" y="146" width="{seg + .5:.1f}" height="8" fill="{color}"/>'
        bx += seg
    body += "</g>"
    for i, (name, size, color) in enumerate(langs):
        x, y = lx0 + (i % 2) * (lw / 2), 186 + (i // 2) * 28
        body += f'<circle cx="{x + 5:.1f}" cy="{y - 4}" r="4.5" fill="{color}"/>'
        body += text(f"{x + 16:.1f}", y, name, 12, SOFT, 500)
        body += text(f"{x + lw / 2 - 12:.1f}", y, f"{100 * size / total:.1f}%", 11, DIM, anchor="end")
    return svg(W, H, body, defs, css)


def button(label, value, color, icon):
    H = 42
    W = round(46 + width(label, 13) + 10 + width(value, 12) + 18)
    defs = (f'<linearGradient id="b" x1="0" y1="0" x2="{W}" y2="{H}" gradientUnits="userSpaceOnUse">'
            f'<stop stop-color="{color}" stop-opacity=".7"/><stop offset=".6" stop-color="{BORDER}"/></linearGradient>')
    body = f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{H / 2 - .5}" fill="{PANEL}" stroke="{BORDER}"/>'
    body += f'<g transform="translate(18 13)"><path d="{icon}" fill="{color}"/></g>'
    body += text(44, 26, label, 13, TEXT, 800)
    body += text(f"{54 + width(label, 13):.1f}", 26, value, 12, MUTED, 500)
    return svg(W, H, body, defs)


def footer():
    W, H = 860, 70
    defs = (f'<linearGradient id="f" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">'
            f'<stop stop-color="{VIOLET_DEEP}" stop-opacity="0"/><stop offset=".3" stop-color="{VIOLET_DEEP}"/>'
            f'<stop offset=".7" stop-color="{CYAN}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>')
    body = f'<rect y="16" width="{W}" height="1.5" fill="url(#f)"/>'
    body += text(W / 2, 50, "refreshed daily by GitHub Actions · rendered from live API data", 11, DIM, anchor="middle")
    return svg(W, H, body, defs)


def main():
    aliases = "".join(
        f'r{i}: repository(owner: "{USER}", name: "{name}") {{ stargazerCount primaryLanguage {{ name color }} }}\n'
        for i, (name, _, _) in enumerate(PROJECTS))
    data = gql(
        f"""query($login: String!) {{
          user(login: $login) {{
            contributionsCollection {{
              totalCommitContributions
              contributionCalendar {{ totalContributions weeks {{ contributionDays {{ contributionCount }} }} }}
            }}
            repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {{
              totalCount
              nodes {{ name languages(first: 10) {{ edges {{ size node {{ name color }} }} }} }}
            }}
          }}
          {aliases}
        }}""", login=USER)
    user = data["user"]

    sizes = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"] == USER:
            continue
        for e in repo["languages"]["edges"]:
            n = e["node"]
            total, color = sizes.get(n["name"], (0, n["color"] or MUTED))
            sizes[n["name"]] = (total + e["size"], color)
    langs = sorted(((k, s, c) for k, (s, c) in sizes.items()), key=lambda x: -x[1])[:6]

    # Build everything first so a failed request never leaves a half-updated set of cards.
    files = {
        "hero.svg": hero(user["contributionsCollection"]["totalCommitContributions"]),
        "stats.svg": stats(user, langs),
    }
    for i, (name, desc, tags) in enumerate(PROJECTS):
        files[f"project-{name}.svg"] = project(name, desc, tags, data[f"r{i}"])
    for slug, label, value, color, icon in BUTTONS:
        files[f"btn-{slug}.svg"] = button(label, value, color, icon)

    OUT.mkdir(exist_ok=True)
    # stack.svg is a committed snapshot, not generated here
    for old in OUT.glob("project-*.svg"):
        if old.name not in files:
            old.unlink()
    for name, content in files.items():
        (OUT / name).write_text(content)


if __name__ == "__main__":
    main()
