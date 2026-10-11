# Brief: pixel art animations for the cabin window website

## What this is for

I'm building a personal website whose whole screen is one pixel art scene: the view from inside a log cabin, looking out of an oak window at mountains, a pine forest, and a waterfall. Things happen in the scene on a timer or on command (a bird flies past, a sasquatch runs out of the woods, the weather changes), and a terminal command line sits at the bottom of the page for triggering them. The site is plain HTML, CSS, and JavaScript drawing to a `<canvas>`.

The static art is finished. Your job is to produce the animations as sprite sheets that my JavaScript can play. I will write the site code and may touch up your art by hand afterwards, so what I need from you is clean, consistent, well-documented assets, not a finished website.

You are drawing pixel art by writing code (for example Python with Pillow) that places pixels, then looking at the result and correcting it. Expect to iterate: render, enlarge, look, fix. A sprite that is technically correct but reads badly at small size is not done.

## Files attached with this brief

- `cabin_window.png`: the window frame, 320×180, transparent where the view shows through. It is always drawn on top of everything else.
- `bg_morning.png`, `bg_day.png`, `bg_afternoon.png`, `bg_night.png`: the outdoor scene, 320×180 each. They are the same scene pixel for pixel, with only the colours changed.
- `wind_gust.png`, `wind_streak.png`: wind animations that already exist (details in section 4).
- `bg.py`: the script that generated the backgrounds. You don't have to run it, but it is the exact source of every shape and colour in the scene, which helps when an animation has to line up with existing pixels.

If any of these are missing, stop and ask for them before drawing anything that must align with the scene (waterfall, stars, treetops, masks).

## The scene you are drawing into

Everything is authored at a native resolution of **320×180** and scaled up by whole numbers in the browser with smoothing off. Coordinates below are in native pixels, origin top-left, inclusive.

| Thing | Where |
|---|---|
| See-through window opening | x 40–279, y 24–130 (240×107) |
| Window sill top surface (items sit here) | x 42–277, y 132–149 |
| Sky | from the top down to the mountain and tree line; baked-in night stars are all above y 92 |
| Mountain peaks | highest at about (100, 50) and (205, 44) |
| Far forest ridge | tree tops around y 92–102 across the full width |
| Waterfall | x 157–163, y 99–123, with a rock cliff around it at x 134–186 |
| Mist at the base of the falls | centred near (160, 123), about 21 wide and 8 tall |
| Pool / lake surface | y 124 and below, mostly hidden behind the near trees |
| Near forest (darker, in front) | rises from about y 123 near the centre to about y 100 at the left and right edges of the opening |

Only the opening is visible on the site, so anything outside x 40–279, y 24–130 is hidden behind wood. Keep the action inside it.

Two facts about the art that should guide your choices:

- **Light comes from the upper left.** Mountains and trees are lit on their left sides and shaded on their right. Shade sprites the same way.
- **The viewer looks slightly downward.** The sill is drawn as if seen from a little above. Anything sitting on the sill must show its top face: for an object N pixels wide, the top is an ellipse or squashed shape roughly a third to half of N tall, with the front face below it. An object drawn flat side-on will look pasted on.

## Colours

The backgrounds use one small palette per time of day. Build sprites from these colours, plus a few new ones where a subject needs them (a red bird, a candle flame, a mug glaze). Each new colour needs a version for all four times of day that sits naturally beside the existing ones. Avoid pure black and avoid gradients; outlines are a dark colour from the palette, not `#000`.

