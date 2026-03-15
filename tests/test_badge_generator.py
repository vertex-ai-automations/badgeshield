import pytest

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
