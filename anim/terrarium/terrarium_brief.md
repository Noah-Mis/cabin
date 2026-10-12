# Terrarium Mini-Game — Asset & Implementation Brief

> For the implementing agent. Every asset referenced here exists in `anim/`.
> All text is rendered at runtime in the site's pixel font — **nothing is baked
> into the sprites.** The sprites are chrome; the words are yours.

---

## 1. Design Premise

The pot on the left interior wall is your **one growing slot**. The journal that
opens when you click it is where the game actually lives.

```
  plant a seed  ->  water it over real time  ->  it grows  ->  harvest seeds
        ^                                                            |
        |                                                            v
   plant hybrid  <-  new species seed  <-  cross two seeds in the journal
```

One pot, infinite genetics. This is deliberate: it keeps the wall uncluttered
(the approved pot+shelf asset is the only new furniture), and it makes the
journal — not the scenery — the place where progress is visible.

**Visible progress** comes from the Codex tab: 12 species, 6 of which only exist
if you breed for them. The rarest (Aurora Bloom) is four crosses deep.

---

## 2. Asset Inventory

All files are in `anim/`, four time-of-day variants each
(`_morning`, `_day`, `_afternoon`, `_night`) — **48 files total**.

| File | Size | Grid | Purpose |
|---|---|---|---|
| `terrarium_potshelf_<t>.png` | 32×36 | 1 | The pot on the wall. **Already approved.** Click target. |
| `terrarium_journal_<t>.png` | 164×124 | 1 | Panel: paper, ruled lines, margin, binding holes, 4 inactive tabs baked on the right edge |
| `terrarium_tab_active_<t>.png` | 16×22 | 1 | Overlay drawn on whichever tab is selected. Must match the baked tab width exactly |
| `terrarium_tabicons_<t>.png` | 40×10 | 4 × 10×10 | Tab glyphs: pot, seed, cross, book |
| `terrarium_seeds_<t>.png` | 96×8 | 12 × 8×8 | One seed per species, colour-coded by signature colour |
| `terrarium_codex_<t>.png` | 192×16 | 12 × 16×16 | Mature-plant portrait per species |
| `terrarium_slot_sm_<t>.png` | 64×16 | 4 × 16×16 | Slot states: empty, hover, filled, locked |
| `terrarium_slot_lg_<t>.png` | 60×20 | 3 × 20×20 | Big slot states: empty, hover, filled |
| `terrarium_meter_<t>.png` | 50×60 | 10 × 50×6 | Rows 0–4 = water 0/25/50/75/100%, rows 5–9 = growth |
| `terrarium_btn_sm_<t>.png` | 120×16 | 3 × 40×16 | Button: normal, hover, disabled |
| `terrarium_btn_lg_<t>.png` | 144×16 | 3 × 48×16 | Wide button: normal, hover, disabled |
| `terrarium_harvest_<t>.png` | 96×8 | 12 × 8×8 | Harvest tokens — the picked item, shown in the basket. Same species order |
| `terrarium_traits_<t>.png` | 48×8 | 6 × 8×8 | height, bloom, vigor, hue, hardiness, rarity |
| `terrarium_stars_<t>.png` | 14×7 | 2 × 7×7 | Rarity star: empty, filled |
| `terrarium_pot_back_<t>.png` | 48×40 | 1 | Zoomed pot, **back half**: rim's far edge, inner wall, soil bed. Drawn *behind* the plant |
| `terrarium_pot_front_<t>.png` | 48×40 | 1 | Zoomed pot, **front half**: rim's near face, body, base, saucer. Drawn *in front of* the plant |
| `terrarium_plants_<t>.png` | 144×192 | 12 rows × 9 cols, 16×16 | Foliage tiles — one row per species (see §8) |
| `terrarium_blooms_<t>.png` | 72×288 | 12 rows × 3 cols, 24×24 | Blooms, 3 stages per species. Bigger than a stem tile by design |
| `terrarium_font.png` | 212×6 | 53 × 4×6 | 3×5 pixel font, **white — tint in JS**. Not per-time. See §3a |

### Sheet indexing

Horizontal strips — frame `i` is `crop(i*w, 0, (i+1)*w, h)`.
The meter is the one **vertical** sheet — state `i` is `crop(0, i*6, 50, (i+1)*6)`.

```js
const waterRow  = state;        // 0..4  -> y = state * 6
const growthRow = 5 + state;    // 0..4  -> y = (5 + state) * 6
```

---

## 3. Panel Geometry

Panel origin on the 320×180 canvas: **`x = 78, y = 28`** (horizontally centred).
Paper occupies local x `0..149`; tabs protrude to x `163`.

Tab hit-boxes, local to the panel:

