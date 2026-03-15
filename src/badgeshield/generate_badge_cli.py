import argparse
import json
import os

from .badge_generator import (
    BadgeBatchGenerator,
    BadgeGenerator,
    BadgeTemplate,
    FrameType,
    LogLevel,
)


def validate_single_badge_args(args):
    """Validate the arguments for single badge generation."""
    # Validate color codes
    # Set output_path to current directory if not provided
    if args.output_path:
        args.output_path = os.path.abspath(args.output_path)
    else:
        args.output_path = os.getcwd()

    args.left_color = BadgeGenerator.validate_color(args.left_color, "left_color")
    if args.right_color:
        args.right_color = BadgeGenerator.validate_color(
            args.right_color, "right_color"
        )
    if args.logo_tint:
        args.logo_tint = BadgeGenerator.validate_color(args.logo_tint, "logo_tint")

    # Validate logo file existence
    if args.logo and not os.path.isfile(args.logo):
        raise ValueError(f"Logo file {args.logo} does not exist.")

    # Validate frame usage with CIRCLE_FRAME template
    template_name = (
        args.template.name
        if isinstance(args.template, BadgeTemplate)
        else str(args.template)
    )
    if template_name.upper() == BadgeTemplate.CIRCLE_FRAME.name and not args.frame:
        raise ValueError(
            "The 'frame' parameter is required when using the CIRCLE_FRAME template."
        )

    # Ensure frame is of type FrameType
    if args.frame:
        args.frame = (
            args.frame
            if isinstance(args.frame, FrameType)
            else FrameType[args.frame.upper()]
        )

    # Ensure output path is a directory
    if not os.path.isdir(args.output_path):
        raise ValueError(f"Output path {args.output_path} is not a valid directory.")

    # Ensure badge_name is valid
    if not args.badge_name.endswith(".svg"):
        raise ValueError(
            f"badge_name {args.badge_name} is not valid, must end with '.svg' (e.g., 'badge.svg')."
        )


def validate_batch_badge_args(args):
    """Validate the arguments for batch badge generation."""
    # Set output_path to current directory if not provided
    if not args.output_path:
        args.output_path = os.getcwd()
    else:
        args.output_path = os.path.abspath(args.output_path)

    # Validate the existence of the configuration file
    if not os.path.isfile(args.config_file):
        raise ValueError(f"Configuration file {args.config_file} does not exist.")

    try:
        with open(args.config_file, "r") as f:
            badge_configs = json.load(f)
        if not isinstance(badge_configs, list):
            raise ValueError(
                "The configuration file must contain a list of badge configurations."
            )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {args.config_file}: {e}")

    if not os.path.isdir(args.output_path):
        raise ValueError(f"Output directory {args.output_path} does not exist.")

    for badge in badge_configs:
        if "badge_name" not in badge or not badge["badge_name"].endswith(".svg"):
            raise ValueError(
                "Each badge configuration must include a valid 'badge_name' ending with '.svg'."
            )

        try:
            badge["left_color"] = BadgeGenerator.validate_color(
                badge["left_color"], "left_color"
            )
            if badge.get("right_color"):
                badge["right_color"] = BadgeGenerator.validate_color(
                    badge["right_color"], "right_color"
                )
            if badge.get("logo_tint"):
                badge["logo_tint"] = BadgeGenerator.validate_color(
                    badge["logo_tint"], "logo_tint"
                )
            if badge.get("frame"):
                badge["frame"] = (
                    badge["frame"]
                    if isinstance(badge["frame"], FrameType)
                    else FrameType[badge["frame"].upper()]
                )
        except KeyError as exc:
            raise ValueError(
                "Each badge configuration must include a 'left_color' entry."
            ) from exc

    return badge_configs


def generate_single_badge(args):
    try:
        validate_single_badge_args(args)
    except ValueError as e:
        print(f"Validation Error: {e}")
        return

    log_level = args.log_level

    # Convert template to BadgeTemplate enum
    template = BadgeTemplate[args.template.upper()]

    generator = BadgeGenerator(template=template, log_level=log_level)
    generator.generate_badge(
        left_text=args.left_text,
        left_color=args.left_color,
        output_path=args.output_path,
        badge_name=args.badge_name,
        right_text=args.right_text,
        right_color=args.right_color,
        logo=args.logo,
        frame=args.frame,
        left_link=args.left_link,
        right_link=args.right_link,
        id_suffix=args.id_suffix,
        left_title=args.left_title,
        right_title=args.right_title,
        logo_tint=args.logo_tint,
    )


