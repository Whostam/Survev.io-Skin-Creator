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
    body_rotation: float = 0.0
    hand_size: int = 52
    hand_offset_x: int = 32
    hand_offset_y: int = 34
    hand_top: Optional[int] = None
    hand_rotation_left: float = 0.0
    hand_rotation_right: float = 0.0
    right_hand_mirror: bool = True
    hands_above_body: bool = True
    backpack_size: int = 148
    backpack_top: int = 110
    backpack_offset_x: int = 0
    show_backpack: bool = True
    overlay_size: int = 160
    overlay_offset_x: int = 0
    overlay_offset_y: int = 0
    overlay_above_body: bool = True
    show_overlay: bool = True
    show_feet: bool = False
    feet_size: int = 38
    feet_offset_x: int = 28
    feet_offset_y: int = 12
    feet_top: Optional[int] = None
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
                body_size=150,
                body_top=156,
                hand_size=60,
                hand_offset_x=70,
                hand_top=282,
                backpack_size=192,
                backpack_top=68,
                overlay_size=200,
                overlay_offset_y=-10,
            ),
            description="Backpack, armor ring, and helmet aligned like the loadout preview.",
        ),
        "Standing": PreviewPreset(
            layout=PreviewLayout(
                stage_width=300,
                stage_height=280,
                body_size=140,
                body_top=92,
                hand_size=56,
                hand_offset_x=78,
                hand_top=206,
                show_backpack=False,
                show_overlay=False,
            ),
            description="Hands and body framing used when a survivor is upright.",
        ),
        "Knocked": PreviewPreset(
            layout=PreviewLayout(
                stage_width=320,
                stage_height=320,
                body_size=130,
                body_top=118,
                body_rotation=-28,
                hand_size=50,
                hand_offset_x=34,
                hand_top=222,
                hand_rotation_left=-18,
                hand_rotation_right=18,
                hands_above_body=False,
                show_backpack=False,
                show_overlay=False,
                show_feet=True,
                feet_size=44,
                feet_offset_x=36,
                feet_top=244,
                feet_rotation_left=-22,
                feet_rotation_right=22,
                feet_above_body=False,
            ),
            description="Top-down knocked pose with limbs tucked under the tilted body.",
        ),
    }
)


def build_preview_html(uris: Dict[str, str], layout: PreviewLayout = PreviewLayout()) -> str:
    body_left = (layout.stage_width - layout.body_size) // 2 + layout.body_left_offset
    backpack_left = (layout.stage_width - layout.backpack_size) // 2 + layout.backpack_offset_x
    hand_left = body_left - layout.hand_offset_x
    hand_right = layout.stage_width - hand_left - layout.hand_size
    hand_top = (
        layout.hand_top
        if layout.hand_top is not None
        else layout.body_top + layout.body_size - layout.hand_offset_y
    )
    overlay_left = body_left - (layout.overlay_size - layout.body_size) // 2 + layout.overlay_offset_x
    overlay_top = layout.body_top - (layout.overlay_size - layout.body_size) // 2 + layout.overlay_offset_y
    feet_left = body_left - layout.feet_offset_x
    feet_right = layout.stage_width - feet_left - layout.feet_size
    feet_top = (
        layout.feet_top
        if layout.feet_top is not None
        else layout.body_top + layout.body_size - layout.feet_offset_y
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
    width: {layout.backpack_size}px;
    height: {layout.backpack_size}px;
  }}
  .preview-body {{
    left: {body_left}px;
    top: {layout.body_top}px;
    width: {layout.body_size}px;
    height: {layout.body_size}px;
    transform: {body_transform};
    transform-origin: center;
  }}
  .preview-overlay {{
    left: {overlay_left}px;
    top: {overlay_top}px;
    width: {layout.overlay_size}px;
    height: {layout.overlay_size}px;
  }}
  .preview-hand-left {{
    left: {hand_left}px;
    top: {hand_top}px;
    width: {layout.hand_size}px;
    height: {layout.hand_size}px;
    transform: {hand_left_transform};
    transform-origin: center;
  }}
  .preview-hand-right {{
    left: {hand_right}px;
    top: {hand_top}px;
    width: {layout.hand_size}px;
    height: {layout.hand_size}px;
    transform: {hand_right_transform};
    transform-origin: center;
  }}
  .preview-feet-left {{
    left: {feet_left}px;
    top: {feet_top}px;
    width: {layout.feet_size}px;
    height: {layout.feet_size}px;
    transform: {feet_left_transform};
    transform-origin: center;
  }}
  .preview-feet-right {{
    left: {feet_right}px;
    top: {feet_top}px;
    width: {layout.feet_size}px;
    height: {layout.feet_size}px;
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