| Tab | Index | Local rect | Icon drawn at |
|---|---|---|---|
| Pot | 0 | `(148, 10, 16, 22)` | `(151, 16)` |
| Seeds | 1 | `(148, 36, 16, 22)` | `(151, 42)` |
| Cross | 2 | `(148, 62, 16, 22)` | `(151, 68)` |
| Codex | 3 | `(148, 88, 16, 22)` | `(151, 94)` |

Draw order per frame: `journal` → `tab_active` at the selected tab's y →
4 tab icons → active tab's content → text.

### Tab 0 — POT

| Element | Local pos | Asset |
|---|---|---|
| Title "TERRARIUM" | `(13, 7)` | text, `accent` |
| Zoomed pot | `(12, 54)` | `pot_back` → plant → `pot_front` (see below) |
| Species name | `(66, 21)` | text, `text` |
| Rarity stars | `(66, 30)`, step 8 | `stars` |
| Status line | `(66, 41)` | text, `text_d` |
| "WATER" label | `(66, 50)` | text, `text_d` |
| Water meter | `(66, 58)` | `meter` row `state` |
| "GROWTH" label | `(66, 68)` | text, `text_d` |
| Growth meter | `(66, 76)` | `meter` row `5 + state` |

Vertical rhythm on this tab is **label at `y`, meter at `y + 8`**, blocks spaced
18px. Keep it — tighter and the 5px glyphs touch the meter border.

#### The mouth is an ellipse, not a rectangle

The pot is drawn as if seen slightly from above, so the opening is a true
ellipse (outer rim 22×7, opening 18×5, centred on pot-local row 14) and the
soil is the filled inner ellipse. That's why the soil can't be blitted as a
rectangle — if you ever regenerate it, keep the ellipse or the dirt goes back
to looking like a slab sitting on top of the pot.

#### The pot is two sprites, and the plant goes between them

A single pot sprite can't work here: the plant has to come *out of* the opening,
which means part of the pot is behind it and part in front. So it ships split at
the rim, both halves 48×40 and pixel-aligned — **composite them at the same
`(x, y)` and they register exactly.**

```js
ctx.drawImage(potBack,  12, 54);   // rim far arc, inner wall, soil
drawPlant(ctx,          12, 54);   // §8 — grows UP from the soil line
ctx.drawImage(potFront, 12, 54);   // rim near arc, body, base, saucer
```

Get this order wrong and the dirt looks like it's sitting on top of the pot
instead of in it.

The pot is placed low in the tab on purpose. Pot-local row 15 is the soil line,
so on the panel it sits at `y = 69`, leaving **49px of empty paper above it**.
That gap is where the plant grows, and watching it fill is the main progress
feedback on this tab — don't reclaim the space for anything else.

Pot-local landmarks, if you need to anchor anything:

| Row | What |
|---|---|
| 8–13 | rim far arc (back sprite) |
| 10–18 | soil ellipse, widest `x 6..42` at row 14 (back sprite) |
| **15** | **soil line — plant anchors here** |
| 15–20 | rim near arc, drawn over the body (front sprite) |
| 14–33 | body (front sprite) |
| 34–36 | base ring (front sprite) |
| 37–39 | saucer (front sprite) |
| Buttons ×3 | `(12,104)`, `(56,104)`, `(100,104)` | `btn_sm` — WATER / TRIM / HARVEST |

Harvest is `disabled` until growth ≥ 1.0. Trim is `disabled` below growth 0.35.
Button labels are centred on `bx + 20`, baseline `y = 110`.

### Tab 1 — SEEDS

12 slots, 6 across × 2 down. Slot `i` at
`x = 14 + (i % 6) * 22`, `y = 26 + floor(i / 6) * 26`.

Seed sprite centres in its slot at `+(4, 4)`. Count badge at `+(12, 10)`.
Slots for species you own 0 of use the `empty` state and draw no seed.
Selecting a slot shows name at `(13, 77)` with its rarity stars at `(40, 76)`,
blurb at `(13, 87)`, and enables the **Plant** button at `(100, 104)`.

Plant is `disabled` when the pot is occupied.

### Tab 2 — CROSS

| Element | Local pos | Asset |
|---|---|---|
| Parent A slot | `(20, 32)` | `slot_lg`; seed at `+(6, 6)` |
| "X" glyph | `(46, 39)` | text |
| Parent B slot | `(60, 32)` | `slot_lg`; seed at `+(6, 6)` |
| ">" glyph | `(90, 39)` | text |
| Result slot | `(108, 32)` | `slot_lg` (`hover` state = predicted) |
| Parent labels | centred on `30`, `70`, `118` at `y = 57` | text |
| Trait row | `(14 + i*22, 66)`, i = 0..5 | `traits` + value text at `+(9, 2)` |
| Odds line | `(13, 87)` | text, `text_d` |
| CROSS button | `(52, 104)` | `btn_lg`, label centred on `76`, `y = 110` |

