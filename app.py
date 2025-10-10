import io
import zipfile
from dataclasses import dataclass
from typing import Tuple

import streamlit as st

# =============== Small helpers ===============

def label_with_help(text: str, help_text: str) -> str:
    """HTML label with a small ? that shows native tooltip."""
    css = """
    <style>
    .help-q {
      display:inline-flex;align-items:center;justify-content:center;
      margin-left:.4rem;width:1rem;height:1rem;border-radius:50%;
      font-weight:700;font-size:.70rem;line-height:1;
      background:#eee;color:#555;cursor:help;user-select:none;
      border:1px solid #ddd;
    }
    .help-q:hover{ background:#e6e6e6; }
    .field-label{ font-weight:600; }
    .downloads-grid button{ width:100%; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return f'<span class="field-label">{text}</span><span class="help-q" title="{help_text}">?</span>'

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.replace("#", "")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

def hex_to_ts_int_literal(hex_color: str) -> int:
    """Return 0xRRGGBB as Python int (what TS would see)."""
    return int(hex_color.replace("#", ""), 16)

def stroke_attrs(stroke_color: str, stroke_width: int) -> str:
    """Return SVG stroke attributes or '' if width is 0."""
    if stroke_width <= 0:
        return ""
    return f' stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"'

def dl_button(label: str, filename: str, data: bytes, key: str):
    st.download_button(label, data=data, file_name=filename, mime="image/svg+xml", key=key)

# =============== Sprite generators (simple, game-aligned) ===============

@dataclass
class Outline:
    color: str
    width: int  # 0 => no outline

@dataclass
class PartColors:
    body_hex: str
    hands_hex: str
    backpack_hex: str

def make_backpack_svg(fill_hex: str, outline: Outline) -> str:
    # simple semicircle "cap" behind the body
    s = stroke_attrs(outline.color, outline.width)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <path d="M20,78 a50,50 0 0 1 100,0 v8 H20z" fill="{fill_hex}"{s}/>
</svg>"""

def make_body_svg(fill_hex: str, outline: Outline) -> str:
    s = stroke_attrs(outline.color, outline.width)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <circle cx="70" cy="78" r="58" fill="{fill_hex}"{s}/>
</svg>"""

def make_hands_svg(fill_hex: str, outline: Outline) -> str:
    s = stroke_attrs(outline.color, outline.width)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <circle cx="44" cy="118" r="18" fill="{fill_hex}"{s}/>
  <circle cx="96" cy="118" r="18" fill="{fill_hex}"{s}/>
</svg>"""

def make_loot_svg(tint_hex: str) -> str:
    """
    Loot icon: by default the game's loot art is tinted at runtime.
    We export a flat shirt silhouette filled with the chosen 'tint' purely as a preview/export convenience.
    """
    # No outline by design (matches your sample files)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <path d="M22 32 L46 22 L56 34 H72 L82 22 L106 32 L92 54 V106 H36 V54 Z" fill="{tint_hex}"/>
</svg>"""

def make_preview_svg(colors: PartColors, outline: Outline) -> str:
    """Composite preview (backpack -> body -> hands)."""
    s = stroke_attrs(outline.color, outline.width)
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="560" height="420" viewBox="0 0 140 105">
  <!-- backpack -->
  <path d="M20,30 a50,50 0 0 1 100,0 v8 H20z" fill="{colors.backpack_hex}"{s}/>
  <!-- body -->
  <circle cx="70" cy="60" r="46" fill="{colors.body_hex}"{s}/>
  <!-- hands -->
  <circle cx="50" cy="88" r="14" fill="{colors.hands_hex}"{s}/>
  <circle cx="90" cy="88" r="14" fill="{colors.hands_hex}"{s}/>
</svg>
"""

# =============== UI ===============

st.set_page_config(page_title="Survev.io Skin Creator", page_icon="🎨", layout="wide")

st.sidebar.header("Meta")
name = st.sidebar.text_input("Skin name", value="Basic Outfit")
lore = st.sidebar.text_area("Lore / Description", value="Pure and simple.")
rarity = st.sidebar.selectbox("Rarity", ["Stock (0)", "Common (1)", "Uncommon (2)", "Rare (3)", "Epic (4)", "Mythic (5)"], index=0)

