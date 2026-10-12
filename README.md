# Cabin

My portfolio website for software engineering and computer science! There are a lot of secrets, so try to find all of them!

## Folder layout

```
index.html            page shell: the stage (canvas) and the terminal
style.css             layout, crisp scaling, terminal colours
anim/                 the art: one folder per scene element, plus manifest.json (source of truth)
  scene/              background, near forest, window frame, sky mask (the static layers)
  waterfall/ stars/ clouds/ rain/ snow/ treetops/ birds/ sasquatch/ mug/ wind/
  tree_snow/          snow settling on the trees in four stages (weather_overlays in manifest.json), and its brief
  smoke/              the smoke pack with its own smoke_manifest.json (listed in config.assetPacks)
  folder/             the folder pack with its own folder_manifest.json
  board/              the achievement board and its pop-up: art, board_layout.json (every position), mockups, brief
  achievements/       achievement sprites, badges, sign, and achievements.json (THE LIST OF ACHIEVEMENTS)
    popup/            the folder pop-up art, popup_layout.json (positions, colours), notes, mockups
  previews/ scripts/  reference previews and the Python that generated the art
js/
  config.js           every tunable: event timers, speeds, fade, file names, clock hours
  main.js             boot: load art, build scene, wire terminal + timers, run the loop
  assets.js           loads manifest.json and images; picks the right <time> file
  sprite.js           plays one sprite sheet: which frame, draw at anchor, mirror
  display.js          whole-number scale (device pixels) that fills the screen, keeping the window in view
  renderer.js         draws the layer list; cross-fades between times of day
  timeofday.js        current time of day, following the clock in "auto"
  weather.js          current weather; spells of rain or snow now and then, on the scheduler
  scheduler.js        random min/max/chance timers that fire events
  terminal.js         one-line prompt, reply bubble, up/down history
  commands.js         the command table
  sill.js             what is on the window sill: one ordered list; hidden `ls`, `rm`, `touch` change it
  random.js           small random helpers
  sequence.js         plays a manifest "sequences" entry (play / loop times / while_looping)
  achievements.js     track(stat, value) and isUnlocked(id); one rule tests every achievement
  progress.js         saved progress; the only module that touches localStorage
  unlock-sign.js      the wooden sign that slides down when something is earned
  geometry.js         inRect / withinRadius for click tests
  sound.js            quiet ambient sound: play(name) for one-shots, loop(name), seamless looper
  pointer.js          mouse hover and click on scene elements, in art pixels
  outline.js          the black hover outline for clickable sill items
  folder-contents.js  what the folder shows when opened: connects it to the pop-up
  popup-frame.js      what every pop-up shares: backdrop, pixel scale, plain fallback, fade, Escape / click-outside
  folder-popup.js     the folder pop-up: folder art at pixel scale, HTML text over its regions, tabs
  board-popup.js      the achievement board pop-up: badge slots, selection, the note, progress
  folder-sections.js  turns content sections (text, items, bullets, tags, links) into HTML
  testmode.js         ?test: fixed state, tick stepping, reference demo
  scene/
    layers.js         THE DRAW ORDER: one line per element (and the sun slot)
    crossing.js       a sprite sliding across the opening (bird, far bird, wind use it)
    background.js  sky.js  stars.js  clouds.js  farbird.js  waterfall.js  pondbank.js
    sasquatch.js  nearforest.js  treesnow.js  treetops.js  bird.js  precipitation.js
    wind.js  windowframe.js  mug.js
    folder.js         `whoami`: the folder on the sill; click to open / close
    board.js          the achievement board on the right-hand log: a pin per achievement; click to open
    aurora.js  shootingstars.js  rainbow.js  deer.js  trophy.js   achievement rewards
    sparkles.js       one-shot twinkles (bird trail, clicked stars, trophy)
    cigarette.js      hidden `cig` easter egg
sounds/               waterfall.mp3 (loops), bird_flap.wav, wind.wav
content/
  folder_content.json EVERY WORD IN THE FOLDER POP-UP: card, stamp, sticky note, each tab
Noah_Misukonis_2026_Resume.pdf   linked from the pop-up (sticky note and Contact tab)
tests/                pixel comparison and behaviour checks (not needed by the site)
```

Every scene element has the same shape:

```js
{ update(dtMs) {...}, draw(ctx, time) {...}, events: { name: (options) => started } }
```

