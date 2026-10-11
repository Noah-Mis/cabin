// sill.js — what is on the window sill, as one ordered array of item names
// (in the order they arrived). Each sill element registers itself and asks
// isOnSill(name) before drawing or taking clicks; the terminal's `ls`, `rm`
// and `touch` read and change the array through here. It lasts for the
// visit, like the folder and the pack always have; a reload starts over.
//
// An item registers four hooks:
//   available()  the visitor has one (a reward must be earned)
//   put()        bring it to the sill (with its animation); false if it can't now
//   take()       take it off at once (closing anything it has open)
//   busy()       in use right now (a sip, a cigarette, sliding in), so it stays
//   follow()     optional, for rewards: join or leave the sill as the
//                achievement is earned or reset. Run before every answer
//                below, so the array is never a frame behind an unlock.
//
// Exports: addSillItem(name, hooks, aliases), isOnSill, markOnSill, markOffSill,
//          sillItems, putAway, findSillItem, putOnSill, takeOffSill

const items = new Map();   // name -> { hooks, aliases }
let onSill = [];

export function addSillItem(name, hooks, aliases = []) {
  items.set(name, { hooks, aliases });
}

function follow() {
  for (const { hooks } of items.values()) hooks.follow?.();
}

export function isOnSill(name) {
  follow();
  return onSill.includes(name);
}

// Elements call these as their item arrives or leaves.
export function markOnSill(name) {
  if (!onSill.includes(name)) onSill.push(name);
}
export function markOffSill(name) {
  onSill = onSill.filter((item) => item !== name);
}

export function sillItems() {
  follow();
  return [...onSill];
}

// Things the visitor has that are not on the sill now.
export function putAway() {
  return [...items].filter(([name, { hooks }]) => hooks.available() && !isOnSill(name)).map(([name]) => name);
}

// The item a typed word means (its name or an alias), or null.
export function findSillItem(word) {
  for (const [name, { aliases }] of items) if (word === name || aliases.includes(word)) return name;
  return null;
}

// 'placed', 'already' (on the sill or on its way), or 'missing' (no such
// item, or not the visitor's yet: the same answer, so rewards stay secret).
export function putOnSill(name) {
  const item = items.get(name);
  if (!item || !item.hooks.available()) return 'missing';
  if (isOnSill(name) || item.hooks.busy()) return 'already';
  return item.hooks.put() === false ? 'already' : 'placed';
}

// 'removed', 'absent' (not on the sill), or 'busy' (in use right now).
export function takeOffSill(name) {
  const item = items.get(name);
  if (!item || !isOnSill(name)) return 'absent';   // isOnSill() follows the rewards first
  if (item.hooks.busy()) return 'busy';
  item.hooks.take();
  markOffSill(name);
  return 'removed';
}
