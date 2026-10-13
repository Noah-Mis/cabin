// terrarium-tools.js — the Pot tab's hands-on half (anim/terrarium/
// terrarium_tools_plan.md): a rail of tools along the bottom of the tab — the
// watering can, the shears, the basket — that you pick up and carry to the
// pot, and, while the pot is empty, a tray of your seeds in their place.
// Only tools that would do something are on the rail, packed left.
//
// One state machine serves dragging, click-to-equip, touch and the keyboard:
//   IDLE    --press a slot-->             HOLDING (its slot shows empty)
//   HOLDING --release over the pot-->     USING
//           --release elsewhere, moved <= 3px-->  stays HOLDING (click to equip)
//           --release elsewhere, moved > 3px-->   IDLE (back to the rail)
//           --press its own slot again / Escape / tab change / close-->  IDLE
//   USING   input is locked while a short animation plays; the state
//           changes on its key frame (the soil darkens with the water
//           meter), then a status line shows for a moment.
// Keyboard: Tab cycles the slots and the pot, Enter or Space picks up or
// uses, Escape puts down. The held thing parks over the focused target.
// The hint line teaches each step once (terrarium.learnHint): "pick up a
// tool" until something is first picked up, "drag to the pot / let go to
// water" until something is first used on the pot. After that it is blank
// unless there is news (no seeds left); the outline keeps showing the way.
// Every position is panel-local, as in the plan.
// Exports: createTools({ art, terrarium, draw }) -> {
//   drawStrip / drawUsing / drawHeld(ctx, time[, colours]), target() -> null | 'held' | 'over',
//   pulse() -> 0..1 (for the pot's outline while something is carried),
//   hideTop() (the picked bloom or crown is off the stem), shownPot() (the pot
//   to draw: during a harvest, the picked plant until the animation ends),
//   status() (a line to show instead of the plant's, or null), hint(), update(dtMs),
//   down / move / up(x, y), leave(), cursor(x, y) -> CSS cursor, key(event) -> handled,
//   drop(), reset(), busy(), holding(), onDiscover(fn) }
//   draw: the journal's helpers { frame, text, plantTop(pot), plantCrown(pot) }

import { config } from './config.js';
import { inRect } from './geometry.js';
import { SPECIES, speciesIndex } from './terrarium-species.js';

const settings = config.terrarium;
const CAN = 0, SHEARS = 1, BASKET = 2;
const IDLE = 0, HELD = 1, ACTIVE = 2;   // tool sheet columns
const FX = { droplets: 0, clippings: 1, sparkle: 2 };
const SLOT_REST = 0, SLOT_HOVER = 1;
const DRAG_PX = 3;              // a press that moved further is a drag
const FX_MS = 120;              // per effect frame
const FLASH_MS = 2000;          // a status line after an action
const TRAY_SLOTS = 6;
const POT_RECT = { x: 12, y: 54, w: 48, h: 40 };
const VERBS = { [CAN]: 'water', [SHEARS]: 'trim', [BASKET]: 'harvest' };
const PULSE_MS = 900;           // one beat of the pot's outline while something is carried
// The harvest (terrarium_tools_plan.md §5): the basket waits under the bloom,
// the bloom comes off and falls into it as the species' own token, which then
// sits behind the rim. Phase ends, in ms from the start.
const PICK = { settle: 500, fall: 760, land: 920, sparkle: 1320, end: 2020 };
const DOING = { [CAN]: 'Watering...', [SHEARS]: 'Trimming...', [BASKET]: 'Harvesting...' };

