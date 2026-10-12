# Terrarium — Direct Manipulation Plan

Replaces the WATER / TRIM / HARVEST buttons and the Seeds-tab Plant button with
tools you pick up and carry to the pot. This supersedes §3 (Pot tab buttons) and
the action half of §10 (terminal commands) of `terrarium_brief.md`; everything
else in that brief stands.

**Scope:** tools exist only inside the terrarium journal, and only on the Pot
tab. Nothing is draggable on the wall, on the sill, or on the other three tabs.

---

## 1. Why this shape

Three constraints drove the design:

**The canvas is 320×180.** The pot's hit area is about 48×40 native pixels.
Drag-only would be fiddly at that scale and worse on touch. Click-only would
throw away the tactility that makes picking up a watering can feel good. So the
same state machine serves both: press a tool to pick it up, and either drag onto
the pot or release and click the pot. One machine, two habits, no mode switch.

**Watering has to visibly do something.** A meter ticking up is not enough. The
soil bed now renders at three wetness levels (§4), so a thirsty pot *looks*
thirsty and pouring visibly darkens it. That change is already made.

**The rail replaces the buttons in place.** Tools hang where the buttons were,
at the bottom of the Pot tab, reading as a potting bench rather than a toolbar.
No new panel real estate is needed.

---

## 2. Interaction model

One state machine. It covers drag, click-to-equip, touch, and keyboard.

```
IDLE
  pointerdown on an enabled rail slot   -> HOLDING(tool), record (x,y)
  pointerdown anywhere else             -> IDLE

HOLDING(tool)
  pointermove                           -> held sprite tracks the pointer
                                           pot shows the glow while hovered
  pointerup over the pot                -> USING(tool)
  pointerup elsewhere, moved <= 3px     -> stay HOLDING   (click-to-equip)
  pointerup elsewhere, moved  > 3px     -> IDLE, tool returns to the rail
  pointerdown on the same slot          -> IDLE (put it back)
  Escape / tab change / popup close     -> IDLE

USING(tool)
  input locked, play the tool's animation (§5)
  on completion -> apply the state change, emit the status line, IDLE
```

The 3px threshold is the whole trick: a press-and-release that never moved is a
click, so the tool stays in hand and the next click on the pot uses it. A press
that *did* move is a drag, so releasing off-target puts the tool back.

### Hit areas (canvas coordinates; panel origin is 78, 28)

| Target | Rect |
|---|---|
| Pot (drop target) | `x 90..138, y 82..122` — the pot sprite at panel `(12, 54)`, 48×40 |
| Rail slot *i* | `x 92 + railX[i] .. +16, y 130..146` — panel `(railX[i], 102)`, 16×16 |

Text baselines on this tab follow the brief's baseline grid (§3a): `y % 10` must
be in `{7, 8, 9, 0, 1}` or a ruled line strikes through the words. The hint at
`(66, 88)` and the button labels at `y = 110` both satisfy it.

`railX = [14, 40, 66, 92]`, assigned left to right to whichever tools are
currently enabled — slots are not reserved per tool, so the rail never shows
gaps.

---

## 3. The rail

Tools appear only when they would do something. This is the whole tutorial: you
never see a tool you cannot use.

| Tool | Row in sheet | Shown when | Does |
|---|---|---|---|
| Watering can | 0 | pot is planted and alive | hydration += 0.25 |
| Shears | 1 | growth >= 0.35 and not ready | trim: clears dead cells, growth -= 0.05, health = 1.0 |
| Basket | 2 | growth >= 1.0 | harvest: 1–2 seeds, mark species discovered, empty the pot |

So the rail reads: growing → can + shears. Ripe → can + shears + basket. At most
three at once. **When the pot is empty the rail is replaced entirely by the seed
tray** (§6) — there is no planting tool.

A slot uses the existing `terrarium_slot_sm` frame — frame 0 at rest, frame 1 on
hover. While a tool is held, its slot renders empty, so the rail shows where the
thing in your hand came from.

