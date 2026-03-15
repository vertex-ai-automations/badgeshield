import base64
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from pylogshield import LogLevel, get_logger
from jinja2 import (
    Environment,
    PackageLoader,
    Template,
    TemplateNotFound,
    select_autoescape,
)

from .utils import BadgeColor, BadgeTemplate, FrameType

try:
    from PIL import Image, ImageColor, ImageFont
except ImportError:
    Image = ImageColor = ImageFont = None


class BadgeBatchGenerator:
    """Generate many badges concurrently using a thread pool."""

    def __init__(
        self, max_workers: int = 5, log_level: Union[LogLevel, str] = LogLevel.INFO
    ):
        """Initializes the batch generator with a specified number of worker threads."""
        self.max_workers = max_workers
        self.log_level = log_level
        self.logger = get_logger(name="badgeshield.batch", log_level=log_level)

    def generate_batch(self, badges: List[Dict]) -> None:
        """Generate multiple badges concurrently.

        Parameters
        ----------
        badges: A list of dictionaries containing keyword arguments accepted by :meth:`BadgeGenerator.generate_badge`.

        Raises
        ------
        ValueError:
            Propagated if any badge definition is invalid.
        FileNotFoundError:
            Propagated when required assets (e.g., logos) are missing.
        RuntimeError:
            Aggregated failures when one or more badges cannot be generated.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_badge = {
                executor.submit(self._generate_single_badge, **badge): badge
                for badge in badges
            }
            errors: List[Tuple[Dict, Exception]] = []

            for future in as_completed(future_to_badge):
                badge = future_to_badge[future]
                try:
                    future.result()  # This will raise any exceptions that occurred during badge generation
                except Exception as exc:
                    self.logger.error(
                        "Failed to generate badge",
                        extra={
                            "badge": badge.get("badge_name", badge),
                            "error": str(exc),
                        },
                    )
                    errors.append((badge, exc))
                else:
                    self.logger.info(
                        "Successfully generated badge",
                        extra={
                            "badge": badge.get("badge_name", badge.get("left_text"))
                        },
                    )

            if errors:
                failure_summaries = ", ".join(
                    f"{failed_badge.get('badge_name', failed_badge.get('left_text', 'unknown'))}: {error}"
                    for failed_badge, error in errors
                )
                raise RuntimeError(
                    f"Failed to generate {len(errors)} badge(s): {failure_summaries}"
                )

    def _generate_single_badge(
        self,
        left_text: str,
        left_color: BadgeColor,
        badge_name: str,
        template: Optional[BadgeTemplate] = BadgeTemplate.DEFAULT,
        output_path: Optional[str] = None,
        right_text: Optional[str] = None,
        right_color: Optional[BadgeColor] = None,
        logo: Optional[str] = None,
        frame: Optional[Union[FrameType, str]] = None,
        left_link: Optional[str] = None,
        right_link: Optional[str] = None,
        id_suffix: str = "",
        left_title: Optional[str] = None,
        right_title: Optional[str] = None,
        logo_tint: Optional[Union[str, BadgeColor]] = None,
    ) -> None:
        """Wrapper to generate a single badge using :class:`BadgeGenerator`.

        All arguments are forwarded directly to :meth:`BadgeGenerator.generate_badge`.
        Any exception raised during badge creation is propagated to the caller so that
        batch execution can report the failure.
        """
        generator = BadgeGenerator(template=template, log_level=self.log_level)
        generator.generate_badge(
            left_text=left_text,
            left_color=left_color,
            badge_name=badge_name,
            output_path=output_path,
            right_text=right_text,
            right_color=right_color,
            logo=logo,
            frame=frame,
            left_link=left_link,
            right_link=right_link,
            id_suffix=id_suffix,
            left_title=left_title,
            right_title=right_title,
            logo_tint=logo_tint,
        )


_DEFAULT_FONT_SIZE = 110
_FALLBACK_DEFAULT_CHAR_WIDTH = 8
_FALLBACK_EAST_ASIAN_CHAR_WIDTH = 16
_FALLBACK_CHAR_WIDTHS = {
    " ": 4,
    "-": 6,
    "_": 6,
    ":": 4,
    ";": 4,
    ".": 4,
    ",": 4,
    "!": 4,
    "?": 7,
    "'": 3,
    '"': 5,
    "`": 4,
    "|": 4,
    "/": 6,
    "\\": 6,
    "(": 5,
    ")": 5,
    "[": 5,
    "]": 5,
    "{": 6,
    "}": 6,
    "i": 4,
    "l": 4,
    "I": 4,
    "t": 5,
    "f": 5,
    "j": 5,
    "r": 6,
    "1": 5,
    "0": 7,
    "2": 7,
    "3": 7,
    "4": 7,
    "5": 7,
    "6": 7,
    "7": 7,
    "8": 7,
    "9": 7,
    "M": 11,
    "W": 11,
    "m": 10,
    "w": 10,
    "@": 12,
    "#": 9,
    "$": 9,
    "%": 12,
    "&": 9,
    "+": 8,
    "=": 8,
}


class BadgeGenerator:
    """Class to generate custom badges for GitLab."""

    _template_cache = {}

    def __init__(
        self,
        template: BadgeTemplate = BadgeTemplate.DEFAULT,
        log_level: Union[LogLevel, str] = LogLevel.WARNING,
    ) -> None:
        """Initializes the BadgeGenerator with a specified template and log level.

        Parameters
        ----------
        template:
            The name of the SVG template file.
        log_level:
            The logging level. Options are 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
        """

        self.template_name = str(template)
        self._setup_jinja2_env()
        self.logger = get_logger(name="badgeshield", log_level=log_level)

    def _setup_jinja2_env(self) -> None:
        """Sets up the Jinja2 environment."""
        self._jinja2_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=PackageLoader("badgeshield", "."),
            autoescape=select_autoescape(["svg"]),
        )

    def _get_template(self, template_name: str) -> Optional[Template]:
        """Return the cached Jinja2 template, loading it if necessary.

        Parameters
        ----------
        template_name:
            Name of the template file packaged with ``badgeshield``.

        Returns
        -------
        Template:
            A compiled Jinja2 template ready for rendering, or ``None`` if the template cannot be located.
        """
        try:
            if template_name not in self._template_cache:
                self._template_cache[template_name] = self._jinja2_env.get_template(
                    template_name
                )
            return self._template_cache[template_name]
        except TemplateNotFound:
            self.logger.error(
                f"Template {self.template_name} not found in package 'badgeshield'"
            )
            return

    @staticmethod
    def is_valid_hex_color(color: str) -> bool:
        """Validate if a string is a valid hex color."""
        return bool(re.match(r"^#([A-Fa-f0-9]{6})$", color))

    def _get_font(self) -> Optional["ImageFont.ImageFont"]:
        """Return a lazily instantiated font object for text measurements."""

        if ImageFont is None:
            return None

        if not hasattr(self, "_badge_font"):
            try:
                self._badge_font = ImageFont.truetype("DejaVuSans.ttf", 110)
            except OSError:
                self._badge_font = ImageFont.load_default()
        return self._badge_font

    @staticmethod
    def validate_color(color: Union[BadgeColor, str], color_name: str) -> str:
        """Validate the color input."""
        if isinstance(color, BadgeColor):
            return color.value
        if isinstance(color, str):
            if BadgeGenerator.is_valid_hex_color(color):
                return color
            try:
                enum_color = BadgeColor[color.upper()]
            except KeyError as exc:
                raise ValueError(
                    f"Invalid {color_name}: {color}. Must be a hex color code (e.g., #00FF00) or a member of BadgeColor."
                ) from exc
            return enum_color.value
        raise TypeError(
            f"{color_name} must be a hex string or an instance of BadgeColor, not {type(color).__name__}."
        )

    @staticmethod
    def validate_frame(frame: Union[FrameType, str]) -> str:
        """Validate the frame input."""
        if frame is None:
            raise ValueError(
                "The 'frame' parameter is required when using the CIRCLE_FRAME template."
            )
        if isinstance(frame, FrameType):
            return frame.value
        if isinstance(frame, str):
            try:
                # Convert the frame string to a FrameType enum instance
                enum_frame = FrameType[frame.upper()]
            except KeyError as exc:
                raise ValueError(
                    f"Invalid frame type '{frame}'. Must be one of {list(FrameType.__members__.keys())}."
                ) from exc
            return enum_frame.value
        raise TypeError(
            f"frame must be an instance of FrameType or str of valid FrameType name, not {type(frame).__name__}."
        )

    def validate_inputs(
        self,
        left_text: str,
        left_color: Union[BadgeColor, str],
        output_path: Optional[str],
        badge_name: str,
        right_text: Optional[str] = None,
        right_color: Optional[Union[BadgeColor, str]] = None,
        logo: Optional[str] = None,
        frame: Optional[FrameType] = None,
    ) -> Tuple[str, str, str, Optional[str]]:
        """Validate parameters shared by the different badge templates.

        Returns
        -------
        tuple:
            Containing the normalized left color, right color, output directory, and frame asset path (when applicable).

        Raises
        ------
        ValueError:
            If any argument is missing or malformed (e.g., empty text, invalid output directory, missing logo file, incorrect badge name suffix).
        TypeError:
            When a value has the wrong type for its expected enum/string input.
        """
        if not left_text:
            raise ValueError("left_text cannot be empty.")

        # Validate the frame parameter if the CIRCLE_FRAME template is used
        frame_value: Optional[str]
        if self.template_name == BadgeTemplate.CIRCLE_FRAME.value:
            frame_value = self.validate_frame(frame)
        elif isinstance(frame, FrameType):
            frame_value = frame.value
        else:
            frame_value = frame

        # Validate color codes
        left_color_value = self.validate_color(left_color, "left_color")
        right_color_value = (
            self.validate_color(right_color, "right_color")
            if right_color
            else left_color_value
        )

        # Validate logo file existence when a logo path is provided
        if logo:
            logo_path = Path(logo)
            if not logo_path.is_absolute():
                logo_path = Path(self.local_path(logo))
            if not logo_path.is_file():
                raise ValueError(f"Logo file {logo} does not exist.")

        # Use current directory if output_path is not provided
        if output_path is not None:
            if output_path == "":
                raise ValueError("output_path cannot be an empty string.")
            output_path = os.path.abspath(output_path)
        else:
            output_path = os.getcwd()

        # Ensure output path is a directory
        if not os.path.isdir(output_path):
            raise ValueError(f"Output path {output_path} is not a valid directory.")

        # Ensure badge_name is valid
        if not badge_name.endswith(".svg"):
            raise ValueError(
                f"badge_name {badge_name} is not valid, must end with '.svg' (e.g., 'badge.svg')."
            )

        return left_color_value, right_color_value, output_path, frame_value

    def local_path(self, relative_path: str) -> str:
        """Get the absolute path for a given relative path.

        Parameters
        ----------
        relative_path:
            The relative path to resolve.

        Returns
        -------
        str:
            The absolute resolved path.
        """
        path_obj = Path(relative_path)
        if path_obj.is_absolute():
            return str(path_obj)

        base_path = Path(__file__).resolve().parent / path_obj
        if base_path.exists():
            return str(base_path)

        return str((Path.cwd() / path_obj).resolve())

    def get_base64_content(self, bin_file: str) -> str:
        """Get the base64 encoded content of a binary file."""
        bin_path = Path(bin_file)
        if not bin_path.is_absolute():
            bin_path = Path(self.local_path(bin_file))
        try:
            with bin_path.open(
                "rb", buffering=16 * 1024
            ) as f:  # Use a larger buffer for efficient file I/O
                data = f.read()
            return base64.b64encode(data).decode()
        except FileNotFoundError:
            self.logger.error(f"File not found: {bin_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading file {bin_path}: {e}")
            raise

    def _calculate_text_width(self, text: Optional[str]) -> int:
        """Calculate text width using real font metrics when Pillow is available."""

        if not text:
            return 0

        font = self._get_font()
        if font:
            try:
                bbox = font.getbbox(text)
            except AttributeError:
                try:
                    width = int(font.getlength(text))  # type: ignore[attr-defined]
                except Exception:
                    width = len(text) * 70
                    bbox = None
                else:
                    bbox = None
            else:
                width = bbox[2] - bbox[0]

            font_size = getattr(font, "size", None)
            if not font_size:
                font_size = self._infer_font_size(font, bbox)

            scale_factor = _DEFAULT_FONT_SIZE / float(font_size) if font_size else 1.0
            scaled_width = max(int(round(width * scale_factor * 0.1)), len(text))
            self.logger.debug(
                "Calculated text width with font metrics",
                extra={
                    "text": text,
                    "width": scaled_width,
                    "font_size": font_size,
                    "scale_factor": scale_factor,
                },
            )
            return scaled_width

        estimated_width = self._fallback_text_width(text)
        self.logger.debug(
            "Calculated text width with fallback estimation",
            extra={"text": text, "width": estimated_width},
        )
        return estimated_width

    @staticmethod
    def _infer_font_size(
        font: "ImageFont.ImageFont", bbox: Optional[Tuple[int, int, int, int]]
    ) -> Optional[float]:
        """Approximate the font size for bitmap fonts lacking explicit size metadata."""

        try:
            ascent, descent = font.getmetrics()
        except Exception:
            ascent = descent = 0

        metrics_height = ascent + descent
        if metrics_height:
            return float(metrics_height)

        if bbox is not None:
            height = bbox[3] - bbox[1]
            if height > 0:
                return float(height)

        try:
            bbox_sample = font.getbbox("Hg")
        except Exception:
            return None

        height = bbox_sample[3] - bbox_sample[1]
        return float(height) if height > 0 else None

    @staticmethod
    def _fallback_text_width(text: str) -> int:
        """Estimate text width heuristically when Pillow is unavailable."""

        estimated_width = 0
        for char in text:
            if unicodedata.east_asian_width(char) in {"F", "W"}:
                estimated_width += _FALLBACK_EAST_ASIAN_CHAR_WIDTH
                continue

            estimated_width += _FALLBACK_CHAR_WIDTHS.get(
                char, _FALLBACK_DEFAULT_CHAR_WIDTH
            )

        # Provide a small buffer so the text is never squished.
        padded_width = max(int(round(estimated_width * 1.05)), len(text))
        return padded_width

    def _calculate_font_size(
        self,
        text: str,
        max_size: int = 35,
        min_size: int = 8,
        circle_diameter: int = 180,
    ) -> int:
        """Calculates an appropriate font size based on the length of the text and the fixed circle size."""
        text_length = len(text)
        # Assuming that the circle's diameter is 90 units (as the circle is centered with a radius of 45)
        # The font size should shrink as the text length increases to ensure it fits within the circle.
        font_size = max(min(max_size, circle_diameter // text_length), min_size)
        return font_size

    def _calculate_logo_size(self, circle_radius: int) -> Tuple[int, int]:
        """Calculates the size of the logo to fit within the circle, accounting for the border width."""
        adjusted_radius = circle_radius
        logo_diameter = adjusted_radius * 2
        return (
            logo_diameter,
            logo_diameter,
        )  # width and height are the same for a square logo

    def _load_logo_image(
        self, logo: str, tint: Optional[Union[str, BadgeColor]]
    ) -> Optional[str]:
        """Load a logo from disk, optionally tinting it before returning a base64 string."""

        if not logo:
            return None

        normalized_tint: Optional[str] = None
        if tint is not None:
            normalized_tint = self.validate_color(tint, "logo_tint")

        if Image is None or normalized_tint is None:
            return self.get_base64_content(logo)

        logo_path = Path(logo)
        if not logo_path.is_absolute():
            logo_path = Path(self.local_path(logo))

        try:
            with Image.open(logo_path).convert("RGBA") as img:
                tint_rgba = ImageColor.getcolor(normalized_tint, "RGBA")
                solid = Image.new("RGBA", img.size, tint_rgba)
                alpha = img.split()[3] if "A" in img.getbands() else None
                if alpha is not None:
                    solid.putalpha(alpha)
                buffered = BytesIO()
                solid.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode()
        except Exception as exc:
            self.logger.warning(
                "Falling back to untinted logo due to processing error",
                extra={"logo": str(logo_path), "error": str(exc)},
            )
            return self.get_base64_content(logo)

    def _render_badge_content(
        self,
        left_text: str,
        left_color: str,
        right_text: Optional[str],
        right_color: Optional[str],
        logo: Optional[str],
        frame: Optional[str],
        left_link: Optional[str],
        right_link: Optional[str],
        id_suffix: str,
        left_title: Optional[str],
        right_title: Optional[str],
        logo_tint: Optional[Union[str, BadgeColor]],
    ) -> str:
        """Renders the badge content using the provided template and parameters.

        Parameters
        ----------
        left_text:
            Text for the left side of the badge.
        left_color:
            Background color for the left side of the badge.
        right_text:
            Text for the right side of the badge. Defaults to None.
        right_color:
            Background color for the right side of the badge. Defaults to None.
        logo:
            URL or path to a logo image. Defaults to None.
        left_link:
            Link for the left side of the badge. Defaults to None.
        right_link:
            Link for the right side of the badge. Defaults to None.
        id_suffix:
            Suffix to add to the ID of the badge elements. Defaults to ''.
        left_title:
            Title text for the left side of the badge. Defaults to None.
        right_title:
            Title text for the right side of the badge. Defaults to None.
        logo_tint:
            Hex color or :class:`BadgeColor` applied to the logo silhouette.

        Returns
        -------
        str:
            The rendered badge content as a string.
        """

        logo_data = self._load_logo_image(logo, logo_tint) if logo else None

        if self.template_name == BadgeTemplate.DEFAULT.value:
            left_text_width = self._calculate_text_width(left_text)
            right_text_width = (
                self._calculate_text_width(right_text) if right_text else 0
            )
            logo_width = 14 if logo else 0
            logo_padding = 3 if logo else 0
            text_padding = 10
            left_width = left_text_width + text_padding + logo_width + logo_padding
            right_width = right_text_width + text_padding if right_text else 0
            total_width = left_width + right_width + (text_padding if right_text else 0)
            return self._jinja2_env.get_template(self.template_name).render(
                left_text=left_text,
                right_text=right_text,
                left_color=left_color,
                right_color=right_color if right_text else left_color,
                left_text_width=left_text_width,
                right_text_width=right_text_width,
                logo=logo_data,
                left_link=left_link,
                right_link=right_link,
                id_suffix=id_suffix,
                left_width=left_width,
                right_width=right_width,
                logo_width=logo_width,
                logo_padding=logo_padding,
                text_padding=text_padding,
                total_width=total_width,
                left_title=left_title,
                right_title=right_title,
            )
        if self.template_name == BadgeTemplate.CIRCLE.value:
            # Calculate the appropriate font size
            font_size = self._calculate_font_size(left_text)
            return self._jinja2_env.get_template(self.template_name).render(
                left_text=left_text,
                right_text=right_text,
                left_color=left_color,
                id_suffix=id_suffix,
                logo=logo_data,
                left_link=left_link,
                left_title=left_title,
                font_size=font_size,
            )

        if self.template_name == BadgeTemplate.CIRCLE_FRAME.value:
            circle_radius = 35
            logo_width, logo_height = self._calculate_logo_size(circle_radius)

            # Calculate the appropriate font size
            font_size = self._calculate_font_size(
                left_text, circle_diameter=circle_radius * 2
            )

            frame_data = self.get_base64_content(frame) if frame else None
            return self._jinja2_env.get_template(self.template_name).render(
                left_text=left_text,
                left_color=left_color,
                logo=logo_data,
                frame=frame_data,
                left_link=left_link,
                left_title=left_title,
                font_size=font_size,
                logo_width=logo_width,
                logo_height=logo_height,
                id_suffix=id_suffix,
            )

    def generate_badge(
        self,
        left_text: str,
        left_color: Union[BadgeColor, str],
        badge_name: str,
        output_path: Optional[str] = None,
        right_text: Optional[str] = None,
        right_color: Optional[Union[BadgeColor, str]] = None,
        logo: Optional[str] = None,
        frame: Optional[FrameType] = None,
        left_link: Optional[str] = None,
        right_link: Optional[str] = None,
        id_suffix: str = "",
        left_title: Optional[str] = None,
        right_title: Optional[str] = None,
        logo_tint: Optional[Union[str, BadgeColor]] = None,
    ) -> None:
        """Generates a badge based on the provided parameters and saves it as an SVG file.

        Parameters
        ----------
        left_text:
            Text for the left side of the badge.
        left_color:
            Background color for the left side of the badge.
        badge_name:
            The name of the badge file to be generated.
        output_path:
            Output path for the generated badge SVG file.
        right_text:
            Text for the right side of the badge. Defaults to None.
        right_color:
            Background color for the right side of the badge. Defaults to None.
        logo:
            URL or path to a logo image. Defaults to None.
        frame:
            Frame template to use, either as a FrameType or its name/path.
        left_link:
            Link for the left side of the badge. Defaults to None.
        right_link:
            Link for the right side of the badge. Defaults to None.
        id_suffix:
            Suffix to add to the ID of the badge elements. Defaults to ''.
        left_title:
            Title text for the left side of the badge. Defaults to None.
        right_title:
            Title text for the right side of the badge. Defaults to None.
        logo_tint:
            Optional color applied to monochrome the logo.

        Raises
        ------
        ValueError:
            If the output_path is empty or invalid.
        TypeError:
            If frame is not an instance of FrameType.
        """
        left_color_value, right_color_value, output_path, frame = self.validate_inputs(
            left_text,
            left_color,
            output_path,
            badge_name,
            right_text,
            right_color,
            logo,
            frame,
        )
        full_path = os.path.join(output_path, badge_name)

        try:
            badge_content = self._render_badge_content(
                left_text,
                left_color_value,
                right_text,
                right_color_value,
                logo,
                frame,
                left_link,
                right_link,
                id_suffix,
                left_title,
                right_title,
                logo_tint,
            )

            with open(full_path, "w", encoding="utf-8") as file:
                file.write(badge_content)
            self.logger.info(f"Badge generated and saved to {full_path}")
        except Exception as e:
            self.logger.error(f"An error occurred while generating the badge: {e}")
            raise
