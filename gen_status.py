#!/usr/bin/env python3
"""Live status dashboard for fawzi.xyz — run to regenerate site/index.html."""
import html, json, os, socket, subprocess, time

DOMAIN = "fawzi.xyz"
ROUTES = ["port", "rl", "groupwatch", "cloud", "music", "audiobooks",
          "code", "kikr", "share", "status", "hermes", "bookmarks", "read", "habits", "syncthing",
          "tasks", "rss", "a", "b", "fawzi.xyz", "fawzi.us", "project.fawzi.xyz", "api"]
HERE = os.path.dirname(os.path.abspath(__file__))

def check(host):
    """Probe one route over HTTPS, hitting local Caddy directly."""
    fqdn = host if "." in host else f"{host}.{DOMAIN}"
    try:
        out = subprocess.run(
            ["curl", "-sk", "-o", "/dev/null", "-w", "%{http_code} %{time_total}",
             "--resolve", f"{fqdn}:443:127.0.0.1", f"https://{fqdn}", "--max-time", "8"],
            capture_output=True, text=True, timeout=10)
        code, _, secs = out.stdout.partition(" ")
        return code, round(float(secs) * 1000)
    except Exception:
        return "000", 0

def system_stats():
    with open("/proc/loadavg") as f:
        load = f.read().split()[0]
    with open("/proc/uptime") as f:
        up = int(float(f.read().split()[0]))
    days, hrs = up // 86400, up % 86400 // 3600
    mem = psutil_free()
    disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
    disk_pct = disk.stdout.strip().splitlines()[-1].split()[4]
    return load, f"{days}d {hrs}h", mem, disk_pct

def psutil_free():
    with open("/proc/meminfo") as f:
        info = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
    total, avail = info["MemTotal"], info["MemAvailable"]
    return f"{(total - avail) / 1e6:.1f}/{total / 1e6:.1f} GB"

def docker_containers():
    out = subprocess.run(["docker", "ps", "--format", "{{.Names}}|{{.Status}}"],
                         capture_output=True, text=True)
    return [tuple(l.split("|", 1)) for l in out.stdout.strip().splitlines() if l]

def main():
    results = {h: check(h) for h in ROUTES}
    containers = docker_containers()
    load, uptime, mem, disk = system_stats()
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    up_count = sum(1 for c, _ in results.values() if c in ("200", "302"))
    code = lambda c: ("up", c) if c in ("200", "302") else ("down", c)

    rows = "\n".join(
        f'<tr class="{s}"><td>{html.escape(h)}</td><td class="code">{c}</td>'
        f'<td>{ms} ms</td></tr>'
        for h, (c, ms) in results.items()
        for s in [code(c)[0]]
    )
    crows = "\n".join(
        f'<li><b>{html.escape(n)}</b> — {html.escape(st)}</li>' for n, st in containers)

    page = f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>fawzi.xyz status</title><style>
body{{background:#0d1117;color:#c9d1d9;font:15px/1.5 -apple-system,Segoe UI,sans-serif;
max-width:760px;margin:2rem auto;padding:0 1rem}}
h1{{color:#58a6ff;font-size:1.5rem}} .pill{{display:inline-block;padding:.2rem .7rem;
border-radius:99px;font-weight:600}}
.up{{background:#12261e;color:#3fb950}} .down{{background:#2d1117;color:#f85149}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}
td,th{{padding:.45rem .8rem;border-bottom:1px solid #21262d;text-align:left}}
tr.up td:first-child{{color:#3fb950}} tr.down td:first-child{{color:#f85149}}
.code{{font-family:monospace}} small{{color:#8b949e}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:.8rem}}
.card b{{color:#58a6ff;display:block;font-size:.8rem;text-transform:uppercase}}
ul{{columns:2;margin:.3rem 0;padding-left:1.2rem}} li{{margin:.2rem 0}}
.warn{{color:#d29922}}
</style></head><body>
<h1>fawzi.xyz <span class="pill {'up' if up_count == len(ROUTES) else 'down'}">{up_count}/{len(ROUTES)} up</span></h1>
<small>generated {ts}</small>
<div class=grid>
<div class=card><b>uptime</b>{uptime}</div>
<div class=card><b>load</b>{load}</div>
<div class=card><b>memory</b>{mem}</div>
<div class="card{' warn' if disk.rstrip('%').isdigit() and int(disk.rstrip('%')) > 90 else ''}"><b>disk</b>{disk} used</div>
</div>
<h2>Routes</h2><table><tr><th>host</th><th>HTTP</th><th>latency</th></tr>
{rows}</table>
<h2>Containers ({len(containers)})</h2><ul>{crows}</ul>
</body></html>"""

    os.makedirs(os.path.join(HERE, "site", "status"), exist_ok=True)
    with open(os.path.join(HERE, "site", "status", "index.html"), "w") as f:
        f.write(page)
    print(f"written: {up_count}/{len(ROUTES)} up, disk {disk}")
    print(json.dumps({h: c for h, (c, _) in results.items()}))

if __name__ == "__main__":
    main()