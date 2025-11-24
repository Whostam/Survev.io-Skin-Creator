"""SVG sprite builders."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from .fills import build_fill
from .helpers import (
    data_uri_from_bytes,
    darken,
    lighten,
    outline,
    svg_footer,
    svg_header,
)


def outline_style_parts(
    style: str,
    stroke_col: Optional[str],
    stroke_w: Optional[float],
    prefix: str,
):
    """Return defs/attributes/outer stroke markup for styled outlines."""

    if stroke_col is None or stroke_w is None:
        return "", "", None

    normalized = (style or "Solid").lower()
    defs = ""
    attrs = outline(stroke_col, stroke_w)
    outer = None

    if normalized == "glow":
        blur = stroke_w / 2
        defs = (
            f'<defs><filter id="{prefix}-glow" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{blur:.2f}" result="blur" />'
            f"<feMerge><feMergeNode in=\"blur\"/><feMergeNode in=\"SourceGraphic\"/></feMerge>"
            f"</filter></defs>"
        )
        attrs = f'stroke="{stroke_col}" stroke-width="{stroke_w}" filter="url(#{prefix}-glow)"'
    elif normalized == "gradient":
        grad_id = f"{prefix}-stroke-grad"
        defs = (
            f'<defs><linearGradient id="{grad_id}" x1="0%" y1="0%" x2="0%" y2="100%">'
            f'<stop offset="0%" stop-color="{lighten(stroke_col, 0.2)}"/>'
            f'<stop offset="100%" stop-color="{darken(stroke_col, 0.2)}"/>'
            f"</linearGradient></defs>"
        )
        attrs = f'stroke="url(#{grad_id})" stroke-width="{stroke_w}"'
    elif normalized == "dashed":
        dash = stroke_w * 1.6
        gap = stroke_w * 0.9
        attrs = (
            f'stroke="{stroke_col}" stroke-width="{stroke_w}" '
            f'stroke-dasharray="{dash:.2f} {gap:.2f}"'
        )
    elif normalized.startswith("double"):
        outer = outline(darken(stroke_col, 0.25), stroke_w * 1.6)
        attrs = outline(stroke_col, stroke_w)

    return defs, attrs, outer

PartConfig = Dict[str, object]


def build_part_svg(
    cfg: PartConfig,
    make_svg: Callable[[str, str, PartConfig, Optional[str], Optional[float], str], str],
    stroke_col: Optional[str] = None,
    stroke_w: Optional[float] = None,
    outline_style: str = "Solid",
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
    return make_svg(defs, fill_ref, cfg, stroke_col, stroke_w, outline_style)


def svg_from_upload(
    data: bytes,
    mime: str,
    fallback_width: int,
    fallback_height: int,
    rotation: float = 0.0,
    scale: float = 1.0,
) -> str:
    """Wrap an uploaded sprite (SVG or bitmap) in an SVG container."""

    data_uri = data_uri_from_bytes(data, mime or "image/png")
    parts = [svg_header(fallback_width, fallback_height)]
    cx = fallback_width / 2
    cy = fallback_height / 2
    transform_attr = ""
    transforms = []
    if abs(rotation) > 1e-6 or abs(scale - 1.0) > 1e-6:
        transforms.append(f"translate({cx:.2f},{cy:.2f})")
        if abs(rotation) > 1e-6:
            transforms.append(f"rotate({rotation:.2f})")
        if abs(scale - 1.0) > 1e-6:
            transforms.append(f"scale({scale:.4f})")
        transforms.append(f"translate({-cx:.2f},{-cy:.2f})")
    if transforms:
        transform_attr = f' transform="{" ".join(transforms)}"'
    parts.append(
        f'<image href="{data_uri}" x="0" y="0" width="{fallback_width}" '
        f'height="{fallback_height}" preserveAspectRatio="xMidYMid meet"{transform_attr} />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_backpack(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#333333",
    stroke_w: float = 11.014,
    outline_style: str = "Solid",
) -> str:
    width = height = 148
    parts = [svg_header(width, height)]
    defs, stroke_attrs, outer = outline_style_parts(
        outline_style, stroke_col, stroke_w, prefix="backpack"
    )
    if fill_defs:
        parts.append(fill_defs)
    if defs:
        parts.append(defs)
    if outer:
        parts.append(
            f'<ellipse cx="74" cy="74" rx="66.5" ry="66.5" fill="none" {outer} />'
        )
    stroke_attr_block = stroke_attrs or outline(stroke_col, stroke_w)
    parts.append(
        f'<ellipse cx="74" cy="74" rx="66.5" ry="66.5" fill="{fill_ref}" '
        f"{stroke_attr_block} />"
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_body(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#000",
    stroke_w: float = 8,
    outline_style: str = "Solid",
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
    outline_style: str = "Solid",
) -> str:
    width = height = 76
    parts = [svg_header(width, height)]
    defs, stroke_attrs, outer = outline_style_parts(
        outline_style, stroke_col, stroke_w, prefix="hands"
    )
    if fill_defs:
        parts.append(fill_defs)
    if defs:
        parts.append(defs)
    shape = cfg.get("shape", "Circle")
    scale_x = float(cfg.get("shape_scale_x", 1.0))
    scale_y = float(cfg.get("shape_scale_y", 1.0))
    cx = cy = 38
    stroke_attr_block = stroke_attrs or outline(stroke_col, stroke_w)

    if shape == "Rounded Square":
        size = 48 * scale_x
        radius = 12 * scale_y
        x = cx - size / 2
        y = cy - size / 2
        if outer:
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" '
                f'rx="{radius:.2f}" ry="{radius:.2f}" fill="none" {outer} />'
            )
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" '
            f'rx="{radius:.2f}" ry="{radius:.2f}" fill="{fill_ref}" {stroke_attr_block} />'
        )
    elif shape == "Diamond":
        half_w = 28 * scale_x
        half_h = 32 * scale_y
        points = [
            (cx, cy - half_h),
            (cx + half_w, cy),
            (cx, cy + half_h),
            (cx - half_w, cy),
        ]
        point_str = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
        if outer:
            parts.append(
                f'<polygon points="{point_str}" fill="none" {outer} />'
            )
        parts.append(
            f'<polygon points="{point_str}" fill="{fill_ref}" {stroke_attr_block} />'
        )
    elif shape == "Teardrop":
        radius = 30 * min(scale_x, scale_y)
        tip_offset = 26 * scale_y
        if outer:
            parts.append(
                f'<path d="M {cx - radius:.2f} {cy:.2f} '
                f'A {radius:.2f} {radius:.2f} 0 1 1 {cx + radius:.2f} {cy:.2f} '
                f'L {cx:.2f} {cy + tip_offset:.2f} Z" fill="none" {outer} />'
            )
        parts.append(
            f'<path d="M {cx - radius:.2f} {cy:.2f} '
            f'A {radius:.2f} {radius:.2f} 0 1 1 {cx + radius:.2f} {cy:.2f} '
            f'L {cx:.2f} {cy + tip_offset:.2f} Z" '
            f'fill="{fill_ref}" {stroke_attr_block} />'
        )
    else:  # Circle / ellipse
        rx = 30.4 * scale_x
        ry = 30.4 * scale_y
        if outer:
            parts.append(
                f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.2f}" ry="{ry:.2f}" fill="none" '
                f"{outer} />"
            )
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill_ref}" '
            f"{stroke_attr_block} />"
        )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_feet(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: str = "#333333",
    stroke_w: float = 4.513,
    outline_style: str = "Solid",
) -> str:
    width = height = 38
    parts = [svg_header(width, height)]
    defs, stroke_attrs, outer = outline_style_parts(
        outline_style, stroke_col, stroke_w, prefix="feet"
    )
    if fill_defs:
        parts.append(fill_defs)
    if defs:
        parts.append(defs)
    if outer:
        parts.append(
            f'<ellipse cx="19" cy="19" rx="15.7" ry="9.8" fill="none" {outer} />'
        )
    stroke_attr_block = stroke_attrs or outline(stroke_col, stroke_w)
    parts.append(
        f'<ellipse cx="19" cy="19" rx="15.7" ry="9.8" fill="{fill_ref}" '
        f"{stroke_attr_block} />"
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


def svg_accessory(
    fill_defs: str,
    fill_ref: str,
    cfg: PartConfig,
    stroke_col: Optional[str] = None,
    stroke_w: Optional[float] = None,
) -> str:
    """Generate a simple accessory sprite using layered ellipses."""

    width = height = 180
    parts = [svg_header(width, height)]
    if fill_defs:
        parts.append(fill_defs)

    center = width / 2
    base_radius = 72
    flare_radius = base_radius * float(cfg.get("flare_scale", 1.1))
    tip_radius = base_radius * float(cfg.get("tip_scale", 0.45))
    tip_offset = base_radius * 0.85

    parts.append(
        f'<circle cx="{center}" cy="{center}" r="{flare_radius:.2f}" fill="{fill_ref}" '
        f"{outline(stroke_col, stroke_w)} />"
    )
    parts.append(
        f'<circle cx="{center}" cy="{center + 16:.2f}" r="{base_radius:.2f}" fill="{fill_ref}" '
        f"{outline(stroke_col, stroke_w)} />"
    )
    highlight = cfg.get("extra", "#ffffff")
    parts.append(
        f'<circle cx="{center}" cy="{center - tip_offset:.2f}" r="{tip_radius:.2f}" fill="{highlight}" '
        'fill-opacity="0.65" />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


__all__ = [
    "build_part_svg",
    "svg_accessory",
    "svg_from_upload",
    "svg_backpack",
    "svg_body",
    "svg_body_preview_overlay",
    "svg_feet",
    "svg_hands",
    "svg_loot_circle_inner",
    "svg_loot_circle_outer",
    "svg_loot_shirt_base",
]
