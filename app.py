import io
import json
import re
import zipfile
from dataclasses import dataclass
from typing import Tuple

import streamlit as st

# ---------------------------
# Helpers
# ---------------------------

def sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", name.strip()) or "Custom"

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def rgb_to_ts_hex(rgb: Tuple[int, int, int]) -> str:
    return f"0x{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def svg_header(w=512, h=512):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'

def svg_footer():
    return "</svg>"

def outline(stroke="#000000", width=8):
    return f'stroke="{stroke}" stroke-width="{width}"'

# ---------------------------
# Fill / pattern generators
# ---------------------------

def def_linear_grad(id_, c1, c2, angle_deg=45):
    # rotate the gradient by angle_deg using gradientTransform
    return (
        f'<defs><linearGradient id="{id_}" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="0" x2="512" y2="0" gradientTransform="rotate({angle_deg} 256 256)">'
        f'<stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/></linearGradient></defs>'
    )

def def_radial_grad(id_, c1, c2):
    return (
        f'<defs><radialGradient id="{id_}" cx="50%" cy="45%" r="60%">'
        f'<stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/></radialGradient></defs>'
    )

def def_stripes(id_, base, stripe, gap=16, angle=45, opacity=0.6):
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap*2}" height="{gap*2}" '
        f'patternTransform="rotate({angle})">'
        f'<rect width="100%" height="100%" fill="{base}"/>'
        f'<rect x="0" y="0" width="{gap}" height="100%" fill="{stripe}" opacity="{opacity}"/></pattern></defs>'
    )

def def_crosshatch(id_, base, stripe, gap=16, opacity=0.6):
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}">'
        f'<rect width="100%" height="100%" fill="{base}"/>'
        f'<path d="M0,0 L{gap},0 M0,0 L0,{gap}" stroke="{stripe}" stroke-width="{gap/2}" opacity="{opacity}"/></pattern></defs>'
    )

def def_dots(id_, base, dot="#000", size=6, gap=22, opacity=0.6):
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}">'
        f'<rect width="100%" height="100%" fill="{base}"/>'
        f'<circle cx="{gap/2}" cy="{gap/2}" r="{size}" fill="{dot}" opacity="{opacity}"/>'
        f'</pattern></defs>'
    )

def def_checker(id_, c1, c2, size=16):
    return (
        f'<defs><pattern id="{id_}" patternUnits="userSpaceOnUse" width="{2*size}" height="{2*size}">'
        f'<rect width="{2*size}" height="{2*size}" fill="{c1}"/>'
        f'<rect x="{size}" width="{size}" height="{size}" y="0" fill="{c2}"/>'
        f'<rect x="0" y="{size}" width="{size}" height="{size}" fill="{c2}"/>'
        f'</pattern></defs>'
    )

# One function to produce (defs, fill_url) for a given style
def build_fill(style: str, base: str, c2: str, extra_color: str, angle: int, gap: int, opacity: float, size: int):
    """Returns (defs, fill_attr)"""
    if style == "Solid":
        return ("", base)
    if style == "Linear Gradient":
        defs = def_linear_grad("lg", base, c2, angle)
        return (defs, 'url(#lg)')
    if style == "Radial Gradient":
        defs = def_radial_grad("rg", base, c2)
        return (defs, 'url(#rg)')
    if style == "Diagonal Stripes":
        defs = def_stripes("ds", base, extra_color, gap, angle, opacity)
        return (defs, 'url(#ds)')
    if style == "Horizontal Stripes":
        defs = def_stripes("hs", base, extra_color, gap, 0, opacity)
        return (defs, 'url(#hs)')
    if style == "Vertical Stripes":
        defs = def_stripes("vs", base, extra_color, gap, 90, opacity)
        return (defs, 'url(#vs)')
    if style == "Crosshatch":
        defs = def_crosshatch("ch", base, extra_color, gap, opacity)
        return (defs, 'url(#ch)')
    if style == "Dots":
        defs = def_dots("pd", base, extra_color, size, gap, opacity)
        return (defs, 'url(#pd)')
    if style == "Checker":
        defs = def_checker("ck", base, c2, size)
        return (defs, 'url(#ck)')
    return ("", base)

# ---------------------------
# Part SVGs (no odd extras)
# ---------------------------

