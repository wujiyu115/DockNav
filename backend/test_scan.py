"""Run me: python test_scan.py"""
from scan import choose, published, slug


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


def test_no_ports_no_service():
    assert choose([], {}) is None
    assert choose([(5432, 5432)], {}) is None


def test_slug():
    assert slug("CouchDB-v2.x") == "couchdb-v2-x"
    assert slug("openconnect-proxy-hk") == "openconnect-proxy-hk"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
