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
    hand_size: int = 52
    hand_offset_x: int = 32
    hand_offset_y: int = 34
    hand_top: Optional[int] = None
    backpack_size: int = 148
    backpack_top: int = 110
    backpack_offset_x: int = 0
    show_backpack: bool = True
    overlay_size: int = 160
    overlay_offset_x: int = 0
    overlay_offset_y: int = 0
    show_overlay: bool = True
    show_feet: bool = False
    feet_size: int = 38
    feet_offset_x: int = 28
    feet_offset_y: int = 12
    feet_top: Optional[int] = None


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
                body_size=132,
                body_top=176,
                hand_size=54,
                hand_offset_x=40,
                hand_offset_y=32,
                backpack_size=168,
                backpack_top=72,
                backpack_offset_x=0,
                overlay_size=180,
                overlay_offset_y=-8,
            ),
            description="Backpack, armor ring, and helmet aligned like the loadout preview.",
        ),
        "Standing": PreviewPreset(
            layout=PreviewLayout(
                stage_width=260,
                stage_height=320,
                body_size=124,
                body_top=128,
                hand_size=48,
                hand_offset_x=34,
                hand_offset_y=28,
                show_backpack=False,
                show_overlay=False,
            ),
            description="Hands and body framing used when a survivor is upright.",
        ),
        "Knocked": PreviewPreset(
            layout=PreviewLayout(
                stage_width=320,
                stage_height=320,
                body_size=116,
                body_top=112,
                hand_size=46,
                hand_offset_x=58,
                hand_offset_y=40,
                hand_top=88,
                show_backpack=False,
                show_overlay=False,
                show_feet=True,
                feet_size=42,
                feet_offset_x=52,
                feet_offset_y=28,
                feet_top=188,
            ),
            description="Top-down knocked pose with hands and feet visible.",
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

    stage_images = []
    if layout.show_backpack:
        stage_images.append(
            f'<img class="preview-backpack" src="{uris["backpack"]}" alt="Backpack" />'
        )
    stage_images.append(
        f'<img class="preview-body" src="{uris["body"]}" alt="Body" />'
    )
    if layout.show_overlay:
        stage_images.append(
            f'<img class="preview-overlay" src="{uris["overlay"]}" alt="Body overlay" />'
        )
    stage_images.append(
        f'<img class="preview-hand-left" src="{uris["hands"]}" alt="Left hand" />'
    )
    stage_images.append(
        f'<img class="preview-hand-right" src="{uris["hands"]}" alt="Right hand" />'
    )
    if layout.show_feet:
        stage_images.append(
            f'<img class="preview-feet-left" src="{uris["feet"]}" alt="Left foot" />'
        )
        stage_images.append(
            f'<img class="preview-feet-right" src="{uris["feet"]}" alt="Right foot" />'
        )

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
  }}
  .preview-hand-right {{
    left: {hand_right}px;
    top: {hand_top}px;
    width: {layout.hand_size}px;
    height: {layout.hand_size}px;
    transform: scaleX(-1);
    transform-origin: center;
  }}
  .preview-feet-left {{
    left: {feet_left}px;
    top: {feet_top}px;
    width: {layout.feet_size}px;
    height: {layout.feet_size}px;
  }}
  .preview-feet-right {{
    left: {feet_right}px;
    top: {feet_top}px;
    width: {layout.feet_size}px;
    height: {layout.feet_size}px;
    transform: scaleX(-1);
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
