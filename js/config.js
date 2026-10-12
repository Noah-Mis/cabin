// config.js — every tunable in one place: timings, chances, speeds, paths.
// Positions and sprite sizes are NOT here; they come from anim/manifest.json.
// Exports: config (a plain object).

export const config = {
  // Where the art lives: each pack is a folder with its own manifest. The
  // first is the scene; the files below are in its folder.
  assetPacks: [
    { dir: 'anim/', manifest: 'manifest.json' },
    { dir: 'anim/smoke/', manifest: 'smoke_manifest.json' },
    { dir: 'anim/folder/', manifest: 'folder_manifest.json' },
    { dir: 'anim/note/', manifest: 'note_manifest.json' },
    { dir: 'anim/achievements/', manifest: 'achievements.json' },
    { dir: 'anim/terrarium/', manifest: 'terrarium_manifest.json' },
  ],
  // "<time>" is replaced by morning/day/afternoon/night. (The window frame's
  // files are listed in the manifest's "window" entry.)
  files: {
    background: 'scene/bg_<time>.png',
    nearForest: 'scene/near_forest_<time>.png',
    skyMask: 'scene/sky_mask.png',
  },

  times: ['morning', 'day', 'afternoon', 'night'],

  // Local hour (0-23) at which each time of day begins, for "time auto".
  timeOfDayStartHour: { morning: 5, day: 10, afternoon: 16, night: 20 },
  clockCheckIntervalSec: 30,
  crossFadeMs: 1500,

  // Every sprite sheet's ms_per_frame is multiplied by this: 1 plays at the
  // manifest's speed, 1.2 makes every animation 20% slower.
  animationSlowdown: 1.2,

  // The front trees sway once, then rest for a random time in this range.
  treetops: {
    restBetweenSwaysSec: [7, 15],
  },

  weathers: ['clear', 'rain', 'snow'],
  defaultWeather: 'clear',
  // Now and then a spell of rain or snow (the `weather` event below) that
  // clears by itself. The hidden `weather` command overrides it.
  weatherSpell: {
    lastsSec: [90, 240],          // how long it rains or snows
    snowShare: 0.35,              // the rest of the spells are rain
  },
  // Rain and snow start light and build up, and thin out before they clear
  // (js/scene/precipitation.js): rain a drop at a time, snow by fading.
  precipitation: {
    rampUpSec: 20,                // from light to full
    rampDownSec: 20,              // from full to gone
    lightShare: 0.15,             // how much shows at the very start (and end)
  },
  // Snow settling on the trees while it snows (js/scene/treesnow.js): it
  // fades in, builds up a stage at a time, and melts back off when it stops.
  // The stages themselves are in the manifest's weather_overlays.tree_snow.
  treeSnow: {
    fadeSec: 3,                   // fading in at the first stage, and out at the end
    stageUpSec: 30,               // continuous snow per stage after that
    stageDownSec: 20,             // melting, per stage, once it stops
  },

  // ── Occasional events ────────────────────────────────────────────────
  // Each event waits a random time between minWaitSec and maxWaitSec, then
  // fires with probability `chance` (0-1), then waits again. `skipWhile`
  // lists events whose visit, if still running, makes this one skip its turn.
  events: {
    bird:      { minWaitSec: 20,  maxWaitSec: 60,  chance: 1.0 },
    farbird:   { minWaitSec: 30,  maxWaitSec: 90,  chance: 1.0 },
    wind:      { minWaitSec: 40,  maxWaitSec: 120, chance: 1.0 },
    sasquatch: { minWaitSec: 180, maxWaitSec: 600, chance: 0.3, skipWhile: ['deer'] },   // they share the forest
    // Achievement rewards: these only do anything once earned (and, for
    // shooting stars, at night).
    shootingstar: { minWaitSec: 30, maxWaitSec: 90, chance: 1.0 },
    deer:      { minWaitSec: 120, maxWaitSec: 300, chance: 1.0, skipWhile: ['sasquatch'] },
    // A spell of weather; it only starts from a clear sky (see weatherSpell above).
    weather:   { minWaitSec: 120, maxWaitSec: 420, chance: 0.5 },
  },

  // ── Moving things ────────────────────────────────────────────────────
  bird: {
    speedPxPerSec: 50,          // manifest suggests 4-6 px per 100 ms frame
    flightHeightPx: [40, 80],   // range of y (anchor) values in the sky
    bobAmplitudePx: 4,
    bobRadPerSec: 3,
    maxAtOnce: 4,
  },
  farBird: {
    speedPxPerSec: 15,
    flightHeightPx: [32, 56],
    maxAtOnce: 3,
  },
  wind: {
    speedPxPerSec: 55,          // manifest: 4-5 px per 80 ms frame
    heightPx: [40, 110],        // top of the 64x24 frame; sky and treeline
    maxAtOnce: 4,
  },
  // Clouds drift right and wrap around the window opening.
  // Start positions are the same as the reference previews use.
  clouds: [
    { sprite: 'cloud_a', x: 52,  y: 30, speedPxPerSec: 5 },
    { sprite: 'cloud_c', x: 196, y: 40, speedPxPerSec: 3 },
    { sprite: 'cloud_b', x: 128, y: 60, speedPxPerSec: 4 },
    { sprite: 'cloud_d', x: 236, y: 70, speedPxPerSec: 2.5 },
  ],

  // Clickable sill items (the folder, the cigarette pack) get this outline on hover.
  hoverOutlineColour: '#000000',

  // A phone held sideways: a touch screen, wider than tall, and short. It
  // gets the desktop pop-ups (art, not the plain panel) and a prompt that
  // brings the keyboard up only when tapped. A desktop window (fine pointer)
  // never matches. style.css repeats this query.
  compactLandscape: {
    query: '(orientation: landscape) and (pointer: coarse) and (max-height: 500px)',
    minCssPxPerArtPx: 1.5,   // pop-ups keep their art down to this scale
  },

  // The pop-up that opens from the folder. Positions, sizes and most colours
  // are in the layout file; every word is in the content file.
  folderPopup: {
    artDir: 'anim/folder/popup/',
    layoutFile: 'anim/folder/popup/popup_layout.json',
    contentFile: 'content/folder_content.json',
    firstTab: 'about',
    // Colours the mockups use that the layout file doesn't list.
    linkColour: '#3C5A96',
    metaColour: '#8C7E74',
    // Below this many CSS pixels per art pixel the folder's text would be
    // cramped, so a plain single-column panel is shown instead.
    minCssPxPerArtPx: 3,
    fadeMs: 200,
  },

  // The welcome note: on a first visit a sasquatch leaves it on the sill;
  // clicking it opens a short note pointing at `help` and `whoami`. Once
  // read it is gone for good. Its words are in the content file.
  welcomeNote: {
    contentFile: 'content/welcome_note.json',
    deliverAfterSec: 2.5,         // after the page opens, so the scene settles first
    minCssPxPerArtPx: 3,          // like the folder: plain panel below this
    fadeMs: 200,
    size: [112, 64],              // the paper, in art pixels
    backdrop: 'rgba(20,12,6,0.6)',   // the same dimming as the folder and the board
  },

  // The achievement board on the right-hand log, and the pop-up it opens.
  // Every position, size and colour is in the layout file.
  board: {
    artDir: 'anim/board/',
    layoutFile: 'anim/board/board_layout.json',
    minCssPxPerArtPx: 3,          // same as the folder: plain panel below this
    fadeMs: 200,
    words: {
      label: 'Achievements',
      how: 'HOW',
      reward: 'REWARD',
      unknown: '???',
      undiscovered: 'Not yet discovered.',
      progress: (earned, total) => `${earned} of ${total} earned`,
    },
  },

  // ── Achievements ─────────────────────────────────────────────────────
  // What they are, their goals and every sprite position are in
  // anim/achievements/achievements.json; these are the tunables.
  achievements: {
    artDir: 'anim/achievements/',   // the pack above; its manifest is achievements.json
    storageKey: 'cabin-window.progress',
    storageVersion: 1,            // bump to start everyone fresh after a format change
    clickPaddingPx: 3,            // creatures are small and moving: forgiving hit boxes
    starClickRadiusPx: 4,
    yetiChance: 0.2,              // share of sasquatch appearances that are the yeti
    auroraChancePerNight: 1 / 3,
    auroraFadeMs: 6000,           // the art asks for a slow fade, never a cut
    rainbowFadeMs: 2500,
    rainbowShowSec: 20,
    birdSparkleEveryMs: 300,      // the golden bird's trail
    birdSparkleBehindPx: 7,       // how far behind the bird's anchor it drops them
    trophySparkleEverySec: [3, 9],
    // The deer's visit (js/scene/deer.js): on the clifftop, out of sight,
    // then down at the pool. Its path and positions are in achievements.json;
    // it walks one path entry (far) or one pixel (near) per animation frame.
    deer: {
      clifftopPauseSec: [2, 4],   // standing at the end of the clifftop path
      intermissionSec: [4, 7],    // out of sight between the two appearances
      approachPauseSec: [1, 2],   // the one stop on the way to the water
      drinkBeatSec: [0.5, 1],     // standing at the water before the first drink
      drinks: [2, 3],             // how many times it drinks
      drinkPauseSec: [0.4, 1.2],  // between drinks
      startleSpeedFactor: 2,      // clicked: back into the trees at double pace
    },
    sign: {
      showMs: 4000,
      slideMs: 450,
      marginTopPx: 4,             // art pixels below the top of the window opening
      textColour: '#F4E3C3',
    },
  },

  // The terrarium: the pot on the left wall and the field journal it opens
  // (anim/terrarium/terrarium_brief.md). Positions and sprite sizes are in
  // anim/terrarium/terrarium_manifest.json; species and crosses are in
  // js/terrarium-species.js; these are the rules' numbers. Time is real time:
  // the plant grows while nobody is watching.
  terrarium: {
    artDir: 'anim/terrarium/',    // a pack above; its manifest is terrarium_manifest.json
    storageKey: 'cabin_terrarium',
    storageVersion: 1,            // unknown or missing version: a fresh start
    tickSec: 60,                  // on load, then this often while the page is open
    offlineCapHours: 48,          // a plant left for a week is thirsty, not dead
    // Ticks further apart than this (a hidden tab, a sleeping laptop) count
    // as time away: the plant dries out but can't die of it.
    watchedGapSec: 300,
    evapPerHour: 0.08,            // divided by (0.6 + hardiness * 0.15)
    growthPerHour: 0.035,         // times (0.8 + vigor * 0.1) times health
    wiltBelow: 0.10,              // at or under this hydration: no growth, wilting
    wiltHealth: 0.5,              // growth rate once it has wilted, until trimmed
    deadAfterDryHours: 24,        // bone dry this long, while visited
    plantHydration: 0.5,          // a freshly planted seed's soil
    waterAmount: 0.25,
    waterDebounceMs: 500,
    saturatedShowSec: 4,          // "Saturated!" after watering past full
    trimFrom: 0.35,               // Trim is disabled below this growth
    trimGrowth: 0.05,             // what a trim costs
    pityStep: 0.05,               // each failed try on a pair adds this to its chance
    pityCap: 0.25,
    starterSeeds: { moss: 3, fern: 2, clover: 2 },
    firstHarvestGift: ['daisy', 'wildflower', 'mushroom'],   // one of these, once
    // Text colours on the paper, per time of day (the font is white).
    colours: {
      morning:   { text: '#382A20', text_d: '#645040', accent: '#90542C' },
      day:       { text: '#342C22', text_d: '#605444', accent: '#8C5830' },
      afternoon: { text: '#362E20', text_d: '#625642', accent: '#925C2E' },
      night:     { text: '#A09888', text_d: '#645E56', accent: '#584834' },
    },
    words: {
      label: 'Terrarium',
      titles: ['TERRARIUM', 'SEED STORE', 'CROSSING BENCH', 'SPECIES CODEX'],
    },
  },

  // ── Sound ────────────────────────────────────────────────────────────
  // Ambience, not a soundtrack: everything sits well below full volume.
  // Volumes are in dB (0 = the file as recorded; -6 is about half as loud).
  sound: {
    dir: 'sounds/',
    masterVolumeDb: 0,            // turn everything up or down together
    loopLookaheadSec: 4,
    endFadeSec: 0.25,             // when a one-shot is cut short
    sounds: {
      waterfall: {
        file: 'waterfall.mp3',
        volumeDb: -17,
        // The recording swells about 5 dB over 3-10 s; loop that part with a
        // cross-fade and cancel the swell, so the level stays steady.
        loop: { startSec: 3, crossfadeSec: 1.5, levelCorrectionDb: -5 },
        // Heard from far across the valley (see createDistance in sound.js).
        distance: { lowpassHz: 1800, highpassHz: 200, stereoWidth: 0.4, reverbMix: 0.35, reverbSec: 2.5 },
      },
      bird: {
        file: 'bird_flap.wav',
        volumeDb: -8,
        panPerSide: 0.6,          // heard from the side the bird flies in on
      },
      wind: {
        file: 'wind.wav',
        volumeDb: -14,            // a soft gust, just above the distant waterfall
        startAtSec: 0.5,          // the file opens with half a second of silence
        stopAtSec: 5.5,           // and ends with two silent seconds
        sweepPan: 0.4,            // moves left to right with the gust
      },
    },
  },

  // ── Page ─────────────────────────────────────────────────────────────
  terminal: {
    maxHistory: 50,
    greeting: 'cabin terminal. type "help" to see what you can do.',
  },
  maxFrameDtMs: 250,   // after a hidden tab, don't fast-forward everything at once

  // ── Test mode only (?test) ───────────────────────────────────────────
  test: {
    tickMs: 100,   // anim.py's compose() works in 100 ms ticks
    // compose() advances some sheets at different speeds than the manifest
    // says. With ?timing=reference these override ms_per_frame so frames
    // line up with compose() tick for tick.
    referenceMsPerFrame: {
      stars: 400, treetops: 300, mug: 200, rain: 100, snow: 200,
      bird_far: 200, wind_gust: 100, wind_streak: 100,
      sasquatch_peek: 157.142857,   // compose() plays 14 frames over 22 ticks
    },
  },
};
