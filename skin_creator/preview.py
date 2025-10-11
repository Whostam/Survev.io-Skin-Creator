"""HTML preview assembly helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PreviewLayout:
    stage_width: int = 420
    stage_height: int = 480
    body_size: int = 134
    backpack_size: int = 148
    hand_size: int = 52
    overlay_size: int = 160
    body_top: int = 190
    backpack_top: int = 110
    hand_offset_x: int = 32
    hand_offset_y: int = 34


def build_preview_html(uris: Dict[str, str], layout: PreviewLayout = PreviewLayout()) -> str:
    body_left = (layout.stage_width - layout.body_size) // 2
    backpack_left = (layout.stage_width - layout.backpack_size) // 2
    hand_left = body_left - layout.hand_offset_x
    hand_right = layout.stage_width - hand_left - layout.hand_size
    hand_top = layout.body_top + layout.body_size - layout.hand_offset_y
    overlay_left = body_left - (layout.overlay_size - layout.body_size) // 2
    overlay_top = layout.body_top - (layout.overlay_size - layout.body_size) // 2

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
</style>
<div style="display:flex;flex-wrap:wrap;gap:32px;align-items:flex-start;justify-content:center;">
  <div class="preview-stage">
    <img class="preview-backpack" src="{uris['backpack']}" alt="Backpack" />
    <img class="preview-body" src="{uris['body']}" alt="Body" />
    <img class="preview-overlay" src="{uris['overlay']}" alt="Body overlay" />
    <img class="preview-hand-left" src="{uris['hands']}" alt="Left hand" />
    <img class="preview-hand-right" src="{uris['hands']}" alt="Right hand" />
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


__all__ = ["PreviewLayout", "build_preview_html"]
