// weather.js — the current weather: one of config.weathers. Rain and snow
// count as seen when shown (track('weatherSeen', name)); clear doesn't.
// Now and then a spell of rain or snow comes on its own (the scheduler's
// `weather` event) and clears after a while. The hidden `weather` command
// sets it by hand, which ends any spell: what you set stays until you change it.
// Exports: createWeather(config) -> { get, set, startSpell, update, running }

import { track } from './achievements.js';
import { randomBetween } from './random.js';

export function createWeather(config) {
  const { lastsSec, snowShare } = config.weatherSpell;
  let current = config.defaultWeather;
  let spellLeftMs = null;   // while a spell is on: how long until it clears

  function show(name) {
    current = name;
    if (name !== config.defaultWeather) track('weatherSeen', name);
  }

  // By hand. Returns false (and changes nothing) for an unknown weather name.
  function set(name) {
    if (!config.weathers.includes(name)) return false;
    spellLeftMs = null;
    show(name);
    return true;
  }

  // The scheduled event: rain or snow (`kind`, or rolled), only from a clear
  // sky. `seconds` fixes how long it lasts, for testing.
  function startSpell({ kind, seconds } = {}) {
    if (current !== config.defaultWeather) return false;
    const name = kind ?? (Math.random() < snowShare ? 'snow' : 'rain');
    if (!config.weathers.includes(name) || name === config.defaultWeather) return false;
    show(name);
    spellLeftMs = (seconds ?? randomBetween(...lastsSec)) * 1000;
    return true;
  }

  return {
    get: () => current,
    set,
    startSpell,
    update(dtMs) {
      if (spellLeftMs === null) return;
      spellLeftMs -= dtMs;
      if (spellLeftMs > 0) return;
      spellLeftMs = null;
      show(config.defaultWeather);
    },
    running: () => spellLeftMs !== null,
  };
}
