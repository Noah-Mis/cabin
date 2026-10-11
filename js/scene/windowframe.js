// windowframe.js — the oak window and log wall, over everything outdoors.
// The manifest's "window" entry lists its files: one for morning, day and
// afternoon, and a dimmer, moonlit one for night, cross-faded like the rest.
// Exports: createWindowFrame(assets) -> scene element

export function createWindowFrame(assets) {
  const frame = assets.variants(assets.manifest.window.files);
  return {
    draw(ctx, time) { ctx.drawImage(frame.imageFor(time), 0, 0); },
  };
}
