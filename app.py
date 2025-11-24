import io
import random
import zipfile

from dataclasses import replace

import streamlit as st

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
    build_preview_document,
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

st.set_page_config(page_title="Zurviv.io Skin Creator", page_icon="🎨", layout="wide")

# ---------------------------
# Sidebar configuration
# ---------------------------

FILL_STYLES = [
    "Solid",
    "Linear Gradient",
    "Radial Gradient",
    "Diagonal Stripes",
    "Horizontal Stripes",
    "Vertical Stripes",
    "Crosshatch",
    "Dots",
    "Checker",
]


BODY_DEFAULTS = dict(
    primary="#f8c574",
    secondary="#f8c574",
    extra="#cba86a",
    style="Solid",
    angle=45,
    gap=24,
    opacity=0.6,
    size=14,
    tint="#f8c574",
)

HAND_DEFAULTS = dict(
    primary="#f8c574",
    secondary="#f8c574",
    extra="#cba86a",
    style="Solid",
    angle=45,
    gap=20,
    opacity=0.6,
    size=10,
    tint="#f8c574",
)

BACKPACK_DEFAULTS = dict(
    primary="#816537",
    secondary="#816537",
    extra="#6e5630",
    style="Solid",
    angle=45,
    gap=22,
    opacity=0.6,
    size=12,
    tint="#816537",
)

LOOT_DEFAULTS = dict(
    shirt="#ffffff",
    border="#ffffff",
    inner="#fcfcfc",
)

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
loadout_overlay_enabled = True
overlay_above_front = True
if selected_preview_label == "Loadout":
    loadout_overlay_enabled = st.sidebar.checkbox(
        "Show armor + helmet overlay", value=True, key="loadout-overlay-enabled"
    )
    overlay_position = st.sidebar.radio(
        "Armor + helmet layering",
        ("Above accessory", "Below accessory"),
        index=0,
        key="loadout-overlay-order",
        disabled=not loadout_overlay_enabled,
    )
    overlay_above_front = overlay_position == "Above accessory"
    if loadout_overlay_enabled:
        active_layout = selected_layout
    else:
        active_layout = replace(selected_layout, show_overlay=False)
else:
    active_layout = selected_layout
body_frame = body_frame_from_layout(active_layout)

# Palette helpers


def _random_hex() -> str:
    return f"#{random.randint(0, 0xFFFFFF):06x}"


def randomize_palette(prefix: str):
    st.session_state[f"{prefix}-primary"] = _random_hex()
    st.session_state[f"{prefix}-secondary"] = _random_hex()
    st.session_state[f"{prefix}-extra"] = _random_hex()
    st.session_state[f"{prefix}-style"] = random.choice(FILL_STYLES)
    st.session_state[f"{prefix}-angle"] = random.randint(0, 180)
    st.session_state[f"{prefix}-gap"] = random.randint(6, 48)
    st.session_state[f"{prefix}-opacity"] = round(random.uniform(0.2, 1.0), 2)
    st.session_state[f"{prefix}-size"] = random.randint(4, 40)
    st.session_state[f"{prefix}-tint"] = _random_hex()


def reset_palettes_to_defaults():
    for prefix, defaults in (
        ("body", BODY_DEFAULTS),
        ("hands", HAND_DEFAULTS),
        ("backpack", BACKPACK_DEFAULTS),
    ):
        for field, value in defaults.items():
            st.session_state[f"{prefix}-{field}"] = value
    st.session_state["loot-shirt-tint"] = LOOT_DEFAULTS["shirt"]
    st.session_state["loot-border-tint"] = LOOT_DEFAULTS["border"]
    st.session_state["loot-inner-tint"] = LOOT_DEFAULTS["inner"]


def randomize_all_palettes():
    for prefix in ("body", "hands", "backpack"):
        randomize_palette(prefix)
    st.session_state["loot-shirt-tint"] = _random_hex()
    st.session_state["loot-border-tint"] = _random_hex()
    st.session_state["loot-inner-tint"] = _random_hex()

