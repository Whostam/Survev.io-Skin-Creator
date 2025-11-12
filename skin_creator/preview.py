"""HTML preview assembly helpers."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Mapping, Optional


@dataclass(frozen=True)
class PreviewLayout:
    stage_width: int = 420
    stage_height: int = 480
    body_size: int = 134
    body_top: int = 190
    body_left_offset: int = 0
    body_width: Optional[int] = None
    body_height: Optional[int] = None
    body_left: Optional[int] = None
    body_rotation: float = 0.0
    hand_size: int = 52
    hand_offset_x: int = 32
    hand_offset_y: int = 34
    hand_top: Optional[int] = None
    hand_left: Optional[int] = None
    hand_right: Optional[int] = None
    hand_width: Optional[int] = None
    hand_height: Optional[int] = None
    hand_left_top: Optional[int] = None
    hand_right_top: Optional[int] = None
    hand_rotation_left: float = 0.0
    hand_rotation_right: float = 0.0
    right_hand_mirror: bool = True
    hands_above_body: bool = True
    backpack_size: int = 148
    backpack_top: int = 110
    backpack_offset_x: int = 0
    backpack_width: Optional[int] = None
    backpack_height: Optional[int] = None
    backpack_left: Optional[int] = None
    show_backpack: bool = True
    overlay_size: int = 160
    overlay_offset_x: int = 0
    overlay_offset_y: int = 0
    overlay_above_body: bool = True
    overlay_width: Optional[int] = None
    overlay_height: Optional[int] = None
    overlay_left: Optional[int] = None
    overlay_top: Optional[int] = None
    show_overlay: bool = True
    show_feet: bool = False
    feet_size: int = 38
    feet_offset_x: int = 28
    feet_offset_y: int = 12
    feet_top: Optional[int] = None
    feet_left: Optional[int] = None
    feet_right: Optional[int] = None
    feet_width: Optional[int] = None
    feet_height: Optional[int] = None
    feet_left_top: Optional[int] = None
    feet_right_top: Optional[int] = None
    feet_rotation_left: float = 0.0
    feet_rotation_right: float = 0.0
    right_foot_mirror: bool = True
    feet_above_body: bool = True


@dataclass(frozen=True)
class PreviewPreset:
    """Named preview preset with optional description."""

    layout: PreviewLayout
    description: str = ""


@dataclass(frozen=True)
class BodyFrame:
    """Computed body bounds for use in previews and controls."""

    left: int
    top: int
    width: int
    height: int
    rotation: float


def body_frame_from_layout(layout: PreviewLayout) -> BodyFrame:
    """Return the body rectangle derived from the provided layout."""

    body_width = layout.body_width if layout.body_width is not None else layout.body_size
    body_height = layout.body_height if layout.body_height is not None else layout.body_size
    body_left = (
        layout.body_left
        if layout.body_left is not None
        else (layout.stage_width - body_width) // 2 + layout.body_left_offset
    )
    return BodyFrame(
        left=int(body_left),
        top=int(layout.body_top),
        width=int(body_width),
        height=int(body_height),
        rotation=float(layout.body_rotation),
    )


PREVIEW_PRESETS: Mapping[str, PreviewPreset] = OrderedDict(
    {
        "Loadout": PreviewPreset(
            layout=PreviewLayout(
                stage_width=360,
                stage_height=420,
                body_top=150,
                body_width=200,
                body_height=200,
                body_left=100,
                hand_width=80,
                hand_height=80,
                hand_left=95,
                hand_right=220,
                hand_top=290,
                backpack_width=200,
                backpack_height=192,
                backpack_left=100,
                backpack_top=90,
                overlay_width=200,
                overlay_height=200,
                overlay_left=100,
                overlay_top=150,
                overlay_above_body=True,
            ),
            description="Backpack, armor ring, and helmet aligned like the loadout preview.",
        ),
        "Standing": PreviewPreset(
            layout=PreviewLayout(
                stage_width=360,
                stage_height=360,
                body_top=92,
                body_width=200,
                body_height=200,
                body_left=80,
                hand_width=80,
                hand_height=80,
                hand_left=60,
                hand_right=210,
                hand_top=220,
                show_backpack=False,
                show_overlay=False,
            ),
            description="Hands and body framing used when a survivor is upright.",
        ),
        "Knocked": PreviewPreset(
            layout=PreviewLayout(
                stage_width=360,
                stage_height=360,
                body_top=118,
                body_width=200,
                body_height=200,
                body_left=95,
                body_rotation=-28,
                hand_width=80,
                hand_height=80,
                hand_left=170,
                hand_right=245,
                hand_left_top=270,
                hand_right_top=200,
                hand_rotation_left=-18,
                hand_rotation_right=18,
                hands_above_body=False,
                show_backpack=False,
                show_overlay=False,
                show_feet=True,
                feet_width=100,
                feet_height=100,
                feet_left=50,
                feet_right=110,
                feet_left_top=170,
                feet_right_top=90,
                feet_rotation_left=216,
                feet_rotation_right=216,
                right_foot_mirror=False,
                feet_above_body=False,
            ),
            description="Top-down knocked pose with limbs tucked under the tilted body.",
        ),
    }
)


def _compute_preview_geometry(
    layout: PreviewLayout,
    front: Optional[Dict[str, object]] = None,
) -> Dict[str, Dict[str, object]]:
    """Return positional metadata for preview elements."""

    front = front or {}

    body_frame = body_frame_from_layout(layout)
    body_width = body_frame.width
    body_height = body_frame.height
    body_left = body_frame.left

    backpack_width = int(
        layout.backpack_width if layout.backpack_width is not None else layout.backpack_size
    )
    backpack_height = int(
        layout.backpack_height if layout.backpack_height is not None else layout.backpack_size
    )
    backpack_left = int(
        layout.backpack_left
        if layout.backpack_left is not None
        else (layout.stage_width - backpack_width) // 2 + layout.backpack_offset_x
    )

    hand_width = int(
        layout.hand_width if layout.hand_width is not None else layout.hand_size
    )
    hand_height = int(
        layout.hand_height if layout.hand_height is not None else layout.hand_size
    )
    hand_left = int(
        layout.hand_left
        if layout.hand_left is not None
        else body_left - layout.hand_offset_x
    )
    hand_right = int(
        layout.hand_right
        if layout.hand_right is not None
        else layout.stage_width - hand_left - hand_width
    )
    base_hand_top = int(
        layout.hand_top
        if layout.hand_top is not None
        else layout.body_top + body_height - layout.hand_offset_y
    )
    hand_left_top = int(
        layout.hand_left_top if layout.hand_left_top is not None else base_hand_top
    )
    hand_right_top = int(
        layout.hand_right_top if layout.hand_right_top is not None else base_hand_top
    )

    overlay_width = int(
        layout.overlay_width if layout.overlay_width is not None else layout.overlay_size
    )
    overlay_height = int(
        layout.overlay_height if layout.overlay_height is not None else layout.overlay_size
    )
    overlay_left = int(
        layout.overlay_left
        if layout.overlay_left is not None
        else body_left - (overlay_width - body_width) // 2 + layout.overlay_offset_x
    )
    overlay_top = int(
        layout.overlay_top
        if layout.overlay_top is not None
        else body_frame.top - (overlay_height - body_height) // 2 + layout.overlay_offset_y
    )

    feet_width = int(
        layout.feet_width if layout.feet_width is not None else layout.feet_size
    )
    feet_height = int(
        layout.feet_height if layout.feet_height is not None else layout.feet_size
    )
    feet_left = int(
        layout.feet_left
        if layout.feet_left is not None
        else body_left - layout.feet_offset_x
    )
    feet_right = int(
        layout.feet_right
        if layout.feet_right is not None
        else layout.stage_width - feet_left - feet_width
    )
    base_feet_top = int(
        layout.feet_top
        if layout.feet_top is not None
        else body_frame.top + body_height - layout.feet_offset_y
    )
    feet_left_top = int(
        layout.feet_left_top if layout.feet_left_top is not None else base_feet_top
    )
    feet_right_top = int(
        layout.feet_right_top if layout.feet_right_top is not None else base_feet_top
    )

    def _build_transform(parts: Optional[list[Optional[str]]]) -> str:
        filtered = [part for part in (parts or []) if part]
        if not filtered:
            return ""
        return " ".join(filtered)

    body_transform = _build_transform([f"rotate({body_frame.rotation}deg)"])
    hand_left_transform = _build_transform([f"rotate({layout.hand_rotation_left}deg)"])
    hand_right_transform = _build_transform(
        ["scaleX(-1)" if layout.right_hand_mirror else None, f"rotate({layout.hand_rotation_right}deg)"]
    )
    feet_left_transform = _build_transform([f"rotate({layout.feet_rotation_left}deg)"])
    feet_right_transform = _build_transform(
        ["scaleX(-1)" if layout.right_foot_mirror else None, f"rotate({layout.feet_rotation_right}deg)"]
    )

    front_enabled = bool(front.get("enabled"))
    front_defaults = dict(
        left=body_left,
        top=body_frame.top,
        width=body_width,
        height=body_height,
        rotation=body_frame.rotation,
    )
    front_geometry = {
        key: int(float(front.get(key, default))) for key, default in front_defaults.items() if key != "rotation"
    }
    front_rotation = float(front.get("rotation", body_frame.rotation))
    front_above_hands = bool(front.get("above_hands"))
    overlay_above_front = bool(front.get("overlay_above_front", True))

    geometry: Dict[str, Dict[str, object]] = {
        "stage": {"width": layout.stage_width, "height": layout.stage_height},
        "body": {
            "left": body_left,
            "top": body_frame.top,
            "width": body_width,
            "height": body_height,
            "transform": body_transform,
            "visible": True,
            "z": 50,
        },
        "backpack": {
            "left": backpack_left,
            "top": layout.backpack_top,
            "width": backpack_width,
            "height": backpack_height,
            "transform": "",
            "visible": layout.show_backpack,
            "z": 10,
        },
        "overlay": {
            "left": overlay_left,
            "top": overlay_top,
            "width": overlay_width,
            "height": overlay_height,
            "transform": "",
            "visible": layout.show_overlay,
            "z": 65,
        },
        "hand_left": {
            "left": hand_left,
            "top": hand_left_top,
            "width": hand_width,
            "height": hand_height,
            "transform": hand_left_transform,
            "visible": True,
            "z": 80 if layout.hands_above_body else 30,
        },
        "hand_right": {
            "left": hand_right,
            "top": hand_right_top,
            "width": hand_width,
            "height": hand_height,
            "transform": hand_right_transform,
            "visible": True,
            "z": 80 if layout.hands_above_body else 30,
        },
        "feet_left": {
            "left": feet_left,
            "top": feet_left_top,
            "width": feet_width,
            "height": feet_height,
            "transform": feet_left_transform,
            "visible": layout.show_feet,
            "z": 70 if layout.feet_above_body else 20,
        },
        "feet_right": {
            "left": feet_right,
            "top": feet_right_top,
            "width": feet_width,
            "height": feet_height,
            "transform": feet_right_transform,
            "visible": layout.show_feet,
            "z": 70 if layout.feet_above_body else 20,
        },
        "front": {
            "left": front_geometry.get("left", body_left),
            "top": front_geometry.get("top", body_frame.top),
            "width": front_geometry.get("width", body_width),
            "height": front_geometry.get("height", body_height),
            "transform": _build_transform([f"rotate({front_rotation}deg)"]),
            "visible": front_enabled,
            "z": 75 if front_above_hands else 55,
        },
    }

    # Adjust layering so overlay can appear above or below the accessory as requested.
    if geometry["overlay"]["visible"]:
        if not front_enabled:
            geometry["overlay"]["z"] = 65
        else:
            if overlay_above_front:
                geometry["overlay"]["z"] = max(geometry["front"]["z"] + 5, geometry["overlay"]["z"])
            else:
                geometry["front"]["z"] = max(geometry["overlay"]["z"] + 5, geometry["front"]["z"])

    if geometry["front"]["visible"] and front_above_hands:
        geometry["front"]["z"] = max(geometry["front"]["z"], geometry["hand_left"]["z"] + 5)

    geometry["front"]["above_hands"] = front_above_hands
    geometry["front"]["overlay_above_front"] = overlay_above_front

    return geometry


def build_preview_html(
    uris: Dict[str, str],
    layout: PreviewLayout = PreviewLayout(),
    front: Optional[Dict[str, object]] = None,
) -> str:
    geometry = _compute_preview_geometry(layout, front)

    def _img_html(key: str, uri_key: str, alt: str) -> str:
        item = geometry[key]
        if not item.get("visible"):
            return ""
        transform = item.get("transform", "") or "rotate(0deg)"
        return (
            f'<img src="{uris[uri_key]}" alt="{alt}" '
            f'style="position:absolute;left:{item["left"]}px;top:{item["top"]}px;'
            f'width:{item["width"]}px;height:{item["height"]}px;'
            f'transform:{transform};transform-origin:center;'
            f'z-index:{item["z"]};image-rendering:optimizeQuality;" />'
        )

    backpack_html = _img_html("backpack", "backpack", "Backpack")
    body_html = _img_html("body", "body", "Body")
    overlay_html = _img_html("overlay", "overlay", "Body overlay")
    front_html = _img_html("front", "front", "Accessory") if uris.get("front") else ""
    hand_left_html = _img_html("hand_left", "hands", "Left hand")
    hand_right_html = _img_html("hand_right", "hands", "Right hand")
    feet_left_html = _img_html("feet_left", "feet", "Left foot")
    feet_right_html = _img_html("feet_right", "feet", "Right foot")

    front_enabled = bool(front_html)
    front_above_hands = bool(geometry["front"].get("above_hands"))
    overlay_above_front = bool(geometry["front"].get("overlay_above_front", True))

    stage_images = []
    if geometry["backpack"]["visible"]:
        stage_images.append(backpack_html)
    if geometry["overlay"]["visible"] and not layout.overlay_above_body:
        stage_images.append(overlay_html)
    if geometry["feet_left"]["visible"] and not layout.feet_above_body:
        stage_images.extend([feet_left_html, feet_right_html])
    if not layout.hands_above_body:
        stage_images.extend([hand_left_html, hand_right_html])
    stage_images.append(body_html)
    if geometry["overlay"]["visible"] and layout.overlay_above_body:
        if front_enabled and not front_above_hands and not overlay_above_front:
            stage_images.append(front_html)
        stage_images.append(overlay_html)
    if front_enabled and not front_above_hands:
        stage_images.append(front_html)
    if geometry["feet_left"]["visible"] and layout.feet_above_body:
        stage_images.extend([feet_left_html, feet_right_html])
    if layout.hands_above_body:
        stage_images.extend([hand_left_html, hand_right_html])
    if geometry["overlay"]["visible"] and layout.overlay_above_body and front_enabled and front_above_hands and not overlay_above_front:
        stage_images.append(overlay_html)
    if front_enabled and front_above_hands:
        stage_images.append(front_html)

    stage_images_html = "\n    ".join(filter(None, stage_images))

    figures = [
        ("Body", uris["body"], 140, 140),
        ("Backpack", uris["backpack"], 148, 148),
        ("Hands", uris["hands"], 76, 76),
        ("Feet", uris["feet"], 38, 38),
    ]
    if front_enabled and uris.get("front"):
        figures.append(("Accessory", uris["front"], geometry["front"]["width"], geometry["front"]["height"]))
    grid_cols = min(3, len(figures))
    figure_html = "\n      ".join(
        f'<figure style="margin:0;text-align:center;"><img src="{src}" width="{width}" height="{height}" '
        f'alt="{label} sprite" style="image-rendering:optimizeQuality;" />'
        f'<figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">{label}</figcaption></figure>'
        for label, src, width, height in figures
    )

    return f"""