Tapping a parent slot opens the seed picker (reuse the Tab 1 grid as an overlay).
The result slot shows the **predicted** species while odds are known; after the
roll it shows what you actually got.

### Tab 3 — CODEX

12 entries, 6 across × 2 down. Entry `i` at
`x = 13 + (i % 6) * 22`, `y = 26 + floor(i / 6) * 30`.

Discovered → `slot_sm` `filled` + the `codex` portrait.
Undiscovered → `slot_sm` `locked` (hatched), no portrait.

Counter at `(13, 80)`, selected entry's name at `(13, 90)` with its rarity stars
at `(60, 89)`, flavour text at `(13, 112)`.

---

## 3a. Text & Font

Ships as `anim/terrarium_font.png` — **not** per-time-of-day. It's white; tint it
in JS to the role colour (§14). Every label position in §3 is measured against
these metrics, so substituting a different font will break the layout.

```
glyph ink   3 x 5 px
cell        4 x 6 px
advance     4 px        (3px glyph + 1px gap)
ink width   len(s) * 4 - 1
```

Glyph index is the character's position in this charset — index 0 is space:

```
 ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,-_/%!?:+><()*'
```

```js
const CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,-_/%!?:+><()*'";
function drawText(ctx, s, x, y, color) {
  s = s.toUpperCase();
  for (let i = 0; i < s.length; i++) {
    const g = CHARSET.indexOf(s[i]);
    if (g < 0) continue;                       // unknown char -> skip
    ctx.drawImage(fontSheet, g * 4, 0, 4, 6, x + i * 4, y, 4, 6);
  }
}
const textWidth = s => s.length * 4 - 1;
const centerText = (s, cx) => cx - ((s.length * 4 - 1) >> 1);
```

**The font is uppercase-only.** Lowercase input is upper-cased on draw, so
"Bluebell" renders as "BLUEBELL". That's the intended look — don't add a
lowercase set without re-checking every width below.

### Baseline grid — text must not sit on a ruled line

The paper carries **nine evenly spaced rules at y = 16, 26, 36 … 86, plus a
solid section divider at y = 96** — every one at `y % 10 == 6`, every one
spanning the full `x 12..143`. There is no separate header rule and nothing is
drawn below the divider, so the button/rail strip is clean paper.

> Earlier revisions had a half-width header rule that stopped mid-page at x 91,
> and a divider at y 100 sitting 4px from the rule at 96 with a further stray
> rule at 106 behind the buttons. If you regenerate the panel, keep the run
> evenly spaced and keep the divider one full 10px step below the last rule.

A glyph is 5 rows tall, so a baseline `y` is safe only when:

```
y % 10  in  {7, 8, 9, 0, 1}
```

Anything else puts a rule straight through the letterforms. `y % 10 == 9` is the
best of them — it centres the text in the band with two clear rows above and
below. Below the divider (`y > 96`, the button/rail strip) there are no rules, so
any baseline is fine there.

Every position in §3 satisfies this. If you add a label, check it:

```js
const onRule = y => y >= 16 && y <= 96 && [2,3,4,5,6].includes(y % 10);
```

Sprites are exempt — slots, meters and buttons are opaque and simply cover the
rule beneath them.

### Label budget

Content runs `x 12..145`, so **33 characters** is the hard line limit, and a
label starting at `x = 66` gets **19**. These are the longest strings the UI
actually needs — all verified to fit:

| String | Chars | Ink | Box | Fits |
|---|---|---|---|---|
| `HARVEST` | 7 | 27px | 40px button | 6px pad each side |
| `CROSS` | 5 | 19px | 48px button | 14px pad |
| `READY TO HARVEST.` | 17 | 67px | 79px to margin | yes |
| `AURORA BLOOM` | 12 | 47px | stars start at x 66+... | keep stars on their own row |
| `CHANCE 15% - NEW SPECIES` | 24 | 95px | 133px content | yes |
| `CROSS SEEDS TO FIND THE REST` | 28 | 111px | 133px content | yes |

If you add a string, check `len * 4 - 1` against the box before shipping it.
Anything longer than 33 chars needs a second line, not a smaller font — there
is no smaller font.

---

## 4. Species Table

Index order **is** the sheet order for both `seeds` and `codex`.

