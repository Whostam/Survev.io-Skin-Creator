"""Fill pattern helpers for generated SVG sprites."""

from __future__ import annotations

from typing import Tuple


def def_linear_grad(id_: str, color_a: str, color_b: str, angle_deg: int = 45) -> str:
    return (
        f'<defs><linearGradient id="{id_}" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="0" x2="512" y2="0" gradientTransform="rotate({angle_deg} 256 256)">'
        f'<stop offset="0%" stop-color="{color_a}"/>'
        f'<stop offset="100%" stop-color="{color_b}"/>'
        f"</linearGradient></defs>"
    )


def def_radial_grad(id_: str, color_a: str, color_b: str) -> str:
    return (
        f'<defs><radialGradient id="{id_}" cx="50%" cy="45%" r="60%">'
        f'<stop offset="0%" stop-color="{color_a}"/>'
        f'<stop offset="100%" stop-color="{color_b}"/>'
        f"</radialGradient></defs>"
    )


def def_stripes(
    id_: str,
    base: str,
    stripe: str,
    gap: int = 16,
    angle: int = 45,
    opacity: float = 0.6,
) -> str:
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap * 2}" height="{gap * 2}" '
        f'patternTransform="rotate({angle})">'
        f'<rect width="100%" height="100%" fill="{base}"/>'
        f'<rect x="0" y="0" width="{gap}" height="100%" fill="{stripe}" opacity="{opacity}"/>'
        f"</pattern></defs>"
    )


def def_crosshatch(
    id_: str,
    base: str,
    stripe: str,
    gap: int = 16,
    opacity: float = 0.6,
) -> str:
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}">'
        f'<rect width="100%" height="100%" fill="{base}"/>'
        f'<path d="M0,0 L{gap},0 M0,0 L0,{gap}" stroke="{stripe}" stroke-width="{gap / 2}" opacity="{opacity}"/>'
        f"</pattern></defs>"
    )


def def_dots(
    id_: str,
    base: str,
    dot: str = "#000",
    size: int = 6,
    gap: int = 22,
    opacity: float = 0.6,
) -> str:
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}">'
        f'<rect width="100%" height="100%" fill="{base}"/>'
        f'<circle cx="{gap / 2}" cy="{gap / 2}" r="{size}" fill="{dot}" opacity="{opacity}"/>'
        f"</pattern></defs>"
    )


def def_checker(id_: str, color_a: str, color_b: str, size: int = 16) -> str:
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{2 * size}" height="{2 * size}">'
        f'<rect width="{2 * size}" height="{2 * size}" fill="{color_a}"/>'
        f'<rect x="{size}" width="{size}" height="{size}" y="0" fill="{color_b}"/>'
        f'<rect x="0" y="{size}" width="{size}" height="{size}" fill="{color_b}"/>'
        f"</pattern></defs>"
    )


def build_fill(
    style: str,
    base: str,
    secondary: str,
    extra_color: str,
    angle: int,
    gap: int,
    opacity: float,
    size: int,
) -> Tuple[str, str]:
    if style == "Solid":
        return "", base
    if style == "Linear Gradient":
        defs = def_linear_grad("lg", base, secondary, angle)
        return defs, "url(#lg)"
    if style == "Radial Gradient":
        defs = def_radial_grad("rg", base, secondary)
        return defs, "url(#rg)"
    if style == "Diagonal Stripes":
        defs = def_stripes("ds", base, extra_color, gap, angle, opacity)
        return defs, "url(#ds)"
    if style == "Horizontal Stripes":
        defs = def_stripes("hs", base, extra_color, gap, 0, opacity)
        return defs, "url(#hs)"
    if style == "Vertical Stripes":
        defs = def_stripes("vs", base, extra_color, gap, 90, opacity)
        return defs, "url(#vs)"
    if style == "Crosshatch":
        defs = def_crosshatch("ch", base, extra_color, gap, opacity)
        return defs, "url(#ch)"
    if style == "Dots":
        defs = def_dots("pd", base, extra_color, size, gap, opacity)
        return defs, "url(#pd)"
    if style == "Checker":
        defs = def_checker("ck", base, secondary, size)
        return defs, "url(#ck)"
    return "", base


__all__ = [
    "build_fill",
    "def_checker",
    "def_crosshatch",
    "def_dots",
    "def_linear_grad",
    "def_radial_grad",
    "def_stripes",
]
