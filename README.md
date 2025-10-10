# Survev.io Skin Creator (Streamlit)

A minimal Streamlit app that designs Survev.io outfits and exports the **exact files your game expects**:

- Separate sprites for **body**, **hands**, **feet**, and **backpack**
- A **loot icon** (shirt)
- A ready-to-paste **TypeScript export** using `defineOutfitSkin(...)` with proper `tint` hex literals, `rarity`, `lore`, and flags (`noDropOnDeath`, `noDrop`, `ghillie`, `obstacleType`, `baseScale`)

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
