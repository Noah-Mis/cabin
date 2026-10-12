// progress.js — the visitor's saved achievement progress, and the only module
// that touches localStorage apart from js/terrarium.js, which keeps the
// terrarium under its own key. Everything lives in one object under one
// versioned key:
//   { version, stats: { name: number | [values] }, unlocked: [ids] }
// Storage can be missing, full, or throw (private windows, blocked cookies);
// then progress simply lasts for this visit. Missing, malformed or
// older-version data means a fresh start, never an error.
// firstVisit() is true when nothing was saved before this page opened.
// Exports: createProgress({ storageKey, version })
//   -> { stats(), unlocked(), add, addToSet, setStat, markUnlocked, reset, persistent(), firstVisit() }

export function createProgress({ storageKey, version }) {
  let firstVisit = true;
  let state = read();
  let persistent = canWrite();

  function read() {
    try {
      const raw = window.localStorage.getItem(storageKey);
      firstVisit = !raw;
      return raw ? clean(JSON.parse(raw), version) : fresh(version);
    } catch {
      return fresh(version);
    }
  }

  function canWrite() {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }

  function save() {
    if (!persistent) return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      persistent = false;   // e.g. storage filled up mid-visit: keep going in memory
    }
  }

  return {
    // Copies, so nobody can change progress without going through here.
    stats: () => structuredClone(state.stats),
    unlocked: () => [...state.unlocked],
    add(stat, amount) {
      state.stats[stat] = (typeof state.stats[stat] === 'number' ? state.stats[stat] : 0) + amount;
      save();
    },
    // Returns true if `value` was new.
    addToSet(stat, value) {
      const set = Array.isArray(state.stats[stat]) ? state.stats[stat] : [];
      if (set.includes(value)) return false;
      state.stats[stat] = [...set, value];
      save();
      return true;
    },
    setStat(stat, value) {
      state.stats[stat] = value;
      save();
    },
    markUnlocked(id) {
      if (state.unlocked.includes(id)) return;
      state.unlocked.push(id);
      save();
    },
    reset() {
      state = fresh(version);
      save();
    },
    persistent: () => persistent,
    firstVisit: () => firstVisit,
  };
}

function fresh(version) {
  return { version, stats: {}, unlocked: [] };
}

// Keeps only well-formed parts of stored data; anything else starts fresh.
function clean(data, version) {
  if (!data || typeof data !== 'object' || data.version !== version) return fresh(version);
  const stats = {};
  if (data.stats && typeof data.stats === 'object') {
    for (const [name, value] of Object.entries(data.stats)) {
      if (typeof value === 'number' && Number.isFinite(value) && value >= 0) stats[name] = value;
      else if (Array.isArray(value) && value.every((v) => typeof v === 'string')) stats[name] = [...new Set(value)];
    }
  }
  const unlocked = Array.isArray(data.unlocked) ? [...new Set(data.unlocked.filter((id) => typeof id === 'string'))] : [];
  return { version, stats, unlocked };
}
