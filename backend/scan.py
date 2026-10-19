"""Discover HTTP services from the Docker daemon by probing published ports."""
import asyncio
import os
import re

import httpx

DOCKER_SOCK = os.getenv("DOCKER_SOCK", "/var/run/docker.sock")
HOST_IP = os.getenv("HOST_IP", "127.0.0.1")
PROBE_TIMEOUT = float(os.getenv("PROBE_TIMEOUT", "3"))
PROBE_LIMIT = int(os.getenv("PROBE_LIMIT", "16"))
# unraid copies every container's icon (template URL or local file) here as <name>-icon.png
UNRAID_ICONS = os.getenv("UNRAID_ICONS", "/var/lib/docker/unraid/images")

# container ports that never speak HTTP, used only when probing finds nothing
NON_HTTP = {5432, 3306, 6379, 1883, 8883, 9001, 27017, 4369, 9100, 6888, 2019, 3012}
# container ports most likely to be the primary web UI, best first
WEB_PREF = [80, 443, 8080, 8000, 3000, 5000, 5001, 8096]
ICON = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/{}.png"
# labels Unraid stamps on every container it manages
UNRAID_MANAGED = "net.unraid.docker.managed"
UNRAID_ICON = "net.unraid.docker.icon"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def is_unraid(containers):
    """True when the Docker host is Unraid: it labels the containers it manages."""
    return any(UNRAID_MANAGED in (c.get("Labels") or {}) for c in containers)


def icon_for(container, name, unraid):
    """Unraid template icon first: remote URL as-is, local file via our /api/icon proxy.

    Unraid caches every container's icon as <name>-icon.png under UNRAID_ICONS,
    already resolving whatever local path the template pointed at.
    """
    if unraid:
        label = (container.get("Labels") or {}).get(UNRAID_ICON, "")
        if label.startswith(("http://", "https://")):
            return label
        cached = f"{name}-icon.png"
        if os.path.isfile(os.path.join(UNRAID_ICONS, cached)):
            return f"/api/icon/{cached}"
    return ICON.format(slug(name))


def published(container):
    """[(host_port, container_port)] for tcp ports bound on all interfaces."""
    seen = {}
    for p in container.get("Ports") or []:
        if p.get("Type") != "tcp" or not p.get("PublicPort"):
            continue
        seen.setdefault(p["PublicPort"], p["PrivatePort"])
    return sorted(seen.items())


def _rank(container_port):
    return WEB_PREF.index(container_port) if container_port in WEB_PREF else len(WEB_PREF)


def targets(ports, schemes):
    """Web UIs of one container, best first, from [(host, container)] + {host: scheme|None}.

    Every port that answered HTTP is kept - a container can expose several Web UIs
    (a UI plus an API/docs port), so the dashboard must not hide the extra ones.
    When nothing answered - slow boot, auth-only endpoint, plain TCP - fall back to
    a single guess by container port.
    """
    by_host = dict(ports)
    live = [(h, schemes[h], True) for h, _ in ports if schemes.get(h)]
    live.sort(key=lambda t: (_rank(by_host[t[0]]), t[0]))
    if live:
        return live
    guess = [(h, "http", False) for h, c in ports if c not in NON_HTTP]
    guess.sort(key=lambda t: (_rank(by_host[t[0]]), t[0]))
    return guess[:1]


def choose(ports, schemes):
    """Primary (host_port, scheme, probed) for the container, or None."""
    found = targets(ports, schemes)
    return found[0] if found else None


async def _probe(client, port, gate):
    async with gate:
        for scheme in ("http", "https"):
            try:
                await client.get(f"{scheme}://{HOST_IP}:{port}")
                return port, scheme  # any status code means something speaks HTTP
            except Exception:
                continue
    return port, None


async def _containers():
    transport = httpx.AsyncHTTPTransport(uds=DOCKER_SOCK)
    async with httpx.AsyncClient(transport=transport, base_url="http://docker", timeout=10) as c:
        r = await c.get("/v1.41/containers/json")
        r.raise_for_status()
        return r.json()


async def scan():
    containers = await _containers()
    unraid = is_unraid(containers)
    ports_by_id = {c["Id"]: published(c) for c in containers}
    every = {h for ports in ports_by_id.values() for h, _ in ports}

    gate = asyncio.Semaphore(PROBE_LIMIT)
    async with httpx.AsyncClient(verify=False, timeout=PROBE_TIMEOUT,
                                 follow_redirects=False) as client:
        results = await asyncio.gather(*(_probe(client, p, gate) for p in sorted(every)))
    schemes = dict(results)

    out = []
    for c in containers:
        found = targets(ports_by_id[c["Id"]], schemes)
        if not found:
            continue
        port, scheme, probed = found[0]
        name = (c.get("Names") or ["/?"])[0].lstrip("/")
        out.append({
            "name": name,
            "image": (c.get("Image") or "").split("@")[0],
            "state": c.get("State", ""),
            "port": port,
            "scheme": scheme,
            "href": f"{scheme}://{HOST_IP}:{port}",
            "icon": icon_for(c, name, unraid),
            "online": probed,
            "links": [{"port": h, "scheme": s, "href": f"{s}://{HOST_IP}:{h}", "online": p}
                      for h, s, p in found],
        })
    out.sort(key=lambda s: s["name"].lower())
    return {"host": HOST_IP, "unraid": unraid, "count": len(out), "services": out}