def generate_batch_badges(args):
    try:
        badge_configs = validate_batch_badge_args(args)
    except ValueError as e:
        print(f"Validation Error: {e}")
        return

    template = BadgeTemplate[args.template.upper()]

    # Add output directory and validate badge_name for each badge config
    for badge in badge_configs:
        badge["output_path"] = args.output_path
        badge["template"] = template
        if template == BadgeTemplate.CIRCLE_FRAME and "frame" not in badge:
            print(
                "Error: The 'frame' parameter is required for CIRCLE_FRAME badges in batch mode as well."
            )
            return
        if "frame" in badge:
            try:
                badge["frame"] = (
                    badge["frame"]
                    if isinstance(badge["frame"], FrameType)
                    else FrameType[badge["frame"].upper()]
                )
            except KeyError as exc:
                print(
                    f"Error: Invalid frame type '{badge['frame']}' for badge '{badge['badge_name']}'. {exc}"
                )
                return

    batch_generator = BadgeBatchGenerator(
        max_workers=args.max_workers, log_level=args.log_level
    )
    batch_generator.generate_batch(badge_configs)


def main():
    parser = argparse.ArgumentParser(description="Generate custom badges for GitLab.")

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Subcommands: 'single' or 'batch'."
    )

    # Subcommand for single badge generation
    single_parser = subparsers.add_parser("single", help="Generate a single badge.")
    single_parser.add_argument(
        "--left_text", required=True, help="Text for the left side of the badge."
    )
    single_parser.add_argument(
        "--left_color",
        required=True,
        help="Background color for the left side of the badge.",
    )
    single_parser.add_argument(
        "--output_path",
        help="Directory where the badge SVG file will be saved. Defaults to current directory.",
    )
    single_parser.add_argument(
        "--badge_name",
        required=True,
        help="Name of the SVG file to be generated (must end with .svg).",
    )
    single_parser.add_argument(
        "--template",
        default="DEFAULT",
        choices=[t.name for t in BadgeTemplate],
        help="Template to use for the badge.",
    )
    single_parser.add_argument(
        "--right_text", help="Text for the right side of the badge."
    )
    single_parser.add_argument(
        "--right_color", help="Background color for the right side of the badge."
    )
    single_parser.add_argument("--logo", help="URL or path to a logo image.")
    single_parser.add_argument(
        "--logo_tint",
        help="Hex color or BadgeColor name to tint the provided logo before embedding.",
    )
    single_parser.add_argument(
        "--frame",
        choices=[t.name for t in FrameType],
        help="Frame type for the badge. Required for CIRCLE_FRAME template.",
    )
    single_parser.add_argument(
        "--left_link", help="Link for the left side of the badge."
    )
    single_parser.add_argument(
        "--right_link", help="Link for the right side of the badge."
    )
    single_parser.add_argument(
        "--id_suffix", default="", help="Suffix to add to the ID of the badge elements."
    )
    single_parser.add_argument(
        "--left_title", help="Title text for the left side of the badge."
    )
    single_parser.add_argument(
        "--right_title", help="Title text for the right side of the badge."
    )
    single_parser.add_argument(
        "--log_level",
        default="INFO",
        choices=[level.name for level in LogLevel],
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # Subcommand for batch badge generation
    batch_parser = subparsers.add_parser(
        "batch", help="Batch generate badges from a configuration file."
    )
    batch_parser.add_argument(
        "config_file",
        help="Path to the JSON configuration file containing badge definitions.",
    )
    batch_parser.add_argument(
        "--output_path",
        help="Directory where the generated badge SVG files will be saved. Defaults to current directory.",
    )
    batch_parser.add_argument(
        "--template",
        default="DEFAULT",
        choices=[t.name for t in BadgeTemplate],
        help="Template to use for the badges.",
    )
    batch_parser.add_argument(
        "--log_level",
        default="INFO",
        choices=[level.name for level in LogLevel],
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    batch_parser.add_argument(
        "--max_workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers for badge generation.",
    )

    args = parser.parse_args()

    if args.command == "single":
        generate_single_badge(args)
    elif args.command == "batch":
        generate_batch_badges(args)


if __name__ == "__main__":
    main()
