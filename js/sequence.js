// sequence.js — plays a list of manifest sequence steps back to back.
// Each step is one of:
//   { play: name }                         the animation once
//   { loop: name, times: n }               the animation n times over
//   { play: name, while_looping: other }   `other` loops underneath while `name` plays
// Exports: createSequence(assets, steps) -> { durationMs, stepAt(ms), draw(ctx, time, ms) }

import { createSprite } from './sprite.js';

export function createSequence(assets, steps) {
  const timeline = [];
  let startMs = 0;
  for (const step of steps) {
    const sprite = placedSprite(assets, step.play ?? step.loop);
    const durationMs = sprite.durationMs * (step.times ?? 1);
    const under = step.while_looping ? placedSprite(assets, step.while_looping) : null;
    timeline.push({ step, sprite, under, startMs, endMs: startMs + durationMs });
    startMs += durationMs;
  }

  function entryAt(ms) {
    return timeline.find((entry) => ms >= entry.startMs && ms < entry.endMs) ?? null;
  }

  return {
    durationMs: startMs,
    // The manifest step playing at `ms`, or null before/after the sequence.
    stepAt: (ms) => entryAt(ms)?.step ?? null,
    draw(ctx, time, ms) {
      const entry = entryAt(ms);
      if (!entry) return;
      const localMs = ms - entry.startMs;
      entry.under?.draw(ctx, time, localMs);
      entry.sprite.draw(ctx, time, localMs);
    },
  };
}

// A sprite that already knows its manifest placement.
function placedSprite(assets, name) {
  const animation = assets.animation(name);
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  return {
    durationMs: sprite.durationMs,
    draw: (ctx, time, ms) => sprite.draw(ctx, time, sprite.frameAt(ms), x, y),
  };
}