| Role | Morning | Day | Afternoon | Night |
|---|---|---|---|---|
| Sky, top → horizon (6 bands) | 5C60A0, 8C74AC, C488A8, ECA094, FABE8C, FEDAA0 | 3A78C8, 4E8ED6, 68A4E2, 86BAEC, A8D0F2, C8E2F6 | 4680C4, 6898CC, 96B2CE, C8C8BE, ECD4A0, FAD682 | 080C22, 0C122E, 101A3C, 16224A, 1C2C58, 243866 |
| Far mountains lit / shade | CEA0AA / AA88A6 | 96B0D0 / 809CC2 | C4B4AA / A09CB0 | 283A64 / 203058 |
| Main mountains lit / shade | BE8C8C / 70608A | 7886A0 / 566282 | B0967C / 666480 | 303E64 / 1A2446 |
| Snow lit / shade | FFE2CE / BEAAC8 | F4F8FC / BCCEE6 | FFF0CE / C4BECE | 96ACD6 / 54689C |
| Far forest base / tree lit / tree shade | 3C5458 / 60745C / 2E4450 | 2C6048 / 407C54 / 225040 | 345C3E / 688446 / 264A3C | 102434 / 1A3440 / 0C1C2C |
| Rock lit / shade / crack | B08A7C / 705C6C / 544458 | 8C847C / 625C60 / 4A444C | B09674 / 706260 / 504448 | 3A425C / 242A42 / 181C30 |
| Waterfall bright / mid / mist | FFF4E8 / DCC4D2 / F8DED6 | FAFCFF / B0D8F0 / D6EAF6 | FFFAEC / CED6DC / F4ECD6 | BED2F0 / 6E8CC4 / 829CCE |
| Water base / highlight / dark | 9682A0 / FAC4A0 / 686490 | 3E80B0 / 7EB8D8 / 2C6496 | 5482A0 / ECD6A0 / 386288 | 142850 / 4664A0 / 0E1C3C |
| Near forest base / tree lit / tree shade / trunk | 1E2E38 / 3A4A42 / 16222E / 281E22 | 163C2C / 285C38 / 102E26 / 302218 | 1A3828 / 3E5C30 / 122A24 / 302218 | 08121C / 0E2028 / 060C16 / 0A0A10 |
| Night stars bright / dim | n/a | n/a | n/a | E6ECFF / 788CC4 |

The cabin wood does not change with time of day: outline 26160C, shade 54341A, mid 84562A, light A8723A, highlight CC9654.

## Conventions for every asset

These exist so my code can treat every animation the same way.

