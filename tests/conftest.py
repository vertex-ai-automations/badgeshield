import struct
import zlib
from pathlib import Path

import pytest

from badgeshield import BadgeGenerator, BadgeTemplate


@pytest.fixture
def badge_generator():
    return BadgeGenerator(template=BadgeTemplate.DEFAULT)


@pytest.fixture
def output_dir(tmp_path):
    # Return Path (not str) — existing tests use path division: output_dir / BADGE_NAME
    return tmp_path


# Network audit performed 2026-03-15: no dependency makes outbound calls.
@pytest.fixture
def block_network(monkeypatch):
    import socket
    def blocked(*args, **kwargs):
        raise OSError("Network blocked by test fixture")
    monkeypatch.setattr(socket, "socket", blocked)


@pytest.fixture(scope="session", autouse=True)
def test_logo_fixture():
    """Create tests/fixtures/test_logo.png if it doesn't exist."""
    path = Path(__file__).parent / "fixtures" / "test_logo.png"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        def chunk(name, data):
            c = struct.pack('>I', len(data)) + name + data
            return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
        idat = chunk(b'IDAT', zlib.compress(b'\x00\x00\x00\x00\x00'))
        iend = chunk(b'IEND', b'')
        path.write_bytes(sig + ihdr + idat + iend)
