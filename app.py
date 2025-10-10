# app.py
import io, zipfile, textwrap
from dataclasses import dataclass
from typing import Tuple
import streamlit as st

# ---------- helpers ----------
def clamp(v, lo, hi): return max(lo, min(hi, v))

def hex_to_rgb(hexstr: str) -> Tuple[int, int, int]:
    hexstr = hexstr.strip().replace("#", "")
    if len(hexstr) == 3:
        hexstr = "".join([c*2 for c in hexstr])
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb

def rgb_to_0x(rgb: Tuple[int,int,int]) -> str:
    return "0x%02x%02x%02x" % rgb

def parse_0x(s: str, fallback_rgb: Tuple[int,int,int]) -> Tuple[int,int,int]:
    try:
        s = s.strip().lower()
        if s.startswith("0x"):
            n = int(s, 16)
            r = (n >> 16) & 255
            g = (n >> 8) & 255
            b = n & 255
            return (r,g,b)
    except Exception:
        pass
    return fallback_rgb

def pattern_defs(kind: str, color: str, opacity: float = 0.6) -> str:
    # SVG <defs> for overlay patterns
    if kind == "None":
        return ""
    if kind == "Diagonal stripes":
        return f"""
        <defs>
          <pattern id="pDiag" patternUnits="userSpaceOnUse" width="16" height="16" patternTransform="rotate(45)">
            <rect width="16" height="16" fill="transparent"/>
            <rect width="8" height="16" fill="{color}" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    if kind == "Vertical stripes":
        return f"""
        <defs>
          <pattern id="pVert" patternUnits="userSpaceOnUse" width="16" height="16">
            <rect width="16" height="16" fill="transparent"/>
            <rect width="8" height="16" fill="{color}" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    if kind == "Horizontal stripes":
        return f"""
        <defs>
          <pattern id="pH" patternUnits="userSpaceOnUse" width="16" height="16">
            <rect width="16" height="16" fill="transparent"/>
            <rect width="16" height="8" y="8" fill="{color}" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    if kind == "Dots":
        return f"""
        <defs>
          <pattern id="pDots" patternUnits="userSpaceOnUse" width="12" height="12">
            <rect width="12" height="12" fill="transparent"/>
            <circle cx="3" cy="3" r="2.5" fill="{color}" opacity="{opacity}"/>
            <circle cx="9" cy="9" r="2.5" fill="{color}" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    if kind == "Grid":
        return f"""
        <defs>
          <pattern id="pGrid" patternUnits="userSpaceOnUse" width="14" height="14">
            <rect width="14" height="14" fill="transparent"/>
            <path d="M0 0 H14 M0 0 V14" stroke="{color}" stroke-width="2" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    if kind == "Zig-zag":
        return f"""
        <defs>
          <pattern id="pZ" patternUnits="userSpaceOnUse" width="16" height="8">
            <polyline points="0,8 4,0 8,8 12,0 16,8" fill="none" stroke="{color}" stroke-width="2" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    if kind == "Chevrons":
        return f"""
        <defs>
          <pattern id="pCh" patternUnits="userSpaceOnUse" width="18" height="18">
            <path d="M0 9 L9 0 L18 9 L9 18 Z" fill="{color}" opacity="{opacity}"/>
          </pattern>
        </defs>
        """
    return ""

def fill_layers(fill_type: str, primary: str, secondary: str) -> str:
    if fill_type == "Solid":
        return f'<rect x="0" y="0" width="100%" height="100%" fill="{primary}"/>'
    if fill_type == "Linear":
        return f"""
        <defs>
          <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{primary}"/>
            <stop offset="100%" stop-color="{secondary}"/>
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="100%" height="100%" fill="url(#g1)"/>
        """
    if fill_type == "Radial":
        return f"""
        <defs>
          <radialGradient id="g2" cx="50%" cy="40%" r="70%">
            <stop offset="0%" stop-color="{secondary}"/>
            <stop offset="100%" stop-color="{primary}"/>
          </radialGradient>
        </defs>
        <rect x="0" y="0" width="100%" height="100%" fill="url(#g2)"/>
        """
    return ""

