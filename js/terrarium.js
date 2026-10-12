// terrarium.js — the terrarium's rules and its saved state: one pot, a seed
// inventory where every seed carries a genome, crossing two seeds for a new
// one, and the codex of species found. The journal (js/terrarium-journal.js)
// and the terminal commands both act through here, so they always agree.
// Time is real time (Date.now): tick() catches up on whatever passed since the
// last one, capped at config.terrarium.offlineCapHours. A plant can only die
// of thirst while the page is open (ticks closer together than watchedGapSec);
// time away just dries it out. Wilting slows it to wiltHealth until trimmed:
// that is the only time a plant needs trimming (needsTrim), and the only time
// the journal offers the shears.
//
// Saved under its own localStorage key (config.terrarium.storageKey), apart
// from the achievements in js/progress.js, as one object:
//   { version, pot, seeds: { id: [genome] }, codex: [ids], pity: { pairKey: n },
//     lastTick, lastWater, tab, hints: [ids of the journal's hints already learned] }
//   pot: null or { species, genome, hydration, growth, health, wilting, dead,
//                  dryMs, plantedAt, stack }
//   genome: { height 1-5, bloom 0-2, vigor 1-5, hue 1-5, hardiness 1-5 }
// Missing, malformed or other-version data starts fresh. Storage that can't
// be written (private windows) lasts for the visit.
// "Discovered" in the codex means harvested, or bred by a cross.
// Seeds: a harvest gives only the plant's own species, 2-4 by rarity
// (config.terrarium.harvestSeedsByRarity). The starters (moss, fern, clover)
// never drop below one: planting the last one keeps it, and crossing may only
// use the spare ones above it. Every other species comes from crossing.
//
// Exports: createTerrarium(settings, { now, random }) -> {
//   get(), tick(), water(), trim(), harvest(), plant(id), cross(a, b), predict(a, b),
//   count(id), spare(id) (how many may be crossed), isStarter(id), needsTrim(pot),
//   stage(pot), status(pot), find(word), setTab(i), reset(),
//   hintSeen(id), learnHint(id) }   the journal's one-time hints
//   Actions return { ok, ... } with a reason when not ok; see each one.
//   stage(pot) -> 'seed' | 'sprout' | 'young' | 'mature' | 'flowering' | 'ready'
//   STAGES: growth thresholds; TRAITS: genome keys in trait-icon order.

import { SPECIES, speciesIndex, findCross, pairKey } from './terrarium-species.js';

export const TRAITS = ['height', 'bloom', 'vigor', 'hue', 'hardiness'];
export const STAGES = [
  { name: 'seed', from: 0, status: 'Just planted.' },
  { name: 'sprout', from: 0.15, status: 'Sprouting.' },
  { name: 'young', from: 0.35, status: 'Growing...' },
  { name: 'mature', from: 0.65, status: 'Filling out.' },
  { name: 'flowering', from: 0.85, status: 'In bloom.' },
  { name: 'ready', from: 1, status: 'Ready to harvest.' },
];
const HOUR_MS = 3600 * 1000;
const MIDDLE_TILES = ['stem_leaves', 'stem_leaf_l', 'stem_leaf_r'];