if st.sidebar.button("🎲 Randomize colors & patterns", key="randomize-palettes"):
    randomize_all_palettes()

if st.sidebar.button("↩️ Reset to basic outfit", key="reset-palettes"):
    reset_palettes_to_defaults()

st.sidebar.markdown("---")
OUTLINE_STYLES = [
    "Solid",
    "Glow",
    "Gradient",
    "Dashed",
    "Double Stroke",
]

st.sidebar.subheader("Backpack Outline")
bp_stroke_col = st.sidebar.color_picker("Backpack outline color", "#333333")
bp_outline_style = st.sidebar.selectbox(
    "Backpack outline style",
    OUTLINE_STYLES,
    index=0,
    key="bp-outline-style",
)
bp_stroke_w = st.sidebar.slider(
    "Backpack outline width",
    min_value=6.0,
    max_value=20.0,
    value=11.0,
    step=0.1,
)

st.sidebar.subheader("Hands Outline")
hand_stroke_col = st.sidebar.color_picker("Hands outline color", "#333333")
hand_outline_style = st.sidebar.selectbox(
    "Hands outline style",
    OUTLINE_STYLES,
    index=0,
    key="hands-outline-style",
)
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
        "When exporting separate files, Zurviv expects tint values to stay at 0xffffff. "
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
if "loot-border-tint" not in st.session_state:
    st.session_state["loot-border-tint"] = LOOT_DEFAULTS["border"]
loot_border_tint = st.sidebar.color_picker(
    "Outer circle stroke tint",
    st.session_state["loot-border-tint"],
    key="loot-border-tint",
)
if "loot-inner-tint" not in st.session_state:
    st.session_state["loot-inner-tint"] = LOOT_DEFAULTS["inner"]
loot_inner_glow = st.sidebar.color_picker(
    "Inner circle glow color",
    st.session_state["loot-inner-tint"],
    key="loot-inner-tint",
)
loot_scale = st.sidebar.slider("Loot scale", 0.05, 0.5, 0.20)

if rgb_to_ts_hex(hex_to_rgb(loot_border_tint)) == "0x000000":
    st.sidebar.warning(
        "Zurviv hides loot borders tinted 0x000000. Try 0xffffff to keep the circle visible."
    )


def part_controls(
    title,
    defaults,
    allow_upload=False,
    show_header=True,
    key_prefix=None,
    allow_scale=False,
):
    section_key = key_prefix or title.lower().replace(" ", "-")
    for field, default_value in defaults.items():
        state_key = f"{section_key}-{field}"
        if state_key not in st.session_state:
            st.session_state[state_key] = default_value
    if show_header:
        st.sidebar.markdown("---")
        st.sidebar.subheader(title)
    primary = st.sidebar.color_picker(
        f"{title} primary",
        st.session_state[f"{section_key}-primary"],
        key=f"{section_key}-primary",
    )
    secondary = st.sidebar.color_picker(
        f"{title} secondary",
        st.session_state[f"{section_key}-secondary"],
        key=f"{section_key}-secondary",
    )
    style = st.sidebar.selectbox(
        f"{title} fill",
        FILL_STYLES,
        index=FILL_STYLES.index(st.session_state.get(f"{section_key}-style", defaults["style"]))
        if st.session_state.get(f"{section_key}-style") in FILL_STYLES
        else 0,
        key=f"{section_key}-style",
    )
    extra = st.sidebar.color_picker(
        f"{title} pattern/extra color",
        st.session_state[f"{section_key}-extra"],
        key=f"{section_key}-extra",
    )
    angle = st.sidebar.slider(
        f"{title} angle (gradients/stripes)",
        0,
        180,
        st.session_state[f"{section_key}-angle"],
        key=f"{section_key}-angle",
    )
    gap = st.sidebar.slider(
        f"{title} gap/spacing", 6, 48, st.session_state[f"{section_key}-gap"], key=f"{section_key}-gap"
    )
    opacity = st.sidebar.slider(
        f"{title} pattern opacity",
        0.0,
        1.0,
        st.session_state[f"{section_key}-opacity"],
        key=f"{section_key}-opacity",
    )
    size = st.sidebar.slider(
        f"{title} dot/check size", 4, 40, st.session_state[f"{section_key}-size"], key=f"{section_key}-size"
    )
    tint = st.sidebar.color_picker(
        f"{title} tint (OutfitDef)", st.session_state[f"{section_key}-tint"], key=f"{section_key}-tint"
    )
    upload_bytes = None
    upload_mime = ""
    upload_active = False
    upload_rotation = 0.0
    upload_scale = 1.0
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
            if allow_scale:
                upload_scale = st.sidebar.slider(
                    f"Scale uploaded {title.lower()}",
                    min_value=0.5,
                    max_value=1.5,
                    value=st.session_state.get(f"{section_key}-upload-scale", 1.0),
                    step=0.05,
                    key=f"{section_key}-upload-scale",
                )
        else:
            upload_active = False
            upload_rotation = 0.0
    else:
        upload_scale = 1.0
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
        upload_scale=upload_scale,
    )


