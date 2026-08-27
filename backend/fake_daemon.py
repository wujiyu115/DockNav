"""Fake Docker daemon on a unix socket. Usage: python fake_daemon.py <sock> <containers.json>"""
import asyncio
import json
import sys

TDARR = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/tdarr.png"
UNRAID = "net.unraid.docker.managed"
ICON = "net.unraid.docker.icon"

# my-media: template icon (tdarr) must beat the name-guess (my-media.png -> 404 on CDN)
# sonarr: managed but no icon label -> name-guess sonarr.png
# broken-icon: label points at a dead URL -> frontend letter fallback
# postgres: only a blacklisted port -> filtered out entirely
CONTAINERS = [
    {"Id": "a" * 64, "Names": ["/my-media"], "Image": "jellyfin/jellyfin:10.9.11@sha256:abc",
     "State": "running",
     "Labels": {UNRAID: "/boot/config/plugins/dockerMan/templates-user/my-media.xml", ICON: TDARR},
     "Ports": [{"IP": "0.0.0.0", "PrivatePort": 8096, "PublicPort": 39871, "Type": "tcp"}]},
    {"Id": "b" * 64, "Names": ["/sonarr"], "Image": "ghcr.io/hotio/sonarr:latest",
     "State": "running",
     "Labels": {UNRAID: "/boot/config/plugins/dockerMan/templates-user/sonarr.xml"},
     "Ports": [{"IP": "0.0.0.0", "PrivatePort": 8989, "PublicPort": 39872, "Type": "tcp"}]},
    {"Id": "c" * 64, "Names": ["/broken-icon"], "Image": "linuxserver/ddclient:latest",
     "State": "running",
     "Labels": {UNRAID: "/boot/config/plugins/dockerMan/templates-user/dd.xml",
                ICON: "https://invalid.example.invalid/nope.png"},
     "Ports": [{"IP": "0.0.0.0", "PrivatePort": 80, "PublicPort": 39874, "Type": "tcp"}]},
    {"Id": "d" * 64, "Names": ["/postgres"], "Image": "postgres:16",
     "State": "running",
     "Labels": {UNRAID: "/boot/config/plugins/dockerMan/templates-user/pg.xml"},
     "Ports": [{"IP": "0.0.0.0", "PrivatePort": 5432, "PublicPort": 39873, "Type": "tcp"}]},
]

PLAIN_CONTAINERS = [
    {"Id": "e" * 64, "Names": ["/my-media"], "Image": "jellyfin/jellyfin:10.9.11",
     "State": "running", "Labels": {},
     "Ports": [{"IP": "0.0.0.0", "PrivatePort": 8096, "PublicPort": 39871, "Type": "tcp"}]},
]


async def handler(reader, writer):
    await reader.readuntil(b"\r\n\r\n")
    body = json.dumps(BODY).encode()
    writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                 + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)
    await writer.drain()
    writer.close()


async def _serve(sock, body):
    global BODY
    BODY = body
    server = await asyncio.start_unix_server(handler, path=sock)
    print(f"fake dockerd on {sock}, mode={body is CONTAINERS and 'unraid' or 'plain'}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    sock, mode = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "unraid"
    asyncio.run(_serve(sock, CONTAINERS if mode == "unraid" else PLAIN_CONTAINERS))