| # | id | Name | Rarity | Obtained by |
|---|---|---|---|---|
| 0 | `moss` | Moss | ★ | starter |
| 1 | `fern` | Fern | ★ | starter |
| 2 | `clover` | Clover | ★ | starter |
| 3 | `daisy` | Daisy | ★★ | starter |
| 4 | `wildflower` | Wildflower | ★★ | starter |
| 5 | `mushroom` | Mushroom | ★★ | starter |
| 6 | `bluebell` | Bluebell | ★★★ | daisy × wildflower |
| 7 | `suncap` | Suncap | ★★★ | mushroom × daisy |
| 8 | `ivy` | Ivy | ★★★ | fern × clover |
| 9 | `thistle` | Thistle | ★★★★ | wildflower × fern |
| 10 | `moonflower` | Moonflower | ★★★★ | bluebell × mushroom |
| 11 | `aurora` | Aurora Bloom | ★★★★★ | moonflower × suncap |

New players start with **3 Moss, 2 Fern, 2 Clover** seeds. Daisy, Wildflower and
Mushroom are starters by rarity but must be found — grant one at random the first
time the player harvests anything, so the early game always opens up.

---

## 5. Cross Table

```js
const CROSSES = [
  { a: 'daisy',      b: 'wildflower', out: 'bluebell',   chance: 0.15 },
  { a: 'mushroom',   b: 'daisy',      out: 'suncap',     chance: 0.15 },
  { a: 'fern',       b: 'clover',     out: 'ivy',        chance: 0.20 },
  { a: 'wildflower', b: 'fern',       out: 'thistle',    chance: 0.12 },
  { a: 'bluebell',   b: 'mushroom',   out: 'moonflower', chance: 0.10 },
  { a: 'moonflower', b: 'suncap',     out: 'aurora',     chance: 0.05 },
];
```

Pairs are **unordered** — match `(a,b)` or `(b,a)`.

### Resolution

1. Look up the pair. If a hybrid exists, roll `chance`.
2. **Hit** → offspring is the hybrid species.
3. **Miss, or no hybrid for this pair** → offspring is one of the two parents,
   chosen at random.
4. Either way the player gets a seed. **A cross is never wasted** — that matters
   for the cozy tone. Both parent seeds are consumed.

### Odds display

Show the real number: `"chance 15% - new species"`. If the pair has no hybrid,
show `"no new species from this pair"` and keep CROSS enabled — mixing traits is
still a reason to do it.

Raise the displayed and rolled chance by **+5 percentage points** for each prior
failed attempt on that same pair, capped at **+25**, and reset on success. Store
in `terrarium.pity[pairKey]`. This keeps Aurora Bloom reachable without making
it cheap.

---

## 6. Genetics

Every seed carries a genome. Species decides what it looks like; the genome
decides how it performs and how it reads in the trait row.

```js
{
  height:    1..5,   // final plant height, picks which stem tiles stack
  bloom:     0..2,   // 0 none, 1 small, 2 full
  vigor:     1..5,   // growth rate multiplier (0.8 + vigor * 0.1)
  hue:       1..5,   // bloom colour shift bucket (see below)
  hardiness: 1..5,   // drought tolerance; slows hydration decay
}
```

**Every trait is a 1–5 bucket** so the trait row renders as single digits. Hue
was originally 0–359; it is bucketed because at 3×5 a three-digit number is
both cramped and ambiguous (`0` and `D` are near-identical). Map the bucket to
degrees only at draw time:

```js
const HUE_DEG = { 1: -40, 2: -20, 3: 0, 4: 20, 5: 40 };   // relative to species base
```

Bucket 3 is the species' own colour; 1 and 5 are the visible extremes. A 40°
swing is enough to read as "a bluer bluebell" without turning it into a
different plant.

Trait icon order in `terrarium_traits.png` matches this order, with `rarity`
(species-derived, not inherited) as icon 5.

### Inheritance

```js
function crossTrait(a, b) {
  const mid = (a + b) / 2;
  const jitter = Math.random() < 0.5 ? -1 : 1;
  return clamp(Math.round(mid + jitter * (Math.random() < 0.3 ? 1 : 0)), 1, 5);
}
// hue wraps on a circle
function crossHue(a, b) {
  let d = ((b - a + 540) % 360) - 180;
  return Math.round((a + d / 2 + (Math.random() * 30 - 15) + 360)) % 360;
}
```

A hybrid species seeds its genome from the crossed parents, then clamps `bloom`
to at least 1 if its species flowers (Bluebell, Thistle, Moonflower, Aurora all
do). Starter seeds roll `height 2-3, bloom by species, vigor 2-4, hardiness 2-4,
hue = species default`.

### Where genome shows up

- `height` → how many stem tiles stack in the zoomed pot
- `bloom` → whether bloom tiles appear at all, and `bloom_bud` vs `bloom_full`
- `vigor` → growth rate
- `hardiness` → hydration decay rate
- `hue` → a hue-rotate on bloom pixels only. Keep stems and leaves untouched or
  plants stop reading as plants.

---

## 7. Growth Simulation