def pattern_fill(kind: str) -> str:
    return "" if kind == "None" else {
        "Diagonal stripes":"url(#pDiag)",
        "Vertical stripes":"url(#pVert)",
        "Horizontal stripes":"url(#pH)",
        "Dots":"url(#pDots)",
        "Grid":"url(#pGrid)",
        "Zig-zag":"url(#pZ)",
        "Chevrons":"url(#pCh)"
    }[kind]

# Basic shapes (clean, no stroke by default)
def svg_backpack(w=512, h=320, stroke=None, stroke_w=0, fill_block="") -> str:
    outline = f'stroke="{stroke}" stroke-width="{stroke_w}"' if stroke else ''
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  {fill_block}
  <path d="M64 {h*0.70} Q {w*0.5} {h*0.55} {w-64} {h*0.70} 
           Q {w-64} {h*0.20} {w*0.5} {h*0.08} 
           Q 64 {h*0.20} 64 {h*0.70}Z" fill="url(#fillBase)" {outline}/>
</svg>
"""

def svg_body(w=640, h=640, stroke=None, stroke_w=0, fill_block="") -> str:
    outline = f'stroke="{stroke}" stroke-width="{stroke_w}"' if stroke else ''
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  {fill_block}
  <circle cx="{w/2}" cy="{h/2}" r="{min(w,h)*0.42}" fill="url(#fillBase)" {outline}/>
</svg>
"""

def svg_hands(w=512, h=220, stroke=None, stroke_w=0, fill_block="") -> str:
    outline = f'stroke="{stroke}" stroke-width="{stroke_w}"' if stroke else ''
    r = 100
    cx1, cx2 = 150, w-150
    cy = h-60
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  {fill_block}
  <circle cx="{cx1}" cy="{cy}" r="{r}" fill="url(#fillBase)" {outline}/>
  <circle cx="{cx2}" cy="{cy}" r="{r}" fill="url(#fillBase)" {outline}/>
</svg>
"""

def make_fill_block(fill_type, pri, sec, pat_kind, pat_color, pat_opacity):
    base = fill_layers(fill_type, pri, sec).replace('url(#g', 'url(#g')  # no-op, keeps ids
    defs = pattern_defs(pat_kind, pat_color, pat_opacity)
    pat = pattern_fill(pat_kind)
    overlay = f'<rect x="0" y="0" width="100%" height="100%" fill="{pat}"/>' if pat else ''
    return base.replace('</defs>', f'</defs>{defs}') if '</defs>' in base else defs + base + overlay

# Loot icon: 128x128 circle with radial grad + two arc bands (game-ish look)
def svg_loot_icon(tint_hex="#ffffff") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <defs>
    <radialGradient id="lg" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="{tint_hex}" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="{tint_hex}" stop-opacity="1.0"/>
    </radialGradient>
  </defs>
  <circle cx="64" cy="64" r="60" fill="url(#lg)"/>
  <path d="M16,64 A48,48 0 0 1 112,64" fill="none" stroke="#00000022" stroke-width="10"/>
  <path d="M24,48 A56,56 0 0 1 104,48" fill="none" stroke="#00000018" stroke-width="8"/>
</svg>"""

@dataclass
class DefaultBase:
    base_tint: Tuple[int,int,int] = (248,197,116)   # 0xf8c574
    hand_tint: Tuple[int,int,int] = (248,197,116)
    foot_tint: Tuple[int,int,int] = (248,197,116)   # kept for TS parity, not used in UI
    backpack_tint: Tuple[int,int,int] = (129,101,55)  # 0x816537
    loot_tint: Tuple[int,int,int] = (255,255,255)   # 0xffffff
    loot_border: str = "loot-circle-outer-01"
    loot_border_tint: Tuple[int,int,int] = (0,0,0)
    loot_scale: float = 0.2
    base_sprite: str = "player-base-01"
    hand_sprite: str = "player-hands-01"
    foot_sprite: str = "player-feet-01"
    backpack_sprite: str = "player-circle-base-01"
    loot_sprite: str = "loot-shirt-01"
    pickup_sound: str = "clothes_pickup_01"

BASE = DefaultBase()

st.set_page_config(page_title="Survev.io Skin Creator", layout="wide")

# ---------- Sidebar (all controls) ----------
with st.sidebar:
    st.header("Meta")
    skin_name = st.text_input("Skin name", value="Basic Outfit")
    lore = st.text_area("Lore / Description", value="Pure and simple.")
    rarity = st.selectbox("Rarity", options=["Stock (0)","Common (1)","Uncommon (2)","Rare (3)","Epic (4)","Mythic (5)"], index=0)

    noDropOnDeath = st.checkbox("noDropOnDeath (keep on death)", value=True,
        help="If set, you keep the outfit when dying.")
    noDrop = st.checkbox("noDrop (never drops)", value=False,
        help="Used on commanders/cobalt etc. Cannot drop this outfit.")
    ghillie = st.checkbox("ghillie (match ghillie color in mode)", value=False,
        help="When true, engine recolors this outfit to the mode's ghillie color.")
    obstacleType = st.text_input("obstacleType (costume skins)", value="", 
        help="For event/costume skins. Uses an obstacle sprite instead of normal player sprites (e.g. tree_07sp).")
    baseScale = st.number_input("baseScale (advanced, leave 1.0)", min_value=0.1, max_value=3.0, step=0.05, value=1.0,
        help="Scale applied to obstacle-type costume skins. Typically 1.0.")

    st.markdown("---")
    st.subheader("Sprite Outline", help="Preview helper. Real game SVGs usually have NO stroke. Leave off for exports.")
    preview_outline_color = st.color_picker("Outline color", "#000000")
    outline_width = st.slider("Outline width", min_value=4, max_value=16, value=10)
    include_outline_in_exports = st.checkbox("Include outline in exports (off = match game)", value=False)

    st.markdown("---")
    st.subheader("Asset Reference")
    ext = st.selectbox("Reference extension used in TS", ["img", "svg"], index=0,
                       help="The TypeScript snippet will reference sprites using this extension. The files you download are SVG.")

# Color + pattern sections
def palette_section(title, default_rgb, help_text_tint):
    st.markdown(f"### {title}")
    col1, col2 = st.columns(2)
    with col1:
        fill_type = st.selectbox("Fill type", ["Solid","Linear","Radial"])
        primary = st.color_picker("Primary color", rgb_to_hex(default_rgb))
        secondary = st.color_picker("Secondary color", "#5aa3ff" if title=="Body" else "#7ecb5a")
    with col2:
        pat = st.selectbox("Pattern", ["None","Diagonal stripes","Vertical stripes","Horizontal stripes","Dots","Grid","Zig-zag","Chevrons"])
        pat_color = st.color_picker("Pattern color", "#85ff00")
        pat_opacity = st.slider("Pattern opacity", 0.0, 1.0, 0.0 if pat=="None" else 0.6)

    st.caption("Tint fields below belong to **OutfitDef**; the game multiplies them at runtime. "
               "Exported SVGs are kept neutral; tint is not baked into the art.")
    tint = st.color_picker(f"{title} tint (OutfitDef)", rgb_to_hex(default_rgb), help=help_text_tint)
    return {
        "fill_type": fill_type,
        "primary": primary,
        "secondary": secondary,
        "pattern": pat,
        "pat_color": pat_color,
        "pat_opacity": pat_opacity,
        "tint": tint
    }

# ---------- Left editing panes ----------
left, right = st.columns([0.38, 0.62], gap="large")

with left:
    st.header("Backpack")
    backpack = palette_section("Backpack", BASE.backpack_tint,
                               "Used for backpackTint in OutfitDef; engine applies at runtime.")
    st.markdown("---")
    st.header("Body")
    body = palette_section("Body", BASE.base_tint,
                           "Used for baseTint in OutfitDef; engine applies at runtime.")
    st.markdown("---")
    st.header("Hands")
    hands = palette_section("Hands", BASE.hand_tint,
                            "Used for handTint in OutfitDef; engine applies at runtime.")
    st.markdown("---")
    st.header("Loot Icon (defaults to BaseDefs)")
    include_loot_extra = st.checkbox("Include loot border + scale fields", value=True, 
        help="Keeps the extra BaseDefs fields: border sprite name, borderTint, and scale.")
    loot_border_name = st.text_input("Border sprite name", BASE.loot_border,
                                     help="Name only; TS snippet adds the extension you chose above.")
    loot_border_tint = st.color_picker("Border tint", "#000000")
    loot_scale = st.slider("Loot scale", 0.05, 0.50, 0.30)
    loot_tint = st.color_picker("Loot tint (OutfitDef)", rgb_to_hex(BASE.loot_tint),
        help="Used by the engine for the in-game icon tint, not baked into the SVG. If set to white (0xFFFFFF) the icon may look blank in some SVG viewers on a white background—that's expected.")

# ---------- Build SVGs (preview + export) ----------
def build_piece(piece, cfg, w, h):
    fill_block = make_fill_block(cfg["fill_type"], cfg["primary"], cfg["secondary"], cfg["pattern"], cfg["pat_color"], cfg["pat_opacity"])
    stroke = preview_outline_color if include_outline_in_exports else None
    sw = outline_width if include_outline_in_exports else 0

    if piece == "backpack":
        return svg_backpack(w=w, h=h, stroke=stroke, stroke_w=sw, fill_block=fill_block.replace('fill="url(#g', 'fill="url(#g').replace('rect', 'rect id="fillBase"', 1).replace('fill="url(#g', 'fill="url(#g'))
    if piece == "body":
        return svg_body(w=w, h=h, stroke=stroke, stroke_w=sw, fill_block=fill_block.replace('rect', 'rect id="fillBase"', 1))
    if piece == "hands":
        return svg_hands(w=w, h=h, stroke=stroke, stroke_w=sw, fill_block=fill_block.replace('rect', 'rect id="fillBase"', 1))
    raise ValueError("unknown piece")

bp_svg = build_piece("backpack", backpack, 640, 360)
body_svg = build_piece("body", body, 720, 720)
hands_svg = build_piece("hands", hands, 640, 260)
loot_svg = svg_loot_icon(loot_tint)

# ---------- Preview ----------
with right:
    st.caption("All settings on the left. Preview shows backpack → body → hands. Download exports as separate sprites + TypeScript snippet.")
    # A light checker backdrop to make white icons visible in preview only
    st.markdown("""
    <style>
    .checker {
      background: linear-gradient(45deg,#eee 25%, transparent 25%) -8px 0/16px 16px,
                  linear-gradient(-45deg,#eee 25%, transparent 25%) -8px 0/16px 16px,
                  linear-gradient(45deg, transparent 75%, #eee 75%),
                  linear-gradient(-45deg, transparent 75%, #eee 75%);
      background-size: 16px 16px;
      background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
      border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Backpack** ❔", help="Previewed with your fill/pattern. Export is a clean SVG (no tint baked) unless you enabled outline-in-export.")
        st.markdown(f'<div class="checker"><img src="data:image/svg+xml;utf8,{bp_svg}"/></div>', unsafe_allow_html=True)
    with c2:
        st.markdown("**Body** ❔", help="Previewed with your fill/pattern. Game tints it with baseTint at runtime.")
        st.markdown(f'<div class="checker"><img src="data:image/svg+xml;utf8,{body_svg}"/></div>', unsafe_allow_html=True)
    with c3:
        st.markdown("**Hands** ❔", help="Previewed with your fill/pattern. Game tints it with handTint at runtime.")
        st.markdown(f'<div class="checker"><img src="data:image/svg+xml;utf8,{hands_svg}"/></div>', unsafe_allow_html=True)

    st.markdown("**Loot Icon** ❔", help="A radial-gradient circle with accent bands (similar to in-game). Note: the game also tints via `lootImg.tint`.")
    st.markdown(f'<div class="checker" style="display:inline-block;padding:8px;border:1px solid #eee;border-radius:8px;"><img width="128" height="128" src="data:image/svg+xml;utf8,{loot_svg}"/></div>', unsafe_allow_html=True)

# ---------- TS snippet ----------
rarity_val = {
    "Stock (0)": 0, "Common (1)": 1, "Uncommon (2)": 2, "Rare (3)": 3, "Epic (4)": 4, "Mythic (5)": 5
}[rarity]

def name_to_id(n: str) -> str:
    safe = "".join(ch for ch in n if ch.isalnum())
    return ("outfit" + safe[:1].upper() + safe[1:]) if not safe.lower().startswith("outfit") else safe

skin_id = name_to_id(skin_name)

def sprite(f): return f"{f}.{ext}"

ts = f"""\
{skin_id}: defineOutfitSkin("outfitBase", {{
    name: "{skin_name}",
    {"noDropOnDeath: true," if noDropOnDeath else ""}
    {"noDrop: true," if noDrop else ""}
    {"ghillie: true," if ghillie else ""}
    {"obstacleType: \""+obstacleType+"\",\"" if obstacleType else ""}{"" if obstacleType else ""}
    {"baseScale: "+str(baseScale)+"," if obstacleType else ""}
    skinImg: {{
        baseTint: {rgb_to_0x(hex_to_rgb(body['tint']))},
        baseSprite: "{sprite('player-base-' + skin_id)}",
        handTint: {rgb_to_0x(hex_to_rgb(hands['tint']))},
        handSprite: "{sprite('player-hands-' + skin_id)}",
        footTint: {rgb_to_0x(BASE.foot_tint)},  // kept for parity
        footSprite: "{sprite('player-feet-01')}", // unchanged default
        backpackTint: {rgb_to_0x(hex_to_rgb(backpack['tint']))},
        backpackSprite: "{sprite('player-circle-base-' + skin_id)}",
    }},
    lootImg: {{
        sprite: "{sprite('loot-shirt-' + skin_id)}",
        tint: {rgb_to_0x(hex_to_rgb(loot_tint))},
        {"border: \""+sprite(loot_border_name)+"\", borderTint: "+rgb_to_0x(hex_to_rgb(loot_border_tint))+", scale: "+str(round(loot_scale,2)) if include_loot_extra else ""}
    }},
    {"rarity: "+str(rarity_val)+"," if rarity_val!=0 else ""}
    {"lore: \""+lore.replace('"','\\"')+"\"," if lore else ""}
}}),"""

# ---------- Downloads ----------
def btn(label, data, filename, mime):
    st.download_button(label=label, data=data, file_name=filename, mime=mime, use_container_width=True)

st.markdown("---")
st.subheader("Downloads")

colA, colB, colC, colD, colE = st.columns(5)
with colA: btn("Backpack SVG", bp_svg, f"player-circle-base-{skin_id}.svg", "image/svg+xml")
with colB: btn("Body SVG", body_svg, f"player-base-{skin_id}.svg", "image/svg+xml")
with colC: btn("Hands SVG", hands_svg, f"player-hands-{skin_id}.svg", "image/svg+xml")
with colD: btn("Loot Icon SVG", loot_svg, f"loot-shirt-{skin_id}.svg", "image/svg+xml")
with colE: btn("TypeScript (txt)", ts, f"{skin_id}.ts.txt", "text/plain")

# full zip
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"img/player-circle-base-{skin_id}.svg", bp_svg)
    z.writestr(f"img/player-base-{skin_id}.svg", body_svg)
    z.writestr(f"img/player-hands-{skin_id}.svg", hands_svg)
    z.writestr(f"img/loot/loot-shirt-{skin_id}.svg", loot_svg)
    z.writestr(f"{skin_id}.ts.txt", ts)

st.download_button("⬇️ Download everything (.zip)", data=buf.getvalue(),
                   file_name=f"{skin_id}_skin_export.zip", mime="application/zip", use_container_width=True)
