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
                feet_rotation_right=145,
                right_foot_mirror=False,
                feet_above_body=False,
            ),
            description="Top-down knocked pose with limbs tucked under the tilted body.",
        ),
    }
)


def build_preview_html(uris: Dict[str, str], layout: PreviewLayout = PreviewLayout()) -> str:
    body_width = layout.body_width if layout.body_width is not None else layout.body_size
    body_height = layout.body_height if layout.body_height is not None else layout.body_size
    body_left = (
        layout.body_left
        if layout.body_left is not None
        else (layout.stage_width - body_width) // 2 + layout.body_left_offset
    )

    backpack_width = (
        layout.backpack_width if layout.backpack_width is not None else layout.backpack_size
    )
    backpack_height = (
        layout.backpack_height if layout.backpack_height is not None else layout.backpack_size
    )
    backpack_left = (
        layout.backpack_left
        if layout.backpack_left is not None
        else (layout.stage_width - backpack_width) // 2 + layout.backpack_offset_x
    )

    hand_width = layout.hand_width if layout.hand_width is not None else layout.hand_size
    hand_height = layout.hand_height if layout.hand_height is not None else layout.hand_size
    hand_left = (
        layout.hand_left
        if layout.hand_left is not None
        else body_left - layout.hand_offset_x
    )
    hand_right = (
        layout.hand_right
        if layout.hand_right is not None
        else layout.stage_width - hand_left - hand_width
    )
    base_hand_top = (
        layout.hand_top
        if layout.hand_top is not None
        else layout.body_top + body_height - layout.hand_offset_y
    )
    hand_left_top = (
        layout.hand_left_top if layout.hand_left_top is not None else base_hand_top
    )
    hand_right_top = (
        layout.hand_right_top if layout.hand_right_top is not None else base_hand_top
    )

    overlay_width = (
        layout.overlay_width if layout.overlay_width is not None else layout.overlay_size
    )
    overlay_height = (
        layout.overlay_height if layout.overlay_height is not None else layout.overlay_size
    )
    overlay_left = (
        layout.overlay_left
        if layout.overlay_left is not None
        else body_left - (overlay_width - body_width) // 2 + layout.overlay_offset_x
    )
    overlay_top = (
        layout.overlay_top
        if layout.overlay_top is not None
        else layout.body_top - (overlay_height - body_height) // 2 + layout.overlay_offset_y
    )

    feet_width = layout.feet_width if layout.feet_width is not None else layout.feet_size
    feet_height = layout.feet_height if layout.feet_height is not None else layout.feet_size
    feet_left = (
        layout.feet_left
        if layout.feet_left is not None
        else body_left - layout.feet_offset_x
    )
    feet_right = (
        layout.feet_right
        if layout.feet_right is not None
        else layout.stage_width - feet_left - feet_width
    )
    base_feet_top = (
        layout.feet_top
        if layout.feet_top is not None
        else layout.body_top + body_height - layout.feet_offset_y
    )
    feet_left_top = (
        layout.feet_left_top if layout.feet_left_top is not None else base_feet_top
    )
    feet_right_top = (
        layout.feet_right_top if layout.feet_right_top is not None else base_feet_top
    )

    def _build_transform(parts: Optional[list[Optional[str]]]) -> str:
        filtered = [part for part in (parts or []) if part]
        if not filtered:
            return "rotate(0deg)"
        return " ".join(filtered)

    body_transform = _build_transform([f"rotate({layout.body_rotation}deg)"])
    hand_left_transform = _build_transform([f"rotate({layout.hand_rotation_left}deg)"])
    hand_right_transform = _build_transform(
        ["scaleX(-1)" if layout.right_hand_mirror else None, f"rotate({layout.hand_rotation_right}deg)"]
    )
    feet_left_transform = _build_transform([f"rotate({layout.feet_rotation_left}deg)"])
    feet_right_transform = _build_transform(
        ["scaleX(-1)" if layout.right_foot_mirror else None, f"rotate({layout.feet_rotation_right}deg)"]
    )

    backpack_html = (
        f'<img class="preview-backpack" src="{uris["backpack"]}" alt="Backpack" />'
        if layout.show_backpack
        else ""
    )
    body_html = f'<img class="preview-body" src="{uris["body"]}" alt="Body" />'
    overlay_html = (
        f'<img class="preview-overlay" src="{uris["overlay"]}" alt="Body overlay" />'
        if layout.show_overlay
        else ""
    )
    hand_left_html = f'<img class="preview-hand-left" src="{uris["hands"]}" alt="Left hand" />'
    hand_right_html = f'<img class="preview-hand-right" src="{uris["hands"]}" alt="Right hand" />'
    feet_left_html = (
        f'<img class="preview-feet-left" src="{uris["feet"]}" alt="Left foot" />'
        if layout.show_feet
        else ""
    )
    feet_right_html = (
        f'<img class="preview-feet-right" src="{uris["feet"]}" alt="Right foot" />'
        if layout.show_feet
        else ""
    )

    stage_images = []
    if layout.show_backpack:
        stage_images.append(backpack_html)
    if layout.show_overlay and not layout.overlay_above_body:
        stage_images.append(overlay_html)
    if layout.show_feet and not layout.feet_above_body:
        stage_images.extend([feet_left_html, feet_right_html])
    if not layout.hands_above_body:
        stage_images.extend([hand_left_html, hand_right_html])
    stage_images.append(body_html)
    if layout.show_overlay and layout.overlay_above_body:
        stage_images.append(overlay_html)
    if layout.show_feet and layout.feet_above_body:
        stage_images.extend([feet_left_html, feet_right_html])
    if layout.hands_above_body:
        stage_images.extend([hand_left_html, hand_right_html])

    stage_images_html = "\n    ".join(stage_images)

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
  .preview-stage img {{
    position: absolute;
    image-rendering: optimizeQuality;
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
  .preview-backpack {{
    left: {backpack_left}px;
    top: {layout.backpack_top}px;
    width: {backpack_width}px;
    height: {backpack_height}px;
  }}
  .preview-body {{
    left: {body_left}px;
    top: {layout.body_top}px;
    width: {body_width}px;
    height: {body_height}px;
    transform: {body_transform};
    transform-origin: center;
  }}
  .preview-overlay {{
    left: {overlay_left}px;
    top: {overlay_top}px;
    width: {overlay_width}px;
    height: {overlay_height}px;
  }}
  .preview-hand-left {{
    left: {hand_left}px;
    top: {hand_left_top}px;
    width: {hand_width}px;
    height: {hand_height}px;
    transform: {hand_left_transform};
    transform-origin: center;
  }}
  .preview-hand-right {{
    left: {hand_right}px;
    top: {hand_right_top}px;
    width: {hand_width}px;
    height: {hand_height}px;
    transform: {hand_right_transform};
    transform-origin: center;
  }}
  .preview-feet-left {{
    left: {feet_left}px;
    top: {feet_left_top}px;
    width: {feet_width}px;
    height: {feet_height}px;
    transform: {feet_left_transform};
    transform-origin: center;
  }}
  .preview-feet-right {{
    left: {feet_right}px;
    top: {feet_right_top}px;
    width: {feet_width}px;
    height: {feet_height}px;
    transform: {feet_right_transform};
    transform-origin: center;
  }}
</style>
<div style="display:flex;flex-wrap:wrap;gap:32px;align-items:flex-start;justify-content:center;">
  <div class="preview-stage">
    {stage_images_html}
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;flex:0 0 auto;align-items:center;">
    <div style="display:grid;grid-template-columns:repeat(2,auto);gap:16px;justify-items:center;">
      <figure style="margin:0;text-align:center;">
        <img src="{uris['body']}" width="140" height="140" alt="Body sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Body</figcaption>
      </figure>
      <figure style="margin:0;text-align:center;">
        <img src="{uris['backpack']}" width="148" height="148" alt="Backpack sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Backpack</figcaption>
      </figure>
      <figure style="margin:0;text-align:center;">
        <img src="{uris['hands']}" width="76" height="76" alt="Hands sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Hands</figcaption>
      </figure>
      <figure style="margin:0;text-align:center;">
        <img src="{uris['feet']}" width="38" height="38" alt="Feet sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Feet</figcaption>
      </figure>
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


__all__ = ["PreviewLayout", "PreviewPreset", "PREVIEW_PRESETS", "build_preview_html"]
