# Welcome Note — Integration Brief (v3)

## Overview

On a visitor's **first ever page load** (no prior `localStorage` history), a sasquatch hand reaches in from the left side of the cabin window — from **outside** — and places a folded note on the sill, then retreats. The note sits on the sill as a clickable item. Clicking it opens an HTML overlay showing a short welcome message that introduces the terminal's `help` and `whoami` commands.

Returning visitors (who have any `localStorage` key from the site) skip the delivery animation entirely and never see the note — it's a one-time onboarding moment.

---

## Assets Produced

| File | Size | Frames | ms/frame | Loop | Purpose |
|------|------|--------|----------|------|---------|
| `note_deliver_<time>.png` | 120×70 | 16 | 120 | no | Sasquatch arm reaches from left, lowers to place note on sill, retreats |
| `note_sill_<time>.png` | 25×17 | 1 | — | — | Static folded note sitting on sill |
| `note_open_<time>.png` | 26×34 | 7 | 110 | no | Note unfolding (proportional envelope→letter) |

`<time>` = `morning`, `day`, `afternoon`, `night` (4 variants each, 12 files total).

---

## Placement

### Delivery animation (`note_deliver`)
- **Frame size:** 120 × 70
- **Placement origin:** `x = 18, y = 86` (top-left of the frame on the 320×180 canvas)
- **⚠️ CRITICAL — Draw order:** Draw **BEFORE** `cabin_window` (behind it). The arm enters from the left edge of the window opening at mid-window height, lowers toward the sill to place the note, then retreats. The opaque window frame naturally occludes where the arm enters, making it look like the sasquatch is reaching in from outside the cabin. Suggested draw position: after `near_forest` / `treetops` but **before** `cabin_window`.
- **Anchor:** `[56, 54]` — the point within the frame where the note comes to rest on the sill

### Static note (`note_sill`)
- **Sprite size:** 25 × 17 (includes 3px shadow)
- **Anchor:** `[11, 13]` (bottom-center-ish)
- **Placement:** `x = 74, y = 148` (anchor point on canvas — left portion of sill, between left window edge and cig_pack)
- **Draw order:** **AFTER** `cabin_window`, same layer as other sill items (mug, folder, cig_pack). Draw BEFORE the mug and folder so it sits behind them visually.
- **Clickable:** Yes — this is an interactive sill item

### Note open (`note_open`)
- **Frame size:** 26 × 34
- **Anchor:** `[13, 30]` (bottom-center)
- **Placement:** Same position as `note_sill` — replaces the static note while playing
- **Draw order:** Same as `note_sill`

---

## Draw Order Summary

This is the critical change from v2. The delivery animation must be split from the sill note in the draw stack:

```
bg
tree_snow_far
sky elements (clouds, stars, moon)
waterfall
sasquatch_peek
near_forest
tree_snow_near
treetops
bird

>>> note_deliver <<<          ← ARM: drawn BEFORE window frame
                                 (frame covers the arm's entry point)

cabin_window                  ← Window frame goes ON TOP of the arm

>>> note_sill / note_open <<< ← NOTE: drawn AFTER window frame
                                 (sits visually on the sill)
cig_pack, folder, mug
smoke overlays
weather, wind
pop-ups
```

The arm is drawn behind the window frame so it appears to reach in from outside. The note (once released and sitting on the sill) is drawn after the window frame so it sits on top of the sill surface.

---

## Sequence of Events

### First visit (no localStorage):

```
1. Page loads normally (bg, window, scene animations start)
2. Wait 2-3 seconds for the scene to settle
3. Play `note_deliver_<time>` once at (18, 86)
   - Arm enters from left side of window at mid-height (clearly visible)
   - Window frame covers the entry point (arm appears to come from outside)
   - Arm lowers toward the sill carrying the note
   - Fingers open at sill level, releasing note
   - Arm pulls back up and retreats to the left, disappearing behind the frame
4. When animation ends (frame 15), hide `note_deliver`
5. Show `note_sill_<time>` at its placement position (ON TOP of cabin_window)
6. The note now sits on the sill as a clickable item
7. Set localStorage key: `cabin_note_delivered = true`
```

### Clicking the note:

```
1. (Optional) Play `note_open_<time>` at note position — the note unfolds
2. Show an HTML overlay with the welcome message (see "Note Content" below)
3. Hide `note_sill` while the overlay is open
4. When the user closes the overlay (click X, click outside, or press Escape):
   - Hide the overlay
   - Remove the note from the sill permanently
   - Set localStorage key: `cabin_note_read = true`
```

### Returning visits:
- If `cabin_note_delivered` exists but `cabin_note_read` does not: show `note_sill` on the sill immediately (skip delivery animation). User can still click to read it.
- If `cabin_note_read` exists: do nothing. No note, no animation.

---

## Note Content (HTML Overlay)

The overlay should look like a small piece of paper/parchment floating above the scene. Style it to match the pixel-art aesthetic.