Time is **real-world** time. The plant grows while nobody is watching; that is
the whole appeal.

```
EVAP_PER_HOUR   = 0.08 / (0.6 + hardiness * 0.15)
GROWTH_PER_HOUR = 0.035 * (0.8 + vigor * 0.1)
OFFLINE_CAP     = 48 hours
```

### Tick

Run on page load and then every 60 s while the tab is open:

```
elapsed = min(now - last_tick, OFFLINE_CAP)
hydration = max(0, hydration - elapsed_hours * EVAP_PER_HOUR)

if (species && hydration > 0.10) {
    growth = min(1, growth + elapsed_hours * GROWTH_PER_HOUR * health)
    advance the growth grid (§8)
}
if (hydration <= 0.10) wilting = true     // reversible
if (hydration == 0 for > 24h) -> dead
last_tick = now
```

`health` is `1.0` normally, `0.5` while wilting. Watering clears `wilting`
immediately — a neglected plant should always be recoverable in one click.

### Stages

| Growth | Stage | Status text |
|---|---|---|
| 0.00 | seed | "Just planted." |
| 0.15 | sprout | "Sprouting." |
| 0.35 | young | "Growing..." |
| 0.65 | mature | "Filling out." |
| 0.85 | flowering | "In bloom." |
| 1.00 | ready | "Ready to harvest." |

Full cycle at vigor 3 is roughly **34 real hours**. Tune `GROWTH_PER_HOUR` if
that feels long — but keep it over a day. The pot should be something you check
on, not something you grind.

### Actions

- **Water** — `hydration = min(1, hydration + 0.25)`, clears wilting.
  Debounce 500 ms. Over 1.0 the extra drains: status reads "Saturated!" and
  nothing bad happens.
- **Trim** — removes dead/overgrown cells from the grid, `growth -= 0.05`,
  `health = 1.0`. Only meaningful above growth 0.35.
- **Harvest** — at growth 1.0: pot empties, player gets **1–2 seeds** of that
  species (2 at `vigor >= 4`), species is marked discovered in the codex.

---

## 8. Growth Rendering

Plants are drawn **between the two pot halves** (see §3), anchored on the soil
line at pot-local `y = 15` and growing upward out of the mouth.

There are two sheets. Foliage is `terrarium_plants_<t>.png` — 12 species rows ×
9 columns of **16×16** tiles. Blooms live separately in
`terrarium_blooms_<t>.png` — 12 species rows × 3 stages of **24×24**, because a
flower has to be able to overhang the stem that carries it.

```
foliage columns
0 seed   1 sprout   2 stem        3 stem_leaves   4 stem_leaf_l
5 stem_leaf_r       6 crown       7 dead          8 wilt

bloom columns
0 bud    1 opening  2 full
```

Row index is the species index from §4 — `moss` is row 0, `aurora` row 11, and
the seed and codex sheets use the same order.

### The connection contract

This is the part to not improvise. Plants are a vertical stack, and the stem has
to hand off at exactly the same pixels or you get a visible step at every tile
boundary.

| | Stem columns inside the tile |
|---|---|
| foliage tile, most species | `x = 7, 8` |
| foliage tile, mushroom & suncap | `x = 6, 7, 8, 9` (thick stipe) |
| bloom tile, most species | `x = 11, 12` |
| bloom tile, mushroom & suncap | `x = 10, 11, 12, 13` |

A bloom is drawn **4px to the left of the stem column**, which is what makes its
stub land on the stem below it:

```js
const BLOOM_OFFSET = -4;
ctx.drawImage(stemTile,  stemX,               y);
ctx.drawImage(bloomTile, stemX + BLOOM_OFFSET, y - 24);
```

Nothing else crosses a tile boundary — every leaf, branch and bract terminates
inside its own tile — so the stem is the only seam, and it is the only thing
that has to line up.

`plants.py` ships with a `verify()` pass that checks all of it:

- every tile needing a connection has opaque pixels on the contract columns
- stem colour is identical top-to-bottom within a tile
- all four stem variants agree with each other
- each bloom's stub matches the stem it lands on
- **nothing floats** — an 8-connected flood fill from the stub at the bottom
  edge has to reach every pixel in the tile. Components of 1–3px are allowed,
  since Aurora Bloom's drifting motes are deliberate.

The float test is the one that earns its keep: it caught the mushroom cap
hovering two rows above its stipe (the stub start was a flat per-stage table,
but gills sit lower than a petal mass) and an empty row between the thistle's
filament spray and its cup. It currently reports **all tiles pass**. Run it
after any edit to the art — including a palette change, since the colour
equality checks are part of it.

### Building a stack

Bottom to top, starting at the soil line. **A stack always ends in a
terminator** — `crown` for species that never flower, or a bloom for those that
do. A bare `stem` tile with nothing above it reads as broken, not as young.

