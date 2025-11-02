import io
import zipfile

import streamlit as st
import urllib.parse

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

from skin_creator.export import (
    ExportOpts,
    RARITY_OPTIONS,
    SPRITE_MODE_BASE,
    SPRITE_MODE_CUSTOM,
    adjust_tints_for_sprite_mode,
    build_filenames,
    build_manifest,
)
from skin_creator.helpers import hex_to_rgb, rgb_to_ts_hex, sanitize, svg_data_uri
from skin_creator.preview import (
    PREVIEW_PRESETS,
    body_frame_from_layout,
    build_preview_html,
)
from skin_creator.sprites import (
    build_part_svg,
    svg_backpack,
    svg_body,
    svg_body_preview_overlay,
    svg_feet,
    svg_from_upload,
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
base_id = sanitize(skin_name).lower()
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
st.sidebar.subheader("Preview")
preview_names = list(PREVIEW_PRESETS.keys())
selected_preview_label = st.sidebar.selectbox(
    "Preview preset",
    preview_names,
    index=0,
)
selected_preview = PREVIEW_PRESETS[selected_preview_label]
if selected_preview.description:
    st.sidebar.caption(selected_preview.description)
selected_layout = selected_preview.layout
body_frame = body_frame_from_layout(selected_layout)

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
    key="sprite-mode",
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


def part_controls(title, defaults, allow_upload=False, show_header=True, key_prefix=None):
    section_key = key_prefix or title.lower().replace(" ", "-")
    if show_header:
        st.sidebar.markdown("---")
        st.sidebar.subheader(title)
    primary = st.sidebar.color_picker(
        f"{title} primary", defaults["primary"], key=f"{section_key}-primary"
    )
    secondary = st.sidebar.color_picker(
        f"{title} secondary", defaults["secondary"], key=f"{section_key}-secondary"
    )
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
        key=f"{section_key}-style",
    )
    extra = st.sidebar.color_picker(
        f"{title} pattern/extra color", defaults["extra"], key=f"{section_key}-extra"
    )
    angle = st.sidebar.slider(
        f"{title} angle (gradients/stripes)", 0, 180, defaults["angle"], key=f"{section_key}-angle"
    )
    gap = st.sidebar.slider(
        f"{title} gap/spacing", 6, 48, defaults["gap"], key=f"{section_key}-gap"
    )
    opacity = st.sidebar.slider(
        f"{title} pattern opacity",
        0.0,
        1.0,
        defaults["opacity"],
        key=f"{section_key}-opacity",
    )
    size = st.sidebar.slider(
        f"{title} dot/check size", 4, 40, defaults["size"], key=f"{section_key}-size"
    )
    tint = st.sidebar.color_picker(
        f"{title} tint (OutfitDef)", defaults["tint"], key=f"{section_key}-tint"
    )
    upload_bytes = None
    upload_mime = ""
    upload_active = False
    upload_rotation = 0.0
    if allow_upload:
        st.sidebar.caption(
            "Upload an SVG or PNG to replace the generated sprite for this body part."
        )
        uploaded = st.sidebar.file_uploader(
            f"Upload custom {title.lower()} sprite",
            type=["svg", "png"],
            key=f"{section_key}-upload",
        )
        if uploaded is not None:
            upload_bytes = uploaded.getvalue()
            upload_mime = uploaded.type or "image/svg+xml"
            upload_active = st.sidebar.checkbox(
                f"Use uploaded {title.lower()} sprite", value=True, key=f"{section_key}-upload-use"
            )
            upload_rotation = st.sidebar.slider(
                f"Rotate uploaded {title.lower()}",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                step=1.0,
                key=f"{section_key}-upload-rotation",
            )
        else:
            upload_active = False
            upload_rotation = 0.0
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
        upload_bytes=upload_bytes,
        upload_mime=upload_mime,
        upload_active=upload_active,
        upload_rotation=upload_rotation,
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
    allow_upload=True,
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
    allow_upload=True,
)
if hand_cfg.get("upload_active") and hand_cfg.get("upload_bytes"):
    st.sidebar.info("Using uploaded hands sprite; geometry controls are disabled.")
else:
    st.sidebar.caption("Adjust the generated hand geometry.")
    hand_cfg["shape"] = st.sidebar.selectbox(
        "Hand shape",
        ["Circle", "Rounded Square", "Diamond", "Teardrop"],
        index=0,
        key="hands-shape",
    )
    hand_cfg["shape_scale_x"] = st.sidebar.slider(
        "Hand width scale",
        0.6,
        1.6,
        1.0,
        0.05,
        key="hands-shape-scale-x",
    )
    hand_cfg["shape_scale_y"] = st.sidebar.slider(
        "Hand height scale",
        0.6,
        1.6,
        1.0,
        0.05,
        key="hands-shape-scale-y",
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
    allow_upload=True,
)