export function createTerrarium(settings, { now = Date.now, random = Math.random } = {}) {
  let state = read();
  let persistent = canWrite();
  let saturatedAt = -Infinity;   // watered past full: "Saturated!" for a moment
  keepStarters();
  tick();

  // ── storage ──
  function read() {
    try {
      const raw = window.localStorage.getItem(settings.storageKey);
      return (raw && clean(JSON.parse(raw))) || fresh();
    } catch {
      return fresh();
    }
  }
  function canWrite() {
    try {
      window.localStorage.setItem(settings.storageKey, JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }
  function save() {
    if (!persistent) return;
    try {
      window.localStorage.setItem(settings.storageKey, JSON.stringify(state));
    } catch {
      persistent = false;
    }
  }

  // A new player: the starter seeds and nothing else.
  function fresh() {
    const seeds = {};
    for (const [id, n] of Object.entries(settings.starterSeeds)) seeds[id] = Array.from({ length: n }, () => starterGenome(id));
    return { version: settings.storageVersion, pot: null, seeds, codex: [], pity: {},
      lastTick: now(), lastWater: 0, tab: 0, hints: [] };
  }

  // Keeps stored data only if every part is well-formed; otherwise null.
  function clean(data) {
    if (!data || typeof data !== 'object' || data.version !== settings.storageVersion) return null;
    const known = (id) => speciesIndex(id) >= 0;
    const seeds = {};
    for (const [id, list] of Object.entries(data.seeds ?? {})) {
      if (!known(id) || !Array.isArray(list) || !list.every(isGenome)) return null;
      if (list.length) seeds[id] = list.map((g) => ({ ...g }));
    }
    let pot = null;
    if (data.pot) {
      const p = data.pot;
      if (!known(p.species) || !isGenome(p.genome) || ![p.hydration, p.growth, p.health, p.plantedAt].every(Number.isFinite)) return null;
      pot = { species: p.species, genome: { ...p.genome }, hydration: clamp(p.hydration, 0, 1), growth: clamp(p.growth, 0, 1),
        health: clamp(p.health, 0, 1), wilting: !!p.wilting, dead: !!p.dead, dryMs: Number.isFinite(p.dryMs) ? p.dryMs : 0,
        plantedAt: p.plantedAt, stack: [] };
      pot.stack = stackFor(pot);
    }
    const codex = Array.isArray(data.codex) ? [...new Set(data.codex.filter(known))] : [];
    const pity = {};
    for (const [key, n] of Object.entries(data.pity ?? {})) if (Number.isInteger(n) && n > 0) pity[key] = n;
    const time = (v) => (Number.isFinite(v) ? v : 0);
    return { version: settings.storageVersion, pot, seeds, codex, pity,
      lastTick: Math.min(time(data.lastTick) || now(), now()), lastWater: time(data.lastWater),
      tab: Number.isInteger(data.tab) && data.tab >= 0 && data.tab < 4 ? data.tab : 0,
      hints: Array.isArray(data.hints) ? [...new Set(data.hints.filter((h) => typeof h === 'string'))] : [] };
  }

  // At least one of every starter, always (a save from before this rule may
  // have none), so nobody can breed themselves into a corner.
  function keepStarters() {
    for (const id of Object.keys(settings.starterSeeds)) if (!count(id)) addSeed(id, starterGenome(id));
    save();
  }
  function isStarter(id) {
    return Object.hasOwn(settings.starterSeeds, id);
  }

  // ── genetics ──
  function starterGenome(id) {
    const { flowers } = SPECIES[speciesIndex(id)];
    return { height: randInt(2, 3), bloom: flowers ? randInt(1, 2) : 0, vigor: randInt(2, 4), hue: 3, hardiness: randInt(2, 4) };
  }
  function crossTrait(a, b, lo = 1, hi = 5) {
    const mid = (a + b) / 2;
    const jitter = random() < 0.5 ? -1 : 1;
    return clamp(Math.round(mid + jitter * (random() < 0.3 ? 1 : 0)), lo, hi);
  }
  function crossGenome(a, b, species) {
    const { flowers } = SPECIES[speciesIndex(species)];
    const genome = {};
    for (const trait of TRAITS) genome[trait] = crossTrait(a[trait], b[trait]);
    genome.bloom = flowers ? crossTrait(a.bloom, b.bloom, 1, 2) : 0;
    return genome;
  }
  function randInt(lo, hi) {
    return lo + Math.floor(random() * (hi - lo + 1));
  }

  function addSeed(id, genome) {
    (state.seeds[id] ??= []).push(genome);
  }
  // The oldest seed of a kind is the one planted or crossed. A starter's last
  // seed is never used up: what is taken is a copy of it.
  function takeSeed(id) {
    const list = state.seeds[id];
    if (isStarter(id) && list?.length === 1) return { ...list[0] };
    const genome = list?.shift() ?? null;
    if (list && !list.length) delete state.seeds[id];
    return genome;
  }
  // Returns true if the species is new to the codex.
  function discover(id) {
    if (state.codex.includes(id)) return false;
    state.codex.push(id);
    return true;
  }

  // ── growth ──
  function evapPerHour(genome) {
    return settings.evapPerHour / (0.6 + genome.hardiness * 0.15);
  }
  // Rarer species take longer; vigor speeds any of them up.
  function growthPerHour(pot) {
    const hours = settings.growHoursByRarity[SPECIES[speciesIndex(pot.species)].rarity - 1];
    return (1 / hours) * (0.8 + pot.genome.vigor * 0.1) / 0.9;
  }

  // Catches the pot up to now. Growth only counts the hours the soil stayed
  // above wiltBelow; drying to zero only counts while the page was watched.
  function tick() {
    const t = now();
    const elapsed = Math.min(Math.max(0, t - state.lastTick), settings.offlineCapHours * HOUR_MS);
    state.lastTick = t;
    const pot = state.pot;
    if (pot && !pot.dead && elapsed > 0) {
      const hours = elapsed / HOUR_MS;
      const evap = evapPerHour(pot.genome);
      const start = pot.hydration;
      const wetHours = start > settings.wiltBelow ? Math.min(hours, (start - settings.wiltBelow) / evap) : 0;
      pot.growth = Math.min(1, pot.growth + wetHours * growthPerHour(pot) * pot.health);
      pot.hydration = Math.max(0, start - hours * evap);
      if (pot.hydration <= settings.wiltBelow && !pot.wilting) {
        pot.wilting = true;
        pot.health = Math.min(pot.health, settings.wiltHealth);
      }
      const watched = elapsed <= settings.watchedGapSec * 1000;
      if (watched && pot.hydration === 0) pot.dryMs += Math.max(0, elapsed - (start / evap) * HOUR_MS);
      if (pot.dryMs > settings.deadAfterDryHours * HOUR_MS) pot.dead = true;
    }
    if (pot) pot.stack = stackFor(pot);
    save();
  }

  function stage(pot) {
    return STAGES.reduce((found, s) => (pot.growth >= s.from ? s : found), STAGES[0]).name;
  }

  // The tiles, bottom to top (brief §8). Always ends in a terminator: the
  // crown, or a bloom for a flowering plant with the bloom gene. The middle
  // tiles vary with an RNG seeded on plantedAt, so a plant redraws the same.
  function stackFor(pot) {
    const st = stage(pot);
    const rng = seeded(pot.plantedAt);
    const middle = (n) => Array.from({ length: n }, (_, i) => (i === 0 ? 'stem_leaves' : MIDDLE_TILES[Math.floor(rng() * 3)]));
    const blooms = SPECIES[speciesIndex(pot.species)].flowers && pot.genome.bloom > 0;
    let stack;
    if (st === 'seed' || st === 'sprout') stack = [st];
    else if (st === 'young') stack = [...middle(1), 'crown'];
    else if (!blooms || st === 'mature') stack = [...middle(2), 'crown'];
    else if (st === 'flowering') stack = [...middle(1), pot.growth < (STAGES[4].from + 1) / 2 ? 'bud' : 'opening'];
    else stack = [...middle(1), pot.genome.bloom >= 2 ? 'full' : 'opening'];
    if (pot.dead) return stack.map(() => 'dead');
    if (pot.wilting) return stack.map((tile) => (MIDDLE_TILES.includes(tile) ? 'wilt' : tile));
    return stack;
  }

  function status(pot) {
    if (!pot) return 'Nothing planted.';
    if (pot.dead) return 'Withered.';
    if (now() - saturatedAt < settings.saturatedShowSec * 1000) return 'Saturated!';
    if (pot.wilting) return 'Thirsty. Water me!';
    if (needsTrim(pot)) return 'Overgrown. Trim it.';
    return STAGES.find((s) => s.name === stage(pot)).status;
  }

  // Wilted and not yet trimmed: growing at wiltHealth.
  function needsTrim(pot) {
    return !!pot && !pot.dead && pot.health < 1;
  }

  // ── actions ──
  // Each catches up first, changes the state, saves, and says what happened.

  // -> { ok, reason: 'empty' | 'dead' | 'wait', saturated }
  function water() {
    tick();
    const pot = state.pot;
    if (!pot) return { ok: false, reason: 'empty' };
    if (pot.dead) return { ok: false, reason: 'dead', species: pot.species };
    if (now() - state.lastWater < settings.waterDebounceMs) return { ok: false, reason: 'wait' };
    const saturated = pot.hydration + settings.waterAmount > 1;
    pot.hydration = Math.min(1, pot.hydration + settings.waterAmount);
    pot.wilting = false;
    pot.dryMs = 0;
    pot.stack = stackFor(pot);
    state.lastWater = now();
    if (saturated) saturatedAt = now();
    save();
    return { ok: true, species: pot.species, saturated };
  }

  // Only a plant that has wilted needs it: back to full health, for a little growth.
  // -> { ok, reason: 'empty' | 'dead' | 'healthy' }
  function trim() {
    tick();
    const pot = state.pot;
    if (!pot) return { ok: false, reason: 'empty' };
    if (pot.dead) return { ok: false, reason: 'dead', species: pot.species };
    if (!needsTrim(pot)) return { ok: false, reason: 'healthy', species: pot.species };
    pot.growth = Math.max(0, pot.growth - settings.trimGrowth);
    pot.health = 1;
    pot.stack = stackFor(pot);
    save();
    return { ok: true, species: pot.species };
  }

  // Ready: 2-4 seeds of the plant's own species, fewer the rarer it is (a
  // legendary always gives 2), each a slight variation of the plant; vigor 4+
  // rolls twice and keeps the better. The species goes in the codex.
  // Dead: clears the pot, no seeds.
  // -> { ok, species, seeds, cleared, discovered } or { ok: false, reason: 'empty' | 'unripe', growth }
  function harvest() {
    tick();
    const pot = state.pot;
    if (!pot) return { ok: false, reason: 'empty' };
    if (pot.dead) {
      state.pot = null;
      save();
      return { ok: true, species: pot.species, seeds: 0, cleared: true, discovered: false };
    }
    if (pot.growth < 1) return { ok: false, reason: 'unripe', species: pot.species, growth: pot.growth };
    const [fewest, most] = settings.harvestSeedsByRarity[SPECIES[speciesIndex(pot.species)].rarity - 1];
    const roll = () => randInt(fewest, most);
    const seeds = pot.genome.vigor >= 4 ? Math.max(roll(), roll()) : roll();
    for (let i = 0; i < seeds; i++) addSeed(pot.species, crossGenome(pot.genome, pot.genome, pot.species));
    const discovered = discover(pot.species);
    state.pot = null;
    save();
    return { ok: true, species: pot.species, seeds, cleared: false, discovered };
  }

  // -> { ok, species } or { ok: false, reason: 'occupied' | 'none', species }
  function plant(id) {
    tick();
    if (state.pot) return { ok: false, reason: 'occupied', species: state.pot.species };
    if (!count(id)) return { ok: false, reason: 'none', species: id };
    const genome = takeSeed(id);
    const pot = { species: id, genome, hydration: settings.plantHydration, growth: 0, health: 1,
      wilting: false, dead: false, dryMs: 0, plantedAt: now(), stack: [] };
    pot.stack = stackFor(pot);
    state.pot = pot;
    save();
    return { ok: true, species: id };
  }

  // What crossing a and b would give: the hybrid (or null), its chance with
  // pity, and the offspring's traits if nothing jitters (midpoints).
  function predict(a, b) {
    const pair = findCross(a, b);
    const tries = state.pity[pairKey(a, b)] ?? 0;
    const chance = pair ? Math.min(1, pair.chance + Math.min(tries * settings.pityStep, settings.pityCap)) : 0;
    const [ga, gb] = [state.seeds[a]?.[0], state.seeds[b]?.[a === b ? 1 : 0]];
    const genome = ga && gb ? Object.fromEntries(TRAITS.map((t) => [t, Math.round((ga[t] + gb[t]) / 2)])) : null;
    return { hybrid: pair?.out ?? null, chance, genome };
  }

  // Both seeds are used up and there is always a seed back: the hybrid on a
  // hit, otherwise one of the parents. Misses on a pair raise its chance.
  // A starter's last seed can't be crossed ('last'), only the spares above it.
  // -> { ok, species, hit, hybrid, chance, discovered } or { ok: false, reason: 'missing' | 'last', species }
  function cross(a, b) {
    tick();
    for (const id of new Set([a, b])) {
      const need = a === b ? 2 : 1;
      if (spare(id) < need) return { ok: false, reason: count(id) >= need ? 'last' : 'missing', species: id };
    }
    const { hybrid, chance } = predict(a, b);
    const ga = takeSeed(a);
    const gb = takeSeed(b);
    const hit = hybrid !== null && random() < chance;
    const species = hit ? hybrid : (random() < 0.5 ? a : b);
    const key = pairKey(a, b);
    if (hit) delete state.pity[key];
    else if (hybrid) state.pity[key] = (state.pity[key] ?? 0) + 1;
    addSeed(species, crossGenome(ga, gb, species));
    const discovered = hit && discover(species);
    save();
    return { ok: true, species, hit, hybrid, chance, discovered };
  }

  function count(id) {
    return state.seeds[id]?.length ?? 0;
  }
  // How many of a kind can go on the crossing bench: all of them, except a
  // starter's last one.
  function spare(id) {
    return Math.max(0, count(id) - (isStarter(id) ? 1 : 0));
  }

  // A species from what someone typed: its id, name, or short name.
  function find(word) {
    const w = String(word ?? '').toLowerCase().trim();
    return SPECIES.find((s) => [s.id, s.name.toLowerCase(), s.short?.toLowerCase()].includes(w))?.id ?? null;
  }

  return {
    get: () => state,   // read-only by agreement: change it through the actions
    tick, water, trim, harvest, plant, cross, predict, count, spare, isStarter, needsTrim, stage, status, find,
    setTab(i) { state.tab = i; save(); },
    hintSeen: (id) => state.hints.includes(id),
    learnHint(id) {
      if (state.hints.includes(id)) return;
      state.hints.push(id);
      save();
    },
    reset() {
      state = fresh();
      saturatedAt = -Infinity;
      save();
    },
  };
}

function isGenome(g) {
  return g && typeof g === 'object'
    && TRAITS.every((t) => Number.isInteger(g[t]) && g[t] >= (t === 'bloom' ? 0 : 1) && g[t] <= (t === 'bloom' ? 2 : 5));
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

// mulberry32: a small seeded RNG, so a plant's leaves are the same every visit.
function seeded(seed) {
  let a = Math.floor(seed) >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
