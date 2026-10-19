"""Run me: python test_scan.py"""
import os
import tempfile

import scan
from scan import ICON, choose, icon_for, is_unraid, published, slug, targets


def test_published_keeps_tcp_only():
    c = {"Ports": [
        {"IP": "0.0.0.0", "PrivatePort": 80, "PublicPort": 4743, "Type": "tcp"},
        {"IP": "::", "PrivatePort": 80, "PublicPort": 4743, "Type": "tcp"},
        {"PrivatePort": 6888, "Type": "udp", "PublicPort": 6888},
        {"PrivatePort": 2019, "Type": "tcp"},
    ]}
    assert published(c) == [(4743, 80)]
    assert published({}) == []


def test_probed_port_wins_over_guess():
    ports = [(8887, 8887), (8888, 8443)]
    assert choose(ports, {8888: "http"}) == (8888, "http", True)
    assert choose(ports, {}) == (8887, "http", False)


def test_probe_beats_blacklist():
    # 5432 is blacklisted, but a real HTTP answer on it still wins
    assert choose([(5432, 5432)], {5432: "http"}) == (5432, "http", True)
    assert choose([(5432, 5432)], {}) is None


def test_guess_prefers_web_container_port():
    assert choose([(9000, 9000), (2080, 80)], {}) == (2080, "http", False)
    assert choose([(3336, 5000)], {}) == (3336, "http", False)


def test_https_scheme_survives():
    assert choose([(8443, 443)], {8443: "https"}) == (8443, "https", True)


def test_every_http_port_is_kept():
    # magpie publishes two web UIs; both must survive, the better-ranked container port first
    ports = [(3425, 443), (3426, 80)]
    assert targets(ports, {3425: "https", 3426: "http"}) == [
        (3426, "http", True), (3425, "https", True)]
    # the non-HTTP sibling is dropped, not merged into the list
    assert targets([(3425, 443), (3427, 5432)], {3425: "http"}) == [(3425, "http", True)]
    # a guess stays a single entry so unprobed containers do not sprout fake links
    assert targets([(3425, 443), (3426, 80)], {}) == [(3426, "http", False)]


def test_no_ports_no_service():
    assert choose([], {}) is None
    assert choose([(5432, 5432)], {}) is None


def test_slug():
    assert slug("CouchDB-v2.x") == "couchdb-v2-x"
    assert slug("openconnect-proxy-hk") == "openconnect-proxy-hk"


def test_is_unraid():
    assert is_unraid([{"Labels": {"net.unraid.docker.managed": "/boot/config/plugins/dockerMan/templates-user/jf.xml"}}])
    assert not is_unraid([{"Labels": {"com.docker.compose.project": "x"}}])
    assert not is_unraid([{}])
    assert not is_unraid([])


def test_unraid_icon_label_wins():
    c = {"Labels": {"net.unraid.docker.icon": "https://raw.githubusercontent.com/x/jf.png"}}
    assert icon_for(c, "jellyfin", True) == "https://raw.githubusercontent.com/x/jf.png"


def test_unraid_icon_falls_back():
    # local path label is unusable from the browser, and missing label / non-unraid host guess by name
    assert icon_for({"Labels": {"net.unraid.docker.icon": "/mnt/user/icons/jf.png"}}, "jellyfin", True) == ICON.format("jellyfin")
    assert icon_for({"Labels": {}}, "jellyfin", True) == ICON.format("jellyfin")
    assert icon_for({"Labels": {"net.unraid.docker.icon": "https://x/y.png"}}, "jellyfin", False) == ICON.format("jellyfin")


def test_unraid_local_icon_via_cache(monkeypatch=None):
    # unraid copies the local icon into its cache dir; we serve it from there
    with tempfile.TemporaryDirectory() as d:
        saved = scan.UNRAID_ICONS
        scan.UNRAID_ICONS = d
        try:
            open(os.path.join(d, "bark-icon.png"), "w").close()
            # label points at a local file on the host - unreachable from the browser
            c = {"Labels": {"net.unraid.docker.icon": "/mnt/user/appdata/icons/bark.png"}}
            assert icon_for(c, "bark", True) == "/api/icon/bark-icon.png"
            # empty label but unraid cached one from the template anyway
            assert icon_for({"Labels": {}}, "bark", True) == "/api/icon/bark-icon.png"
            # no cached copy -> name-guess fallback
            assert icon_for({"Labels": {"net.unraid.docker.icon": "/mnt/user/x.png"}}, "nosuch", True) == ICON.format("nosuch")
        finally:
            scan.UNRAID_ICONS = saved


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
