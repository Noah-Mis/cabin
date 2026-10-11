// crossing.js — one sprite sliding sideways across the window opening.
// Shared by the bird, the far bird and the wind, which differ only in sprite,
// speed and whether they bob. Position is "start + whole pixels travelled",
// so movement is always in clean 1-pixel steps.
// Exports: createCrossing(sprite, options)
//            -> { update, draw(ctx, time, sheet?), done, position, direction, contains }
//            options: { x, y, direction (+1 right, -1 left), speedPxPerSec,
//                       bobAmplitudePx, bobRadPerSec, opening }
//          entryX(direction, sprite, opening) -> a start x just off-screen

export function createCrossing(sprite, options) {
  const { x, y, direction, speedPxPerSec, opening } = options;
  const bobAmplitudePx = options.bobAmplitudePx ?? 0;
  const bobRadPerSec = options.bobRadPerSec ?? 0;
  let elapsedMs = 0;

  function position() {
    const travelled = Math.floor(speedPxPerSec * elapsedMs / 1000);
    const bob = Math.round(bobAmplitudePx * Math.sin(bobRadPerSec * elapsedMs / 1000));
    return { x: x + direction * travelled, y: y + bob };
  }

  // Finished once a one-shot animation ends or the sprite has left the opening.
  function done() {
    if (sprite.isFinished(elapsedMs)) return true;
    const p = position();
    const pastRight = direction > 0 && p.x - sprite.width > opening.x + opening.w;
    const pastLeft = direction < 0 && p.x + sprite.width < opening.x;
    return pastRight || pastLeft;
  }

  return {
    update(dtMs) { elapsedMs += dtMs; },
    // `sheet` swaps in another sheet of the same size and timing (the golden
    // bird); it defaults to the crossing's own.
    draw(ctx, time, sheet = sprite) {
      const p = position();
      sheet.draw(ctx, time, sheet.frameAt(elapsedMs), p.x, p.y, direction < 0);
    },
    done,
    position,
    direction,
    // Whether art pixel (px, py) is on it right now, with some padding.
    contains: (px, py, padding) => {
      const p = position();
      return sprite.contains(px, py, p.x, p.y, direction < 0, padding);
    },
  };
}

// Where a crossing should start so it enters from just outside the opening.
export function entryX(direction, sprite, opening) {
  return direction > 0 ? opening.x - sprite.width : opening.x + opening.w + sprite.width;
}