body_cfg = part_controls(
    "Body",
    BODY_DEFAULTS,
    allow_upload=True,
    allow_scale=True,
)
hand_cfg = part_controls(
    "Hands",
    HAND_DEFAULTS,
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
    BACKPACK_DEFAULTS,
    allow_upload=True,
)

if "loot-shirt-tint" not in st.session_state:
    st.session_state["loot-shirt-tint"] = LOOT_DEFAULTS["shirt"]
loot_icon_tint = st.sidebar.color_picker(
    "Loot shirt tint",
    st.session_state["loot-shirt-tint"],
    key="loot-shirt-tint",
)
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
    default_front_left = body_frame.left
    default_front_top = body_frame.top
    default_front_width = body_frame.width
    default_front_height = body_frame.height
    default_front_rotation = body_frame.rotation
    if selected_preview_label == "Knocked" and active_layout.show_feet:
        default_front_rotation = active_layout.feet_rotation_left or default_front_rotation
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
    front_preview["overlay_above_front"] = overlay_above_front

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

front_preview.setdefault("overlay_above_front", overlay_above_front)

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
        float(body_cfg.get("upload_scale", 1.0)),
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
    hands_svg_text = build_part_svg(
        hand_cfg, svg_hands, hand_stroke_col, hand_stroke_w, hand_outline_style
    )

if bp_cfg.get("upload_active") and bp_cfg.get("upload_bytes"):
    backpack_svg_text = svg_from_upload(
        bp_cfg["upload_bytes"],
        bp_cfg.get("upload_mime", ""),
        148,
        148,
        float(bp_cfg.get("upload_rotation", 0.0)),
    )
else:
    backpack_svg_text = build_part_svg(
        bp_cfg, svg_backpack, bp_stroke_col, bp_stroke_w, bp_outline_style
    )

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
front_preview["overlay_above_front"] = front_preview.get("overlay_above_front", overlay_above_front)

# ---------------------------
# Combined preview
# ---------------------------