loot_icon_tint = st.sidebar.color_picker("Loot shirt tint", "#ffffff")
feet_stroke_w = hand_stroke_w * (4.513 / 11.096)

st.sidebar.markdown("---")
st.sidebar.subheader("Front accessory (optional)")
front_mode = st.sidebar.selectbox(
    "Front sprite source",
    ["None", "Upload image/SVG"],
    index=0,
)
front_enabled = front_mode != "None"
front_stub_default = f"outfit-{base_id}-accessory" if base_id else "outfit-accessory"
front_stub = front_stub_default
front_svg_text = ""
front_upload_bytes = None
front_upload_mime = ""
front_tint_hex = "#ffffff"
front_above_hand = False
front_pos_x = 0
front_pos_y = 0
front_preview = {"enabled": False}

if front_enabled:
    front_stub = st.sidebar.text_input(
        "Front sprite filename base",
        front_stub_default,
        key="front-sprite-stub",
    )
    front_tint_hex = st.sidebar.color_picker(
        "Accessory tint (OutfitDef)", "#ffffff", key="front-export-tint"
    )
    front_above_hand = st.sidebar.checkbox(
        "Draw accessory above hands in-game",
        value=False,
        key="front-above-hands",
    )
    front_pos_x = st.sidebar.slider(
        "Front sprite offset X", -24, 24, 0, 1, key="front-offset-x"
    )
    front_pos_y = st.sidebar.slider(
        "Front sprite offset Y", -24, 24, 0, 1, key="front-offset-y"
    )
    st.sidebar.caption("Offsets mirror the `frontSpritePos` values applied in-game.")

    st.sidebar.markdown("**Preview placement**")
    front_preview_key_prefix = f"front-preview-{selected_preview_label.lower()}"
    default_front_left = 80
    default_front_top = 140
    default_front_width = 240
    default_front_height = 240
    default_front_rotation = 90.0
    front_preview_left = st.sidebar.number_input(
        "Preview left (px)",
        value=int(default_front_left),
        step=1,
        key=f"{front_preview_key_prefix}-left",
    )
    front_preview_top = st.sidebar.number_input(
        "Preview top (px)",
        value=int(default_front_top),
        step=1,
        key=f"{front_preview_key_prefix}-top",
    )
    front_preview_width = st.sidebar.number_input(
        "Preview width (px)",
        value=int(default_front_width),
        step=1,
        key=f"{front_preview_key_prefix}-width",
    )
    front_preview_height = st.sidebar.number_input(
        "Preview height (px)",
        value=int(default_front_height),
        step=1,
        key=f"{front_preview_key_prefix}-height",
    )
    front_preview_rotation = st.sidebar.slider(
        "Preview rotation",
        -180.0,
        180.0,
        float(default_front_rotation),
        1.0,
        key=f"{front_preview_key_prefix}-rotation",
    )
    front_preview = dict(
        enabled=True,
        left=int(front_preview_left),
        top=int(front_preview_top),
        width=int(front_preview_width),
        height=int(front_preview_height),
        rotation=float(front_preview_rotation),
        above_hands=front_above_hand,
    )

    if front_mode == "Upload image/SVG":
        uploaded_front = st.sidebar.file_uploader(
            "Upload accessory sprite",
            type=["svg", "png"],
            key="front-upload",
        )
        if uploaded_front is not None:
            front_upload_bytes = uploaded_front.getvalue()
            front_upload_mime = uploaded_front.type or "image/svg+xml"
        else:
            st.sidebar.warning("Upload an SVG or PNG accessory to export a front sprite.")

if sprite_mode == SPRITE_MODE_BASE and front_enabled:
    existing_sprite_ids["front"] = st.sidebar.text_input(
        "Front accessory sprite ID",
        front_stub or front_stub_default,
        key="front-sprite-id",
    )

# ---------------------------
# Build fills & sprites
# ---------------------------

if body_cfg.get("upload_active") and body_cfg.get("upload_bytes"):
    body_svg_text = svg_from_upload(
        body_cfg["upload_bytes"],
        body_cfg.get("upload_mime", ""),
        140,
        140,
        float(body_cfg.get("upload_rotation", 0.0)),
    )
else:
    body_svg_text = build_part_svg(body_cfg, svg_body, None, None)

if hand_cfg.get("upload_active") and hand_cfg.get("upload_bytes"):
    hands_svg_text = svg_from_upload(
        hand_cfg["upload_bytes"],
        hand_cfg.get("upload_mime", ""),
        76,
        76,
        float(hand_cfg.get("upload_rotation", 0.0)),
    )
else:
    hands_svg_text = build_part_svg(hand_cfg, svg_hands, hand_stroke_col, hand_stroke_w)

if bp_cfg.get("upload_active") and bp_cfg.get("upload_bytes"):
    backpack_svg_text = svg_from_upload(
        bp_cfg["upload_bytes"],
        bp_cfg.get("upload_mime", ""),
        148,
        148,
        float(bp_cfg.get("upload_rotation", 0.0)),
    )