| Stage | Stack (bottom → top) | Height |
|---|---|---|
| seed | `seed` | 16px |
| sprout | `sprout` | 16px |
| young | `stem_leaves`, `crown` | 32px |
| mature | `stem_leaves`, `stem_leaves`, `crown` | 48px |
| flowering | `stem_leaves`, `bud` → `opening` | 40px |
| ready | `stem_leaves`, `full` | 40px |
| wilting | same stack, `wilt` in place of each `stem_leaves` | — |
| dead | same stack, `dead` in every slot including the top | — |

Species with `bloom` style `none` (moss, fern, clover, ivy) never leave the
`crown` terminator — for them *mature* is the final look, and harvesting is
gated on growth, not on a flower appearing.

Vary the middle of the stack with `stem_leaf_l` / `stem_leaf_r` instead of
always using `stem_leaves`; pick per slot from an RNG seeded on `plantedAt` so a
given plant redraws identically on every reload.

### Pixel budget

The panel gives the plant **49px** above the soil line. The table above is built
to fit inside that: the tallest stack is *mature* at 48px. The `height` gene
does **not** stretch the stack past this — the zoomed pot is a portrait, not a
scale model, and height is reported as a number in the trait row instead. If you
want height to read visually, spend it on which middle tiles get leaves, not on
adding rows.

### Hue

The `hue` gene shifts **bloom pixels only** (§6). Leave stems and leaves alone —
rotate those and the plant stops reading as a plant. In practice: composite the
bloom tile to an offscreen canvas, apply the hue rotation there, then draw it.

---

## 9. State Schema

One key, one object. Easier to migrate than nine loose keys.

```js
localStorage['cabin_terrarium'] = JSON.stringify({
  version: 1,

  pot: {                       // null when empty
    species: 'bluebell',
    genome: { height:3, bloom:2, vigor:4, hue:4, hardiness:3 },
    hydration: 0.72,           // 0..1
    growth: 0.48,              // 0..1
    health: 1.0,
    wilting: false,
    dead: false,
    plantedAt: 1760000000000,
    stack: ['stem_leaves','full'],   // §8, resolved bottom -> top
  },

  seeds: {                     // species id -> array of genomes
    moss: [ {...}, {...}, {...} ],
    fern: [ {...}, {...} ],
  },

  codex: ['moss','fern','clover','daisy','wildflower','mushroom','bluebell'],

  pity: { 'daisy|wildflower': 2 },   // failed crosses per pair, sorted key

  lastTick: 1760000000000,
  lastWater: 1759990000000,
  tab: 0,                      // remembered tab
});
```

Write on every mutating action and on tick. Read once on load. If `version`
is missing or unknown, reset to a fresh state rather than guessing.

---

## 10. Terminal Commands

The journal and the terminal drive the same state. Anything done in one shows up
in the other immediately — if the journal is open when a command lands, re-render it.

| Command | Effect |
|---|---|
| `terrarium` | Opens the journal on the Pot tab |
| `terrarium status` | Prints species, stage, water %, growth % — no popup |
| `water` | Same as the Water button |
| `trim` | Same as the Trim button |
| `harvest` | Same as the Harvest button; prints what you got |
| `plant <species>` | Plants a seed of that species if you own one |
| `seeds` | Lists inventory with counts |
| `cross <a> <b>` | Runs a cross; prints the result and the odds it rolled |
| `codex` | Prints discovered / total and the missing names |

Errors stay in character: `"the pot's already got a bluebell in it."`

---

## 11. Interaction Map

```js
// pot on the wall — opens the journal
{ x: 5, y: 112, w: 32, h: 36, cursor: 'pointer', action: 'terrarium:open' }

// journal panel origin
const PX = 78, PY = 28;
// tab i hit-box (canvas coords)
{ x: PX + 150, y: PY + [10,36,62,88][i], w: 14, h: 22 }
```

Close on the X-less panel via: `Escape`, a click outside the panel rect, or a
second click on the pot. The journal is a **top-layer modal** — draw it after
weather, after sill items, after everything.

Hover: swap the slot/button sprite to its `hover` frame. Nothing moves on hover;
the frame swap is the whole feedback.

---

## 12. Manifest Additions