def svg_backpack(fill_defs: str, fill_ref: str, stroke_col="#000", stroke_w=8):
    W = H = 512
    parts = [svg_header(W, H)]
    parts.append(fill_defs)
    # Dome backpack
    parts.append(f'<path d="M128,184 A128,128 0 0 1 384,184 L384,210 A256,120 0 0 0 128,210 Z" fill="{fill_ref}" {outline(stroke_col, stroke_w)}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def svg_body(fill_defs: str, fill_ref: str, stroke_col="#000", stroke_w=8):
    W = H = 512
    parts = [svg_header(W, H)]
    parts.append(fill_defs)
    # Simple body circle – no extra band
    parts.append(f'<circle cx="256" cy="288" r="170" fill="{fill_ref}" {outline(stroke_col, stroke_w)}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def svg_hands(fill_defs: str, fill_ref: str, stroke_col="#000", stroke_w=8):
    W = H = 512
    parts = [svg_header(W, H)]
    parts.append(fill_defs)
    parts.append(f'<circle cx="160" cy="420" r="48" fill="{fill_ref}" {outline(stroke_col, stroke_w)}/>')
    parts.append(f'<circle cx="352" cy="420" r="48" fill="{fill_ref}" {outline(stroke_col, stroke_w)}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

def svg_loot(tint_hex: str, stroke_col="#000", stroke_w=8):
    W = H = 256
    parts = [svg_header(W, H)]
    parts.append(f'<path d="M40,70 L90,50 L120,80 L136,80 L166,50 L216,70 L190,110 L190,200 L66,200 L66,110 Z" fill="{tint_hex}" {outline(stroke_col, stroke_w)}/>')
    parts.append(svg_footer())
    return "\n".join(parts)

# ---------------------------
# Export model
# ---------------------------

RARITY = {
    "Common (1)": 1,
    "Uncommon (2)": 2,
    "Rare (3)": 3,
    "Epic (4)": 4,
    "Legendary (5)": 5,
}

@dataclass
class ExportOpts:
    skin_name: str
    lore: str
    rarity: int
    noDropOnDeath: bool
    noDrop: bool
    ghillie: bool
    obstacleType: str
    baseScale: float
    lootBorderOn: bool
    lootBorderName: str
    lootBorderTint: str
    lootScale: float
    soundPickup: str
    ref_ext: str  # ".img" or ".svg"
    stroke_col: str
    stroke_w: int

    def ts_block(self, ident: str, filenames, tints) -> str:
        # filenames: dict with base/hand/foot/backpack/loot/border
        # tints: dict with base/hand/foot/backpack/loot
        lines = []
        lines.append(f'export const {ident} = defineOutfitSkin("outfitBase", {{')
        lines.append(f'  name: {json.dumps(self.skin_name)},')
        if self.noDropOnDeath:
            lines.append(f'  noDropOnDeath: true,')
        if self.noDrop:
            lines.append(f'  noDrop: true,')
        if self.rarity:
            lines.append(f'  rarity: {self.rarity},')
        if self.lore:
            lines.append(f'  lore: {json.dumps(self.lore)},')
        if self.ghillie:
            lines.append(f'  ghillie: true,')
        if self.obstacleType:
            lines.append(f'  obstacleType: {json.dumps(self.obstacleType)},')
        if abs(self.baseScale - 1.0) > 1e-6:
            lines.append(f'  baseScale: {self.baseScale},')

        lines.append('  skinImg: {')
        lines.append(f'    baseTint: {tints["base"]},')
        lines.append(f'    baseSprite: "{filenames["base"]}",')
        lines.append(f'    handTint: {tints["hand"]},')
        lines.append(f'    handSprite: "{filenames["hands"]}",')
        lines.append(f'    footTint: {tints["foot"]},')
        lines.append(f'    footSprite: "{filenames["feet"]}",')
        lines.append(f'    backpackTint: {tints["backpack"]},')
        lines.append(f'    backpackSprite: "{filenames["backpack"]}",')
        lines.append('  },')

        lines.append('  lootImg: {')
        lines.append(f'    sprite: "{filenames["loot"]}",')
        lines.append(f'    tint: {tints["loot"]},')
        if self.lootBorderOn and filenames.get("border"):
            lines.append(f'    border: "{filenames["border"]}",')
            lines.append(f'    borderTint: {tints["border"]},')
            lines.append(f'    scale: {self.lootScale},')
        lines.append('  },')

        if self.soundPickup:
            lines.append('  sound: {')
            lines.append(f'    pickup: {json.dumps(self.soundPickup)},')
            lines.append('  },')

        lines.append('});')
        return "\n".join(lines)

# ---------------------------
# UI – All controls on the left
# ---------------------------

st.set_page_config(page_title="Survev.io Skin Creator", page_icon="🎨", layout="wide")

st.sidebar.title("Meta")
skin_name = st.sidebar.text_input("Skin name", "DJ Hyperfresh")
lore = st.sidebar.text_area("Lore / description", "Ya gonna marry the pink short squid already?")
rarity_label = st.sidebar.selectbox("Rarity", list(RARITY.keys()), index=2)
noDropOnDeath = st.sidebar.checkbox("noDropOnDeath (keep on death)", value=True)
noDrop = st.sidebar.checkbox("noDrop (never drops)", value=False)
ghillie = st.sidebar.checkbox("ghillie (match ghillie color in mode)", value=False)
obstacleType = st.sidebar.text_input("obstacleType (costume skins)", "")
baseScale = st.sidebar.number_input("baseScale", value=1.0, format="%.2f")

st.sidebar.markdown("---")
st.sidebar.subheader("Sprite Outline")
stroke_col = st.sidebar.color_picker("Outline color", "#000000")
stroke_w = st.sidebar.slider("Outline width", 4, 16, 8)

st.sidebar.markdown("---")
st.sidebar.subheader("Asset Reference")
ref_ext = st.sidebar.selectbox("Reference extension used in TS", [".img", ".svg"], index=0)
st.sidebar.caption("ZIP always contains SVG files; choose how your TS should reference them in-game.")

st.sidebar.markdown("---")
st.sidebar.subheader("Loot Icon (Optional extras)")
loot_border_on = st.sidebar.checkbox("Include loot border + scale fields", value=False)
loot_border_name = st.sidebar.text_input("Border sprite name", "loot-circle-outer-01")
loot_border_tint = st.sidebar.color_picker("Border tint", "#000000")
loot_scale = st.sidebar.slider("Loot scale", 0.05, 0.5, 0.20)

# Part controls (Body / Hands / Backpack). Feet = Hands automatically.
def part_controls(title, defaults):
    st.sidebar.markdown("---")
    st.sidebar.subheader(title)
    primary = st.sidebar.color_picker(f"{title} primary", defaults["primary"])
    secondary = st.sidebar.color_picker(f"{title} secondary", defaults["secondary"])
    style = st.sidebar.selectbox(f"{title} fill", ["Solid","Linear Gradient","Radial Gradient","Diagonal Stripes","Horizontal Stripes","Vertical Stripes","Crosshatch","Dots","Checker"], index=1 if title=="Body" else 0, key=f"{title}-style")
    extra = st.sidebar.color_picker(f"{title} pattern/extra color", defaults["extra"])
    angle = st.sidebar.slider(f"{title} angle (gradients/stripes)", 0, 180, defaults["angle"])
    gap = st.sidebar.slider(f"{title} gap/spacing", 6, 48, defaults["gap"])
    opacity = st.sidebar.slider(f"{title} pattern opacity", 0.0, 1.0, defaults["opacity"])
    size = st.sidebar.slider(f"{title} dot/check size", 4, 40, defaults["size"])
    tint = st.sidebar.color_picker(f"{title} tint (OutfitDef)", defaults["tint"])
    return dict(primary=primary, secondary=secondary, style=style, extra=extra, angle=angle, gap=gap, opacity=opacity, size=size, tint=tint)

body_cfg = part_controls("Body", dict(primary="#a66cff", secondary="#58a5ff", extra="#a7ff3f", angle=45, gap=24, opacity=0.6, size=14, tint="#a66cff"))
hand_cfg = part_controls("Hands", dict(primary="#ffcc88", secondary="#ff9966", extra="#cc8855", angle=45, gap=20, opacity=0.6, size=10, tint="#ffcc88"))
bp_cfg   = part_controls("Backpack", dict(primary="#97e27d", secondary="#6cd46b", extra="#ade86a", angle=45, gap=22, opacity=0.6, size=12, tint="#97e27d"))

loot_tint = st.sidebar.color_picker("Loot tint (OutfitDef)", "#a66cff")

# ---------------------------
# Build fills & sprites
# ---------------------------

def part_svg_from_cfg(make_svg):
    defs, fill_ref = build_fill(
        style=cfg["style"],
        base=cfg["primary"],
        c2=cfg["secondary"],
        extra_color=cfg["extra"],
        angle=cfg["angle"],
        gap=cfg["gap"],
        opacity=cfg["opacity"],
        size=cfg["size"],
    )
    return make_svg(defs, fill_ref, stroke_col, stroke_w)

cfg = body_cfg
body_svg_text = part_svg_from_cfg(svg_body)
cfg = hand_cfg
hands_svg_text = part_svg_from_cfg(svg_hands)
cfg = bp_cfg
backpack_svg_text = part_svg_from_cfg(svg_backpack)
loot_svg_text = svg_loot(loot_tint, stroke_col, stroke_w)

# Feet = hands (no separate UI), tints copy hands tint
feet_svg_text = hands_svg_text  # sprite duplication

# ---------------------------
# Combined preview
# ---------------------------

st.title("Survev.io Skin Creator")
st.caption("Left: all settings. Right: combined preview. Download gives separate sprites + TypeScript snippet.")
col_prev = st.container()

# Composite preview simply draws the shapes again with positions
W = H = 640
preview = [svg_header(W, H)]
# Backpack (behind)
preview.append(backpack_svg_text.replace('width="512"', 'width="512"').replace('height="512"', 'height="512"').replace('viewBox="0 0 512 512"', 'viewBox="0 0 512 512"'))
# Body
preview.append(body_svg_text)
# Hands on top (we show the left/right ones near bottom)
preview.append(hands_svg_text)
preview.append(svg_footer())
col_prev.markdown(f'<div style="width:100%;max-width:820px;">{ "".join(preview) }</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------
# Export (ZIP + TS)
# ---------------------------

ident = f'outfit{sanitize(skin_name)}'
base_id = sanitize(skin_name).lower()

ext_ref = "img" if ref_ext == ".img" else "svg"

filenames = {
    "base": f"player-base-{base_id}.{ext_ref}",
    "hands": f"player-hands-{base_id}.{ext_ref}",
    "feet": f"player-feet-{base_id}.{ext_ref}",           # still exported; same art as hands
    "backpack": f"player-circle-base-{base_id}.{ext_ref}",
    "loot": f"loot-shirt-outfit{base_id}.{ext_ref}",
    "border": f"{loot_border_name}.{ext_ref}" if loot_border_on and loot_border_name else "",
}

tints = {
    "base": rgb_to_ts_hex(hex_to_rgb(body_cfg["tint"])),
    "hand": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "foot": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),   # foot = hand
    "backpack": rgb_to_ts_hex(hex_to_rgb(bp_cfg["tint"])),
    "loot": rgb_to_ts_hex(hex_to_rgb(loot_tint)),
    "border": rgb_to_ts_hex(hex_to_rgb(loot_border_tint)),
}

opts = ExportOpts(
    skin_name=skin_name,
    lore=lore,
    rarity=RARITY[rarity_label],
    noDropOnDeath=noDropOnDeath,
    noDrop=noDrop,
    ghillie=ghillie,
    obstacleType=obstacleType.strip(),
    baseScale=float(baseScale),
    lootBorderOn=loot_border_on,
    lootBorderName=loot_border_name,
    lootBorderTint=loot_border_tint,
    lootScale=float(loot_scale),
    soundPickup="clothes_pickup_01",
    ref_ext=ref_ext,
    stroke_col=stroke_col,
    stroke_w=stroke_w,
)

ts_code = opts.ts_block(
    ident=ident,
    filenames=filenames,
    tints=tints,
)

left, right = st.columns(2)
with left:
    st.subheader("TypeScript export")
    st.code(ts_code, language="typescript")
with right:
    st.subheader("What’s inside the ZIP")
    st.markdown(
        f"""
- `{filenames["base"]}` (body)
- `{filenames["hands"]}` (hands)
- `{filenames["feet"]}` (feet, auto = hands)
- `{filenames["backpack"]}` (backpack)
- `{filenames["loot"]}` (loot icon)
- `export/{ident}.ts` (ready `defineOutfitSkin(...)`)
        """.strip()
    )

# Create a zip with SVG files + TS snippet
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(filenames["base"].replace(".img", ".svg"), body_svg_text)
    zf.writestr(filenames["hands"].replace(".img", ".svg"), hands_svg_text)
    zf.writestr(filenames["feet"].replace(".img", ".svg"), feet_svg_text)
    zf.writestr(filenames["backpack"].replace(".img", ".svg"), backpack_svg_text)
    zf.writestr(filenames["loot"].replace(".img", ".svg"), loot_svg_text)
    zf.writestr(f"export/{ident}.ts", ts_code)
zip_bytes = buf.getvalue()

st.download_button(
    "⬇️ Download sprites + TypeScript config (ZIP)",
    data=zip_bytes,
    file_name=f"{base_id}_survev_skin.zip",
    mime="application/zip",
)