else:
    backpack_svg_text = build_part_svg(bp_cfg, svg_backpack, bp_stroke_col, bp_stroke_w)

feet_svg_text = build_part_svg(hand_cfg, svg_feet, hand_stroke_col, feet_stroke_w)
loot_svg_text = svg_loot_shirt_base(loot_icon_tint)
loot_inner_svg_text = svg_loot_circle_inner(loot_inner_glow)
loot_outer_svg_text = svg_loot_circle_outer(loot_border_tint)
preview_overlay_svg_text = svg_body_preview_overlay()

front_has_sprite = False
if front_enabled:
    if front_mode == "Upload image/SVG" and front_upload_bytes:
        front_svg_text = svg_from_upload(
            front_upload_bytes, front_upload_mime, body_frame.width, body_frame.height
        )
        front_has_sprite = True
    if not front_has_sprite:
        front_preview["enabled"] = False
front_preview["enabled"] = front_has_sprite
front_preview["above_hands"] = front_above_hand

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
    "front": svg_data_uri(front_svg_text) if front_has_sprite else "",
}

st.markdown(
    build_preview_html(uris, layout=selected_layout, front=front_preview),
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------------------------
# Export (ZIP + TS)
# ---------------------------

ident = f"outfit{sanitize(skin_name)}"
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
    include_front=front_has_sprite,
    front_stub=front_stub or front_stub_default,
)

tints = {
    "base": rgb_to_ts_hex(hex_to_rgb(body_cfg["tint"])),
    "hand": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "foot": rgb_to_ts_hex(hex_to_rgb(hand_cfg["tint"])),
    "backpack": rgb_to_ts_hex(hex_to_rgb(bp_cfg["tint"])),
    "loot": rgb_to_ts_hex(hex_to_rgb(loot_icon_tint)),
    "border": rgb_to_ts_hex(hex_to_rgb(loot_border_tint)),
}
if front_has_sprite:
    tints["front"] = rgb_to_ts_hex(hex_to_rgb(front_tint_hex))

ts_tints = adjust_tints_for_sprite_mode(tints, sprite_mode)

rarity_value = next(value for label, value in RARITY_OPTIONS if label == rarity_label)

front_meta = {
    "enabled": front_has_sprite,
    "pos_x": int(front_pos_x),
    "pos_y": int(front_pos_y),
    "aboveHand": front_above_hand,
}

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
    front_enabled=front_has_sprite,
    front_pos_x=int(front_pos_x),
    front_pos_y=int(front_pos_y),
    front_above_hand=front_above_hand,
)

ts_code = opts.ts_block(ident=ident, filenames=filenames, tints=ts_tints)
manifest_json = build_manifest(
    ident=ident,
    opts=opts,
    filenames=filenames,
    ui_tints=tints,
    export_tints=ts_tints,
    sprite_mode=sprite_mode,
    preview_preset=selected_preview_label,
    front_meta=front_meta,
)

left, right = st.columns(2)
with left:
    st.subheader("TypeScript export")
    st.code(ts_code, language="typescript")
    if sprite_mode == SPRITE_MODE_CUSTOM:
        st.caption(
            "Tint fields are fixed to 0xffffff when exporting separate files so the game keeps your custom colors."
        )
    with st.expander("Asset manifest (JSON)"):
        st.code(manifest_json, language="json")
with right:
    st.subheader("What’s inside the ZIP")
    zip_lines = [
        f"- `{filenames['base']}` (body)",
        f"- `{filenames['hands']}` (hands)",
        f"- `{filenames['feet']}` (feet)",
        f"- `{filenames['backpack']}` (backpack)",
    ]
    if front_has_sprite and filenames.get("front"):
        zip_lines.append(f"- `{filenames['front']}` (front accessory)")
    if loot_border_on and filenames.get("border"):
        zip_lines.append(f"- `{filenames['border']}` (loot border)")
    if loot_border_on and filenames.get("inner"):
        zip_lines.append(f"- `{filenames['inner']}` (loot inner glow)")
    zip_lines.extend(
        [
            f"- `{filenames['loot']}` (loot icon – shirt silhouette, no stroke)",
            f"- `export/{ident}.ts` (ready `defineOutfitSkin(...)`)",
            f"- `export/{ident}.manifest.json` (asset + metadata manifest)",
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
    if front_has_sprite and filenames.get("front"):
        zf.writestr(filenames["front"].replace(".img", ".svg"), front_svg_text)
    zf.writestr(f"export/{ident}.ts", ts_code)
    zf.writestr(f"export/{ident}.manifest.json", manifest_json)
zip_bytes = buf.getvalue()

st.download_button(
    "⬇️ Download sprites + TypeScript config (ZIP)",
    data=zip_bytes,
    file_name=f"{base_id}_survev_skin.zip",
    mime="application/zip",
)