### Suggested overlay styling:
```css
.welcome-note {
    position: absolute;
    /* Center it over the window area */
    left: 50%;
    top: 40%;
    transform: translate(-50%, -50%);
    /* Scale with the canvas */
    width: 60%;
    max-width: 280px;
    padding: 16px 20px;
    /* Paper look */
    background: #f5efdf;
    border: 2px solid #a89878;
    box-shadow: 2px 3px 0px rgba(0,0,0,0.25);
    /* Pixel font */
    font-family: monospace;
    font-size: 11px;
    line-height: 1.5;
    color: #3a3028;
    image-rendering: pixelated;
    cursor: default;
    z-index: 100;
}
.welcome-note .close-btn {
    position: absolute;
    top: 4px;
    right: 8px;
    cursor: pointer;
    font-size: 14px;
    color: #8a7a68;
}
.welcome-note .close-btn:hover {
    color: #3a3028;
}
```

### Note text:

```
Hey stranger,

Welcome to the cabin. Looks like you
found your way here.

If you're lost, type "help" in the
terminal below — it'll show you around.

And if you're curious who lives here...
try "whoami".

    — S.
```

The `"help"` and `"whoami"` should be styled as inline code (e.g., `<code>help</code>`) to make them visually distinct and hint that they're commands. Clicking on either word could optionally auto-type that command into the terminal.

The signature `— S.` is intentionally mysterious (sasquatch).

---

## Night mode

When the overlay appears at night, use darker paper colors:
```css
/* Night variant */
.welcome-note.night {
    background: #2a2830;
    border-color: #4a4660;
    color: #b0aab8;
}
.welcome-note.night code {
    color: #90c8a0;
    background: #1e1c24;
}
```

---

## Hover / cursor

The `note_sill` sprite should show a pointer cursor on hover to indicate it's clickable. Optionally, apply a subtle brightness increase on hover (CSS filter or swap to a slightly brighter sprite).

---

## Integration with existing sill items

The note occupies the LEFT side of the sill. Existing sill items and their positions:
- **cig_pack:** x=101, y=148
- **folder:** x=160, y=149
- **mug:** x=218, y=146

The note at x=74 sits to the LEFT of the cigarette pack with comfortable spacing. It does not overlap any existing item.

Once the note is read and removed, that sill space is simply empty — no replacement item appears.

---

## Edge cases

1. **User clears localStorage:** The note delivery replays on next visit. This is fine — it's a nice moment.
2. **Time-of-day changes while note is on sill:** Swap `note_sill_<time>` like every other time-of-day asset.
3. **Time changes during delivery animation:** Let the current animation finish with its starting time-of-day sprites, then show `note_sill_<current_time>`.
4. **User clicks note during delivery:** Ignore clicks until the delivery animation finishes and the static note appears.
5. **Terminal is already focused:** The note overlay should appear above the terminal. If `help` or `whoami` is clicked in the note, it should focus the terminal and type the command.

---

## Manifest additions

Add to `animations`:

```json
"note_deliver": {
    "files": [
        "note_deliver_morning.png",
        "note_deliver_day.png",
        "note_deliver_afternoon.png",
        "note_deliver_night.png"
    ],
    "frame_w": 120,
    "frame_h": 70,
    "frames": 16,
    "ms_per_frame": 120,
    "loop": false,
    "anchor": [56, 54],
    "placement": { "x": 18, "y": 86 },
    "draw_layer": "before_cabin_window",
    "note": "First-visit only. 16 frames. Sasquatch arm enters from the LEFT at mid-window height, lowers to the sill to place the note, then retreats. MUST be drawn BEFORE cabin_window so the window frame naturally occludes the arm's entry point. The note (once placed on the sill) is a separate sprite drawn AFTER cabin_window."
},
"note_sill": {
    "files": [
        "note_sill_morning.png",
        "note_sill_day.png",
        "note_sill_afternoon.png",
        "note_sill_night.png"
    ],
    "frame_w": 25,
    "frame_h": 17,
    "frames": 1,
    "ms_per_frame": 0,
    "loop": false,
    "anchor": [11, 13],
    "placement": { "x": 74, "y": 148, "region": "sill band" },
    "draw_layer": "after_cabin_window",
    "note": "Static folded note on the sill. Clickable — opens the welcome overlay. Shown after note_deliver finishes (first visit) or immediately (return visit, note unread). Removed permanently after the user reads it. Draw AFTER cabin_window (on top of sill)."
},
"note_open": {
    "files": [
        "note_open_morning.png",
        "note_open_day.png",
        "note_open_afternoon.png",
        "note_open_night.png"
    ],
    "frame_w": 26,
    "frame_h": 34,
    "frames": 7,
    "ms_per_frame": 110,
    "loop": false,
    "anchor": [13, 30],
    "placement": { "x": 74, "y": 148, "region": "sill band" },
    "draw_layer": "after_cabin_window",
    "note": "Note unfolding before the HTML overlay appears. Replaces note_sill while playing. Draw AFTER cabin_window."
}
```

Add to `sequences`:

```json
"welcome_note": {
    "trigger": "first_visit",
    "delay_ms": 2500,
    "steps": [
        { "play": "note_deliver" },
        { "show": "note_sill", "clickable": true }
    ],
    "on_click": [
        { "play": "note_open" },
        { "show": "welcome_overlay" },
        { "hide": "note_sill" }
    ],
    "on_close": [
        { "hide": "welcome_overlay" },
        { "remove": "note_sill" },
        { "set": "cabin_note_read" }
    ],
    "note": "The whole sequence only runs when localStorage has no cabin history. See brief for full logic."
}
```
