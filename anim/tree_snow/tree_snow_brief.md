# Add-on: snow settling on the trees when it snows (with accumulation stages)

## What this is
Overlay images that lay snow on the pine forest while the weather is **snow**, matching the
snow already on the mountains. Nothing is animated — they are still overlays. There are **four
accumulation stages**, from a light dusting to a heavy blanket, so the snow can visibly build
up the longer it snows and melt back off when it stops.

## The files (in `anim/`)
`tree_snow_<layer>_<time>_s<N>.png`
- `<layer>` = `near` (the front `near_forest_<time>` trees) or `far` (the background hill forest baked into `bg_<time>`).
- `<time>`  = `morning` | `day` | `afternoon` | `night` (tinted to each palette's snow colours — swap together like all time-of-day assets).
- `<N>`     = `1`..`4` accumulation stage. **s1 = light dusting, s4 = heavy blanket.**
- Each is a full 320×180 transparent canvas; every snow pixel already sits on a tree pixel, so draw at (0,0), no offset.
- Each stage is a strict superset of the one before it, so stepping up a stage only *adds* snow — it never reshuffles.

## Draw order (keep depth correct)
`bg` → **tree_snow_far_<time>_sN** → stars/clouds → waterfall → sasquatch → `near_forest` →
**tree_snow_near_<time>_sN** → treetops → bird → rain/snow → wind → window → sill items.
The far and near layer always use the **same** stage N.

## When / how to drive the stages
Show the effect only while `weather === 'snow'`:
1. When snow begins, fade the effect in (tie its master opacity to the falling-`snow` overlay's fade) starting at **stage 1**.
2. While it keeps snowing, step the stage up over time — e.g. advance one stage every ~20–40 s of continuous snow, cross-fading from sN to sN+1, capping at **stage 4**.
3. When the snow stops (or a "thaw"), step the stage back down the same way, then fade out at stage 1.

A single `stage` value (1–4) plus a master opacity drives everything; cross-fade between the
current and next stage image as `stage` changes. Keep it simple — even just snapping between
stages behind the master fade looks fine.

## Manifest
See `weather_overlays.tree_snow` in `manifest.json` (source of truth) for the file naming,
stage count, draw positions and fade notes.

## Tuning
Stage depth/coverage is set in `scripts/treesnow.py` (`STAGES = [...]`). Want lighter or heavier
overall, or more/fewer stages? It's a one-line change there and a regenerate.