```json
"terrarium_potshelf": {
  "files": ["terrarium_potshelf_morning.png","terrarium_potshelf_day.png",
            "terrarium_potshelf_afternoon.png","terrarium_potshelf_night.png"],
  "frame_w": 32, "frame_h": 36, "frames": 1, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "placement": { "x": 5, "y": 112 },
  "draw_layer": "after_cabin_window", "clickable": true,
  "click_action": "terrarium:open",
  "note": "Pot + shelf on the left interior wall. Click target for the journal."
},
"terrarium_journal": {
  "files": ["terrarium_journal_morning.png","terrarium_journal_day.png",
            "terrarium_journal_afternoon.png","terrarium_journal_night.png"],
  "frame_w": 164, "frame_h": 124, "frames": 1, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "placement": { "x": 78, "y": 28 }, "draw_layer": "modal",
  "note": "Tabbed field journal. Composited at runtime with tab_active, tabicons, and the active tab's content. All text is JS-rendered."
},
"terrarium_tab_active": {
  "files": ["terrarium_tab_active_morning.png","terrarium_tab_active_day.png",
            "terrarium_tab_active_afternoon.png","terrarium_tab_active_night.png"],
  "frame_w": 16, "frame_h": 22, "frames": 1, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0],
  "placement": { "relative_to": "terrarium_journal", "x": 148, "y": "[10,36,62,88][activeTab]" },
  "note": "Drawn over the baked inactive tab for whichever tab is selected."
},
"terrarium_tabicons": {
  "files": ["terrarium_tabicons_morning.png","terrarium_tabicons_day.png",
            "terrarium_tabicons_afternoon.png","terrarium_tabicons_night.png"],
  "frame_w": 10, "frame_h": 10, "frames": 4, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0],
  "placement": { "relative_to": "terrarium_journal", "x": 151, "y": "tabY + 6" },
  "note": "0 pot, 1 seed, 2 cross, 3 book."
},
"terrarium_seeds": {
  "files": ["terrarium_seeds_morning.png","terrarium_seeds_day.png",
            "terrarium_seeds_afternoon.png","terrarium_seeds_night.png"],
  "frame_w": 8, "frame_h": 8, "frames": 12, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "placement": { "relative_to": "slot", "x": 4, "y": 4 },
  "note": "Frame index == species index. Colour-coded by signature colour."
},
"terrarium_codex": {
  "files": ["terrarium_codex_morning.png","terrarium_codex_day.png",
            "terrarium_codex_afternoon.png","terrarium_codex_night.png"],
  "frame_w": 16, "frame_h": 16, "frames": 12, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "placement": { "relative_to": "codex_slot", "x": 0, "y": 0 },
  "note": "Mature-plant portraits. Frame index == species index."
},
"terrarium_slot_sm": {
  "files": ["terrarium_slot_sm_morning.png","terrarium_slot_sm_day.png",
            "terrarium_slot_sm_afternoon.png","terrarium_slot_sm_night.png"],
  "frame_w": 16, "frame_h": 16, "frames": 4, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "note": "0 empty, 1 hover, 2 filled, 3 locked."
},
"terrarium_slot_lg": {
  "files": ["terrarium_slot_lg_morning.png","terrarium_slot_lg_day.png",
            "terrarium_slot_lg_afternoon.png","terrarium_slot_lg_night.png"],
  "frame_w": 20, "frame_h": 20, "frames": 3, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "note": "0 empty, 1 hover, 2 filled. Crossing bench slots."
},
"terrarium_meter": {
  "files": ["terrarium_meter_morning.png","terrarium_meter_day.png",
            "terrarium_meter_afternoon.png","terrarium_meter_night.png"],
  "frame_w": 50, "frame_h": 6, "frames": 10, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "stacking": "vertical",
  "note": "VERTICAL sheet. Rows 0-4 water 0/25/50/75/100%, rows 5-9 growth. Crop at y = row * 6."
},
"terrarium_btn_sm": {
  "files": ["terrarium_btn_sm_morning.png","terrarium_btn_sm_day.png",
            "terrarium_btn_sm_afternoon.png","terrarium_btn_sm_night.png"],
  "frame_w": 40, "frame_h": 16, "frames": 3, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "note": "0 normal, 1 hover, 2 disabled. Label drawn in JS."
},
"terrarium_btn_lg": {
  "files": ["terrarium_btn_lg_morning.png","terrarium_btn_lg_day.png",
            "terrarium_btn_lg_afternoon.png","terrarium_btn_lg_night.png"],
  "frame_w": 48, "frame_h": 16, "frames": 3, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "note": "0 normal, 1 hover, 2 disabled. CROSS button."
},
"terrarium_traits": {
  "files": ["terrarium_traits_morning.png","terrarium_traits_day.png",
            "terrarium_traits_afternoon.png","terrarium_traits_night.png"],
  "frame_w": 8, "frame_h": 8, "frames": 6, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "note": "0 height, 1 bloom, 2 vigor, 3 hue, 4 hardiness, 5 rarity."
},
"terrarium_stars": {
  "files": ["terrarium_stars_morning.png","terrarium_stars_day.png",
            "terrarium_stars_afternoon.png","terrarium_stars_night.png"],
  "frame_w": 7, "frame_h": 7, "frames": 2, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0], "note": "0 empty, 1 filled. Draw rarity count side by side, step 8px."
},
"terrarium_plants": {
  "files": ["terrarium_plants_morning.png","terrarium_plants_day.png",
            "terrarium_plants_afternoon.png","terrarium_plants_night.png"],
  "frame_w": 16, "frame_h": 16, "frames": 9, "rows": 12,
  "ms_per_frame": 0, "loop": false, "anchor": [0,0],
  "note": "Foliage tiles. Row = species index (§4), col = 0 seed, 1 sprout, 2 stem, 3 stem_leaves, 4 stem_leaf_l, 5 stem_leaf_r, 6 crown, 7 dead, 8 wilt. Stem occupies x 7-8 on both the top and bottom edge (x 6-9 for mushroom and suncap) — that is the stacking seam."
},
"terrarium_blooms": {
  "files": ["terrarium_blooms_morning.png","terrarium_blooms_day.png",
            "terrarium_blooms_afternoon.png","terrarium_blooms_night.png"],
  "frame_w": 24, "frame_h": 24, "frames": 3, "rows": 12,
  "ms_per_frame": 0, "loop": false, "anchor": [0,0],
  "placement": { "relative_to": "stem_tile", "x": -4, "y": -24 },
  "note": "Blooms, 3 stages: 0 bud, 1 opening, 2 full — each larger than the last. Row = species index. Draw 4px LEFT of the stem column so the stub at x 11-12 lands on the stem at x 7-8. Species with bloom style none (moss, fern, clover, ivy) have empty rows; use the crown foliage tile instead."
},
"terrarium_pot_back": {
  "files": ["terrarium_pot_back_morning.png","terrarium_pot_back_day.png",
            "terrarium_pot_back_afternoon.png","terrarium_pot_back_night.png"],
  "frame_w": 48, "frame_h": 40, "frames": 1, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0],
  "placement": { "relative_to": "terrarium_journal", "x": 12, "y": 54 },
  "draw_layer": "behind_plant",
  "note": "Back half of the zoomed pot: rim far arc plus the elliptical soil bed (rows 10-18, widest x 6-42). Draw BEFORE the plant grid."
},
"terrarium_pot_front": {
  "files": ["terrarium_pot_front_morning.png","terrarium_pot_front_day.png",
            "terrarium_pot_front_afternoon.png","terrarium_pot_front_night.png"],
  "frame_w": 48, "frame_h": 40, "frames": 1, "ms_per_frame": 0, "loop": false,
  "anchor": [0,0],
  "placement": { "relative_to": "terrarium_journal", "x": 12, "y": 54 },
  "draw_layer": "in_front_of_plant",
  "note": "Front half: rim near arc, body, base, saucer. Same x/y as pot_back — they are pixel-aligned. Draw AFTER the plant grid so the plant emerges from behind the rim."
}
```

