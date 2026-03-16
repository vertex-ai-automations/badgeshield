import re

import pytest

from badgeshield import BadgeGenerator, BadgeTemplate
from badgeshield.badge_generator import BadgeBatchGenerator, BadgeGenerator
from badgeshield.utils import BadgeColor, BadgeTemplate, FrameType

BADGE_NAME = "test_output.svg"


def _badge_file(output_dir):
    return output_dir / BADGE_NAME


def test_generate_badge_basic(badge_generator, output_dir):
    """Test generating a badge with basic parameters."""
    badge_generator.generate_badge(
        left_text="flake8",
        left_color="#44cc11",
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
    )
    assert _badge_file(output_dir).exists()


def test_generate_badge_with_right_text(badge_generator, output_dir):
    """Test generating a badge with both left and right text."""
    badge_generator.generate_badge(
        left_text="flake8",
        right_text="tests",
        left_color="#44cc11",
        right_color=BadgeColor.DARK_GRAY,
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
    )
    assert _badge_file(output_dir).exists()


def test_generate_badge_with_logo(badge_generator, output_dir):
    """Test generating a badge with a logo."""
    logo_path = _badge_file(output_dir).with_name("logo.png")
    logo_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    badge_generator.generate_badge(
        left_text="flake8",
        left_color=BadgeColor.GREEN,
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
        logo=str(logo_path),
    )
    assert _badge_file(output_dir).exists()


def test_generate_badge_without_gradients_or_shadows(badge_generator, output_dir):
    """Badges should render with flat colors and no shadow filters."""

    logo_path = _badge_file(output_dir).with_name("logo.png")
    logo_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    badge_generator.generate_badge(
        left_text="flake8",
        left_color="#44cc11",
        right_text="tests",
        right_color="#222222",
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
        logo=str(logo_path),
        logo_tint="#ffffff",
    )

    assert _badge_file(output_dir).exists()

    render_context = badge_generator._last_render_context
    assert render_context is not None

    assert render_context["left_color"] == "#44cc11"
    assert render_context["right_color"] == "#222222"
    assert "gradient_defs" not in render_context
    assert "drop_shadow" not in render_context


def test_circle_badge_renders_flat_colors(output_dir):
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE, log_level="DEBUG")

    generator.generate_badge(
        left_text="circle",
        left_color="#123456",
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
    )

    context = generator._last_render_context
    assert context is not None

    assert context["left_color"] == "#123456"
    assert "gradient_defs" not in context
    assert "drop_shadow" not in context


def test_circle_frame_badge_renders_without_effects(output_dir):
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME, log_level="DEBUG")

    generator.generate_badge(
        left_text="framed",
        left_color="#abcdef",
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
        frame=FrameType.FRAME1,
    )

    context = generator._last_render_context
    assert context is not None

    assert context["left_color"] == "#abcdef"
    assert "gradient_defs" not in context
    assert "drop_shadow" not in context


def test_generate_badge_with_links(badge_generator, output_dir):
    """Test generating a badge with left and right links."""
    badge_generator.generate_badge(
        left_text="flake8",
        left_color="#44cc11",
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
        left_link="https://example.com/build",
        right_link="https://example.com/status",
    )
    assert _badge_file(output_dir).exists()


def test_generate_badge_with_titles(badge_generator, output_dir):
    """Test generating a badge with left and right titles."""
    badge_generator.generate_badge(
        left_text="flake8",
        left_color="#44cc11",
        badge_name=BADGE_NAME,
        output_path=str(output_dir),
        left_title="Build Status",
        right_title="Test Coverage",
    )
    assert _badge_file(output_dir).exists()


def test_text_width_fallback_handles_wide_characters(monkeypatch):
    """Fallback width estimation should differentiate wide and narrow glyphs."""

    from badgeshield import badge_generator as badge_module

    monkeypatch.setattr(badge_module, "ImageFont", None)

    generator = BadgeGenerator(log_level="DEBUG")
    wide_width = generator._calculate_text_width("WWW")
    narrow_width = generator._calculate_text_width("iii")

    assert wide_width > narrow_width
    assert wide_width >= len("WWW")


def test_invalid_log_level():
    """Test initializing the generator with an invalid log level."""
    with pytest.raises(ValueError):
        BadgeGenerator(log_level="INVALID")