A one-line hint sits at panel `(66, 88)`, under the growth meter, and names what
the held tool will do — `PICK UP A TOOL` at rest, `WATER THE SOIL` while
carrying the can. It lives in the readout column because the pot sprite occupies
`y 54..94` on the left; put the hint under the rail and it lands on the pot.

---

## 4. Assets

New, and already generated:

| File | Size | Layout |
|---|---|---|
| `terrarium_tools_<t>.png` | 48×48 | 3 rows (can, shears, basket) × 3 cols (idle, held, active), 16×16 |
| `terrarium_fx_<t>.png` | 48×48 | 3 rows (droplets, clippings, sparkle) × 3 frames, 16×16 |
| `terrarium_pot_glow_<t>.png` | 48×40 | mouth ellipse traced in warm outline; drawn over `pot_back` while a tool hovers |
| `terrarium_harvest_<t>.png` | 96×8 | 12 species tokens, 8×8 — what you actually picked (§5) |

Changed:

| File | Was | Now |
|---|---|---|
| `terrarium_pot_back_<t>.png` | 48×40 | **48×120** — three 48×40 panes stacked: dry (y 0), moist (y 40), wet (y 80) |

Pick the pane by hydration: `< 0.33` dry, `< 0.66` moist, else wet. Everything
else about the pot is unchanged, including the back/plant/front draw order.

```js
const WET = hydration < 0.33 ? 0 : hydration < 0.66 ? 1 : 2;
ctx.drawImage(potBack, 0, WET*40, 48, 40, potX, potY, 48, 40);
if (hoveringWithTool) ctx.drawImage(potGlow, potX, potY);
drawPlant(ctx, potX, potY);
ctx.drawImage(potFront, potX, potY);
```

The `idle` and `held` tool frames differ only slightly (the can lifts 1px) —
held is drawn centred on the pointer rather than in a slot, and that relocation
is most of the feedback.

**The can's pouring frame is the idle can rotated 90° counter-clockwise**, not a
separate drawing. Every other angle was tried and a 16px sprite does not survive
arbitrary rotation — only a right angle is lossless, and it keeps the pouring
can recognisably the same object as the one on the rail. Tipped that way the
body sits right, the handle loop left, and the spout runs down-left with its tip
at local `(5, 14)`. `tools.py` derives it at build time, so editing the idle can
updates both frames.

Place the pouring can so its spout tip clears the plant: panel `(48, 30)` puts
the tip at `(53, 44)`, above the right of the mouth and clear of the bloom.
Centre it over the plant and the can covers the flower you are watering.

---

## 5. Per-tool flow

Each use is a short locked animation. Keep them under ~700ms; this is a cozy
game, not a cutscene, and the player may be doing this several times a session.

### Watering can — ~600ms
1. Can swaps to `active` (tilted, spout down) positioned above and left of the
   pot mouth, around panel `(18, 30)`.
2. `fx` row 0 plays frames 0→2 over the soil, ~120ms each.
3. On frame 2, raise hydration and swap `pot_back` to the new wetness pane. The
   soil darkening and the meter fill should land on the same frame — split them
   and the cause/effect reads as two unrelated events.
4. Can returns to the rail. Status: `WATERED`.

Debounce 500ms. Watering at full reads `SATURATED!` and changes nothing.

### Shears — ~500ms
1. Shears swap to `active` (blades open) beside the plant's upper third.
2. `fx` row 1 (clippings) falls past the pot, frames 0→2.
3. Apply trim. Status: `TRIMMED`.

### Basket — ~1100ms, and it holds the real thing

The basket does not fill with generic seeds. The bloom **detaches from the stem,
falls, and lands in the basket as that species' own token** — harvest a bluebell
and there is a bluebell in the basket.

