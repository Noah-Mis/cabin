// terrarium-species.js — the terrarium's twelve species and the crosses that
// breed the six you can't start with (terrarium_brief.md §4, §5). Index order
// is the sheet order: row i of the plant and bloom sheets, frame i of the
// seed and codex sheets.
// Every string is drawn in the journal's 3x5 font, upper-cased: a line from
// x 12 to the margin holds 33 characters, so blurbs and flavour stay under that.
//   short     the name under a crossing-bench slot, which has ~9 characters
//   flowers   has a bloom (its row in the bloom sheet isn't empty)
//   stalk     a mushroom-style 4px stipe instead of a 2px stem
// Exports: SPECIES, CROSSES, speciesIndex(id), findCross(a, b), pairKey(a, b)

export const SPECIES = [
  { id: 'moss', name: 'Moss', rarity: 1, flowers: false,
    blurb: 'Common - a hardy mat', flavour: 'Grows on whatever holds still.' },
  { id: 'fern', name: 'Fern', rarity: 1, flowers: false,
    blurb: 'Common - unfurls slowly', flavour: 'Older than the dinosaurs.' },
  { id: 'clover', name: 'Clover', rarity: 1, flowers: false,
    blurb: 'Common - three leaves, mostly', flavour: 'Keep looking for the fourth.' },
  { id: 'daisy', name: 'Daisy', rarity: 2, flowers: true,
    blurb: 'Uncommon - a cheerful flower', flavour: 'Opens with the morning light.' },
  { id: 'wildflower', name: 'Wildflower', short: 'Wildflwr', rarity: 2, flowers: true,
    blurb: 'Uncommon - grows where it likes', flavour: 'Nobody planted it. Here it is.' },
  { id: 'mushroom', name: 'Mushroom', rarity: 2, flowers: true, stalk: true,
    blurb: 'Uncommon - likes it damp', flavour: 'Not technically a plant.' },
  { id: 'bluebell', name: 'Bluebell', rarity: 3, flowers: true,
    blurb: 'Rare - rings without a sound', flavour: 'Carpets the woods in spring.' },
  { id: 'suncap', name: 'Suncap', rarity: 3, flowers: true, stalk: true,
    blurb: 'Rare - a cap full of sunlight', flavour: 'Glows faintly after sundown.' },
  { id: 'ivy', name: 'Ivy', rarity: 3, flowers: false,
    blurb: 'Rare - climbs anything', flavour: 'Give it a wall and a year.' },
  { id: 'thistle', name: 'Thistle', rarity: 4, flowers: true,
    blurb: 'Very rare - prickly but kind', flavour: "The bees don't mind the spikes." },
  { id: 'moonflower', name: 'Moonflower', short: 'Moonflwr', rarity: 4, flowers: true,
    blurb: 'Very rare - blooms at night', flavour: 'Turns its face to the moon.' },
  { id: 'aurora', name: 'Aurora Bloom', short: 'Aurora', rarity: 5, flowers: true,
    blurb: 'Legendary - the northern lights', flavour: 'A little of the night sky.' },
];

// Pairs are unordered. A miss (or a pair with no entry) gives one of the parents.
export const CROSSES = [
  { a: 'daisy',      b: 'wildflower', out: 'bluebell',   chance: 0.15 },
  { a: 'mushroom',   b: 'daisy',      out: 'suncap',     chance: 0.15 },
  { a: 'fern',       b: 'clover',     out: 'ivy',        chance: 0.20 },
  { a: 'wildflower', b: 'fern',       out: 'thistle',    chance: 0.12 },
  { a: 'bluebell',   b: 'mushroom',   out: 'moonflower', chance: 0.10 },
  { a: 'moonflower', b: 'suncap',     out: 'aurora',     chance: 0.05 },
];

export function speciesIndex(id) {
  return SPECIES.findIndex((species) => species.id === id);
}

export function findCross(a, b) {
  return CROSSES.find((cross) => (cross.a === a && cross.b === b) || (cross.a === b && cross.b === a)) ?? null;
}

// The pity counter's key: the pair, sorted, so a x b and b x a share it.
export function pairKey(a, b) {
  return [a, b].sort().join('|');
}
