import io
import zipfile

import streamlit as st

from skin_creator.export import (
    ExportOpts,
    RARITY_OPTIONS,
    SPRITE_MODE_BASE,
    SPRITE_MODE_CUSTOM,
    adjust_tints_for_sprite_mode,
    build_filenames,
)
from skin_creator.helpers import hex_to_rgb, rgb_to_ts_hex, sanitize, svg_data_uri
from skin_creator.preview import build_preview_html
from skin_creator.sprites import (
    build_part_svg,
    svg_backpack,
    svg_body,
    svg_body_preview_overlay,
    svg_feet,
    svg_hands,
    svg_loot_circle_inner,
    svg_loot_circle_outer,
    svg_loot_shirt_base,
)


# ---------------------------
# Streamlit configuration
# ---------------------------

st.set_page_config(page_title="Survev.io Skin Creator", page_icon="🎨", layout="wide")

# ---------------------------
# Sidebar configuration
# ---------------------------

st.sidebar.title("Meta")
skin_name = st.sidebar.text_input("Skin name", "Basic Outfit")
lore = st.sidebar.text_area("Lore / description", "")
rarity_label = st.sidebar.selectbox(
    "Rarity", [label for label, _ in RARITY_OPTIONS], index=0
)
st.sidebar.caption(
    "Use the numeric rarity values from 1 (Common) to 5 (Mythic). Leave on '(omit)' for Stock skins."
)
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
st.sidebar.caption(
    "ZIP always contains SVG files; choose how your TS should reference them in-game."
)

sprite_mode = st.sidebar.radio(
    "Sprite filename strategy",
    (SPRITE_MODE_CUSTOM, SPRITE_MODE_BASE),
    index=0,
)

custom_dirs = {"player": "img/player/", "loot": "img/loot/"}

if sprite_mode == SPRITE_MODE_CUSTOM:
    st.sidebar.caption(
        "ZIP exports will ship your freshly generated SVGs and the TypeScript snippet "
        "will reference those unique filenames."
    )
    custom_dirs["player"] = st.sidebar.text_input(
        "Player sprite folder",
        "img/player/",
    )
    custom_dirs["loot"] = st.sidebar.text_input(
        "Loot sprite folder",
        "img/loot/",
    )
    st.sidebar.info(
        "When exporting separate files, Survev expects tint values to stay at 0xffffff. "
        "We'll set those automatically in the TypeScript snippet so your custom art renders correctly."
    )

existing_sprite_ids = {}
if sprite_mode == SPRITE_MODE_BASE:
    st.sidebar.caption(
        "Enter existing sprite IDs without an extension. We'll append the reference "
        "extension selected above so your TypeScript export points at in-game art. "
        "The exported tint values still recolor those shared sprites in-game, so your "
        "custom palette shows up even though the filenames stay stock."
    )
    existing_sprite_ids["base"] = st.sidebar.text_input(
        "Body sprite ID",
        "player-base-01",
        key="base-sprite-id",
    )
    existing_sprite_ids["hands"] = st.sidebar.text_input(
        "Hands sprite ID",
        "player-hands-01",
        key="hands-sprite-id",
    )
    existing_sprite_ids["feet"] = st.sidebar.text_input(
        "Feet sprite ID",
        "player-feet-01",
        key="feet-sprite-id",
    )
    existing_sprite_ids["backpack"] = st.sidebar.text_input(
        "Backpack sprite ID",
        "player-circle-base-01",
        key="backpack-sprite-id",
    )
    existing_sprite_ids["loot"] = st.sidebar.text_input(
        "Loot shirt sprite ID",
        "loot-shirt-01",
        key="loot-shirt-sprite-id",
    )

st.sidebar.markdown("---")

st.sidebar.subheader("Loot Icon (defaults to BaseDefs)")
loot_border_on = st.sidebar.checkbox("Include loot border + scale fields", value=True)
loot_border_name = st.sidebar.text_input("Outer circle sprite name", "loot-circle-outer-01")
loot_inner_name = st.sidebar.text_input("Inner circle sprite name", "loot-circle-inner-01")
loot_border_tint = st.sidebar.color_picker("Outer circle stroke tint", "#ffffff")
loot_inner_glow = st.sidebar.color_picker("Inner circle glow color", "#fcfcfc")
loot_scale = st.sidebar.slider("Loot scale", 0.05, 0.5, 0.20)

if rgb_to_ts_hex(hex_to_rgb(loot_border_tint)) == "0x000000":
    st.sidebar.warning(
        "Survev hides loot borders tinted 0x000000. Try 0xffffff to keep the circle visible."
    )


