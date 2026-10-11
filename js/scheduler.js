// scheduler.js — fires occasional events on random timers.
// For every entry in config.events it waits a random time between minWaitSec
// and maxWaitSec, rolls `chance`, fires the event if the roll succeeds, and
// starts waiting again. Time only passes through update(dt), so a paused or
// test-mode scene never fires anything by itself.
// Exports: createScheduler(eventTimings, events) -> { update, timers }

export function createScheduler(eventTimings, events, random = Math.random) {
  const timers = {};
  for (const [name, timing] of Object.entries(eventTimings)) {
    if (!events[name]) {
      console.error(`config.events.${name} has no matching scene event`);
      continue;
    }
    timers[name] = { timing, remainingMs: randomWaitMs(timing, random) };
  }

  function update(dtMs) {
    for (const [name, timer] of Object.entries(timers)) {
      timer.remainingMs -= dtMs;
      if (timer.remainingMs > 0) continue;
      if (random() < timer.timing.chance) events[name]();
      timer.remainingMs = randomWaitMs(timer.timing, random);
    }
  }

  return { update, timers };
}

function randomWaitMs({ minWaitSec, maxWaitSec }, random) {
  return (minWaitSec + random() * (maxWaitSec - minWaitSec)) * 1000;
}
