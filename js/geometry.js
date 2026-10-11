// geometry.js — small shape tests shared by the clickable scene elements.
// Exports: inRect(x, y, { x, y, w, h }), withinRadius(x, y, cx, cy, radius)

export function inRect(x, y, rect) {
  return x >= rect.x && x < rect.x + rect.w && y >= rect.y && y < rect.y + rect.h;
}

export function withinRadius(x, y, cx, cy, radius) {
  return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2;
}