def test_generate_badge_with_empty_left_text(badge_generator, output_dir):
    """Empty left text should raise a ValueError."""
    with pytest.raises(ValueError):
        badge_generator.generate_badge(
            left_text="",
            left_color="#44cc11",
            badge_name=BADGE_NAME,
            output_path=str(output_dir),
        )


def test_generate_badge_with_empty_colors(badge_generator, output_dir):
    """Empty colors should raise a ValueError."""
    with pytest.raises(ValueError):
        badge_generator.generate_badge(
            left_text="flake8",
            left_color="",
            badge_name=BADGE_NAME,
            output_path=str(output_dir),
        )


def test_generate_badge_with_invalid_logo_path(badge_generator, output_dir):
    """Invalid logo paths should raise a ValueError."""
    with pytest.raises(ValueError):
        badge_generator.generate_badge(
            left_text="flake8",
            left_color="#44cc11",
            badge_name=BADGE_NAME,
            output_path=str(output_dir),
            logo="missing-logo.png",
        )


def test_generate_badge_with_empty_output_path(badge_generator):
    """Test generating a badge with an empty output path."""
    with pytest.raises(ValueError):
        badge_generator.generate_badge(
            left_text="flake8",
            left_color="#44cc11",
            badge_name=BADGE_NAME,
            output_path="",
        )


