# Brief: build the cabin window website

## What this is

I have a finished set of pixel art for a personal website: the view from inside a log cabin, through an oak window, onto mountains, a pine forest, and a waterfall, with a steaming coffee cup on the sill. There are sprite sheets for everything that moves, a manifest describing them, and preview images showing exactly how the assembled scene should look.

Your job is to turn those assets into a working website in plain HTML, CSS, and JavaScript: the scene fills the screen and animates on its own, and a terminal command line at the bottom lets a visitor trigger things by typing.

Two things matter more than anything else, and the rest of this brief is organised around them:

1. **The code must be extremely modular and easy to follow.** I am a computer science student and I will be reading, extending, and maintaining this myself. I will add a moving sun, new creatures, and new commands later. Every one of those should be a small, obvious change in one place.
2. **The site must look exactly like the reference previews, and you must prove it does.** The art already exists and has been approved. Success is the browser showing the same picture, not a similar one.

No art needs drawing. If an asset looks wrong or is missing, tell me instead of redrawing or substituting it.

## What you are given

One folder, `anim/`, containing:

- **Static scene:** `bg_morning.png`, `bg_day.png`, `bg_afternoon.png`, `bg_night.png` (the outdoor view, identical shapes in four palettes) and `cabin_window.png` (the window frame, transparent where the view shows).
- **Layers and masks:** `sky_mask.png` (opaque where the background is sky) and `near_forest_<time>.png` (the front row of trees on transparency).
- **Animations:** waterfall, twinkling stars, four clouds, rain, snow, swaying treetops, a flapping bird, a far-off bird, a sasquatch peeking from the trees, a small sasquatch run, the coffee cup with steam, and two wind effects. Most come in four files, one per time of day.
- **`manifest.json`:** for every animation, its file names, frame size, frame count, milliseconds per frame, whether it loops, its anchor point, and where it goes in the scene. It also records the canvas size, the window opening, the sill area, and the draw order. Treat this file as the source of truth and read values from it at runtime; do not copy its numbers into the code.
- **`previews/`:** animated GIFs of the assembled scene for each time of day and for rain and snow, a still image of four scenes (`stills.png`), and a contact sheet of the sprites.
- **`scripts/`:** the Python that generated everything. `anim.py` contains a `compose()` function that builds a complete scene frame for a given time of day and tick. This is the reference renderer: it defines precisely what "correct" looks like.

Start by reading `manifest.json` and looking at the previews. If the manifest and this brief disagree, trust the manifest and tell me.

## The scene, in brief

- Everything is authored at **320×180** native pixels. The site scales that canvas up by the largest whole number that fits the browser window, centres it, and fills the rest with a dark colour. Scaling must stay crisp: no smoothing, no fractional scale factors, no blur on high-density screens.
- Layers are drawn back to front in the order the manifest lists: background, sky elements (stars, clouds, far birds) clipped by the sky mask so they pass behind the mountains, waterfall, sasquatch, near forest, treetops, bird, weather, wind, window frame, coffee cup.
- The sasquatch is drawn before the near forest, which is what makes him appear from behind the trees. He only ever appears at the spots listed in the manifest.
- Characters face right in the art. Flip them in code when they travel left.

## What to build

**Always running:** the waterfall, the treetop sway, the coffee steam, slowly drifting clouds, and, at night only, twinkling stars.

**Occasional events,** each triggered by a timer and also available as a command:

- A bird flaps across the view, sometimes left to right and sometimes right to left, at varying heights. A far-off bird occasionally crosses the sky.
- A wind gust or streak sweeps across.
- The sasquatch peeks from a randomly chosen spot. This should be rare.

Each event has a minimum wait, a maximum wait, and a chance of firing, all defined together in one clearly labelled configuration object so I can tune how often things happen without touching logic. Start with: bird every 20–60 seconds; wind every 40–120 seconds; sasquatch a 30% chance every 3–10 minutes.

**Time of day:** morning, day, afternoon, and night. Switching swaps every time-dependent asset together and cross-fades over a second or two. This works because the four versions of each asset are identical in shape. By default the site follows the visitor's local clock; a command can override it. Leave a clearly marked, empty place in the draw order between the background and the sky elements where I will later add a sun that moves across the sky. Do not build the sun.

**Weather:** clear, rain, or snow, drawn as a repeating tile over the view. Clear by default.

