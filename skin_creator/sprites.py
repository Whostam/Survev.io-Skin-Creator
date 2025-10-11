"""SVG sprite builders."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from .fills import build_fill
from .helpers import darken, lighten, outline, svg_footer, svg_header

PartConfig = Dict[str, object]


def build_part_svg(
    cfg: PartConfig,
    make_svg: Callable[[str, str, PartConfig, Optional[str], Optional[float]], str],
    stroke_col: Optional[str] = None,
    stroke_w: Optional[float] = None,
) -> str:
    defs, fill_ref = build_fill(
        cfg["style"],
        cfg["primary"],
        cfg["secondary"],
        cfg["extra"],
        cfg["angle"],
        cfg["gap"],
        cfg["opacity"],
        cfg["size"],
    )
    return make_svg(defs, fill_ref, cfg, stroke_col, stroke_w)


def svg_backpack(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#333333",
    stroke_w: float = 11.014,
) -> str:
    width = height = 148
    parts = [svg_header(width, height)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(
        f'<ellipse cx="74" cy="74" rx="66.5" ry="66.5" fill="{fill_ref}" '
        f"{outline(stroke_col, stroke_w)} />"
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_body(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#000",
    stroke_w: float = 8,
) -> str:
    width = height = 140
    parts = [svg_header(width, height)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(f'<ellipse cx="70" cy="70" rx="66" ry="66" fill="{fill_ref}" />')
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_hands(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#333333",
    stroke_w: float = 11.096,
) -> str:
    width = height = 76
    parts = [svg_header(width, height)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(
        f'<ellipse cx="38" cy="38" rx="30.4" ry="30.4" fill="{fill_ref}" '
        f"{outline(stroke_col, stroke_w)} />"
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_feet(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#333333",
    stroke_w: float = 4.513,
) -> str:
    width = height = 38
    parts = [svg_header(width, height)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(
        f'<ellipse cx="19" cy="19" rx="15.7" ry="9.8" fill="{fill_ref}" '
        f"{outline(stroke_col, stroke_w)} />"
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_body_preview_overlay() -> str:
    """Return the preview-only armor ring and helmet accent."""
    width = height = 160
    parts = [svg_header(width, height)]
    center = width / 2
    ring_stroke = "#20160a"
    ring_width = 12
    parts.append(
        f'<circle cx="{center}" cy="{center}" r="70" fill="none" '
        f'stroke="{ring_stroke}" stroke-width="{ring_width}" />'
    )
    helmet_radius = 40
    helmet_cy = center - 22
    helmet_stroke = "#174173"
    helmet_width = 8
    parts.append(
        f'<circle cx="{center}" cy="{helmet_cy}" r="{helmet_radius}" fill="#3c7fda" '
        f'stroke="{helmet_stroke}" stroke-width="{helmet_width}" />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_loot_shirt_base(tint_hex: str) -> str:
    """Return the loot shirt silhouette with the provided tint."""
    path_d = (
        "M63.993 8.15c-10.38 0-22.796 3.526-30.355 7.22-8.038 3.266-14.581 7.287-19.253 14.509C8.102 "
        "39.594 5.051 54.6 7.13 78.482c5.964 2.07 11.333 1.45 16.842-.415-1.727-7.884-1.448-15.764.496-22.204 "
        "2.126-7.044 6.404-12.722 12.675-13.701l2.77-.432.074 2.803c.054 2.043.09 4.17.116 6.335l.027 "
        "6.312c-.037 8.798-.382 18.286-1.277 27.845 5.637 1.831 14.806 2.954 23.964 3.019l4.597-.058c8.53-.275 "
        "16.742-1.449 21.665-3.063-1.093-14.65-1.166-29.434-1.52-41.334l-.097-3.283 3.18.824c6.238 1.617 "
        "10.55 7.376 12.76 14.507 2.02 6.51 2.353 14.37.64 22.248a29.764 29.764 0 0 0 12.847 1.181l4.399-.588c1.033-18.811-1.433"
        "-37.403-6.27-46.264l-4.408-6.376c-4.647-5.357-10.62-8.399-17.665-11.074-6.746-3.458-18.358-6.614-28.95-6.614zm0 3.05c6.494 0 13."
        "37 1.942 19.274 4.516-3.123 2.758-6.971 4.665-11.067 5.754l-7.852 17.31-6.838-16.882c-4.757-.93-9.26-2.957-12.783-6.174C50.9 13."
        "081 57.809 11.2 63.993 11.2zm.58 28.539l3.512 5.327-3.497 5.053-3.53-5.053zm0 11.888l3.512 5.328-3.497 5.052-3.53-5.053 3.514-5."
        "327zm0 11.733l3.512 5.327-3.497 5.054-3.53-5.054zm0 11.876l3.512 5.327-3.497 5.054-3.53-5.053 3.514-5.327zm25.079 13.715c-6.61 2"
        ".055-15.829 2.907-25.277 2.951-9.5.045-18.965-.744-25.902-2.892-.205 1.785-.43 3.569-.678 5.347 5.968 2.132 16.346 3.408 26.497"
        "3.36 10.143-.05 20.355-1.444 25.912-3.433a241.302 241.302 0 0 1-.552-5.333zm1.368 9.086c-6.782 2.308-16.533 3.262-26.53 3.31-2.9"
        "35.015-5.866-.052-8.724-.213l-4.227-.315c-5.358-.5-10.307-1.382-14.329-2.758-.897 5.43-2.02 10.772-3.413 15.903 2.117 1.06 4.41"
        "1.968 6.835 2.733l3.97 1.096c15.85 3.805 35.88 2.156 49.601-3.513-1.355-5.09-2.387-10.57-3.183-16.243z"
    )
    parts = [svg_header(128, 128)]
    parts.append(f'<path d="{path_d}" fill="{tint_hex}"/>')
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_loot_circle_inner(base_hex: str) -> str:
    highlight = lighten(base_hex, 0.25)
    fade = darken(base_hex, 0.65)
    parts = [svg_header(148, 148)]
    parts.append(
        "<defs>"
        "<radialGradient id=\"lootInner\" cx=\"50%\" cy=\"50%\" r=\"50%\" gradientUnits=\"userSpaceOnUse\">"
        f"<stop offset=\"0%\" stop-color=\"{highlight}\" stop-opacity=\"1\"/>"
        f"<stop offset=\"100%\" stop-color=\"{fade}\" stop-opacity=\"0\"/>"
        "</radialGradient>"
        "</defs>"
    )
    parts.append(
        '<ellipse cx="74" cy="74" rx="68.861" ry="68.769" fill="url(#lootInner)" />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_loot_circle_outer(stroke_hex: str) -> str:
    fill_col = lighten(stroke_hex, 0.6)
    parts = [svg_header(146, 146)]
    parts.append(
        f'<ellipse cx="73" cy="73" rx="68.861" ry="68.769" fill="{fill_col}" '
        'fill-opacity="0.27" '
        f'stroke="{stroke_hex}" stroke-width="6.21" stroke-opacity="0.77" />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


__all__ = [
    "build_part_svg",
    "svg_backpack",
    "svg_body",
    "svg_body_preview_overlay",
    "svg_feet",
    "svg_hands",
    "svg_loot_circle_inner",
    "svg_loot_circle_outer",
    "svg_loot_shirt_base",
]
