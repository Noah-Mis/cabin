// pointer.js — lets scene elements react to the mouse. An element opts in by
// having `pointer: { contains(x, y), setHovered(on), click(x, y) }`, with x
// and y in art pixels (the click is converted from screen pixels first). A
// group, like the sky, lists its children's pointers as `pointers`. The
// topmost element under the mouse gets the hover and the click, and the
// cursor becomes a hand over it.
// Exports: trackPointer(canvas, layers)

export function trackPointer(canvas, layers) {
  const targets = layers.flatMap((layer) => [...(layer.pointers ?? []), layer.pointer].filter(Boolean)).reverse();
  let hovered = null;

  // Mouse position in art pixels, whatever the canvas's on-screen scale.
  function artPoint(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: Math.floor((event.clientX - rect.left) * canvas.width / rect.width),
      y: Math.floor((event.clientY - rect.top) * canvas.height / rect.height),
    };
  }

  const targetAt = ({ x, y }) => targets.find((target) => target.contains(x, y)) ?? null;

  function hover(target) {
    if (target === hovered) return;
    hovered?.setHovered(false);
    hovered = target;
    hovered?.setHovered(true);
    canvas.style.cursor = hovered ? 'pointer' : '';
  }

  canvas.addEventListener('pointermove', (event) => hover(targetAt(artPoint(event))));
  canvas.addEventListener('pointerleave', () => hover(null));
  canvas.addEventListener('click', (event) => {
    const point = artPoint(event);
    targetAt(point)?.click(point.x, point.y);
    hover(targetAt(point));   // a click can make something stop being clickable
  });
}
