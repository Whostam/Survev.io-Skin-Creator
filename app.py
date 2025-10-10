import io
import json
import math
import re
import zipfile
from dataclasses import dataclass, asdict
from typing import Dict, Tuple

import streamlit as st

# ==============================
# Small utilities
# ==============================

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """#RRGGBB -> (r,g,b)"""
    h = hex_str.strip().lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex_literal(rgb: Tuple[int, int, int]) -> str:
    """(r,g,b) -> 0xRRGGBB (TypeScript numeric hex literal)"""
    return f"0x{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def sanitize(name: str) -> str:
    """make a safe id fragment"""
    out = re.sub(r"[^A-Za-z0-9]+", "", name.strip())
    return out or "Custom"

# basic SVG helpers
def svg_header(w=512, h=512):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'

def svg_footer():
    return "</svg>"

def mk_linear_gradient(id_, c1, c2):
    return (
        f'<defs>'
        f'<linearGradient id="{id_}" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>'
        f'</linearGradient>'
        f'</defs>'
    )

def mk_diagonal_stripes(id_, base_color="#ffffff", stripe_color="#999999", opacity=0.5, gap=16):
    # pattern sized to 32px to tile nicely
    return (
        f'<defs>'
        f'<pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap*2}" height="{gap*2}" patternTransform="rotate(45)">'
        f'<rect width="100%" height="100%" fill="{base_color}"/>'
        f'<rect x="0" y="0" width="{gap}" height="100%" fill="{stripe_color}" opacity="{opacity}"/>'
        f'</pattern>'
        f'</defs>'
    )

def outline():
    return 'stroke="#000000" stroke-width="8"'

# ==============================
# Sprite generators
# ==============================

