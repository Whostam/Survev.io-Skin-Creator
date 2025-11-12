# Zurviv.io Skin Creator (Streamlit)

Build and preview custom Zurviv.io outfits with a Streamlit-powered editor. The app lets you design recolors or brand-new sprites, try them across multiple preview poses, and export everything needed for integration.

## Highlights

- **Layered preview presets** for Loadout, Standing, and Knocked poses with optional armor/helmet overlays and accessory layering controls.
- **Randomizer** to shuffle body/backpack/hand palettes and fill patterns without disturbing outlines or gameplay flags.
- **Sprite uploads & transforms** for body, hands, backpack, and front accessories, including rotation and body scaling for quick alignment.
- **Accessory workflow** that supports uploadable front sprites, placement offsets, optional above-hand rendering, and manifest metadata.
- **Flexible exports**: Zurviv-style TypeScript snippet, JSON asset manifest, preview HTML snapshot, per-sprite SVGs, and combined ZIP bundles.
- **Automated tests** covering color math, filename helpers, manifest generation, and preview layout calculations.

## Project layout

```
app.py                # Streamlit UI + orchestration
skin_creator/         # Helper modules for fills, sprites, preview, exports
tests/                # Regression tests (run with `python -m unittest discover`)
requirements.txt      # Python dependencies
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## What the app exports

- Individual SVG sprites for body, hands, feet, backpack, loot circles, loot icon, and optional accessory.
- Zurviv-flavored TypeScript snippet (`export/{ident}.ts`) ready for `defineOutfitSkin("outfitBase", …)`.
- Asset manifest (`export/{ident}.manifest.json`) capturing filenames, tint values, preview options, and accessory metadata.
- Preview HTML snapshot (`preview/<preset>.html`) that mirrors the layered stage with current colors and uploaded art.
- Download shortcuts for sprites only, TypeScript only, manifest only, preview only, or any single sprite.

All of the above are bundled in the “Zurviv bundle” ZIP download alongside the individual download buttons.