**Terminal:** a command line pinned to the bottom of the page, styled to suit the cabin (monospace, dark, warm tones from the wood palette), with a short scrolling history of output above the input. It keeps focus so a visitor can simply start typing, supports up and down arrows for previous commands, and never covers the scene: the canvas scales to the space above it. Commands to start with:

- `help`: list the commands
- `bird`, `wind`, `sasquatch`: trigger that event now
- `time morning|day|afternoon|night|auto`
- `weather rain|snow|clear`
- `clear`: clear the terminal output

An unknown command prints a friendly one-line hint. Commands and timers call the same functions, so there is one code path per event.

## How the code should be organised

This is a small static site with no framework, no build step, and no dependencies: native JavaScript modules, one stylesheet, one HTML file. It must work when the folder is served by any static host (GitHub Pages is the target).

Modularity is the main quality bar. Concretely:

- **One job per file.** Loading assets, playing a sprite sheet, drawing the layer stack, scheduling events, managing time of day, managing weather, and running the terminal are each their own module. No file should need to know how another one works inside, only what it exports.
- **Each scene element is self-contained.** The bird, the waterfall, the sasquatch, and so on each live in their own small file with the same shape: something like `update(dt)` and `draw(ctx)`. The main loop only walks a list of these in draw order.
- **Adding things is additive.** Adding a new creature should mean adding one file and one line that registers it. Adding a command should mean adding one entry to the command table. If either requires editing several files, the structure is wrong.
- **Configuration is separate from logic.** Timings, probabilities, speeds, and paths sit in one config file with plain names and units in the names or comments.
- **No magic numbers in logic.** Positions and sizes come from the manifest; tunables come from config.
- **Readable over clever.** Short functions, descriptive names, and a comment at the top of each file saying what it is for and what it exports. Comment the why, not the what. Avoid abstractions that only have one user.
- **A README** that explains the folder layout, how to run it locally, how to add an event, and how to add a command, each in a few lines.

Propose the file layout before writing code, in a short list with one line per file, and then follow it.

## Checking that it works and matches

Treat verification as part of the build, not a final step. I would rather receive fewer features that are proven correct than every feature unverified.

**Make the scene deterministic for testing.** Give the site a test mode (a URL parameter is fine) that fixes the time of day and weather, turns off random events, and advances animation by a tick number instead of the real clock. The reference renderer in `scripts/anim.py` works in ticks of 100 ms, so the two can be lined up frame for frame.

**Compare against the reference, pixel for pixel.** Using a headless browser, capture the canvas at native 320×180 in test mode and compare it with frames produced by `compose()` for the same time of day and tick. Do this for all four times of day, and for rain and snow, at several ticks each. The always-on layers (background, waterfall, treetops, near forest, stars, window, coffee cup) should match exactly; report the number of differing pixels for each comparison. Where the site intentionally differs from the reference (for example, the reference places clouds and the bird at fixed demo positions), make the test mode able to reproduce those positions, or exclude those layers from that comparison and say so.

**Look at it.** Take screenshots at a few browser sizes, including a phone-sized one, and view them. Check that the pixels are crisp, the scale is a whole number, the scene is centred, and the terminal is usable and not overlapping the scene.

**Exercise every behaviour.** Run each command and confirm its effect in a screenshot or by inspecting state. Confirm each scheduled event fires on its own by temporarily shortening its timer. Confirm time-of-day switching swaps every layer, with no asset left behind in the old palette. Confirm an unknown command, an empty command, and rapid repeated commands all behave sensibly. Confirm the browser console shows no errors or warnings and no asset fails to load.

**Check the loops.** The waterfall, treetops, steam, and stars should cycle with no visible jump, at the speeds in the manifest.

If something cannot be verified in your environment, say exactly what was not checked and why. Do not describe anything as working unless you ran it.

## Order of work

1. Read the manifest, view the previews, and confirm the assets are all present. Propose the file layout.
2. Canvas, crisp scaling, asset loading, and the static scene (background plus window). Verify against the reference before going further.
3. The always-on animations, added one at a time and compared against the reference after each.
4. Time of day and weather.
5. Events and the scheduler.
6. The terminal and commands.
7. Full verification pass, README, and report.

## What to send back

- The complete site folder, ready to upload to a static host.
- The test script and the comparison results.
- Screenshots of each time of day and each weather state as rendered by the site.
- A short report that leads with anything I need to decide or fix, then covers: what was built, the pixel-comparison results, anything that differs from the reference and why, and anything you could not verify.
