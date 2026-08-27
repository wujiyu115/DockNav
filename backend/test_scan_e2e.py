"""Run me: python test_scan_e2e.py - full scan() against a fake Docker socket."""
import asyncio
import json
import os
import tempfile

import scan

JF_ICON = "https://raw.githubusercontent.com/selfhosters/selfhostedpro/master/Runbooks/Jellyfin/jellyfin.png"

# what an Unraid host reports: every container carries the managed label,
# one also carries the icon URL configured in its template
UNRAID_CONTAINERS = [
    {
        "Id": "a" * 64,
        "Names": ["/my-media"],
        "Image": "jellyfin/jellyfin:10.9.11@sha256:abc",
        "State": "running",
        "Labels": {
            "net.unraid.docker.managed": "/boot/config/plugins/dockerMan/templates-user/my-media.xml",
            "net.unraid.docker.icon": JF_ICON,
        },
        "Ports": [{"IP": "0.0.0.0", "PrivatePort": 8096, "PublicPort": 39871, "Type": "tcp"}],
    },
    {
        "Id": "b" * 64,
        "Names": ["/sonarr"],
        "Image": "ghcr.io/hotio/sonarr:latest",
        "State": "running",
        "Labels": {
            "net.unraid.docker.managed": "/boot/config/plugins/dockerMan/templates-user/sonarr.xml",
        },
        "Ports": [{"IP": "0.0.0.0", "PrivatePort": 8989, "PublicPort": 39872, "Type": "tcp"}],
    },
    {
        "Id": "c" * 64,
        "Names": ["/postgres"],
        "Image": "postgres:16",
        "State": "running",
        "Labels": {
            "net.unraid.docker.managed": "/boot/config/plugins/dockerMan/templates-user/postgres.xml",
        },
        "Ports": [{"IP": "0.0.0.0", "PrivatePort": 5432, "PublicPort": 39873, "Type": "tcp"}],
    },
]


async def _fake_daemon(reader, writer):
    await reader.readuntil(b"\r\n\r\n")
    body = json.dumps(UNRAID_CONTAINERS).encode()
    writer.write(
        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
        + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
        + body,
    )
    await writer.drain()
    writer.close()


async def _scan(sock_path):
    server = await asyncio.start_unix_server(_fake_daemon, path=sock_path)
    saved = (scan.DOCKER_SOCK, scan.PROBE_TIMEOUT)
    scan.DOCKER_SOCK, scan.PROBE_TIMEOUT = sock_path, 0.5
    try:
        return await scan.scan()
    finally:
        scan.DOCKER_SOCK, scan.PROBE_TIMEOUT = saved
        server.close()
        await server.wait_closed()


def test_scan_pipeline_prefers_unraid_icon():
    with tempfile.TemporaryDirectory() as d:
        data = asyncio.run(_scan(os.path.join(d, "dockerd.sock")))

    assert data["unraid"] is True
    by_name = {s["name"]: s for s in data["services"]}
    # postgres only publishes a blacklisted port, so it never shows up
    assert set(by_name) == {"my-media", "sonarr"}
    # unraid template icon wins even though the container name would guess a CDN url
    assert by_name["my-media"]["icon"] == JF_ICON
    # no template icon -> old guess-by-name behaviour
    assert by_name["sonarr"]["icon"] == scan.ICON.format("sonarr")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
