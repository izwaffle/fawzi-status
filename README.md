# fawzi.xyz status page

A single-file, dependency-free status dashboard for `fawzi.xyz`. It probes every
public route over HTTPS by hitting the local Caddy instance directly, reads
system stats from `/proc`, lists running Docker containers, and writes one
self-contained `index.html`.

Live: https://status.fawzi.xyz

## What it does

For each route in `ROUTES` it runs an equivalent of:

```
curl -sk -o /dev/null -w "%{http_code} %{time_total}" \
  --resolve <host>:443:127.0.0.1 https://<host> --max-time 8
```

The `--resolve` trick points the hostname at `127.0.0.1`, so the request goes
straight to the local Caddy container and measures the real backend round trip
without leaving the box. A route counts as up if it returns `200` or `302`.

System stats come from `/proc/loadavg`, `/proc/uptime` and `/proc/meminfo`, plus
`df -h /`. Containers come from `docker ps --format '{{.Names}}|{{.Status}}'`.

## Usage

```bash
python3 gen_status.py
```

Writes `site/status/index.html` next to the script and prints a one-line summary.
It is run on a schedule; point Caddy at the output directory with:

```
status.example.com {
    root * /srv/status
    file_server
}
```

## Layout

```
gen_status.py   the generator (stdlib only: html, json, os, socket, subprocess, time)
index.html      a snapshot of the generated output
```

`index.html` is a point-in-time render included so the page can be previewed
without running the generator. Do not hand-edit it — it is overwritten on every
run.

## Notes

- Stdlib only. No pip install, no API keys, no credentials.
- `socket` is imported but currently unused.
- A route in the list that is not yet configured will report `502`/`000`, which
  is the correct signal — the table shows the real state, it does not hide
  things that are broken.
