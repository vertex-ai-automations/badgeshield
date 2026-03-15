## Command-Line Interface (CLI)

You can generate badges directly from the command line using the CLI tool.

### Single Badge Generation 

| Commands | Desc |
| ------ | ------ |
| single | Generate single badge. |

| Parameter | Required | Description |
| --- | :---: | --- |
| `--left_text` | ✅ | Text on the left segment. |
| `--left_color` | ✅ | `BadgeColor` enum member or hex color. |
| `--badge_name` | ✅ | Output SVG file name (must end in `.svg`). |
| `--output_path` |  | Directory for the generated file. Defaults to CWD. |
| `--right_text` |  | Text on the right segment. |
| `--right_color` |  | Color for the right segment. |
| `--template` |  | `BadgeTemplate` enum name. |
| `--frame` |  | Required when using `CIRCLE_FRAME`. Accepts `FrameType`. |
| `--logo` |  | Path to an image encoded into the badge. |
| `--logo_tint` |  | Hex/enum color used to tint the supplied logo. |
| `--left_link` |  | Hyperlink for the left segment. |
| `--right_link` |  | Hyperlink for the right segment. |
| `--id_suffix` |  | Appends a suffix to SVG element IDs. |
| `--left_title` |  | Accessible title for the left segment. |
| `--right_title` |  | Accessible title for the right segment. |
| `--log_level` |  | Logging verbosity (`DEBUG`, `INFO`, etc.). |

### Example

```bash
badgeshield single --left_text="flake8" --left_color="#FF0000" --output_path="./badges" --badge_name="build_success.svg" --log_level DEBUG
```

### Badge with Right Text

Generate a badge with both left and right text:

```bash
badgeshield single --left_text="flake8" --left_color="#FF0000" --right_text="tests" --right_color="#FFA500" --output_path="./badges" --badge_name="build_success.svg"
```

### Badge with Logo

Generate a badge with a logo:

```bash
badgeshield single --left_text="flake8" --left_color="#FF0000" --logo="logo.png" --output_path="./badges" --badge_name="build_success.svg"
```

### Badge with Links

Generate a badge with left and right links:

```bash
badgeshield single --left_text="flake8" --left_color="#FF0000" --left_link="https://example.com/build" --right_link="https://example.com/status" --output_path="./badges" --badge_name="build_success.svg"
```

Generate a badge with Frame template:

```bash
badgeshield single --left_text="flake8" --left_color="#FF0000" --output_path="./badge" --badge_name="build_success.svg" --template CIRCLE_FRAME --frame FRAME1
```

## Multiple Badge Generation 

Provide a JSON configuration containing an array of badge definitions and generate them in parallel:

| Commands | Desc |
| ------ | ------ |
| batch | Generate multiple badges. |

| Parameters | Value | Type |
| ------ | ------ | ------ |
| config-file | required | str |
| --output_path | optional | BadgeColor |
| --template | optional | str |
| --log_level | optional | LogLevel |
| --max_workers | optional | str |

### Example

```bash
badgeshield batch badges.json --output_dir badges --log_level INFO --max_workers 4
```

Configuration example (`badges.json`):

```json
[
  {
    "left_text": "build",
    "left_color": "GREEN",
    "badge_name": "build.svg"
  },
  {
    "left_text": "coverage",
    "left_color": "#ffc107",
    "right_text": "85%",
    "badge_name": "coverage.svg"
  }
]
```