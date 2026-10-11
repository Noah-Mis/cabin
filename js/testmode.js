// testmode.js — a deterministic scene for automated checks, turned on with
// ?test in the URL. Random events are off, the time of day and weather are
// fixed, and animation advances in whole ticks (config.test.tickMs) instead
// of following the real clock, so a frame can be lined up with compose() in
// anim/scripts/anim.py.
//
// URL parameters (all optional, all need ?test):
//   time=morning|day|afternoon|night   weather=clear|rain|snow
//   timing=reference   play sheets at compose()'s speeds instead of the manifest's
//   demo=reference     replay compose()'s bird, far bird and sasquatch
//   wind=1             also replay compose()'s wind (its day/afternoon previews)
//
// The page then exposes window.cabin.test:
//   advanceTo(tick)  step forward to `tick` (never backwards) and draw it
//   capture()        the canvas as a PNG data URL, at native size
//
// Without timing=reference, sheets play at the manifest's speed times
// config.animationSlowdown, like the live site.
//
// Exports: readTestOptions(search), useReferenceTiming(manifest, overrides),
//          useTestSettings(config), startTestMode(app, options)

// compose() draws these at fixed demo positions. The numbers are copied from
// anim.py on purpose: this is the reference being reproduced, not tuning.
const REFERENCE_DEMO = [
  { tick: 0, event: 'bird', params: { direction: 1, x: 40, y: 52 } },
  { tick: 0, event: 'farbird', params: { direction: -1, x: 253, y: 39, speedPxPerSec: 15 } },
  { tick: 2, event: 'sasquatch', params: { spotIndex: 2 } },
  { tick: 24, event: 'sasquatch', params: { spotIndex: 4 } },
];
const REFERENCE_WIND = [
  { tick: 0, event: 'wind', params: { kind: 'gust', x: 70, y: 76, speedPxPerSec: 50 } },
  { tick: 20, event: 'wind', params: { kind: 'streak', x: 130, y: 96, speedPxPerSec: 40 } },
  { tick: 30, event: 'wind', params: { kind: 'gust', x: 50, y: 100, speedPxPerSec: 50 } },
];

export function readTestOptions(search) {
  const params = new URLSearchParams(search);
  if (!params.has('test')) return null;
  return {
    time: params.get('time') ?? 'day',
    weather: params.get('weather') ?? 'clear',
    referenceTiming: params.get('timing') === 'reference',
    demo: params.get('demo') === 'reference',
    wind: params.get('wind') === '1',
  };
}

export function useReferenceTiming(manifest, overrides) {
  for (const [name, ms] of Object.entries(overrides)) manifest.animations[name].ms_per_frame = ms;
}

// compose() sways the front trees non-stop, so test mode does too. Rewards
// that roll dice (the yeti, the aurora) only happen when an event asks.
export function useTestSettings(config) {
  config.treetops.restBetweenSwaysSec = [0, 0];
  config.achievements.yetiChance = 0;
  config.achievements.auroraChancePerNight = 0;
}

// app: { update(dtMs), render(), events, canvas, tickMs }
export function startTestMode(app, options) {
  const script = [
    ...(options.demo ? REFERENCE_DEMO : []),
    ...(options.wind ? REFERENCE_WIND : []),
  ];
  let tick = -1;

  function advanceTo(target) {
    while (tick < target) {
      if (tick >= 0) app.update(app.tickMs);
      tick += 1;
      for (const step of script) if (step.tick === tick) app.events[step.event](step.params);
    }
    app.render();
    return tick;
  }

  window.cabin.test = {
    advanceTo,
    capture: () => app.canvas.toDataURL('image/png'),
  };
  advanceTo(0);
}