This costs one 96×8 sheet, not twelve basket sprites. `terrarium_harvest_<t>.png`
holds a 8×8 token per species, indexed the same as every other species sheet
(row order from §4 of the brief). The basket's `active` frame is a deliberately
**empty** basket, and the token composites in at

```js
const BASKET_TOKEN_ANCHOR = [4, 1];   // relative to the 16×16 basket tile

// ONCE LANDED, DRAW THE TOKEN FIRST AND THE BASKET OVER IT:
ctx.drawImage(token,  bx + 4, by - 1);
ctx.drawImage(basket, bx,     by);
```

The order matters more than the anchor. The basket has no hollow interior —
its body is solid from the rim down — so containment is sold entirely by
occlusion: the flower head clears the rim while the stem disappears behind the
weave. Composite the token last and it sits on the basket like a sticker
instead of in it.

While the token is still *falling* it draws in front, since it is above the
basket anyway; it swaps behind on the frame it lands.

The `+1` lands the head in the basket's **opening** — the band between the
handle (top edge on row 2, sides on rows 3–5) and the rim (rows 6–8). Every
token is drawn to the same contract to make that single anchor work:

```
token rows 0..4   the head        (what identifies the species)
token rows 5..7   the stem        (hidden behind the rim)
```

The two bell species originally sat two rows lower than the rest and had to be
raised to match; the moss cushion likewise. Without that contract each species
would need its own anchor.

So one basket sprite serves all twelve species, and the motion is pure code.

| Frame | ms | What |
|---|---|---|
| 0 | 500 | Basket settles under the bloom. `fx` sparkle frame 0 shimmers on the ripe flower. Status `READY TO PICK` |
| 1 | 130 | Bloom sprite is removed from the stem; the token appears at the bloom's centre and begins to fall |
| 2 | 130 | Token continues down — lerp from the bloom centre to `basket + ANCHOR` |
| 3 | 160 | Token lands and swaps BEHIND the basket. `fx` sparkle frame 1 at the mouth. Basket swaps to `active` |
| 4 | 400 | `fx` sparkle frame 2. Status flips to `+2 BLUEBELL SEEDS` |
| 5 | 700 | Basket settles 1px, token resting inside. Pot is now empty |

The stem stays in the pot through the fall and only clears on completion — the
plant visibly loses its flower before the pot resets, which is what makes it
read as picking rather than deleting.

Non-flowering species (moss, fern, clover, ivy) have tokens too: a cutting in
the species' own foliage style — a moss cushion, a fern frond, a clover trefoil,
an ivy leaf pair. Without that they all came back as the same anonymous green
sprig.

### Planting — see §6

---

## 6. Planting — the seed tray

There is no seed packet and no popover. When the pot is empty, the rail strip
*becomes* your seed inventory: the seeds you own, laid out and pickable in one
click.

```
  EMPTY POT                        . . . . . . . . . . . . . .
  NOTHING PLANTED
  WATER   [          ]
  GROWTH  [          ]
  PICK A SEED
  ──────────────────────────────────────────────────────
  [moss] [fern] [clover] [daisy] [mush]              <- the tray
```

### Geometry

Same strip as the rail, so the two never coexist and the layout never shifts.

| | |
|---|---|
| Slots | `x = 14 + i * 22`, `y = 102`, 16×16 — so `14, 36, 58, 80, 102, 124` |
| Frame | `terrarium_slot_sm` frame 0, frame 1 on hover or focus |
| Seed sprite | `terrarium_seeds` row for the species, drawn at slot `+(4, 4)` |
| Count badge | at slot `+(12, 10)`, same place the Seeds tab puts it |

Only species with `count > 0` appear, in species-index order (§4 of the brief)
so the tray and the Seeds tab always agree. Owning more than six distinct
species is late-game; when it happens the sixth slot becomes a `>` pager showing
five seeds at a time.

### Flow

1. Click a seed in the tray → `HOLDING(seed)`. The held sprite is that 8×8 seed
   centred on the pointer; the slot it came from renders empty.
