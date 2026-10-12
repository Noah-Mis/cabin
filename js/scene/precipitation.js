// precipitation.js — rain or snow, a seamless tile repeated over the canvas.
// Which one (if any) comes from the weather module. It doesn't switch on or
// off all at once: from a clear sky it starts light and builds up over
// config.precipitation.rampUpSec, and thins out again before it clears.
// Rain gets heavier a drop at a time. The whole pattern moves by the same
// step every frame, so each drop keeps to its own line through the tile;
// lines join one by one and a drop never blinks out halfway down. Snowflakes
// drift and change shape from frame to frame, so snow fades instead.
// A page that opens with rain or snow already falling (test mode) shows it
// at full strength straight away.
// Exports: createPrecipitation(assets, weather) -> scene element

import { config } from '../config.js';
import { createSprite } from '../sprite.js';

export function createPrecipitation(assets, weather) {
  const [width, height] = assets.manifest.canvas;
  const { rampUpSec, rampDownSec, lightShare } = config.precipitation;
  // Weather names that have a sheet of the same name in the manifest.
  const sprites = {
    rain: createSprite(assets.animation('rain')),
    snow: createSprite(assets.animation('snow')),
  };
  const drops = dropLines(assets.animation('rain'));
  const tile = document.createElement('canvas');
  tile.width = sprites.rain.width;
  tile.height = sprites.rain.height;
  const tileCtx = tile.getContext('2d');

  let elapsedMs = 0;
  let shown;       // the sheet being drawn ('rain', 'snow' or null); undefined before the first frame
  let level = 0;   // how far it has built up, 0-1

  const wanted = () => (sprites[weather.get()] ? weather.get() : null);
  function settle() {
    if (shown !== undefined) return;
    shown = wanted();
    level = shown ? 1 : 0;
  }

  // Builds up while the weather matches; otherwise thins out, and only once
  // it is gone does the next one (if any) start.
  function update(dtMs) {
    settle();
    elapsedMs += dtMs;
    const target = wanted();
    if (shown && shown === target) level = Math.min(1, level + dtMs / 1000 / rampUpSec);
    else if (shown) {
      level -= dtMs / 1000 / rampDownSec;
      if (level <= 0) { shown = null; level = 0; }
    }
    if (!shown && target) { shown = target; level = 0; }
  }

  function draw(ctx, time) {
    settle();
    if (!shown) return;   // clear skies
    const sprite = sprites[shown];
    const frame = sprite.frameAt(elapsedMs);
    const share = level >= 1 ? 1 : lightShare + (1 - lightShare) * level;
    let source = null;   // a tile to repeat, when only some of the drops show
    if (share < 1 && shown === 'rain') {
      tileCtx.clearRect(0, 0, tile.width, tile.height);
      sprite.draw(tileCtx, time, frame, 0, 0);
      tileCtx.globalCompositeOperation = 'destination-in';
      tileCtx.drawImage(drops.mask(share), frame * tile.width, 0, tile.width, tile.height, 0, 0, tile.width, tile.height);
      tileCtx.globalCompositeOperation = 'source-over';
      source = tile;
    } else if (share < 1) {
      ctx.globalAlpha = share;
    }
    for (let y = 0; y < height; y += sprite.height) {
      for (let x = 0; x < width; x += sprite.width) {
        if (source) ctx.drawImage(source, x, y);
        else sprite.draw(ctx, time, frame, x, y);
      }
    }
  }

  return { update, draw };
}

// The lines the rain falls along, worked out from the sheet. Every frame is
// the one before moved by the same step (dx, dy), so a drop stays on the line
// where x * dy - y * dx (wrapped to the tile) is constant, even as it wraps
// round the tile. Neighbouring lit lines are one drop (or a few, which then
// come and go together). Returns { mask(share) }: a sheet-sized mask with
// that share of the drops, the same drops on every frame. The drops join in
// a fixed, spread-out order. The shape is the same at every time of day, so
// the day sheet stands for all.
function dropLines(animation) {
  const { frame_w: w, frame_h: h, frames } = animation.info;
  const sheet = document.createElement('canvas');
  sheet.width = w * frames;
  sheet.height = h;
  const sheetCtx = sheet.getContext('2d', { willReadFrequently: true });
  sheetCtx.drawImage(animation.imageFor('day'), 0, 0);
  const alpha = sheetCtx.getImageData(0, 0, sheet.width, h).data;
  const lit = (f) => {
    const points = [];
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) if (alpha[(y * sheet.width + f * w + x) * 4 + 3] > 0) points.push([x, y]);
    }
    return points;
  };

  // The step from frame 0 to frame 1: the offset that lines up the most pixels.
  const votes = new Map();
  const next = new Set(lit(1 % frames).map(([x, y]) => y * w + x));
  for (const [x, y] of lit(0)) {
    for (const key of next) {
      const step = `${(key % w - x + w) % w},${(Math.floor(key / w) - y + h) % h}`;
      votes.set(step, (votes.get(step) ?? 0) + 1);
    }
  }
  const [dx, dy] = [...votes].reduce((best, vote) => (vote[1] > best[1] ? vote : best))[0].split(',').map(Number);
  const g = gcd(dx, dy);   // the step's direction in lowest terms, or lines would share a number
  const lineOf = (x, y) => (((x * (dy / g) - y * (dx / g)) % w) + w) % w;

  // Runs of neighbouring lit lines are one drop each.
  const used = new Array(w).fill(false);
  for (let f = 0; f < frames; f++) for (const [x, y] of lit(f)) used[lineOf(x, y)] = true;
  const dropOfLine = new Array(w).fill(-1);
  const start = used.indexOf(false);   // begin in a gap, so a run that wraps stays whole
  let count = 0;
  for (let i = 1; i <= w; i++) {
    const line = (start + i) % w;
    if (!used[line]) continue;
    if (!used[(line - 1 + w) % w]) count += 1;
    dropOfLine[line] = count - 1;
  }
  // The order drops join in: spread evenly around the tile (golden ratio).
  const order = Array.from({ length: count }, (_, drop) => drop)
    .sort((a, b) => ((a * 0.618034) % 1) - ((b * 0.618034) % 1));
  const joinsAt = new Array(count);
  order.forEach((drop, i) => { joinsAt[drop] = i; });

  const masks = new Map();   // number of drops showing -> mask canvas
  return {
    mask(share) {
      const showing = Math.max(1, Math.ceil(share * count));
      if (!masks.has(showing)) {
        const mask = document.createElement('canvas');
        mask.width = sheet.width;
        mask.height = h;
        const maskCtx = mask.getContext('2d');
        const image = maskCtx.createImageData(sheet.width, h);
        for (let f = 0; f < frames; f++) {
          for (const [x, y] of lit(f)) {
            if (joinsAt[dropOfLine[lineOf(x, y)]] < showing) image.data[(y * sheet.width + f * w + x) * 4 + 3] = 255;
          }
        }
        maskCtx.putImageData(image, 0, 0);
        masks.set(showing, mask);
      }
      return masks.get(showing);
    },
  };
}

function gcd(a, b) {
  return b === 0 ? a : gcd(b, a % b);
}