def part_controls(title, defaults):
    st.sidebar.markdown("---")
    st.sidebar.subheader(title)
    primary = st.sidebar.color_picker(f"{title} primary", defaults["primary"])
    secondary = st.sidebar.color_picker(f"{title} secondary", defaults["secondary"])
    style = st.sidebar.selectbox(
        f"{title} fill",
        [
            "Solid",
            "Linear Gradient",
            "Radial Gradient",
            "Diagonal Stripes",
            "Horizontal Stripes",
            "Vertical Stripes",
            "Crosshatch",
            "Dots",
            "Checker",
        ],
        index=0,
        key=f"{title}-style",
    )
    extra = st.sidebar.color_picker(f"{title} pattern/extra color", defaults["extra"])
    angle = st.sidebar.slider(f"{title} angle (gradients/stripes)", 0, 180, defaults["angle"])
    gap = st.sidebar.slider(f"{title} gap/spacing", 6, 48, defaults["gap"])
    opacity = st.sidebar.slider(f"{title} pattern opacity", 0.0, 1.0, defaults["opacity"])
    size = st.sidebar.slider(f"{title} dot/check size", 4, 40, defaults["size"])
    tint = st.sidebar.color_picker(f"{title} tint (OutfitDef)", defaults["tint"])
    return dict(
        primary=primary,
        secondary=secondary,
        style=style,
        extra=extra,
        angle=angle,
        gap=gap,
        opacity=opacity,
        size=size,
        tint=tint,
    )


# BaseDefs defaults
body_cfg = part_controls(
    "Body",
    dict(
        primary="#f8c574",
        secondary="#f8c574",
        extra="#cba86a",
        angle=45,
        gap=24,
        opacity=0.6,
        size=14,
        tint="#f8c574",
    ),
)
hand_cfg = part_controls(
    "Hands",
    dict(
        primary="#f8c574",
        secondary="#f8c574",
        extra="#cba86a",
        angle=45,
        gap=20,
        opacity=0.6,
        size=10,
        tint="#f8c574",
    ),
)
bp_cfg = part_controls(
    "Backpack",
    dict(
        primary="#816537",
        secondary="#816537",
        extra="#6e5630",
        angle=45,
        gap=22,
        opacity=0.6,
        size=12,
        tint="#816537",
    ),
)

loot_icon_tint = st.sidebar.color_picker("Loot shirt tint", "#ffffff")
feet_stroke_w = hand_stroke_w * (4.513 / 11.096)

# ---------------------------
# Build fills & sprites
# ---------------------------

body_svg_text = build_part_svg(body_cfg, svg_body, None, None)
hands_svg_text = build_part_svg(hand_cfg, svg_hands, hand_stroke_col, hand_stroke_w)
backpack_svg_text = build_part_svg(bp_cfg, svg_backpack, bp_stroke_col, bp_stroke_w)
feet_svg_text = build_part_svg(hand_cfg, svg_feet, hand_stroke_col, feet_stroke_w)
loot_svg_text = svg_loot_shirt_base(loot_icon_tint)
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

uris = {
    "body": svg_data_uri(body_svg_text),
    "hands": svg_data_uri(hands_svg_text),
    "feet": svg_data_uri(feet_svg_text),
    "backpack": svg_data_uri(backpack_svg_text),
    "loot": svg_data_uri(loot_svg_text),
    "loot_inner": svg_data_uri(loot_inner_svg_text),
    "loot_outer": svg_data_uri(loot_outer_svg_text),
    "overlay": svg_data_uri(preview_overlay_svg_text),
}

st.markdown(build_preview_html(uris), unsafe_allow_html=True)

st.markdown("---")

# ---------------------------
# Export (ZIP + TS)
# ---------------------------

ident = f"outfit{sanitize(skin_name)}"
base_id = sanitize(skin_name).lower()
ext_ref = "img" if ref_ext == ".img" else "svg"

filenames = build_filenames(
    base_id=base_id,
    sprite_mode=sprite_mode,
    existing_sprite_ids=existing_sprite_ids,
    custom_dirs=custom_dirs,
    ext_ref=ext_ref,
    loot_border_on=loot_border_on,
    loot_border_name=loot_border_name,
    loot_inner_name=loot_inner_name,
)

tints = {
    "base": rgb_to_ts_hex(hex_to_rgb(body_cfg["tint"])),
    "hand": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "foot": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "backpack": rgb_to_ts_hex(hex_to_rgb(bp_cfg["tint"])),
    "loot": rgb_to_ts_hex(hex_to_rgb(loot_icon_tint)),
    "border": rgb_to_ts_hex(hex_to_rgb(loot_border_tint)),
}

ts_tints = adjust_tints_for_sprite_mode(tints, sprite_mode)

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

ts_code = opts.ts_block(ident=ident, filenames=filenames, tints=ts_tints)

left, right = st.columns(2)
with left:
    st.subheader("TypeScript export")
    st.code(ts_code, language="typescript")
    if sprite_mode == SPRITE_MODE_CUSTOM:
        st.caption(
            "Tint fields are fixed to 0xffffff when exporting separate files so the game keeps your custom colors."
        )
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
