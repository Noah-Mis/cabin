// deer.js — the deer's visit. Act one: small and far away, it walks out
// along the clifftop left of the falls, stands, and walks back behind the
// trees. A few seconds out of sight. Act two: closer, it steps out of the
// front trees onto the bank of the pool, drinks, and slips back into the
// trees. It never touches the water: every pixel stays left of the
// forbidden zone in achievements.json, and its feet stay on the bank.
// Reward (cabin_fever): the scheduled `deer` event only does anything once
// earned, in clear weather. Clicking it startles it back into the trees.
//
// One state machine; each state knows how long it lasts and what follows:
//   hidden -> clifftopOut -> clifftopPause -> clifftopBack -> intermission
//          -> approach (with one pause) -> drink -> leave -> hidden
// Rain or snow arriving mid-visit lets the current act finish, then ends it.
//
// Two draw layers: `far` (the clifftop deer and the tree patch that hides
// it) goes behind the rainbow, which would otherwise be cut by that patch;
// the element itself (the deer at the pool) goes where the sasquatch is,
// just before the near forest.
// Exports: createDeer(assets, { weather }) -> scene element with events.deer,
//          running.deer, stage(), pointer, and far (a scene element with a pointer)

import { config } from '../config.js';
import { createSprite, drawnBoxes } from '../sprite.js';
import { randomBetween } from '../random.js';
import { isUnlocked } from '../achievements.js';
import { inRect } from '../geometry.js';