st.title("Zurviv.io Skin Creator")
st.caption(
    "All settings on the left. Preview shows a layered mock-up (backpack, body, optional armor overlay, hands, accessory) plus individual sprites."
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
    build_preview_html(uris, layout=active_layout, front=front_preview),
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
    "overlayAboveFront": overlay_above_front,
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
preview_options = {
    "overlayEnabled": bool(active_layout.show_overlay),
    "overlayAboveFront": overlay_above_front,
}
manifest_json = build_manifest(
    ident=ident,
    opts=opts,
    filenames=filenames,
    ui_tints=tints,
    export_tints=ts_tints,
    sprite_mode=sprite_mode,
    preview_preset=selected_preview_label,
    front_meta=front_meta,
    preview_options=preview_options,
)
preview_document_html = build_preview_document(
    uris, layout=active_layout, front=front_preview
)
preview_bytes = preview_document_html.encode("utf-8")
preview_filename_base = selected_preview_label.lower().replace(" ", "-")
sprite_exports = [
    ("base", body_svg_text),
    ("hands", hands_svg_text),
    ("feet", feet_svg_text),
    ("backpack", backpack_svg_text),
    ("loot", loot_svg_text),
]
if loot_border_on and filenames.get("border"):
    sprite_exports.append(("border", loot_outer_svg_text))
if loot_border_on and filenames.get("inner"):
    sprite_exports.append(("inner", loot_inner_svg_text))
if front_has_sprite and filenames.get("front"):
    sprite_exports.append(("front", front_svg_text))
sprite_labels = {
    "base": "body",
    "hands": "hands",
    "feet": "feet",
    "backpack": "backpack",
    "loot": "loot icon – shirt silhouette, no stroke",
    "border": "loot border",
    "inner": "loot inner glow",
    "front": "front accessory",
}
sprite_button_labels = {
    "base": "Body",
    "hands": "Hands",
    "feet": "Feet",
    "backpack": "Backpack",
    "loot": "Loot icon",
    "border": "Loot border",
    "inner": "Loot inner glow",
    "front": "Accessory",
}

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
    zip_lines = []
    for key, _ in sprite_exports:
        name = filenames.get(key)
        if not name:
            continue
        label = sprite_labels.get(key, key)
        zip_lines.append(f"- `{name}` ({label})")
    zip_lines.append(
        f"- `preview/{preview_filename_base}.html` (preview snapshot for {selected_preview_label})"
    )
    zip_lines.extend(
        [
            f"- `export/{ident}.ts` (ready `defineOutfitSkin(...)`)",
            f"- `export/{ident}.manifest.json` (asset + metadata manifest)",
        ]
    )
    st.markdown("\n".join(zip_lines))

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    for key, svg_text in sprite_exports:
        name = filenames.get(key)
        if not name:
            continue
        zip_name = name if name.endswith(".svg") else name.replace(".img", ".svg")
        zf.writestr(zip_name, svg_text)
    zf.writestr(f"export/{ident}.ts", ts_code)
    zf.writestr(f"export/{ident}.manifest.json", manifest_json)
    zf.writestr(f"preview/{preview_filename_base}.html", preview_document_html)
zip_bytes = buf.getvalue()

sprites_only_buf = io.BytesIO()
with zipfile.ZipFile(sprites_only_buf, "w", zipfile.ZIP_DEFLATED) as zf:
    for key, svg_text in sprite_exports:
        name = filenames.get(key)
        if not name:
            continue
        zip_name = name if name.endswith(".svg") else name.replace(".img", ".svg")
        zf.writestr(zip_name, svg_text)
sprites_only_zip_bytes = sprites_only_buf.getvalue()

st.download_button(
    "⬇️ Download Zurviv bundle (ZIP)",
    data=zip_bytes,
    file_name=f"{(base_id or 'zurviv')}_zurviv_skin.zip",
    mime="application/zip",
)
st.download_button(
    "⬇️ Sprites only (ZIP)",
    data=sprites_only_zip_bytes,
    file_name=f"{(base_id or 'zurviv')}_zurviv_sprites.zip",
    mime="application/zip",
)
st.download_button(
    "⬇️ TypeScript only",
    data=ts_code.encode("utf-8"),
    file_name=f"{ident}.ts",
    mime="application/typescript",
)
st.download_button(
    "⬇️ Asset manifest JSON",
    data=manifest_json.encode("utf-8"),
    file_name=f"{ident}.manifest.json",
    mime="application/json",
)
st.download_button(
    "⬇️ Preview only (HTML)",
    data=preview_bytes,
    file_name=f"{ident}-{preview_filename_base}.html",
    mime="text/html",
)

st.markdown("#### Individual sprite downloads")
sprite_cols = st.columns(2)
for idx, (key, svg_text) in enumerate(sprite_exports):
    name = filenames.get(key)
    if not name:
        continue
    svg_name = name if name.endswith(".svg") else name.replace(".img", ".svg")
    col = sprite_cols[idx % 2]
    col.download_button(
        f"⬇️ {sprite_button_labels.get(key, key.title())}",
        data=svg_text,
        file_name=svg_name,
        mime="image/svg+xml",
        key=f"download-{key}-svg",
    )
