# Usage Guide

## Programmatic Usage

You can also generate badges programmatically within your Python code.

### Parameters

| Parameters | Value | Type |
| ------ | ------ | ------ |
| left_text | required | str |
| left_color | required | BadgeColor |
| badge_name | required | str |
| output_path | optional | str |
| right_text | optional | str |
| right_color | optional | BadgeColor |
| frame | optional | FrameType |
| logo | optional | str |
| left_link | optional | str |
| right_link | optional | str |
| id_suffix | optional | str |
| left_title | optional | str |
| right_title | optional | str |
| log_level | optional | LogLevel |
| logo_tint | optional | BadgeColor |

### Basic Usage

```python
from badgeshield import BadgeGenerator, LogLevel

generator = BadgeGenerator(log_level=LogLevel.INFO)
generator.generate_badge(
    left_text="MH",
    left_color="#FF0000",
    badge_name="build.svg",
    right_text="tests for you",
    right_color="#000555",
    left_link="https://example.com/build",
    right_link="https://example.com/status",
    left_title="Build Status",
    right_title="Test Coverage"
)
```

### Using Frame Template
```python
from badgeshield import BadgeGenerator, LogLevel, FrameType, BadgeTemplate

generator = BadgeGenerator(template=BadgeTemplate.CIRCLE_FRAME, log_level=LogLevel.INFO)
generator.generate_badge(
    left_text="MH",
    left_color="#FF0000",
    badge_name="build.svg",
    right_text="tests for you",
    right_color="#000555",
    left_link="https://example.com/build",
    right_link="https://example.com/status",
    left_title="Build Status",
    right_title="Test Coverage",
    frame=FrameType.FRAME1,
    output_path="autosave",
    logo_tint="#FFFFFF",
)
```

## Apply Badge in HTML or Gitlab

You can use embed it within an HTML `<img>` tag and wrapped inside an `<a>` tag with your corresponding link. 

**HTML embed**

```
<a href="https://gitlab.fbi.gov/dtxu/custom-badges"><img alt="Name" src="https://gitlab.fbi.gov/dtxu/custom-badges/-/raw/main/resources/samples/name.svg" /></a>
```

**Markdown syntax to dispaly image**

```
[![pipeline status](https://gitlab.fbi.gov/dtxu/custom-badges/-/raw/main/resources/samples/name.svg)](https://gitlab.fbi.gov/dtxu/custom-badges)
```

!!!warning
    Gitlab markdown renderer doesn't interpret links inside the SVG when linking the SVG file directly. 
    
----