def test_batch_generator_propagates_errors(output_dir):
    """Batch generation should surface failures instead of printing them."""

    batch_generator = BadgeBatchGenerator(max_workers=1, log_level="DEBUG")

    badges = [
        {
            "left_text": "",
            "left_color": "#ffffff",
            "badge_name": "one.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
    ]

    with pytest.raises(RuntimeError):
        batch_generator.generate_batch(badges)


def test_path_traversal_rejected(badge_generator, output_dir):
    """badge_name with directory traversal must raise ValueError."""
    with pytest.raises(ValueError, match="traversal"):
        badge_generator.generate_badge(
            left_text="test",
            left_color="#44cc11",
            badge_name="../escape.svg",
            output_path=str(output_dir),
        )


def test_absolute_badge_name_rejected(badge_generator, output_dir):
    """Absolute paths in badge_name must raise ValueError."""
    with pytest.raises(ValueError):
        badge_generator.generate_badge(
            left_text="test",
            left_color="#44cc11",
            badge_name="/tmp/evil.svg",
            output_path=str(output_dir),
        )


def test_circle_font_size_stays_in_range():
    """Font size for circle badges must remain in the 8-35pt range."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE)
    # Short text — should be near max size
    assert 8 <= generator._calculate_font_size("Hi") <= 35
    # Longer text — should shrink but stay above minimum
    assert 8 <= generator._calculate_font_size("A longer badge label") <= 35
    # Font size must not increase as text gets longer
    assert generator._calculate_font_size("Hi") >= generator._calculate_font_size("A longer badge label")


def test_batch_progress_callback_called_for_each_badge(output_dir):
    """progress_callback must be called once per badge regardless of success/failure."""
    called_with = []

    batch_generator = BadgeBatchGenerator(max_workers=1)
    badges = [
        {
            "left_text": "badge1",
            "left_color": "#44cc11",
            "badge_name": "one.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        },
        {
            "left_text": "badge2",
            "left_color": "#0000ff",
            "badge_name": "two.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        },
    ]

    batch_generator.generate_batch(badges, progress_callback=lambda name: called_with.append(name))

    assert len(called_with) == 2
    assert set(called_with) == {"one.svg", "two.svg"}


def test_batch_failures_stored_on_instance(output_dir):
    """_failures must contain (badge_name, error_str) tuples for each failed badge."""
    batch_generator = BadgeBatchGenerator(max_workers=1)
    badges = [
        {
            "left_text": "",  # empty text triggers ValueError
            "left_color": "#ffffff",
            "badge_name": "bad.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
    ]

    with pytest.raises(RuntimeError):
        batch_generator.generate_batch(badges)

    assert len(batch_generator._failures) == 1
    assert batch_generator._failures[0][0] == "bad.svg"


def test_batch_happy_path(output_dir):
    """Batch generation should create all submitted badge files."""
    batch_generator = BadgeBatchGenerator(max_workers=2)
    badges = [
        {
            "left_text": f"badge{i}",
            "left_color": "#44cc11",
            "badge_name": f"badge{i}.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
        for i in range(3)
    ]
    batch_generator.generate_batch(badges)
    for i in range(3):
        assert (output_dir / f"badge{i}.svg").exists()


def test_concurrent_batch_no_corruption(output_dir):
    """Concurrent batch with multiple workers must produce non-empty files."""
    batch_generator = BadgeBatchGenerator(max_workers=3)
    badges = [
        {
            "left_text": f"t{i}",
            "left_color": "#0000ff",
            "badge_name": f"t{i}.svg",
            "output_path": str(output_dir),
            "template": BadgeTemplate.DEFAULT,
        }
        for i in range(6)
    ]
    batch_generator.generate_batch(badges)
    for i in range(6):
        path = output_dir / f"t{i}.svg"
        assert path.exists()
        assert path.stat().st_size > 0


def test_circle_template_creates_svg_with_circle(output_dir):
    """CIRCLE template SVG must contain a <circle element."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE)
    generator.generate_badge(
        left_text="test",
        left_color="#123456",
        badge_name="circle.svg",
        output_path=str(output_dir),
    )
    content = (output_dir / "circle.svg").read_text()
    assert "<circle" in content


def test_circle_frame_with_valid_frame(output_dir):
    """CIRCLE_FRAME template with a valid FrameType must create the SVG."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME)
    generator.generate_badge(
        left_text="framed",
        left_color="#abcdef",
        badge_name="framed.svg",
        output_path=str(output_dir),
        frame=FrameType.FRAME1,
    )
    assert (output_dir / "framed.svg").exists()


def test_circle_frame_without_frame_raises(output_dir):
    """CIRCLE_FRAME template without frame parameter must raise ValueError."""
    generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME)
    with pytest.raises(ValueError, match="frame"):
        generator.generate_badge(
            left_text="framed",
            left_color="#abcdef",
            badge_name="framed.svg",
            output_path=str(output_dir),
        )


def test_badge_name_missing_svg_suffix(badge_generator, output_dir):
    """badge_name without .svg extension must raise ValueError."""
    with pytest.raises(ValueError, match=".svg"):
        badge_generator.generate_badge(
            left_text="test",
            left_color="#44cc11",
            badge_name="no_extension",
            output_path=str(output_dir),
        )


def test_get_base64_content_missing_file(badge_generator):
    """get_base64_content with a nonexistent file must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        badge_generator.get_base64_content("/nonexistent/path/logo.png")


def test_logo_tinting_fallback_without_pillow(monkeypatch, output_dir):
    """Without Pillow, _load_logo_image returns plain base64 without error."""
    import badgeshield.badge_generator as badge_module

    logo_path = output_dir / "logo.png"
    # Write minimal valid PNG bytes
    logo_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")

    monkeypatch.setattr(badge_module, "Image", None)

    generator = BadgeGenerator()
    result = generator._load_logo_image(str(logo_path), tint="#ff0000")
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


LOGO_PATH = "tests/fixtures/test_logo.png"

_SVG_AUDIT_PARAMS = [
    (
        BadgeTemplate.DEFAULT,
        dict(left_text="build", left_color=BadgeColor.GREEN,
             right_text="passing", right_color=BadgeColor.BLUE,
             logo=LOGO_PATH, left_link="#left", right_link="#right",
             badge_name="test.svg"),
    ),
    (
        BadgeTemplate.CIRCLE,
        dict(left_text="OK", left_color=BadgeColor.GREEN,
             logo=LOGO_PATH, left_link="#link", badge_name="test.svg"),
    ),
    (
        BadgeTemplate.CIRCLE_FRAME,
        dict(left_text="OK", left_color=BadgeColor.GREEN,
             frame=FrameType.FRAME1, logo=LOGO_PATH, badge_name="test.svg"),
    ),
]

@pytest.mark.parametrize("template,kwargs", _SVG_AUDIT_PARAMS,
                         ids=["DEFAULT", "CIRCLE", "CIRCLE_FRAME"])
def test_generated_svg_has_no_external_urls(template, kwargs, tmp_path):
    gen = BadgeGenerator(template=template)
    gen.generate_badge(output_path=str(tmp_path), **kwargs)
    svg_content = (tmp_path / "test.svg").read_text(encoding="utf-8")
    # Strip standard SVG/XLink namespace declarations before scanning for
    # external URLs — these are identifier strings, not network requests.
    stripped = re.sub(r'xmlns(?::\w+)?="https?://[^"]*"', '', svg_content)
    assert not re.search(r'https?://', stripped), \
        f"Template {template} generated SVG with external URLs"