- **Format:** PNG with transparency. One animation per file, frames laid left to right in a single row, all frames the same size, no padding between them.
- **Pixels:** hard edges only. No anti-aliasing, no blur, no scaling inside the file. Pixels are either fully opaque or fully transparent, except where this brief says otherwise (wind, mist, glow, rain).
- **Direction:** characters and birds face and move **right**. I will mirror them in code for the other direction.
- **Loops:** the last frame must lead back into the first with no visible jump. Check this by viewing the loop, not by assuming.
- **Naming:** `<name>_<time>.png` when the asset has a version per time of day (`bird_flap_day.png`), plain `<name>.png` when one version serves all four.
- **Manifest:** write `manifest.json` listing, for every animation: file names, frame width and height, frame count, milliseconds per frame, whether it loops, the anchor point inside the frame (for example the bird's centre, or the bottom-centre of something standing on the sill), and where it belongs in the scene (a fixed position, a path, or a region). Add a one-line note on how it is meant to be used.
- **Previews:** for each animation, an animated GIF showing it in place: composited over the matching background, with `cabin_window.png` on top, scaled 3× or 4× with nearest-neighbour. These are how I judge the work, so make them representative.

## What to make

### 1. Small looping sprites

**Bird flap.** A small bird seen from the side at a distance, 3–4 frames, about 100 ms per frame. Around 10–12 pixels wingspan in a frame of about 16×12. The wing positions should read clearly as up, level, down; at this size the silhouette is the whole drawing. It will be moved across the sky by code, so draw the flap in place. A second, smaller silhouette (5–6 pixels, 2 frames) for far-off birds would be welcome.

**Sasquatch run cycle.** A tall, shaggy, long-armed figure running in profile, 6–8 frames, about 90 ms per frame. It appears among the near trees, which are 9–16 pixels tall, so make it about 16–18 pixels tall in a frame of about 24×24 so it reads as large but distant. Keep the feet on a constant ground line so it doesn't bob unnaturally when the code slides it sideways, and give it the classic swinging-arm stride. This is the hardest asset in the brief; spend the most iteration here, and say plainly in your report if it still looks stiff.

**Flickering candle.** Sits on the window sill, so it follows the looking-down rule: a short candle with its top face visible, a flame of 4–6 frames at about 120 ms, flickering irregularly instead of pulsing evenly. Include a soft glow as a separate sheet (`candle_glow.png`, partial transparency allowed) so I can show it only at night and in the morning.

**Steaming mug.** Also on the sill, also seen from slightly above: the rim is an ellipse with the dark drink visible inside. The mug is static; the steam is a loop of about 6 frames at 150 ms, rising, drifting, and thinning out. Steam may use partial transparency.

For both sill items, the anchor is the bottom-centre of the object's base, and the base should land anywhere in the sill band (y 132–149) and look right.

### 2. Scene effects

**Flowing waterfall.** An overlay that replaces the falls region with moving water. The existing falls are vertical streaks of the bright and mid waterfall colours that repeat every 6 pixels down each column, so scrolling the pattern down 1 pixel per frame gives a seamless 6-frame loop. Animate the mist at the base (puffing and dissolving) and a few glints on the pool as well. Deliver it as a patch with its top-left position in the manifest, sized to cover only the falls, mist, and pool, and make sure it never draws over the trees in front.

**Twinkling stars.** Night only. `bg_night.png` already has static stars painted in using the two star colours in the palette table; find them by colour. Make an overlay loop in which a subset brighten, dim, or briefly vanish, on staggered timing so they don't blink in unison. Slow: about 4 frames at 400 ms or more.

**Drifting clouds.** Three or four cloud shapes of different sizes (roughly 20×8 up to 56×18), flat-bottomed and lumpy on top, two or three tones each. They are static images that my code slides across the sky, so no frames are needed. They need all four palette versions, and the night ones should be dim and bluish.

**Rain and snow.** Each is a tile that repeats seamlessly in both directions (64×64 is a good size) and loops in time. Rain: thin diagonal streaks, 4 frames, fast. Snow: scattered single and double pixels drifting down with a little sideways wobble, about 8 frames, slow. Partial transparency is fine for rain. They should be visible over both sky and forest at every time of day; adjust the tint per time of day if needed.

**Swaying treetops.** The tips of the near-forest trees lean a pixel one way and back, 4 frames at about 250 ms. Deliver it as a full-width overlay containing only the pixels that change, aligned to the existing trees. Neighbouring trees should not all move in the same frame, so it reads as a breeze passing through. Subtle is right here: if the forest looks like it's vibrating, it's too much.

**Two masks, needed to make the above usable.** The backgrounds are single flattened images, so nothing can pass behind anything without help. Derive these from the background by colour and deliver them at 320×180:

- `sky_mask.png`: opaque where the pixel is sky (the six sky colours, or a star), transparent elsewhere. Lets clouds, birds, and the sun I'm adding later pass behind the mountains.
- `near_forest_<time>.png`: only the near-forest pixels, in their real colours, on transparency. Drawn on top of the sasquatch, it lets him emerge from behind the trees.

### 3. Palette variants

Every asset above that sits in the outdoor light needs four versions, matched to morning, day, afternoon, and night: bird, sasquatch, clouds, waterfall, treetops, near-forest layer, rain, and snow. The candle and mug are indoors on the sill: make one base version, plus a darker night version of each.

Do this by recolouring, not redrawing. Author each sprite once in the day palette using a fixed, small set of colours, then produce the other three by swapping each colour for its counterpart. The four versions of an animation must be identical in shape, frame for frame, so I can cross-fade between times of day. For colours that aren't in the table above, choose counterparts that follow the same shift the scenery makes: warm and pink-violet in the morning, golden in the afternoon, dark desaturated blue at night.

### 4. Wind animations (already made; integrate them)

These exist and should not be redrawn:

- `wind_gust.png`: 14 frames of 64×24. A white line sweeps in, curls into a small loop, and sweeps out, fading at the tail.
- `wind_streak.png`: 10 frames of 64×24. A shorter plain streak.

Both are meant to play once at about 80 ms per frame while the code slides them right 4–5 pixels per frame. They use white at three opacity levels.

Your tasks for these: add them to `manifest.json`; make tinted versions for morning and night, where pure white is too harsh (the snow colours in the palette table are a good guide); and include them in a preview alongside the treetop sway, since the two will usually play together.

## How to work

Begin by loading the backgrounds and confirming the coordinates in this brief against the actual pixels. If something here disagrees with the files, trust the files and tell me.

Then build in this order, because each step is cheaper to correct than the next: the two masks; the waterfall and stars (they align to existing pixels and prove your pipeline); the bird; the sill items; clouds, rain, snow, and treetops; the sasquatch; and finally the palette variants and wind integration.

After each asset, render a contact sheet of its frames enlarged at least 6×, and a GIF in the scene, and look at them before moving on. Things to check each time: the silhouette reads at native size; the loop has no jump; nothing strays outside the window opening or over the foreground; only intended colours are present; and all four palette versions have identical shapes.

## What to send back

- All sprite sheets, masks, and layers, in one folder.
- `manifest.json`.
- The preview GIFs and contact sheets.
- The scripts that generated everything, so the art can be regenerated or adjusted.
- A short report: what you made, any numbers in this brief you found to be wrong, and an honest note on each asset saying whether you consider it finished or a rough base that needs hand polishing. Lead with anything I need to decide or fix.