export function createTools({ art, terrarium, draw: helpers }) {
  const toolsInfo = art.tools.info;
  const { rail, tray } = toolsInfo;
  const railSize = art.slot_lg.info.frame_w;
  // Each tool's offset in its rail slot that centres its opaque pixels.
  const centring = (() => {
    const { frame_w: w, frame_h: h } = toolsInfo;
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const cx = c.getContext('2d', { willReadFrequently: true });
    return [CAN, SHEARS, BASKET].map((tool) => {
      cx.clearRect(0, 0, w, h);
      cx.drawImage(art.tools.imageFor('day'), IDLE * w, tool * h, w, h, 0, 0, w, h);
      const alpha = cx.getImageData(0, 0, w, h).data;
      let x0 = w, x1 = -1, y0 = h, y1 = -1;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          if (!alpha[(y * w + x) * 4 + 3]) continue;
          x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
        }
      }
      return { x: Math.floor((railSize - (x1 - x0 + 1)) / 2) - x0, y: Math.floor((railSize - (y1 - y0 + 1)) / 2) - y0 };
    });
  })();
  const [pourX, pourY] = toolsInfo.pour_at;

  let held = null;     // { kind: 'tool', tool } | { kind: 'seed', id }
  let press = null;    // { x, y, moved, slot } for the gesture in progress
  let using = null;    // { item, ms, applied, time, ...animation }
  let mouse = null;    // panel-local, while over the canvas
  let focus = null;    // keyboard: the key of a target, or null
  let page = 0;        // the tray's page, once there are more than six kinds
  let flashes = [];    // [{ text, ms }] shown one after another
  let wasDead = false;
  let clockMs = 0;     // for the pulse
  let discovered = () => {};

  // ── what's on the strip ──
  function enabledTools(pot) {
    if (!pot) return [];
    const list = [];
    if (!pot.dead) list.push(CAN);
    if (terrarium.needsTrim(pot)) list.push(SHEARS);   // only once it has wilted: see terrarium.js
    if (pot.dead || pot.growth >= 1) list.push(BASKET);
    return list;
  }

  // The strip's slots this frame: { key, rect, item } left to right.
  function slots() {
    const pot = terrarium.get().pot;
    if (pot) {
      return enabledTools(pot).map((tool, i) => ({
        key: `tool${tool}`, rect: { x: rail.x[i], y: rail.y, w: railSize, h: railSize }, item: { kind: 'tool', tool },
      }));
    }
    // The tray: the seeds you own, in species order (as on the Seeds tab).
    const owned = SPECIES.filter((s) => terrarium.count(s.id) > 0).map((s) => s.id);
    const perPage = owned.length > TRAY_SLOTS ? TRAY_SLOTS - 1 : TRAY_SLOTS;
    const pages = Math.max(1, Math.ceil(owned.length / perPage));
    page %= pages;
    const shown = owned.slice(page * perPage, page * perPage + perPage);
    const list = shown.map((id, i) => ({ key: `seed:${id}`, rect: slotRect(tray.x + i * tray.step), item: { kind: 'seed', id } }));
    if (pages > 1) list.push({ key: 'pager', rect: slotRect(tray.x + perPage * tray.step), item: { kind: 'pager' } });
    return list;
  }
  const slotRect = (x) => ({ x, y: tray.y, w: 16, h: 16 });   // a tray slot
  const keyOf = (item) => (item.kind === 'tool' ? `tool${item.tool}` : `seed:${item.id}`);

  // Keyboard targets: the slots, then the pot.
  function targets() {
    return [...slots(), { key: 'pot', rect: POT_RECT, item: { kind: 'pot' } }];
  }

  // ── actions ──
  function pickUp(item) {
    if (item.kind === 'pager') {
      page += 1;
      return;
    }
    held = held && keyOf(held) === keyOf(item) ? null : item;   // the same slot again puts it back
    if (held) terrarium.learnHint('pot-pickup');
  }

  function drop() {
    held = null;
    press = null;
  }

  // Starts the held thing's animation on the pot; the state changes on its
  // key frame (see update).
  function use() {
    if (!held || using) return;
    const pot = terrarium.get().pot;
    if (held.kind === 'seed' && pot) return drop();
    if (held.kind === 'tool' && !enabledTools(pot).includes(held.tool)) return drop();
    const top = pot ? helpers.plantTop(pot) : POT_RECT.y;
    using = { item: held, ms: 0, applied: false, time: null, top, height: POT_RECT.y + 15 - top };
    if (held.kind === 'tool' && held.tool === BASKET) using.pick = pickPlan(pot);
    terrarium.learnHint('pot-use');
    if (held.kind === 'seed') terrarium.learnHint('seeds-plant');   // the Seeds tab's pointer here
    held = null;
    press = null;
    focus = null;
  }

  // Each animation: how long it lasts and when its change lands.
  const TIMELINE = {
    [CAN]: { total: 600, apply: 120 + 2 * FX_MS },          // the third droplet frame
    [SHEARS]: { total: 500, apply: 100 + 3 * FX_MS },       // once the clippings have fallen
    [BASKET]: { total: PICK.end, apply: PICK.land },        // the seeds count once it lands; the stem clears at the end
    clear: { total: 700, apply: 700 },                      // a withered plant: the basket, then an empty pot
    seed: { total: 520, apply: 150 },                       // the seed lands, then a sparkle
  };
  const timeline = (item, pick) => TIMELINE[item.kind === 'seed' ? 'seed' : item.tool === BASKET && !pick?.token ? 'clear' : item.tool];

  // Where a harvest happens: the basket on the stem just under the bloom (or
  // crown), and the token's fall from the bloom's centre into the basket.
  // A withered plant has no token: the basket just clears it.
  function pickPlan(pot) {
    const crown = helpers.plantCrown(pot);
    const basket = { x: crown.stemTileX, y: crown.y + crown.h + 2 };
    const [ax, ay] = art.harvest.info.basket_anchor;
    const half = art.harvest.info.frame_w / 2;
    return {
      pot: structuredClone(pot),   // drawn until the end, so the stem stays while the flower falls
      basket,
      token: pot.dead ? null : speciesIndex(pot.species),
      from: { x: crown.x + crown.w / 2 - half, y: crown.y + crown.h / 2 - half },
      to: { x: basket.x + ax, y: basket.y + ay },
      bloom: { x: crown.x + crown.w / 2 - 8, y: crown.y + crown.h / 2 - 8 },   // the sparkle on it
    };
  }

  function apply(item) {
    const flash = (...lines) => { flashes = lines.filter(Boolean).map((text) => ({ text, ms: FLASH_MS })); };
    if (item.kind === 'seed') {
      const result = terrarium.plant(item.id);
      if (result.ok) flash(fit((name) => `Planted ${name}`, item.id));
      return;
    }
    if (item.tool === CAN) {
      const result = terrarium.water();
      if (result.ok) flash(result.saturated ? 'Saturated!' : 'Watered');
    } else if (item.tool === SHEARS) {
      terrarium.learnHint('pot-trim');
      if (terrarium.trim().ok) flash('Trimmed');
    } else {
      const result = terrarium.harvest();
      if (!result.ok) return;
      if (result.cleared) return flash('Pot cleared');
      if (result.discovered) discovered();
      flash(fit((name) => `+${result.seeds} ${name} seed${result.seeds > 1 ? 's' : ''}`, result.species),
        result.discovered && 'New species found!');
    }
  }

  function update(dtMs) {
    clockMs += dtMs;
    const pot = terrarium.get().pot;
    // A plant that withers while you hold something: put it down, say so.
    const dead = !!pot?.dead;
    if (dead && !wasDead && (held || press)) {
      drop();
      flashes = [{ text: 'Withered.', ms: FLASH_MS }];
    }
    wasDead = dead;
    // A tool that stopped making sense (the terminal harvested, say) goes back.
    if (held?.kind === 'tool' && !enabledTools(pot).includes(held.tool)) drop();
    if (held?.kind === 'seed' && (pot || !terrarium.count(held.id))) drop();

    if (using) {
      using.ms += dtMs;
      const { total, apply: at } = timeline(using.item, using.pick);
      if (!using.applied && using.ms >= at) {
        using.applied = true;
        apply(using.item);
      }
      if (using.ms >= total) using = null;
    } else if (flashes.length) {
      flashes[0].ms -= dtMs;
      if (flashes[0].ms <= 0) flashes.shift();
    }
  }

  // ── pointer ──
  function down(x, y) {
    focus = null;
    if (using) return;
    const slot = slots().find((s) => inRect(x, y, s.rect));
    press = { x, y, moved: false, slot: slot?.key ?? null };
    if (slot) pickUp(slot.item);
  }

  function move(x, y) {
    mouse = { x, y };
    if (press && Math.hypot(x - press.x, y - press.y) > DRAG_PX) press.moved = true;
  }

  function up(x, y) {
    if (!press) return;
    const gesture = press;
    press = null;
    if (!held || using) return;
    if (overDrop(x, y)) return use();
    if (gesture.moved) drop();   // a drag let go off the pot: back to the rail
  }

  // The pointer left the canvas: a drag in progress is an invalid release.
  function leave() {
    mouse = null;
    if (press?.moved) drop();
    press = null;
  }

  // Where a carried thing can be let go: the pot, and the plant above it.
  function dropRect() {
    const pot = terrarium.get().pot;
    const top = pot ? Math.min(POT_RECT.y, helpers.plantTop(pot)) : POT_RECT.y;
    return { x: POT_RECT.x, y: top, w: POT_RECT.w, h: POT_RECT.y + POT_RECT.h - top };
  }
  const overDrop = (x, y) => inRect(x, y, dropRect());

  // A closed hand while dragging, a hand over the pot when a click would use
  // what is held, an open hand over something to pick up.
  function cursor(x, y) {
    if (using) return '';
    if (held && press) return 'grabbing';
    if (held && overDrop(x, y)) return 'pointer';
    return slots().some((s) => inRect(x, y, s.rect)) ? 'grab' : '';
  }

  // ── keyboard ──
  function key(event) {
    if (using) return event.key === 'Tab' || event.key === 'Enter' || event.key === ' ';
    if (event.key === 'Tab') {
      const list = targets();
      const at = list.findIndex((t) => t.key === focus);
      const step = event.shiftKey ? -1 : 1;
      const next = at < 0 ? (step > 0 ? 0 : list.length - 1) : (at + step + list.length) % list.length;
      focus = list[next].key;
      return true;
    }
    if ((event.key === 'Enter' || event.key === ' ') && focus) {
      const target = targets().find((t) => t.key === focus);
      if (!target) return (focus = null), false;
      if (target.item.kind === 'pot') use();
      else pickUp(target.item);
      return true;
    }
    if (event.key === 'Escape' && held) {   // put it down; with nothing in hand Escape closes the journal
      drop();
      return true;
    }
    return false;
  }

  // ── drawing ──
  function toolFrame(ctx, time, tool, state, x, y) {
    const { frame_w: w, frame_h: h } = toolsInfo;
    ctx.drawImage(art.tools.imageFor(time), state * w, tool * h, w, h, x, y, w, h);
  }
  function fxFrame(ctx, time, row, frame, x, y) {
    const { frame_w: w, frame_h: h } = art.fx.info;
    ctx.drawImage(art.fx.imageFor(time), frame * w, row * h, w, h, x, y, w, h);
  }
  const fxAt = (ms, from) => Math.max(0, Math.min(2, Math.floor((ms - from) / FX_MS)));

  // The pot as a target: null with nothing in hand, 'held' while something
  // is carried (the pot's outline pulses: bring it here), 'over' once it is
  // over the pot or the plant (solid outline and the glow: let go here).
  function target() {
    if (!held || using) return null;
    if (focus) return focus === 'pot' ? 'over' : 'held';   // the keyboard's target wins over where the mouse was left
    return mouse && overDrop(mouse.x, mouse.y) ? 'over' : 'held';
  }
  const pulse = () => 0.5 - 0.5 * Math.cos((clockMs % PULSE_MS) / PULSE_MS * 2 * Math.PI);

  // The picked bloom (or crown) is off the stem once it starts to fall.
  function hideTop() {
    return !!using?.pick && using.pick.token !== null && using.ms >= PICK.settle;
  }
  // During a harvest the plant stays in the pot until the animation ends,
  // though the state has already emptied it.
  function shownPot() {
    return using?.pick?.token != null ? using.pick.pot : terrarium.get().pot;
  }

  function drawStrip(ctx, time, colours) {
    for (const slot of slots()) {
      const lit = !using && ((mouse && inRect(mouse.x, mouse.y, slot.rect)) || focus === slot.key);
      const isTool = slot.item.kind === 'tool';
      helpers.frame(ctx, time, isTool ? 'slot_lg' : 'slot_sm', lit ? SLOT_HOVER : SLOT_REST, slot.rect.x, slot.rect.y);
      const { item, rect } = slot;
      const away = (held && keyOf(held) === slot.key) || (using && keyOf(using.item) === slot.key);
      if (item.kind === 'pager') {
        helpers.text(ctx, '>', rect.x + 7, rect.y + 5, colours.text);
      } else if (item.kind === 'tool') {
        const at = centring[item.tool];
        if (!away) toolFrame(ctx, using ? using.time ?? time : time, item.tool, IDLE, rect.x + at.x, rect.y + at.y);
      } else {
        const n = terrarium.count(item.id) - (away ? 1 : 0);
        if (n > 0) {
          helpers.frame(ctx, time, 'seeds', speciesIndex(item.id), rect.x + 4, rect.y + 4);
          helpers.text(ctx, n, rect.x + 12 - (String(n).length - 1) * 4, rect.y + 10, colours.text);
        }
      }
    }
  }

  // The animation of the thing in use, over the pot.
  function drawUsing(ctx, time) {
    if (!using) return;
    using.time ??= time;              // finish on the sprites it started with
    const t = using.time;
    const { ms, item, top, height } = using;
    if (item.kind === 'seed') {
      const y = Math.min(1, ms / 150);
      if (ms < 150) helpers.frame(ctx, t, 'seeds', speciesIndex(item.id), 32, Math.round(52 + y * 10));
      else fxFrame(ctx, t, FX.sparkle, fxAt(ms, 150), 28, 57);
      return;
    }
    if (item.tool === CAN) {
      toolFrame(ctx, t, CAN, ACTIVE, pourX, pourY);
      if (ms >= 120) fxFrame(ctx, t, FX.droplets, fxAt(ms, 120), 44, 48);
    } else if (item.tool === SHEARS) {
      const y = top + Math.round(height / 3) - 8;
      toolFrame(ctx, t, SHEARS, ACTIVE, 40, y);
      if (ms >= 100) fxFrame(ctx, t, FX.clippings, fxAt(ms, 100), 30, y + 4);
    } else {
      drawPick(ctx, t, ms, using.pick);
    }
  }

  // The harvest, phase by phase (PICK). The token falls in front of the
  // basket, then lands BEHIND it, so the rim hides its stem and only the head
  // shows in the opening: that is what makes it read as in the basket.
  function drawPick(ctx, t, ms, pick) {
    const { basket } = pick;
    if (pick.token === null) {   // a withered plant: just the basket
      toolFrame(ctx, t, BASKET, HELD, basket.x, basket.y);
      return;
    }
    const landed = ms >= PICK.fall;
    const settled = ms >= PICK.sparkle ? 1 : 0;   // the basket sinks 1px as it rests
    const token = (x, y) => {
      const { frame_w: w, frame_h: h } = art.harvest.info;
      ctx.drawImage(art.harvest.imageFor(t), pick.token * w, 0, w, h, Math.round(x), Math.round(y), w, h);
    };
    if (ms < PICK.settle) {
      toolFrame(ctx, t, BASKET, HELD, basket.x, basket.y);
      fxFrame(ctx, t, FX.sparkle, 0, pick.bloom.x, pick.bloom.y);   // a shimmer on the ripe flower
    } else if (!landed) {
      const f = (ms - PICK.settle) / (PICK.fall - PICK.settle);
      const e = f * f;   // falling: it speeds up
      toolFrame(ctx, t, BASKET, HELD, basket.x, basket.y);
      token(pick.from.x + (pick.to.x - pick.from.x) * e, pick.from.y + (pick.to.y - pick.from.y) * e);
    } else {
      token(pick.to.x, pick.to.y + settled);
      toolFrame(ctx, t, BASKET, ACTIVE, basket.x, basket.y + settled);
      if (ms < PICK.sparkle) fxFrame(ctx, t, FX.sparkle, ms < PICK.land ? 1 : 2, basket.x, basket.y - 6);
    }
  }

  // The thing in hand: on the pointer, or parked over the focused target.
  function drawHeld(ctx, time) {
    if (!held) return;
    const at = (focus && targets().find((t) => t.key === focus)?.rect) || null;
    const centre = at ? { x: at.x + at.w / 2, y: at.y + (at === POT_RECT ? 8 : at.h / 2) } : mouse;
    if (!centre) {
      // Equipped with no pointer over the canvas: it waits above its slot.
      const home = slots().find((s) => s.key === keyOf(held));
      if (!home) return;
      return drawHeldAt(ctx, time, home.rect.x + 8, home.rect.y - 6);
    }
    drawHeldAt(ctx, time, centre.x, centre.y);
  }
  function drawHeldAt(ctx, time, cx, cy) {
    if (held.kind === 'seed') helpers.frame(ctx, time, 'seeds', speciesIndex(held.id), Math.round(cx - 4), Math.round(cy - 4));
    else toolFrame(ctx, time, held.tool, HELD, Math.round(cx - 8), Math.round(cy - 8));
  }

  function status() {
    if (using?.pick) {
      if (using.pick.token === null) return 'Clearing...';
      if (using.ms < PICK.settle) return 'Ready to pick';
      if (!using.applied) return 'Picking...';
      return flashes[0]?.text ?? null;   // "+2 Bluebell seeds", while it settles
    }
    if (using) return using.item.kind === 'seed' ? 'Planting...' : DOING[using.item.tool];
    return flashes[0]?.text ?? null;
  }

  // What to do next, in words: bring it to the pot, then let go (or click,
  // or press Enter, whichever way it is being carried). Each step only until
  // it has been done once.
  function hint() {
    const pot = terrarium.get().pot;
    const once = (id, text) => (terrarium.hintSeen(id) ? '' : text);
    if (using) return '';   // the status line is saying what is happening
    if (held) {
      const verb = held.kind === 'seed' ? 'plant' : held.tool === BASKET && pot?.dead ? 'clear' : VERBS[held.tool];
      if (focus) return once('pot-use', target() === 'over' ? `Enter to ${verb}` : 'Tab to the pot');
      if (press) return once('pot-use', target() === 'over' ? `Let go to ${verb}` : 'Drag to the pot');
      return once('pot-use', target() === 'over' ? `Click to ${verb}` : 'Click the pot');
    }
    if (!pot && !Object.keys(terrarium.get().seeds).length) return 'No seeds left';
    if (terrarium.needsTrim(pot) && terrarium.hintSeen('pot-pickup')) return once('pot-trim', 'Trim it with shears');
    return once('pot-pickup', pot ? 'Pick up a tool' : 'Pick up a seed');
  }

  return {
    target, pulse, hideTop, shownPot, drawStrip, drawUsing, drawHeld, status, hint, update,
    down, move, up, leave, cursor, key, drop, busy: () => !!using,
    holding: () => !!held,
    reset() { drop(); using = null; flashes = []; focus = null; },
    onDiscover(fn) { discovered = fn; },
  };
}

// A status line names the species in full if that fits beside the pot
// (19 characters), otherwise by its short name.
const STATUS_CHARS = 19;
function fit(line, id) {
  const species = SPECIES[speciesIndex(id)];
  const full = line(species.name);
  return full.length <= STATUS_CHARS ? full : line(species.short ?? species.name);
}
