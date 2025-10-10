# Survev.io Skin Creator (Streamlit)

**Built for your OutfitDef.** Controls on the left, a single combined preview on the right, and exports that drop into your `outfitDefs.ts`:

- Exports separate sprites for **body**, **hands**, **feet** (auto = hands, no UI), and **backpack**.
- Exports a ready `defineOutfitSkin("outfitBase", { ... })` block with:
  - `skinImg` tints + sprite names,
  - `lootImg.sprite/tint` (and optional `border`, `borderTint`, `scale`),
  - optional `noDropOnDeath`, `noDrop`, `rarity`, `lore`, `ghillie`, `obstacleType`, `baseScale`,
  - `sound: { pickup: "clothes_pickup_01" }`.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
