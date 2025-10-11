import io
import json
import re
import zipfile
from dataclasses import dataclass
from typing import Optional, Tuple

import streamlit as st
import urllib.parse

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
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" shape-rendering="geometricPrecision" '
        f'text-rendering="geometricPrecision">'
    )

def svg_footer():
    return "</svg>"

def outline(stroke: Optional[str] = "#000000", width: Optional[float] = 8):
    if stroke is None or width is None:
        return ""
    return f'stroke="{stroke}" stroke-width="{width}"'


def clamp_byte(value: float) -> int:
    return max(0, min(255, int(round(value))))


def lighten(hex_str: str, amount: float) -> str:
    r, g, b = hex_to_rgb(hex_str)
    r = clamp_byte(r + (255 - r) * amount)
    g = clamp_byte(g + (255 - g) * amount)
    b = clamp_byte(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def darken(hex_str: str, amount: float) -> str:
    r, g, b = hex_to_rgb(hex_str)
    r = clamp_byte(r * (1 - amount))
    g = clamp_byte(g * (1 - amount))
    b = clamp_byte(b * (1 - amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def svg_data_uri(svg_text: str) -> str:
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg_text)

# ---------------------------
# Fill / pattern generators
# ---------------------------

def def_linear_grad(id_, c1, c2, angle_deg=45):
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

def build_fill(style: str, base: str, c2: str, extra_color: str, angle: int, gap: int, opacity: float, size: int):
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
# Clean part SVGs
# ---------------------------

def svg_backpack(
    fill_defs: str,
    fill_ref: str,
    cfg,
    stroke_col="#333333",
    stroke_w=11.014,
):
    W = H = 148
    parts = [svg_header(W, H)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(
        f'<ellipse cx="74" cy="74" rx="66.5" ry="66.5" fill="{fill_ref}" '
        f'{outline(stroke_col, stroke_w)} />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_body(fill_defs: str, fill_ref: str, cfg, stroke_col="#000", stroke_w=8):
    W = H = 140
    parts = [svg_header(W, H)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(f'<ellipse cx="70" cy="70" rx="66" ry="66" fill="{fill_ref}" />')
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_hands(
    fill_defs: str,
    fill_ref: str,
    cfg,
    stroke_col="#333333",
    stroke_w=11.096,
):
    W = H = 76
    parts = [svg_header(W, H)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(
        f'<ellipse cx="38" cy="38" rx="30.4" ry="30.4" fill="{fill_ref}" '
        f'{outline(stroke_col, stroke_w)} />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_feet(
    fill_defs: str,
    fill_ref: str,
    cfg,
    stroke_col="#333333",
    stroke_w=4.513,
):
    W = H = 38
    parts = [svg_header(W, H)]
    if fill_defs:
        parts.append(fill_defs)
    parts.append(
        f'<ellipse cx="19" cy="19" rx="15.7" ry="9.8" fill="{fill_ref}" '
        f'{outline(stroke_col, stroke_w)} />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_body_preview_overlay() -> str:
    # Preview-only overlay that mimics the in-game body outline and helmet.
    W = H = 160
    parts = [svg_header(W, H)]
    # Outer armor ring to mimic the in-game decorative outline
    center = W / 2
    ring_stroke = "#20160a"
    ring_width = 12
    parts.append(
        f'<circle cx="{center}" cy="{center}" r="{70}" fill="none" '
        f'stroke="{ring_stroke}" stroke-width="{ring_width}" />'
    )
    # Circular helmet accent (preview only)
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

# --- Loot icon that matches loot-shirt-outfitBase.svg (no stroke, tint fill) ---
def svg_loot_shirt_base(tint_hex: str):
    # This is the exact silhouette path used by loot-shirt-outfitBase.svg;
    # we only change the fill color to the chosen tint.
    path_d = (
        "M63.993 8.15c-10.38 0-22.796 3.526-30.355 7.22-8.038 3.266-14.581 7.287-19.253 14.509C8.102 "
        "39.594 5.051 54.6 7.13 78.482c5.964 2.07 11.333 1.45 16.842-.415-1.727-7.884-1.448-15.764.496-22.204 "
        "2.126-7.044 6.404-12.722 12.675-13.701l2.77-.432.074 2.803c.054 2.043.09 4.17.116 6.335l.027 "
        "6.312c-.037 8.798-.382 18.286-1.277 27.845 5.637 1.831 14.806 2.954 23.964 3.019l4.597-.058c8.53-.275 "
        "16.742-1.449 21.665-3.063-1.093-14.65-1.166-29.434-1.52-41.334l-.097-3.283 3.18.824c6.238 1.617 "
        "10.55 7.376 12.76 14.507 2.02 6.51 2.353 14.37.64 22.248a29.764 29.764 0 0 0 12.847 1.181l4.399-.588c1.033-18.811-1.433-37.403-6.27-46.264l-4.408-6.376c-4.647-5.357-10.62-8.399-17.665-11.074-6.746-3.458-18.358-6.614-28.95-6.614zm0 3.05c6.494 0 13.37 1.942 19.274 4.516-3.123 2.758-6.971 4.665-11.067 5.754l-7.852 17.31-6.838-16.882c-4.757-.93-9.26-2.957-12.783-6.174C50.9 13.081 57.809 11.2 63.993 11.2zm.58 28.539l3.512 5.327-3.497 5.053-3.53-5.053zm0 11.888l3.512 5.328-3.497 5.052-3.53-5.053 3.514-5.327zm0 11.733l3.512 5.327-3.497 5.054-3.53-5.054zm0 11.876l3.512 5.327-3.497 5.054-3.53-5.053 3.514-5.327zm25.079 13.715c-6.61 2.055-15.829 2.907-25.277 2.951-9.5.045-18.965-.744-25.902-2.892-.205 1.785-.43 3.569-.678 5.347 5.968 2.132 16.346 3.408 26.497 3.36 10.143-.05 20.355-1.444 25.912-3.433a241.302 241.302 0 0 1-.552-5.333zm1.368 9.086c-6.782 2.308-16.533 3.262-26.53 3.31-2.935.015-5.866-.052-8.724-.213l-4.227-.315c-5.358-.5-10.307-1.382-14.329-2.758-.897 5.43-2.02 10.772-3.413 15.903 2.117 1.06 4.41 1.968 6.835 2.733l3.97 1.096c15.85 3.805 35.88 2.156 49.601-3.513-1.355-5.09-2.387-10.57-3.183-16.243z"
    )
    parts = [svg_header(128, 128)]
    parts.append(f'<path d="{path_d}" fill="{tint_hex}"/>')  # no stroke
    parts.append(svg_footer())
    return "\n".join(parts)


def svg_loot_circle_inner(base_hex: str):
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


def svg_loot_circle_outer(stroke_hex: str):
    fill_col = lighten(stroke_hex, 0.6)
    parts = [svg_header(146, 146)]
    parts.append(
        f'<ellipse cx="73" cy="73" rx="68.861" ry="68.769" fill="{fill_col}" '
        'fill-opacity="0.27" '
        f'stroke="{stroke_hex}" stroke-width="6.21" stroke-opacity="0.77" />'
    )
    parts.append(svg_footer())
    return "\n".join(parts)

# ---------------------------
# Export model
# ---------------------------

RARITY_OPTIONS = [
    ("(omit)", None),
    ("Stock", "Rarity.Stock"),
    ("Common", "Rarity.Common"),
    ("Uncommon", "Rarity.Uncommon"),
    ("Rare", "Rarity.Rare"),
    ("Epic", "Rarity.Epic"),
    ("Legendary", "Rarity.Legendary"),
    ("Mythic", "Rarity.Mythic"),
]

@dataclass
class ExportOpts:
    skin_name: str
    lore: str
    rarity: Optional[str]
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
    ref_ext: str

    def ts_block(self, ident: str, filenames, tints) -> str:
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
# UI – Defaults = BaseDefs outfitBase
# ---------------------------

st.set_page_config(page_title="Survev.io Skin Creator", page_icon="🎨", layout="wide")

st.sidebar.title("Meta")
skin_name = st.sidebar.text_input("Skin name", "Basic Outfit")
lore = st.sidebar.text_area("Lore / description", "")
rarity_label = st.sidebar.selectbox("Rarity", [label for label, _ in RARITY_OPTIONS], index=0)
noDropOnDeath = st.sidebar.checkbox("noDropOnDeath (keep on death)", value=False)
noDrop = st.sidebar.checkbox("noDrop (never drops)", value=False)
ghillie = st.sidebar.checkbox("ghillie (match ghillie color in mode)", value=False)
obstacleType = st.sidebar.text_input("obstacleType (costume skins)", "")
baseScale = st.sidebar.number_input("baseScale", value=1.0, format="%.2f")

st.sidebar.markdown("---")
st.sidebar.subheader("Backpack Outline")
bp_stroke_col = st.sidebar.color_picker("Backpack outline color", "#333333")
bp_stroke_w = st.sidebar.slider(
    "Backpack outline width",
    min_value=6.0,
    max_value=20.0,
    value=11.0,
    step=0.1,
)

st.sidebar.subheader("Hands Outline")
hand_stroke_col = st.sidebar.color_picker("Hands outline color", "#333333")
hand_stroke_w = st.sidebar.slider(
    "Hands outline width",
    min_value=6.0,
    max_value=20.0,
    value=11.1,
    step=0.1,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Asset Reference")
ref_ext = st.sidebar.selectbox("Reference extension used in TS", [".img", ".svg"], index=0)
st.sidebar.caption("ZIP always contains SVG files; choose how your TS should reference them in-game.")

st.sidebar.markdown("---")

st.sidebar.subheader("Loot Icon (defaults to BaseDefs)")
loot_border_on = st.sidebar.checkbox("Include loot border + scale fields", value=True)
loot_border_name = st.sidebar.text_input("Outer circle sprite name", "loot-circle-outer-01")
loot_inner_name = st.sidebar.text_input("Inner circle sprite name", "loot-circle-inner-01")
loot_border_tint = st.sidebar.color_picker("Outer circle stroke tint", "#000000")
loot_inner_glow = st.sidebar.color_picker("Inner circle glow color", "#fcfcfc")
loot_scale = st.sidebar.slider("Loot scale", 0.05, 0.5, 0.20)

def part_controls(title, defaults):
    st.sidebar.markdown("---")
    st.sidebar.subheader(title)
    primary = st.sidebar.color_picker(f"{title} primary", defaults["primary"])
    secondary = st.sidebar.color_picker(f"{title} secondary", defaults["secondary"])
    style = st.sidebar.selectbox(
        f"{title} fill",
        ["Solid","Linear Gradient","Radial Gradient","Diagonal Stripes","Horizontal Stripes","Vertical Stripes","Crosshatch","Dots","Checker"],
        index=0, key=f"{title}-style"
    )
    extra = st.sidebar.color_picker(f"{title} pattern/extra color", defaults["extra"])
    angle = st.sidebar.slider(f"{title} angle (gradients/stripes)", 0, 180, defaults["angle"])
    gap = st.sidebar.slider(f"{title} gap/spacing", 6, 48, defaults["gap"])
    opacity = st.sidebar.slider(f"{title} pattern opacity", 0.0, 1.0, defaults["opacity"])
    size = st.sidebar.slider(f"{title} dot/check size", 4, 40, defaults["size"])
    tint = st.sidebar.color_picker(f"{title} tint (OutfitDef)", defaults["tint"])
    return dict(primary=primary, secondary=secondary, style=style, extra=extra, angle=angle, gap=gap, opacity=opacity, size=size, tint=tint)

# BaseDefs defaults
body_cfg = part_controls("Body",     dict(primary="#f8c574", secondary="#f8c574", extra="#cba86a", angle=45, gap=24, opacity=0.6, size=14, tint="#f8c574"))
hand_cfg = part_controls("Hands",    dict(primary="#f8c574", secondary="#f8c574", extra="#cba86a", angle=45, gap=20, opacity=0.6, size=10, tint="#f8c574"))
bp_cfg   = part_controls("Backpack", dict(primary="#816537", secondary="#816537", extra="#6e5630", angle=45, gap=22, opacity=0.6, size=12, tint="#816537"))

loot_icon_tint = st.sidebar.color_picker("Loot shirt tint", "#ffffff")
feet_stroke_w = hand_stroke_w * (4.513 / 11.096)

# ---------------------------
# Build fills & sprites
# ---------------------------

def build_part_svg(cfg, make_svg, stroke_col=None, stroke_w=None):
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


body_svg_text = build_part_svg(body_cfg, svg_body, None, None)
hands_svg_text = build_part_svg(
    hand_cfg, svg_hands, hand_stroke_col, hand_stroke_w
)
backpack_svg_text = build_part_svg(
    bp_cfg, svg_backpack, bp_stroke_col, bp_stroke_w
)
feet_svg_text = build_part_svg(
    hand_cfg, svg_feet, hand_stroke_col, feet_stroke_w
)
loot_svg_text = svg_loot_shirt_base(loot_icon_tint)  # << matches outfitBase asset
loot_inner_svg_text = svg_loot_circle_inner(loot_inner_glow)
loot_outer_svg_text = svg_loot_circle_outer(loot_border_tint)
preview_overlay_svg_text = svg_body_preview_overlay()

# ---------------------------
# Combined preview
# ---------------------------

st.title("Survev.io Skin Creator")
st.caption(
    "All settings on the left. Preview shows a layered mock-up (backpack, body, armor overlay, hands) plus individual sprites."
)

body_uri = svg_data_uri(body_svg_text)
hands_uri = svg_data_uri(hands_svg_text)
feet_uri = svg_data_uri(feet_svg_text)
backpack_uri = svg_data_uri(backpack_svg_text)
loot_uri = svg_data_uri(loot_svg_text)
loot_inner_uri = svg_data_uri(loot_inner_svg_text)
loot_outer_uri = svg_data_uri(loot_outer_svg_text)
overlay_uri = svg_data_uri(preview_overlay_svg_text)

stage_width, stage_height = 420, 480
body_w = body_h = 134
backpack_w = backpack_h = 148
hand_w = hand_h = 52
overlay_w = overlay_h = 160

body_left = (stage_width - body_w) // 2
body_top = 190
backpack_left = (stage_width - backpack_w) // 2
backpack_top = 110
hand_left = body_left - 32
hand_right = stage_width - hand_left - hand_w
hand_top = body_top + body_h - 34
overlay_left = body_left - (overlay_w - body_w) // 2
overlay_top = body_top - (overlay_h - body_h) // 2

combined_preview = f"""
<style>
  .preview-stage {{
    position: relative;
    width: {stage_width}px;
    height: {stage_height}px;
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
    top: {backpack_top}px;
    width: {backpack_w}px;
    height: {backpack_h}px;
  }}
  .preview-body {{
    left: {body_left}px;
    top: {body_top}px;
    width: {body_w}px;
    height: {body_h}px;
  }}
  .preview-overlay {{
    left: {overlay_left}px;
    top: {overlay_top}px;
    width: {overlay_w}px;
    height: {overlay_h}px;
  }}
  .preview-hand-left {{
    left: {hand_left}px;
    top: {hand_top}px;
    width: {hand_w}px;
    height: {hand_h}px;
  }}
  .preview-hand-right {{
    left: {hand_right}px;
    top: {hand_top}px;
    width: {hand_w}px;
    height: {hand_h}px;
    transform: scaleX(-1);
    transform-origin: center;
  }}
</style>
<div style="display:flex;flex-wrap:wrap;gap:32px;align-items:flex-start;justify-content:center;">
  <div class="preview-stage">
    <img class="preview-backpack" src="{backpack_uri}" alt="Backpack" />
    <img class="preview-body" src="{body_uri}" alt="Body" />
    <img class="preview-overlay" src="{overlay_uri}" alt="Body overlay" />
    <img class="preview-hand-left" src="{hands_uri}" alt="Left hand" />
    <img class="preview-hand-right" src="{hands_uri}" alt="Right hand" />
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;flex:0 0 auto;align-items:center;">
    <div style="display:grid;grid-template-columns:repeat(2,auto);gap:16px;justify-items:center;">
      <figure style="margin:0;text-align:center;">
        <img src="{body_uri}" width="140" height="140" alt="Body sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Body</figcaption>
      </figure>
      <figure style="margin:0;text-align:center;">
        <img src="{backpack_uri}" width="148" height="148" alt="Backpack sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Backpack</figcaption>
      </figure>
      <figure style="margin:0;text-align:center;">
        <img src="{hands_uri}" width="76" height="76" alt="Hands sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Hands</figcaption>
      </figure>
      <figure style="margin:0;text-align:center;">
        <img src="{feet_uri}" width="38" height="38" alt="Feet sprite" style="image-rendering:optimizeQuality;" />
        <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Feet</figcaption>
      </figure>
    </div>
    <figure style="margin:0;text-align:center;">
      <div class="loot-stage">
        <img class="loot-outer" src="{loot_outer_uri}" alt="Loot outer" />
        <img class="loot-inner" src="{loot_inner_uri}" alt="Loot inner" />
        <img class="loot-shirt" src="{loot_uri}" alt="Loot shirt" />
      </div>
      <figcaption style="font-size:0.8rem;color:#666;margin-top:4px;">Loot icon</figcaption>
    </figure>
  </div>
</div>
"""

st.markdown(combined_preview, unsafe_allow_html=True)

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
    "feet": f"player-feet-{base_id}.{ext_ref}",
    "backpack": f"player-circle-base-{base_id}.{ext_ref}",
    "loot": f"loot-shirt-outfit{base_id}.{ext_ref}",
    "border": f"{loot_border_name}.{ext_ref}" if loot_border_on and loot_border_name else "",
    "inner": f"{loot_inner_name}.{ext_ref}" if loot_border_on and loot_inner_name else "",
}

tints = {
    "base": rgb_to_ts_hex(hex_to_rgb(body_cfg["tint"])),
    "hand": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "foot": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "backpack": rgb_to_ts_hex(hex_to_rgb(bp_cfg["tint"])),
    "loot": rgb_to_ts_hex(hex_to_rgb(loot_icon_tint)),
    "border": rgb_to_ts_hex(hex_to_rgb(loot_border_tint)),
}

rarity_value = next(value for label, value in RARITY_OPTIONS if label == rarity_label)

opts = ExportOpts(
    skin_name=skin_name,
    lore=lore,
    rarity=rarity_value,
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
)

ts_code = opts.ts_block(ident=ident, filenames=filenames, tints=tints)

left, right = st.columns(2)
with left:
    st.subheader("TypeScript export")
    st.code(ts_code, language="typescript")
with right:
    st.subheader("What’s inside the ZIP")
    zip_lines = [
        f"- `{filenames['base']}` (body)",
        f"- `{filenames['hands']}` (hands)",
        f"- `{filenames['feet']}` (feet)",
        f"- `{filenames['backpack']}` (backpack)",
    ]
    if loot_border_on and filenames.get("border"):
        zip_lines.append(f"- `{filenames['border']}` (loot border)")
    if loot_border_on and filenames.get("inner"):
        zip_lines.append(f"- `{filenames['inner']}` (loot inner glow)")
    zip_lines.extend(
        [
            f"- `{filenames['loot']}` (loot icon – shirt silhouette, no stroke)",
            f"- `export/{ident}.ts` (ready `defineOutfitSkin(...)`)",
        ]
    )
    st.markdown("\n".join(zip_lines))

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(filenames["base"].replace(".img", ".svg"), body_svg_text)
    zf.writestr(filenames["hands"].replace(".img", ".svg"), hands_svg_text)
    zf.writestr(filenames["feet"].replace(".img", ".svg"), feet_svg_text)
    zf.writestr(filenames["backpack"].replace(".img", ".svg"), backpack_svg_text)
    zf.writestr(filenames["loot"].replace(".img", ".svg"), loot_svg_text)
    if loot_border_on and filenames.get("border"):
        zf.writestr(filenames["border"].replace(".img", ".svg"), loot_outer_svg_text)
    if loot_border_on and filenames.get("inner"):
        zf.writestr(filenames["inner"].replace(".img", ".svg"), loot_inner_svg_text)
    zf.writestr(f"export/{ident}.ts", ts_code)
zip_bytes = buf.getvalue()

st.download_button(
    "⬇️ Download sprites + TypeScript config (ZIP)",
    data=zip_bytes,
    file_name=f"{base_id}_survev_skin.zip",
    mime="application/zip",
)