def body_svg(primary="#a66cff", secondary="#58a5ff", pattern="none",
             pattern_color="#a7ff3f", pattern_opacity=0.6, diag_width=24):
    W, H = 512, 512
    parts = [svg_header(W, H)]
    fill = primary
    defs = ""

    if pattern == "linear":
        defs = mk_linear_gradient("g1", primary, secondary)
        fill = 'url(#g1)'
    elif pattern == "diagonal":
        defs = mk_diagonal_stripes("p1", base_color=primary, stripe_color=pattern_color,
                                   opacity=pattern_opacity, gap=max(8, int(diag_width)))
        fill = 'url(#p1)'

    parts.append(defs)
    # base circle body
    parts.append(f'<circle cx="256" cy="288" r="170" fill="{fill}" {outline()}/>')
    # simple head band (so backpack shows clearly when layered)
    parts.append(f'<path d="M110,210 Q256,120 402,210 L402,240 Q256,180 110,240 Z" fill="{secondary}" {outline()}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def hands_svg(primary="#ffcc88", secondary="#ff9966", pattern="linear"):
    W, H = 512, 512
    parts = [svg_header(W, H)]
    defs = ""
    fill = primary
    if pattern == "linear":
        defs = mk_linear_gradient("h1", primary, secondary)
        fill = 'url(#h1)'

    parts.append(defs)
    # two hands as side circles
    parts.append(f'<circle cx="160" cy="420" r="48" fill="{fill}" {outline()}/>')
    parts.append(f'<circle cx="352" cy="420" r="48" fill="{fill}" {outline()}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def feet_svg(primary="#58a5ff", secondary="#3f7bdc", pattern="linear"):
    W, H = 512, 512
    parts = [svg_header(W, H)]
    defs = ""
    fill = primary
    if pattern == "linear":
        defs = mk_linear_gradient("f1", primary, secondary)
        fill = 'url(#f1)'

    parts.append(defs)
    # two feet as rounded capsules
    parts.append(f'<rect x="124" y="430" rx="40" ry="40" width="110" height="58" fill="{fill}" {outline()}/>')
    parts.append(f'<rect x="278" y="430" rx="40" ry="40" width="110" height="58" fill="{fill}" {outline()}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def backpack_svg(primary="#97e27d", secondary="#6cd46b", pattern="diagonal",
                 pattern_color="#ade86a", pattern_opacity=0.6, diag_width=22):
    W, H = 512, 512
    parts = [svg_header(W, H)]
    defs = ""
    fill = primary
    if pattern == "linear":
        defs = mk_linear_gradient("b1", primary, secondary)
        fill = 'url(#b1)'
    elif pattern == "diagonal":
        defs = mk_diagonal_stripes("b2", base_color=primary, stripe_color=pattern_color,
                                   opacity=pattern_opacity, gap=max(8, int(diag_width)))
        fill = 'url(#b2)'

    parts.append(defs)
    # backpack dome + strap
    parts.append(f'<path d="M128,184 A128,128 0 0 1 384,184 L384,210 A256,120 0 0 0 128,210 Z" fill="{fill}" {outline()}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def loot_shirt_svg(tint="#a66cff"):
    W, H = 256, 256
    parts = [svg_header(W, H)]
    # cute tee icon
    parts.append(f'<path d="M40,70 L90,50 L120,80 L136,80 L166,50 L216,70 L190,110 L190,200 L66,200 L66,110 Z" fill="{tint}" {outline()}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

# ==============================
# Data model for export
# ==============================

RARITY_MAP = {
    "Common (1)": 1,
    "Uncommon (2)": 2,
    "Rare (3)": 3,
    "Epic (4)": 4,
    "Legendary (5)": 5,
}

@dataclass
class OutfitTS:
    name: str
    baseTint: str
    handTint: str
    footTint: str
    backpackTint: str
    baseSprite: str
    handSprite: str
    footSprite: str
    backpackSprite: str
    lootSprite: str
    lootTint: str
    nodrop_on_death: bool
    rarity: int
    lore: str
    no_drop: bool
    obstacle_type: str
    base_scale: float
    ghillie: bool

    def to_typescript(self, outfit_id: str) -> str:
        # Build a defineOutfitSkin(...) block mirroring the game's format
        return f"""// Auto-generated by Survev.io Skin Creator
// Place sprite files under your game's /img paths or update paths below.

export const {outfit_id} = defineOutfitSkin("outfitBase", {{
  name: "{self.name}",
  noDropOnDeath: {str(self.nodrop_on_death).lower()},
  rarity: {self.rarity},
  lore: {json.dumps(self.lore)},
  skinImg: {{
    baseTint: {self.baseTint},
    baseSprite: "{self.baseSprite}",
    handTint: {self.handTint},
    handSprite: "{self.handSprite}",
    footTint: {self.footTint},
    footSprite: "{self.footSprite}",
    backpackTint: {self.backpackTint},
    backpackSprite: "{self.backpackSprite}",
  }},
  lootImg: {{
    sprite: "{self.lootSprite}",
    tint: {self.lootTint},
  }},
  {"baseType: \"outfit\"," if True else ""}
  {"noDrop: true," if self.no_drop else ""}
  {"obstacleType: " + json.dumps(self.obstacle_type) + "," if self.obstacle_type else ""}
  {"baseScale: " + str(self.base_scale) + "," if self.base_scale not in (1.0, 0.0) else ""}
  {"ghillie: true," if self.ghillie else ""}
}});"""

# ==============================
# UI
# ==============================

st.set_page_config(page_title="Survev.io Skin Creator", page_icon="🎨", layout="wide")
st.title("Survev.io Skin Creator")

with st.sidebar:
    st.header("Meta")
    skin_name = st.text_input("Skin name", value="DJ Hyperfresh")
    lore = st.text_area("Lore / Description", value="Ya gonna marry the pink short squid already?")
    rarity_label = st.selectbox("Rarity", list(RARITY_MAP.keys()), index=2)
    no_drop_on_death = st.checkbox("noDropOnDeath (keep on death)", value=True)
    no_drop_flag = st.checkbox("noDrop (never drops)", value=False)
    ghillie = st.checkbox("ghillie (match ghillie color in mode)", value=False)
    obstacle_type = st.text_input("obstacleType (for event skins)", value="")
    base_scale = st.number_input("baseScale (advanced, leave 1.0)", value=1.0, format="%.2f")

st.subheader("Backpack")
bp_col1, bp_col2, bp_col3 = st.columns(3)
with bp_col1:
    bp_primary = st.color_picker("Backpack primary", "#97e27d")
with bp_col2:
    bp_secondary = st.color_picker("Backpack secondary", "#6cd46b")
with bp_col3:
    bp_pattern = st.selectbox("Backpack fill type", ["diagonal", "linear", "none"], index=0)
bp_diag_color = st.color_picker("Backpack diag color", "#ade86a")
bp_diag_width = st.slider("Backpack diag width", 8, 48, 22)
bp_opacity = st.slider("Pattern opacity", 0.0, 1.0, 0.6)

st.subheader("Body")
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    body_primary = st.color_picker("Body primary", "#a66cff")
with b_col2:
    body_secondary = st.color_picker("Body secondary", "#58a5ff")
with b_col3:
    body_pattern = st.selectbox("Body fill type", ["none", "linear", "diagonal"], index=2)
body_diag_color = st.color_picker("Body diag color", "#a7ff3f")
body_diag_width = st.slider("Body diag width", 8, 48, 26)
body_opacity = st.slider("Body pattern opacity", 0.0, 1.0, 0.68)

st.subheader("Hands")
h_col1, h_col2 = st.columns(2)
with h_col1:
    hands_primary = st.color_picker("Hands primary", "#ffcc88")
with h_col2:
    hands_secondary = st.color_picker("Hands secondary", "#ff9966")

st.subheader("Feet")
f_col1, f_col2 = st.columns(2)
with f_col1:
    feet_primary = st.color_picker("Feet primary", "#58a5ff")
with f_col2:
    feet_secondary = st.color_picker("Feet secondary", "#3f7bdc")

st.subheader("Loot Icon")
loot_tint = st.color_picker("Loot shirt tint", "#a66cff")

# Previews (stacked to resemble in-game layering: backpack -> body -> hands/feet)
st.header("Preview")
prev_col = st.columns(3)

bp_svg = backpack_svg(bp_primary, bp_secondary, bp_pattern, bp_diag_color, bp_opacity, bp_diag_width)
body_svg_str = body_svg(body_primary, body_secondary, body_pattern, body_diag_color, body_opacity, body_diag_width)
hands_svg_str = hands_svg(hands_primary, hands_secondary)
feet_svg_str = feet_svg(feet_primary, feet_secondary)
loot_svg_str = loot_shirt_svg(loot_tint)

def show_svg(svg_str, title):
    st.markdown(f"**{title}**", help=title)
    st.markdown(f"<div>{svg_str}</div>", unsafe_allow_html=True)

with prev_col[0]:
    show_svg(bp_svg, "Backpack")
with prev_col[1]:
    show_svg(body_svg_str, "Body")
with prev_col[2]:
    show_svg(hands_svg_str, "Hands")
    show_svg(feet_svg_str, "Feet")

st.markdown("---")

# ==============================
# Export section
# ==============================
st.header("Export")

colA, colB = st.columns(2)
with colA:
    outfit_id = sanitize(skin_name)  # TS variable id
    base_rgb = hex_to_rgb(body_primary)
    hand_rgb = hex_to_rgb(hands_primary)
    foot_rgb = hex_to_rgb(feet_primary)
    backpack_rgb = hex_to_rgb(bp_primary)
    loot_rgb = hex_to_rgb(loot_tint)

    # default in-zip paths that mirror game
    baseSpritePath = f"img/player/player-base-{outfit_id.lower()}.svg"
    handSpritePath = f"img/player/player-hands-{outfit_id.lower()}.svg"
    footSpritePath = f"img/player/player-feet-{outfit_id.lower()}.svg"
    backpackSpritePath = f"img/player/player-circle-base-{outfit_id.lower()}.svg"
    lootSpritePath = f"img/loot/loot-shirt-outfit{outfit_id}.svg"

    outf = OutfitTS(
        name=skin_name,
        baseTint=rgb_to_hex_literal(base_rgb),
        handTint=rgb_to_hex_literal(hand_rgb),
        footTint=rgb_to_hex_literal(foot_rgb),
        backpackTint=rgb_to_hex_literal(backpack_rgb),
        baseSprite=baseSpritePath,
        handSprite=handSpritePath,
        footSprite=footSpritePath,
        backpackSprite=backpackSpritePath,
        lootSprite=lootSpritePath,
        lootTint=rgb_to_hex_literal(loot_rgb),
        nodrop_on_death=no_drop_on_death,
        rarity=RARITY_MAP[rarity_label],
        lore=lore,
        no_drop=no_drop_flag,
        obstacle_type=obstacle_type.strip(),
        base_scale=float(base_scale),
        ghillie=ghillie,
    )

    ts_code = outf.to_typescript(outfit_id=f"outfit{outfit_id}")

    st.code(ts_code, language="typescript")

with colB:
    st.markdown("**What you’ll get in the ZIP**")
    st.markdown("""
- `img/player/player-base-<name>.svg` (body)
- `img/player/player-hands-<name>.svg` (hands)
- `img/player/player-feet-<name>.svg` (feet)
- `img/player/player-circle-base-<name>.svg` (backpack)
- `img/loot/loot-shirt-outfit<name>.svg` (loot icon)
- `export/outfit_<name>.ts` (ready `defineOutfitSkin(...)` block)
    """.strip())

# Create ZIP
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(baseSpritePath, body_svg_str)
    zf.writestr(handSpritePath, hands_svg_str)
    zf.writestr(footSpritePath, feet_svg_str)
    zf.writestr(backpackSpritePath, bp_svg)
    zf.writestr(lootSpritePath, loot_svg_str)
    zf.writestr(f"export/outfit_{outfit_id}.ts", ts_code)
zip_bytes = buf.getvalue()

st.download_button(
    "⬇️ Download sprites + TypeScript config (ZIP)",
    data=zip_bytes,
    file_name=f"{outfit_id}_survev_skin.zip",
    mime="application/zip",
)

st.caption("Tip: move the generated `img/...` files into your game's asset folder and paste the exported TypeScript into your skins file.")
