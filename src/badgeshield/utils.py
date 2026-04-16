from enum import Enum


class BadgeColor(Enum):
    # Standard Colors
    RED = "#FF0000"
    GREEN = "#00FF00"
    BLUE = "#0000FF"
    YELLOW = "#FFFF00"
    ORANGE = "#FFA500"
    PURPLE = "#800080"
    PINK = "#FFC0CB"
    BROWN = "#A52A2A"
    BLACK = "#000000"
    WHITE = "#FFFFFF"
    GRAY = "#808080"
    CYAN = "#00FFFF"
    MAGENTA = "#FF00FF"

    # Light Colors
    LIGHT_RED = "#FF6666"
    LIGHT_GREEN = "#66FF66"
    LIGHT_BLUE = "#6666FF"
    LIGHT_YELLOW = "#FFFF66"
    LIGHT_ORANGE = "#FFD580"
    LIGHT_PURPLE = "#D580FF"
    LIGHT_PINK = "#FFB6C1"
    LIGHT_BROWN = "#C19A6B"
    LIGHT_GRAY = "#D3D3D3"
    LIGHT_CYAN = "#E0FFFF"
    LIGHT_MAGENTA = "#FF77FF"

    # Dark Colors
    DARK_RED = "#8B0000"
    DARK_GREEN = "#006400"
    DARK_BLUE = "#00008B"
    DARK_YELLOW = "#CCCC00"
    DARK_ORANGE = "#FF8C00"
    DARK_PURPLE = "#4B0082"
    DARK_PINK = "#FF1493"
    DARK_BROWN = "#654321"
    DARK_GRAY = "#696969"
    DARK_CYAN = "#008B8B"
    DARK_MAGENTA = "#8B008B"

    # Pastel Colors
    PASTEL_RED = "#FF6961"
    PASTEL_GREEN = "#77DD77"
    PASTEL_BLUE = "#AEC6CF"
    PASTEL_YELLOW = "#FDFD96"
    PASTEL_ORANGE = "#FFB347"
    PASTEL_PURPLE = "#C3B1E1"
    PASTEL_PINK = "#FFB3DE"
    PASTEL_BROWN = "#D2B48C"
    PASTEL_GRAY = "#CFCFC4"
    PASTEL_CYAN = "#B2DFEE"
    PASTEL_MAGENTA = "#FFB2E6"

    # Neon Colors
    NEON_RED = "#FF073A"
    NEON_GREEN = "#39FF14"
    NEON_BLUE = "#1B03A3"
    NEON_YELLOW = "#FFFF33"
    NEON_ORANGE = "#FF6700"
    NEON_PURPLE = "#D300FF"
    NEON_PINK = "#FF6EC7"
    NEON_CYAN = "#0FF0FC"
    NEON_MAGENTA = "#FF44CC"

    def __str__(self) -> str:
        return self.value


class FrameType(Enum):
    FRAME1 = "templates/frames/frame1.png"
    FRAME2 = "templates/frames/frame2.png"
    FRAME3 = "templates/frames/frame3.png"
    FRAME4 = "templates/frames/frame4.png"
    FRAME5 = "templates/frames/frame5.png"
    FRAME6 = "templates/frames/frame6.png"
    FRAME7 = "templates/frames/frame7.png"
    FRAME8 = "templates/frames/frame8.png"
    FRAME9 = "templates/frames/frame9.png"
    FRAME10 = "templates/frames/frame10.png"
    FRAME11 = "templates/frames/frame11.png"

    def __str__(self) -> str:
        return self.value


class BadgeTemplate(Enum):
    DEFAULT      = "templates/label.svg"
    CIRCLE_FRAME = "templates/circle_frame.svg"
    CIRCLE       = "templates/circle.svg"
    PILL         = "templates/pill.svg"
    BANNER       = "templates/banner.svg"

    def __str__(self) -> str:
        return self.value


class BadgeStyle(str, Enum):
    """Visual style preset for badge rendering."""
    FLAT     = "flat"      # default — no visual change
    ROUNDED  = "rounded"   # 8px border-radius on rectangular corners
    GRADIENT = "gradient"  # gradient: left section lighter → base color
    SHADOWED = "shadowed"  # SVG feDropShadow filter