2. Drop it on the pot → the seed drops into the soil, `fx` row 2 plays once at
   small scale, the plant renders at its `seed` tile and the pot takes the
   species' genome from that seed.
3. Status: `PLANTED MOSS`. The tray is replaced by the tool rail on the next
   frame, since the pot is no longer empty.
4. Release anywhere else → the seed goes back to its slot.

### What this changes elsewhere

The **Seeds tab loses its Plant button**. It becomes a pure inventory and detail
view — name, rarity, blurb, counts — and planting happens only from the tray.
That removes the one place where an action lived on a different tab from its
target, which was the whole problem with the packet idea: a popover that
duplicated a grid already one tab away.

## 7. Feedback rules

- **Hover a rail slot** → slot frame 1. Nothing moves.
- **Hover the pot while holding** → `pot_glow` over `pot_back`. The pot is the
  only valid target, so this is the entire targeting system.
- **Invalid release** → tool returns to its slot. No error text; the hint line
  already says what the tool was for.
- **Disabled tool** → not rendered at all rather than greyed out. A rail of
  three live tools beats a rail of six where half are dead.
- **Status line** replaces the plant's status text for 2s, then reverts.

---

## 8. Keyboard and terminal

The GUI is now the primary path, but it must not be the only one.

**Keyboard.** Tab cycles rail slots → pot. Enter or Space on a slot picks the
tool up; Enter on the pot uses it; Escape drops it. Focus draws the same frame-1
slot used for hover. The held sprite parks over the focused target rather than
following a pointer.

**Terminal.** Keep `water`, `trim`, `harvest`, `plant <species>` working. They
are the accessible path and they cost nothing to retain. What changes is
framing: the journal is how the game is played, and the commands are a
shortcut — so `help` should lead with "click the pot" rather than listing them.

> One judgement call to confirm: the request said "instead of commands or
> buttons," which could mean retiring the commands outright. I have kept them
> because dropping them leaves no non-pointer path to play, and `terrarium
> status`, `seeds` and `codex` are read-only anyway. Say the word and the four
> action commands come out.

---

## 9. Edge cases

1. **Tab switched while holding** → drop the tool or seed, return it to its
   slot. Nothing is ever carried onto another tab.
2. **Journal closed while holding** → same. State resets on open.
3. **Plant dies while holding the basket** → basket disappears from the rail
   mid-hold; drop to IDLE and show `WITHERED`.
3b. **Last seed of a species is planted** → that slot leaves the tray; remaining
   slots close up rather than leaving a hole.
4. **Time of day changes mid-animation** → let the current animation finish on
   its starting sprites, then swap. Same rule the brief already uses elsewhere.
5. **Terminal command fires while holding a tool** → apply it, drop the tool,
   re-render. Do not try to animate a command.
6. **Rapid clicking the pot while holding** → `USING` locks input; ignore.
7. **Pointer leaves the canvas while dragging** → treat as an invalid release.
8. **Touch long-press** → no context menu; `touch-action: none` on the canvas.

---

## 10. Build order

Each phase is shippable on its own.

1. **Rail and state machine.** Render the rail, implement IDLE/HOLDING/USING,
   wire the can only. No animation yet — apply hydration on release. This proves
   the interaction before any art timing matters.
2. **Wetness + glow.** Swap `pot_back` panes by hydration, add the hover glow.
   The can now visibly works.
3. **Animations.** Add the three `fx` rows and the `active` tool frames.
4. **Shears and basket.** Same machine, two more rows; harvest wires into the
   existing seed/codex code.
5. **Seed tray.** Swap the rail for the tray when the pot is empty, and
   retire the Seeds-tab Plant button.
6. **Keyboard.** Tab order, Enter/Escape, focus rendering.

Phase 1 is the risky one — if the pick-up/carry feel is wrong at 320×180, it is
wrong before any art is involved, and that is the cheapest moment to find out.
