"""Run me: python test_scan_e2e.py - full scan() against a fake Docker socket."""
import asyncio
import json
import os
import tempfile

import scan

JF_ICON = "https://raw.githubusercontent.com/selfhosters/selfhostedpro/master/Runbooks/Jellyfin/jellyfin.png"
UNRAID = "net.unraid.docker.managed"
ICON = "net.unraid.docker.icon"

# what an Unraid host reports: every container carries the managed label,
# one has a remote icon URL, one points at a local file that only exists on the host
UNRAID_CONTAINERS = [
    {
        "Id": "a" * 64,
        "Names": ["/my-media"],
        "Image": "jellyfin/jellyfin:10.9.11@sha256:abc",
        "State": "running",
        "Labels": {UNRAID: "my-media.xml", ICON: JF_ICON},
        "Ports": [{"IP": "0.0.0.0", "PrivatePort": 8096, "PublicPort": 39871, "Type": "tcp"}],
    },
    {
        "Id": "b" * 64,
        "Names": ["/bark"],
        "Image": "finab/bark-server:latest",
        "State": "running",
        "Labels": {UNRAID: "bark.xml", ICON: "/mnt/user/appdata/icons/bark.png"},
        "Ports": [
            {"IP": "0.0.0.0", "PrivatePort": 8080, "PublicPort": 39872, "Type": "tcp"},
            {"IP": "0.0.0.0", "PrivatePort": 8081, "PublicPort": 39874, "Type": "tcp"},
        ],
    },
    {
        "Id": "c" * 64,
        "Names": ["/postgres"],
        "Image": "postgres:16",
        "State": "running",
        "Labels": {UNRAID: "postgres.xml"},
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


def _scan_with(sock_path, icons_dir):
    async def run():
        server = await asyncio.start_unix_server(_fake_daemon, path=sock_path)
        saved = (scan.DOCKER_SOCK, scan.UNRAID_ICONS, scan.PROBE_TIMEOUT)
        scan.DOCKER_SOCK, scan.UNRAID_ICONS, scan.PROBE_TIMEOUT = sock_path, icons_dir, 0.5
        try:
            return await scan.scan()
        finally:
            scan.DOCKER_SOCK, scan.UNRAID_ICONS, scan.PROBE_TIMEOUT = saved
            server.close()
            await server.wait_closed()
    return asyncio.run(run())


def test_scan_pipeline_prefers_unraid_icon():
    with tempfile.TemporaryDirectory() as d:
        icons = os.path.join(d, "icons")
        os.mkdir(icons)
        # only bark has a cached copy, like a real host where some icons never cached
        with open(os.path.join(icons, "bark-icon.png"), "wb") as f:
            f.write(b"\x89PNG fake")

        data = _scan_with(os.path.join(d, "dockerd.sock"), icons)

    assert data["unraid"] is True
    by_name = {s["name"]: s for s in data["services"]}
    # postgres only publishes a blacklisted port, so it never shows up
    assert set(by_name) == {"my-media", "bark"}
    # remote URL label wins even though the container name would guess a CDN url
    assert by_name["my-media"]["icon"] == JF_ICON
    # local path label is served through our proxy pointing at unraid's cache
    assert by_name["bark"]["icon"] == "/api/icon/bark-icon.png"
    # an unprobed container still yields exactly one (guessed) link
    assert len(by_name["my-media"]["links"]) == 1
    # every port of bark is listed, and none of them answered in this fake run
    assert [l["port"] for l in by_name["bark"]["links"]] == [39872]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