`update` and `events` are optional. `time` is morning/day/afternoon/night; during
a cross-fade the whole stack is drawn once per time, so `draw` must only use it
to pick images.

## Run it locally

ES modules don't load from `file://`, so serve the folder:

```
python -m http.server 8000
```

and open http://localhost:8000. For GitHub Pages, push the folder as-is.

## Add a creature or event

1. Write `js/scene/fox.js` exporting `createFox(assets)` that returns
   `{ update, draw, events: { fox: (options) => true } }`. Take positions and
   sizes from `assets.animation('fox').info` (the manifest), tunables from `config`.
2. Add one line, `createFox(assets),` to `js/scene/layers.js` where it belongs in the draw order.
3. Put it on a timer: add `fox: { minWaitSec, maxWaitSec, chance }` to
   `config.events`. Creatures and wind only ever come from these timers; they
   are deliberately not terminal commands.
4. If it must never be out at the same time as another visitor, return
   `running: { fox: () => boolean }` too and add `skipWhile: ['sasquatch']` to
   its timer (the deer and the sasquatch do this).

The sun goes in the marked **SUN SLOT** at the top of the sky group in
`layers.js`, which clips it to the sky so it sets behind the mountains.

To make an element clickable, give it
`pointer: { contains(x, y), setHovered(on), click() }` (art pixels); see
`js/scene/cigarette.js`. A command with `hidden: true` works but is left out of `help`.

## Add a command

Add one entry to `commands` in `js/commands.js`:

```js
hello: {
  usage: 'hello',
  about: 'say hello',
  run(args, app) { app.print('hello from the cabin.'); },
},
```

`args` are the words after the command name. `app` has `events`,
`timeOfDay`, `weather`, `print` and `clearOutput`. Everything a command prints
appears together in the speech bubble above the prompt, which the next command
replaces and `clear` removes. `help` lists the new command automatically.

## Achievements

`anim/achievements/achievements.json` lists them: each has a `stat` and a
`goal`. The site reports what happens with `track(stat, value)` (a number adds
to a counter, a string adds to a set) and asks `isUnlocked(id)` wherever a
reward is drawn. One rule in `js/achievements.js` (`isMet`) tests every goal:
a count, a set's size, a value a set must contain (`"night"`), or `"all"`.

To add a fourteenth: add an entry to the JSON (and a badge frame), call
`track('yourStat', ...)` where it happens, and draw the reward in the scene
element it changes, behind `isUnlocked('your_id')`. Tunables (yeti chance,
aurora chance, rainbow time, hit padding, sign timing) are in
`config.achievements`.

Progress is saved under one key in localStorage (`config.achievements.storageKey`,
with a `storageVersion`: bump it to start everyone fresh). If storage is
unavailable it lasts for the visit.

"Use every command" (Power User) means every command `help` lists from the
start, except `reset`; the rule is written where the commands are, at the top
of `js/commands.js`.

For testing without grinding, add `?debug` to the URL; then
`debug unlock <id|all>`, `debug set <stat> <value>`, `debug event <name> key=value`
and `debug stats` work in the terminal. Without `?debug` the command doesn't exist.

## Sound

Files are in `sounds/`; volumes (in dB), the waterfall's loop region and the
wind's trim are in `config.sound`. A scene element calls `play('bird')` or
`loop('waterfall')` from `js/sound.js`; nothing else touches Web Audio.
Browsers only allow sound after the visitor clicks or presses a key, so the
waterfall starts then. Sound pauses in a hidden tab; `sound off` mutes it.
To add a sound: drop the file in `sounds/`, add an entry under
`config.sound.sounds`, and call `play('name')` where it happens.

## Tests

```
pip install playwright pillow numpy      # uses your installed Chrome
python tests/reference.py                # anim.py's compose() rebuilds the shipped art exactly
python tests/compare.py                  # site vs compose(), pixel for pixel
python tests/behaviour.py                # layout, crispness, commands, terminal, timers, console
python tests/achievements.py             # all 13 earned for real, rewards in place, persistence, edges
python tests/sound.py                    # seamless waterfall loop, which sounds play when, mute, console
```

Results land in `tests/results/`. Test mode on its own: open
`index.html?test&time=night&weather=snow`, then in the console
`cabin.test.advanceTo(30)` (each tick is 100 ms).