<style>
  .preview-stage {{
    position: relative;
    width: {layout.stage_width}px;
    height: {layout.stage_height}px;
    flex: 0 0 auto;
    background: transparent;
    margin-right: 32px;
  }}
  .loot-stage {{
    position: relative;
    width: 148px;
    height: 148px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .loot-stage img {{
    position: absolute;
    image-rendering: optimizeQuality;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }}
  .loot-outer {{
    width: 146px;
    height: 146px;
  }}
  .loot-inner {{
    width: 148px;
    height: 148px;
  }}
  .loot-shirt {{
    width: 128px;
    height: 128px;
  }}
</style>
<div style="display:flex;flex-wrap:wrap;gap:32px;align-items:flex-start;justify-content:center;">
  <div class="preview-stage">
    {stage_images_html}
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;flex:0 0 auto;align-items:center;">
    <div style="display:grid;grid-template-columns:repeat({grid_cols},auto);gap:16px;justify-items:center;">
      {figure_html}
    </div>
    <figure style="margin:0;text-align:center;">
      <div class="loot-stage">
        <img class="loot-outer" src="{uris['loot_outer']}" alt="Loot outer" />
        <img class="loot-inner" src="{uris['loot_inner']}" alt="Loot inner" />
        <img class="loot-shirt" src="{uris['loot']}" alt="Loot shirt" />
      </div>
      <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Loot icon</figcaption>
    </figure>
  </div>
</div>
"""


def build_preview_document(
    uris: Dict[str, str],
    layout: PreviewLayout = PreviewLayout(),
    front: Optional[Dict[str, object]] = None,
) -> str:
    """Wrap the preview HTML in a minimal standalone document for export."""

    inner = build_preview_html(uris=uris, layout=layout, front=front)
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head><meta charset=\"utf-8\" /><title>Zurviv.io Preview</title></head>\n"
        "<body style=\"margin:24px;font-family:system-ui,sans-serif;background:#f5f5f5;\">"
        f"{inner}"
        "</body></html>"
    )


__all__ = [
    "PreviewLayout",
    "PreviewPreset",
    "BodyFrame",
    "PREVIEW_PRESETS",
    "build_preview_document",
    "build_preview_html",
    "body_frame_from_layout",
]
