// weather.js — the current weather: one of config.weathers. Rain and snow
// count as seen when shown (track('weatherSeen', name)); clear doesn't.
// Exports: createWeather(config) -> { get, set }

import { track } from './achievements.js';

export function createWeather(config) {
  let current = config.defaultWeather;

  // Returns false (and changes nothing) for an unknown weather name.
  function set(name) {
    if (!config.weathers.includes(name)) return false;
    current = name;
    if (name !== config.defaultWeather) track('weatherSeen', name);
    return true;
  }

  return { get: () => current, set };
}
