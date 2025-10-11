"""General helper utilities for the Survev.io skin creator."""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional, Tuple


def sanitize(name: str) -> str:
    """Return a filesystem-safe identifier for export assets."""
    return re.sub(r"[^A-Za-z0-9]+", "", name.strip()) or "Custom"


def ensure_extension(name: str, ext: str) -> str:
    """Force a filename to use the provided extension."""
    name = name.strip()
    if not name:
        return ""
    if name.endswith(f".{ext}"):
        return name
    if "." in name:
        name = name[: name.rfind(".")]
    return f"{name}.{ext}"


def apply_prefix(prefix: str, filename: str) -> str:
    """Prepend a directory prefix unless the filename already contains one."""
    if "/" in filename:
        return filename
    prefix = prefix.strip()
    if not prefix:
        return filename
    if not prefix.endswith("/"):
        prefix = prefix + "/"
    return f"{prefix}{filename}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert a CSS hex color to RGB tuple."""
    h = hex_str.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_ts_hex(rgb: Tuple[int, int, int]) -> str:
    """Render an RGB triple as a TypeScript-style hexadecimal literal."""
    return f"0x{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def svg_header(width: int = 512, height: int = 512) -> str:
    """Return the shared SVG header used across generated assets."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="geometricPrecision" '
        f'text-rendering="geometricPrecision">'
    )


def svg_footer() -> str:
    """Return the closing SVG tag."""
    return "</svg>"


def outline(stroke: Optional[str] = "#000000", width: Optional[float] = 8) -> str:
    """Build a stroke attribute block for outline-enabled sprites."""
    if stroke is None or width is None:
        return ""
    return f'stroke="{stroke}" stroke-width="{width}"'


def clamp_byte(value: float) -> int:
    """Clamp a floating-point channel to the 0-255 byte range."""
    return max(0, min(255, int(round(value))))


def lighten(hex_str: str, amount: float) -> str:
    """Lighten a hex color by the provided amount (0-1)."""
    r, g, b = hex_to_rgb(hex_str)
    r = clamp_byte(r + (255 - r) * amount)
    g = clamp_byte(g + (255 - g) * amount)
    b = clamp_byte(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def darken(hex_str: str, amount: float) -> str:
    """Darken a hex color by the provided amount (0-1)."""
    r, g, b = hex_to_rgb(hex_str)
    r = clamp_byte(r * (1 - amount))
    g = clamp_byte(g * (1 - amount))
    b = clamp_byte(b * (1 - amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def svg_data_uri(svg_text: str) -> str:
    """Encode raw SVG text as a data URI for inline previews."""
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg_text)

__all__ = [
    "apply_prefix",
    "clamp_byte",
    "darken",
    "ensure_extension",
    "hex_to_rgb",
    "lighten",
    "outline",
    "rgb_to_ts_hex",
    "sanitize",
    "svg_data_uri",
    "svg_footer",
    "svg_header",
]
