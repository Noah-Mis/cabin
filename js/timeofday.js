// timeofday.js — which time of day the scene shows, and the cross-fade
// between two of them. In "auto" mode it follows the visitor's local clock.
// A time counts as seen (track('timesSeen', time)) once it is fully on
// screen, however it got there: the clock, a fade, or a command.
// Exports: createTimeOfDay(config, startTime?) -> { set, update, view, mode, current }
//   startTime overrides the clock's time of day at the start (test mode).
//          timeForHour(hour, startHours)

import { track } from './achievements.js';

export function createTimeOfDay(config, startTime) {
  let mode = 'auto';                  // 'auto' or a fixed time name
  let from = startTime ?? timeForHour(new Date().getHours(), config.timeOfDayStartHour);
  let to = from;
  let fadeElapsedMs = 0;
  let sinceClockCheckMs = 0;
  track('timesSeen', to);

  function startFade(target, instant) {
    if (instant) { from = to = target; track('timesSeen', target); return; }
    if (target === to) return;
    // Interrupting a fade: start the new one from whatever is fully drawn.
    from = view().mix < 0.5 ? from : to;
    to = target;
    fadeElapsedMs = 0;
  }

  // name: one of config.times, or 'auto'. Returns false for anything else.
  function set(name, { instant = false } = {}) {
    if (name === 'auto') {
      mode = 'auto';
      startFade(timeForHour(new Date().getHours(), config.timeOfDayStartHour), instant);
      return true;
    }
    if (!config.times.includes(name)) return false;
    mode = name;
    startFade(name, instant);
    return true;
  }

  function update(dtMs) {
    if (to !== from) {
      fadeElapsedMs += dtMs;
      if (fadeElapsedMs >= config.crossFadeMs) { from = to; track('timesSeen', to); }
    }
    sinceClockCheckMs += dtMs;
    if (mode === 'auto' && sinceClockCheckMs >= config.clockCheckIntervalSec * 1000) {
      sinceClockCheckMs = 0;
      startFade(timeForHour(new Date().getHours(), config.timeOfDayStartHour), false);
    }
  }

  function view() {
    const mix = to === from ? 0 : Math.min(1, fadeElapsedMs / config.crossFadeMs);
    return { from, to, mix };
  }

  return { set, update, view, mode: () => mode, current: () => to };
}

// The time of day whose start hour is the latest one not after `hour`.
// Before the earliest start (e.g. 2am) it is still the last one (night).
export function timeForHour(hour, startHours) {
  const byStart = Object.entries(startHours).sort((a, b) => a[1] - b[1]);
  let result = byStart[byStart.length - 1][0];
  for (const [name, start] of byStart) if (hour >= start) result = name;
  return result;
}
