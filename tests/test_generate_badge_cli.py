import json
from argparse import Namespace
from pathlib import Path

import pytest

from badgeshield.generate_badge_cli import (
    validate_batch_badge_args,
    validate_single_badge_args,
)
from badgeshield.utils import BadgeTemplate


def _base_single_args(output_dir: Path) -> Namespace:
    return Namespace(
        left_text="cli",
        left_color="red",
        right_text=None,
        right_color="light_blue",
        output_path=str(output_dir),
        badge_name="cli.svg",
        template=BadgeTemplate.DEFAULT.name,
        logo=None,
        frame=None,
        left_link=None,
        right_link=None,
        id_suffix="",
        left_title=None,
        right_title=None,
        logo_tint=None,
        log_level="INFO",
    )


def test_single_validation_accepts_badge_color_names(output_dir):
    args = _base_single_args(output_dir)

    validate_single_badge_args(args)

    assert args.left_color == "#FF0000"
    assert args.right_color == "#6666FF"


def test_single_validation_requires_frame_for_circle_frame(output_dir):
    args = _base_single_args(output_dir)
    args.template = BadgeTemplate.CIRCLE_FRAME.name

    with pytest.raises(ValueError):
        validate_single_badge_args(args)


def test_batch_validation_normalizes_colors(tmp_path):
    config_path = tmp_path / "config.json"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    config_path.write_text(
        json.dumps(
            [
                {"badge_name": "one.svg", "left_text": "one", "left_color": "green"},
                {
                    "badge_name": "two.svg",
                    "left_text": "two",
                    "left_color": "#123456",
                    "right_color": "magenta",
                },
            ]
        )
    )

    args = Namespace(
        config_file=str(config_path),
        output_path=str(output_dir),
        template=BadgeTemplate.DEFAULT.name,
    )

    configs = validate_batch_badge_args(args)

    assert configs[0]["left_color"] == "#00FF00"
    assert configs[1]["right_color"] == "#FF00FF"
    assert args.output_path == str(output_dir.resolve())


def test_batch_validation_requires_left_color(tmp_path):
    config_path = tmp_path / "config.json"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    config_path.write_text(json.dumps([{"badge_name": "one.svg", "left_text": "one"}]))

    args = Namespace(
        config_file=str(config_path),
        output_path=str(output_dir),
        template=BadgeTemplate.DEFAULT.name,
    )

    with pytest.raises(ValueError):
        validate_batch_badge_args(args)
