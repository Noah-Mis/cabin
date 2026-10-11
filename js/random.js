// random.js — small random helpers shared by the events.
// Exports: randomBetween(min, max), randomItem(list), randomDirection()

export function randomBetween(min, max) {
  return min + Math.random() * (max - min);
}

export function randomItem(list) {
  return list[Math.floor(Math.random() * list.length)];
}

// +1 (rightwards) or -1 (leftwards), equally likely.
export function randomDirection() {
  return Math.random() < 0.5 ? 1 : -1;
}
