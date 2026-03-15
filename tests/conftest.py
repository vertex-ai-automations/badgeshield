import pytest

from badgeshield import BadgeGenerator, BadgeTemplate


@pytest.fixture
def badge_generator():
    return BadgeGenerator(template=BadgeTemplate.DEFAULT)


@pytest.fixture
def output_dir(tmp_path):
    # Return Path (not str) — existing tests use path division: output_dir / BADGE_NAME
    return tmp_path