no_drop_on_death = st.sidebar.checkbox("noDropOnDeath (keep on death)", value=False)
no_drop = st.sidebar.checkbox("noDrop (never drops)", value=False)
ghillie = st.sidebar.checkbox("ghillie (match ghillie color in mode)", value=False)

st.sidebar.markdown(label_with_help("obstacleType (costume skins)", "Only for event/costume skins (e.g., barrel_01, tree_07sp). Leave blank for normal outfits."), unsafe_allow_html=True)
obstacle_type = st.sidebar.text_input(label="", value="")

st.sidebar.markdown(label_with_help("baseScale (advanced)", "Scale used when obstacleType is set. Keep 1.0 unless you need it."), unsafe_allow_html=True)
base_scale = st.sidebar.number_input(label="", min_value=0.1, max_value=2.0, value=1.0, step=0.05)

st.sidebar.write("---")
st.sidebar.markdown(label_with_help("Sprite Outline", "Preview helper. Game SVGs normally have NO stroke. Leave 0 to export with no outline."), unsafe_allow_html=True)
outline_color = st.sidebar.color_picker("Outline color", value="#000000", label_visibility="collapsed")
# >>> CHANGE #1: default to 0 (no outline)
outline_width = st.sidebar.slider("Outline width", min_value=0, max_value=16, value=0)

st.sidebar.write("---")
st.sidebar.markdown(label_with_help("Asset sprites (filenames used in OutfitDef)", "These are the sprite names referenced by the TS defs. They are not baked into the art."), unsafe_allow_html=True)
base_sprite = st.sidebar.text_input("Body baseSprite", value="player-base-01.img")
hands_sprite = st.sidebar.text_input("Hands handSprite", value="player-hands-01.img")
backpack_sprite = st.sidebar.text_input("Backpack backpackSprite", value="player-circle-base-01.img")
loot_sprite = st.sidebar.text_input("Loot sprite", value="loot-shirt-01.img")
loot_border_default_on = st.sidebar.checkbox("Include loot border + scale fields", value=True)
loot_border_name = st.sidebar.text_input("Loot border sprite name", value="loot-circle-outer-01.img", disabled=not loot_border_default_on)
st.sidebar.markdown(label_with_help("Border tint", "Loot border tint stored in OutfitDef. White means 'keep original'."), unsafe_allow_html=True)
loot_border_tint = st.sidebar.color_picker("border-tint", value="#000000", label_visibility="collapsed", disabled=not loot_border_default_on)
loot_scale = st.sidebar.slider("Loot scale", min_value=0.05, max_value=0.50, value=0.30, step=0.01, disabled=not loot_border_default_on)

st.sidebar.write("---")
st.sidebar.markdown("### Tints (saved in OutfitDef)")
st.sidebar.markdown(label_with_help("Body tint (OutfitDef)", "Saved as baseTint; applied by the engine at runtime."), unsafe_allow_html=True)
body_hex = st.sidebar.color_picker("body", value="#F8C574", label_visibility="collapsed")

st.sidebar.markdown(label_with_help("Hands tint (OutfitDef)", "Saved as handTint; applied at runtime."), unsafe_allow_html=True)
hands_hex = st.sidebar.color_picker("hands", value="#F8C574", label_visibility="collapsed")

st.sidebar.markdown(label_with_help("Backpack tint (OutfitDef)", "Saved as backpackTint; applied at runtime."), unsafe_allow_html=True)
backpack_hex = st.sidebar.color_picker("backpack", value="#816537", label_visibility="collapsed")

st.sidebar.markdown(label_with_help("Loot tint (OutfitDef)", "Saved as lootImg.tint; the loot icon in-game is tinted via code."), unsafe_allow_html=True)
loot_tint_hex = st.sidebar.color_picker("loot_tint", value="#FFFFFF", label_visibility="collapsed")

# Build objects for render/export
outline = Outline(color=outline_color, width=outline_width)
colors = PartColors(body_hex=body_hex, hands_hex=hands_hex, backpack_hex=backpack_hex)