---

## 13. Edge Cases

1. **Empty pot** — zoomed pot shows bare soil, name reads "Empty pot", Water /
   Trim / Harvest all `disabled`, Seeds tab's Plant button enabled.
2. **Dead plant** — portrait uses the `dead` tile, status "Withered.".
   Harvest becomes "Clear" and returns no seeds. Never auto-clear; let the
   player decide when to let go.
3. **Time-of-day change with the journal open** — swap every sprite to the new
   variant and re-pick text colours. Nothing else changes.
4. **Terminal command with the journal open** — mutate state, then re-render the
   current tab. Do not force a tab switch.
5. **Weather while open** — rain and snow render *behind* the modal.
6. **Zero seeds of everything** — grant the starter set (3 moss, 2 fern,
   2 clover). This is also the recovery path if a player breeds themselves into
   a corner, so check it on every load, not just first run.
7. **Cross with the same species in both slots** — allowed. Offspring is that
   species with mixed traits. Odds line reads "no new species from this pair".
8. **Offline longer than 48 h** — clamp to 48 h. A plant left for a week is
   thirsty, not dead. Dying should take sustained neglect *while visiting*.
9. **localStorage cleared** — fresh state, starter seeds, empty codex.
10. **Harvest on the last empty inventory slot** — inventory is unbounded;
    the grid shows the first 12 species, which is all of them.

---

## 14. Text Positions & Colours

Every label is JS-drawn. Colours come from the paper palette per time of day:

| Role | day | night |
|---|---|---|
| `text` (primary) | `#342C22` | `#A09888` |
| `text_d` (secondary) | `#605444` | `#645E56` |
| `accent` (headers) | `#8C5830` | `#584834` |

Headers go at `(13, 7)` on every tab. Keep body text inside `x 12..145` —
the red margin rule sits at x 9 and the tabs start at x 150.
