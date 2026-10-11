// achievements.js — the achievements, as data from anim/achievements/
// achievements.json. Two functions are all the rest of the site needs:
//
//   track(stat, value)  report something that happened. A number adds to a
//                       counter (track('birdClicks', 1)); a string adds to a
//                       set (track('tabsSeen', 'resume')). Callers never
//                       mention achievements, only what happened.
//   isUnlocked(id)      the one place that answers "is this earned?". Scene
//                       elements ask it when choosing a sprite.
//
// Each achievement's test is the same rule applied to its JSON entry
// (`stat` and `goal`), in isMet() below. A 14th achievement is one JSON
// entry, plus a reward wherever the thing it changes is drawn.
//
// Exports: startAchievements({ definitions, progress, universes, onUnlock }),
//          track, isUnlocked, listAchievements, latestUnlocked,
//          resetAchievements, debugSetStat, debugUnlock

let definitions = [];
let progress = null;          // js/progress.js store; null until started
let universes = {};           // stat -> every possible value, for goal "all"
let onUnlock = () => {};

export function startAchievements(options) {
  ({ definitions, progress, universes, onUnlock } = options);
  checkForUnlocks();          // stored stats may already meet a goal
}

export function track(stat, value = 1) {
  if (!progress) return;
  if (typeof value === 'string') {
    if (!progress.addToSet(stat, value)) return;
  } else {
    progress.add(stat, value);
  }
  checkForUnlocks();
}

export function isUnlocked(id) {
  return progress ? progress.unlocked().includes(id) : false;
}

// Every achievement with whether it is earned and, for countable ones,
// how far along the visitor is: { definition, unlocked, count: {value, goal} | null }.
export function listAchievements() {
  const stats = progress?.stats() ?? {};
  const unlocked = progress?.unlocked() ?? [];
  return definitions.map((definition) => ({
    definition,
    unlocked: unlocked.includes(definition.id),
    count: countOf(definition, stats, unlocked),
  }));
}

// The id of the achievement earned most recently, or null.
export function latestUnlocked() {
  return progress?.unlocked().at(-1) ?? null;
}

export function resetAchievements() {
  progress?.reset();
}

// For testing without grinding (only reachable with ?debug).
export function debugSetStat(stat, value) {
  progress?.setStat(stat, value);
  checkForUnlocks();
}
export function debugUnlock(id) {
  if (!definitions.some((d) => d.id === id) || !progress || isUnlocked(id)) return false;
  progress.markUnlocked(id);
  onUnlock([definitions.find((d) => d.id === id)]);
  checkForUnlocks();
  return true;
}

// Unlocks everything whose goal is now met. Loops because one unlock can
// complete another (the "earn all the others" achievement).
function checkForUnlocks() {
  const earned = [];
  let changed = true;
  while (changed) {
    changed = false;
    for (const definition of definitions) {
      if (isUnlocked(definition.id) || !isMet(definition, progress.stats(), progress.unlocked())) continue;
      progress.markUnlocked(definition.id);
      earned.push(definition);
      changed = true;
    }
  }
  if (earned.length) onUnlock(earned);
}

// The one rule. `goal` is a number (a count, or a set's size), a single
// value the set must contain ("night"), or "all" (every value the stat can
// take, from `universes`). The special stat "unlocked" counts the others.
function isMet(definition, stats, unlocked) {
  const value = valueOf(definition, stats, unlocked);
  const { goal } = definition;
  if (goal === 'all') {
    const everything = universes[definition.stat] ?? [];
    return everything.length > 0 && everything.every((item) => value.includes(item));
  }
  if (typeof goal === 'string') return Array.isArray(value) && value.includes(goal);
  return (Array.isArray(value) ? value.length : value) >= goal;
}

function countOf(definition, stats, unlocked) {
  const value = valueOf(definition, stats, unlocked);
  if (definition.goal === 'all') {
    const everything = universes[definition.stat] ?? [];
    return { value: everything.filter((item) => value.includes(item)).length, goal: everything.length };
  }
  if (typeof definition.goal !== 'number') return null;
  return { value: Math.min(definition.goal, Math.floor(Array.isArray(value) ? value.length : value)), goal: definition.goal };
}

function valueOf(definition, stats, unlocked) {
  if (definition.stat === 'unlocked') return unlocked.filter((id) => id !== definition.id).length;
  const value = stats[definition.stat];
  if (Array.isArray(value)) return value;
  if (typeof value === 'number') return value;
  return typeof definition.goal === 'number' ? 0 : [];
}