# =============== Main content ===============
left, right = st.columns([1, 1.6])

with left:
    st.subheader("Preview")
    st.caption("Preview shows backpack → body → hands. Exports are separate sprites.")
    st.markdown(make_preview_svg(colors, outline), unsafe_allow_html=True)

with right:
    st.subheader("Export")

    # Generate each SVG now
    svg_backpack = make_backpack_svg(colors.backpack_hex, outline)
    svg_body = make_body_svg(colors.body_hex, outline)
    svg_hands = make_hands_svg(colors.hands_hex, outline)
    svg_loot = make_loot_svg(loot_tint_hex)

    st.markdown("#### Download one part")
    # >>> CHANGE #2: single-part downloads
    dl_button("Download Backpack SVG", f"player-circle-base-custom.svg", svg_backpack.encode("utf-8"), key="dl_bpk")
    dl_button("Download Body SVG", f"player-base-custom.svg", svg_body.encode("utf-8"), key="dl_body")
    dl_button("Download Hands SVG", f"player-hands-custom.svg", svg_hands.encode("utf-8"), key="dl_hands")
    dl_button("Download Loot SVG", f"loot-shirt-custom.svg", svg_loot.encode("utf-8"), key="dl_loot")

    st.markdown("---")
    st.markdown("#### Download everything (ZIP + TypeScript snippet)")

    # TypeScript OutfitDef snippet matching your structure
    rarity_map = {
        "Stock (0)": 0, "Common (1)": 1, "Uncommon (2)": 2,
        "Rare (3)": 3, "Epic (4)": 4, "Mythic (5)": 5
    }
    rarity_value = rarity_map[rarity]

    loot_border_str = f'"{loot_border_name}"' if loot_border_default_on else 'undefined'
    loot_border_tint_int = hex_to_ts_int_literal(loot_border_tint) if loot_border_default_on else 0
    loot_scale_num = loot_scale if loot_border_default_on else 0.2

    ts_snippet = f"""// OutfitDef snippet (paste into your SkinDefs and adjust the key)
defineOutfitSkin("outfitBase", {{
  name: "{name}",
  {"noDropOnDeath: true," if no_drop_on_death else ""}
  {"noDrop: true," if no_drop else ""}
  {"ghillie: true," if ghillie else ""}
  {"obstacleType: \"" + obstacle_type + "\",": "" if not obstacle_type else ""}
  {"baseScale: " + str(base_scale) + "," if obstacle_type else ""}
  rarity: {rarity_value},
  lore: "{lore}",
  skinImg: {{
    baseTint: 0x{hex_to_ts_int_literal(body_hex):06X},
    baseSprite: "{base_sprite}",
    handTint: 0x{hex_to_ts_int_literal(hands_hex):06X},
    handSprite: "{hands_sprite}",
    footTint: 0x{hex_to_ts_int_literal(hands_hex):06X},
    footSprite: "player-feet-01.img",
    backpackTint: 0x{hex_to_ts_int_literal(backpack_hex):06X},
    backpackSprite: "{backpack_sprite}",
  }},
  lootImg: {{
    sprite: "{loot_sprite}",
    tint: 0x{hex_to_ts_int_literal(loot_tint_hex):06X},
    border: {loot_border_str},
    borderTint: 0x{loot_border_tint_int:06X},
    scale: {loot_scale_num},
  }},
}})"""

    # Build a zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("img/player/player-circle-base-custom.svg", svg_backpack)
        z.writestr("img/player/player-base-custom.svg", svg_body)
        z.writestr("img/player/player-hands-custom.svg", svg_hands)
        z.writestr("img/loot/loot-shirt-custom.svg", svg_loot)
        z.writestr("outfit.ts.txt", ts_snippet)
    buf.seek(0)

    st.download_button(
        "Download ZIP (sprites + TS snippet)",
        data=buf,
        file_name="survevio-skin-export.zip",
        mime="application/zip",
        key="dl_all",
    )

st.caption("ℹ️ Tints are saved to OutfitDef (as 0xRRGGBB) and **not** baked into the SVGs. \
Game code applies tints at runtime. Outline width **0** exports clean SVGs matching in-game files.")