export function createDeer(assets, { weather }) {
  const settings = config.achievements.deer;
  const farAnimation = assets.animation('deer_far');
  const far = part(farAnimation);
  const coverAnimation = assets.animation('far_trees_cover');
  const cover = createSprite(coverAnimation);
  const walk = part(assets.animation('deer_walk'));
  const graze = part(assets.animation('deer_graze'));
  const path = farAnimation.info.placement.path;
  const { start_x: startX, stop_x: stopX, feet_y: feetY } = walk.info.placement.bank;
  const [forbiddenX] = walk.info.placement.forbidden_x;

  // The clifftop walk stops at the last path entry that keeps every pixel of
  // the deer left of the forbidden zone.
  const farRight = Math.max(...far.boxes.map((box) => box.x + box.w - 1)) - far.info.anchor[0];
  const pathStop = path.findLastIndex(([x]) => x + farRight < forbiddenX);

  let visit = null;   // { stage, elapsedMs, ...what that stage needs }

  const between = ([min, max]) => randomBetween(min, max);
  const steps = (ms, info, speed = 1) => Math.floor(ms * speed / info.ms_per_frame);
  // How long a walk of `distance` steps takes, ending with one whole frame
  // on its last step (so a deer walking out of sight is drawn hidden once).
  const walkedMs = (distance, info, speed = 1) => (distance + 1) * info.ms_per_frame / speed;
  const clearSky = () => weather.get() === config.defaultWeather;

  function enter(stage, details = {}) {
    visit = { ...visit, stage, elapsedMs: 0, ...details };
  }

  // options.start: 'pool' skips act one (for testing).
  function arrive({ start } = {}) {
    if (!isUnlocked('cabin_fever') || visit || !clearSky()) return false;
    visit = { startled: false };
    if (start === 'pool') enterApproach();
    else enter('clifftopOut', { from: 0 });
    return true;
  }

  function enterApproach() {
    // One pause, somewhere along the way (not at either end).
    enter('approach', { from: startX, pauseAt: Math.round(randomBetween(startX + 1, stopX - 1)), paused: false });
  }

  function enterDrink() {
    // A short beat, then drinks with brief pauses between: [kind, ms] segments.
    const count = Math.round(between(settings.drinks));
    const segments = [['stand', between(settings.drinkBeatSec) * 1000]];
    for (let i = 0; i < count; i++) {
      if (i > 0) segments.push(['stand', between(settings.drinkPauseSec) * 1000]);
      segments.push(['graze', graze.info.frames * graze.info.ms_per_frame]);
    }
    enter('drink', { segments });
  }

  // Where the near deer is now (approach, pause, drink and leave), in x.
  function nearX() {
    if (visit.stage === 'approach') return Math.min(visit.from + steps(visit.elapsedMs, walk.info), visit.paused ? stopX : visit.pauseAt);
    if (visit.stage === 'pause') return visit.pauseAt;
    if (visit.stage === 'drink') return stopX;
    return Math.max(startX, visit.from - steps(visit.elapsedMs, walk.info, visit.speed));   // leave
  }

  // The clifftop path entry the far deer is on now.
  function farIndex() {
    if (visit.stage === 'clifftopOut') return Math.min(pathStop, visit.from + steps(visit.elapsedMs, far.info));
    if (visit.stage === 'clifftopPause') return pathStop;
    return Math.max(0, visit.from - steps(visit.elapsedMs, far.info, visit.speed));   // clifftopBack
  }

  // How each stage ends, and what follows.
  function advance() {
    const { stage, elapsedMs: ms } = visit;
    if (stage === 'clifftopOut' && ms >= walkedMs(pathStop - visit.from - 1, far.info)) {
      enter('clifftopPause', { ms: between(settings.clifftopPauseSec) * 1000 });
    } else if (stage === 'clifftopPause' && ms >= visit.ms) {
      enter('clifftopBack', { from: pathStop, speed: 1 });
    } else if (stage === 'clifftopBack' && ms >= walkedMs(visit.from, far.info, visit.speed)) {
      if (visit.startled || !clearSky()) visit = null;   // the act is over; so is the visit
      else enter('intermission', { ms: between(settings.intermissionSec) * 1000 });
    } else if (stage === 'intermission' && ms >= visit.ms) {
      if (clearSky()) enterApproach();
      else visit = null;
    } else if (stage === 'approach' && ms >= walkedMs((visit.paused ? stopX : visit.pauseAt) - visit.from, walk.info)) {
      if (visit.paused) enterDrink();
      else enter('pause', { ms: between(settings.approachPauseSec) * 1000 });
    } else if (stage === 'pause' && ms >= visit.ms) {
      enter('approach', { from: visit.pauseAt, paused: true });
    } else if (stage === 'drink' && ms >= visit.segments.reduce((sum, [, segmentMs]) => sum + segmentMs, 0)) {
      enter('leave', { from: stopX, speed: 1 });
    } else if (stage === 'leave' && ms >= walkedMs(visit.from - startX, walk.info, visit.speed)) {
      visit = null;
    }
  }

  // The near deer's sheet, frame, x, and whether it faces left.
  function nearPose() {
    const x = nearX();
    if (visit.stage === 'approach') return [walk, steps(visit.elapsedMs, walk.info) % walk.info.frames, x, false];
    if (visit.stage === 'leave') return [walk, steps(visit.elapsedMs, walk.info, visit.speed) % walk.info.frames, x, true];
    if (visit.stage === 'drink') {
      let t = visit.elapsedMs;
      for (const [kind, ms] of visit.segments) {
        if (t < ms) return [graze, kind === 'graze' ? Math.min(graze.info.frames - 1, steps(t, graze.info)) : 0, x, false];
        t -= ms;
      }
    }
    return [graze, 0, x, false];   // standing: graze frame 0 is the plain standing pose
  }

  function farPose() {
    const [x, y] = path[farIndex()];
    if (visit.stage === 'clifftopPause') return [0, x, y, false];
    const speed = visit.stage === 'clifftopBack' ? visit.speed : 1;
    return [steps(visit.elapsedMs, far.info, speed) % far.info.frames, x, y, visit.stage === 'clifftopBack'];
  }

  const onClifftop = () => visit !== null && visit.stage.startsWith('clifftop');
  const atPool = () => visit !== null && ['approach', 'pause', 'drink', 'leave'].includes(visit.stage);

  // Startled: turn toward the trees and leave at double pace; the visit ends there.
  function startle() {
    if (visit.startled) return;
    if (onClifftop()) enter('clifftopBack', { from: farIndex(), speed: settings.startleSpeedFactor, startled: true });
    else enter('leave', { from: nearX(), speed: settings.startleSpeedFactor, startled: true });
  }

  // Is (px, py) on the drawn part of this frame, give or take the click padding?
  const hit = (p, [frame, ax, ay, mirrored], px, py) => {
    const box = p.boxes[frame];
    if (!box) return false;
    const left = mirrored ? ax - (p.info.frame_w - 1 - p.info.anchor[0]) + (p.info.frame_w - box.x - box.w) : ax - p.info.anchor[0] + box.x;
    const pad = config.achievements.clickPaddingPx;
    return inRect(px, py, { x: left - pad, y: ay - p.info.anchor[1] + box.y - pad, w: box.w + 2 * pad, h: box.h + 2 * pad });
  };

  return {
    update(dtMs) {
      if (!visit) return;
      visit.elapsedMs += dtMs;
      advance();
    },
    draw(ctx, time) {
      if (!atPool()) return;
      const [sheet, frame, x, mirrored] = nearPose();
      sheet.sprite.draw(ctx, time, frame, x, feetY, mirrored);
    },
    events: { deer: arrive },
    running: { deer: () => visit !== null },
    stage: () => visit?.stage ?? 'hidden',
    pointer: {
      contains: (px, py) => {
        if (!atPool()) return false;
        const [sheet, frame, x, mirrored] = nearPose();
        return hit(sheet, [frame, x, feetY, mirrored], px, py);
      },
      setHovered() {},
      click: startle,
    },
    far: {
      draw(ctx, time) {
        if (!onClifftop()) return;
        const [frame, x, y, mirrored] = farPose();
        far.sprite.draw(ctx, time, frame, x, y, mirrored);
        // Only while the far deer is out: it repaints the trees it passes behind.
        cover.draw(ctx, time, 0, coverAnimation.info.placement.x, coverAnimation.info.placement.y);
      },
      pointer: {
        contains: (px, py) => onClifftop() && hit(far, farPose(), px, py),
        setHovered() {},
        click: startle,
      },
    },
  };
}

// A sheet with its sprite, manifest info and per-frame drawn boxes.
function part(animation) {
  return { sprite: createSprite(animation), info: animation.info, boxes: drawnBoxes(animation) };
}
