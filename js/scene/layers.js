// layers.js — the scene, back to front, in the manifest's draw_order.
// To add a scene element: write its file, import it, and add one line here.
// Achievement rewards are ordinary elements that draw nothing until earned.
// Exports: buildLayers(assets, { weather, timeOfDay, board }) -> list of scene elements
//   board: { layout, images, popup } for the achievement board (see board.js)

import { createBackground } from './background.js';
import { createSky } from './sky.js';
import { createAurora } from './aurora.js';
import { createStars } from './stars.js';
import { createShootingStars } from './shootingstars.js';
import { createClouds } from './clouds.js';
import { createFarBird } from './farbird.js';
import { createWaterfall } from './waterfall.js';
import { createPondBank } from './pondbank.js';
import { createRainbow } from './rainbow.js';
import { createSasquatch } from './sasquatch.js';
import { createDeer } from './deer.js';
import { createNearForest } from './nearforest.js';
import { createTreeSnow } from './treesnow.js';
import { createTreetops } from './treetops.js';
import { createBird } from './bird.js';
import { createPrecipitation } from './precipitation.js';
import { createWind } from './wind.js';
import { createWindowFrame } from './windowframe.js';
import { createBoard } from './board.js';
import { createMug } from './mug.js';
import { createTrophy } from './trophy.js';
import { createFolder } from './folder.js';
import { createCigarette } from './cigarette.js';

export function buildLayers(assets, { weather, timeOfDay, board }) {
  const mug = createMug(assets);
  const deer = createDeer(assets, { weather });
  const treeSnow = createTreeSnow(assets, { weather });
  return [
    createBackground(assets),
    treeSnow.far,                     // snow on the hill forest baked into the background, while it snows
    createSky(assets, [               // everything in here is clipped to the sky
      // ── SUN SLOT ── a sun that moves across the sky goes here, first, so it
      //    sits behind the stars and clouds and sets behind the mountains.
      createAurora(assets, { timeOfDay }),         // under the stars
      createStars(assets, { timeOfDay }),          // and the constellation
      createShootingStars(assets, { timeOfDay }),
      createClouds(assets),
      createFarBird(assets),
    ]),
    createWaterfall(assets),
    createPondBank(assets),           // over the water it repaints, so the deer stands on land
    deer.far,                         // the deer on the clifftop, behind the trees left of the falls
    createRainbow(assets, { weather }),            // after the falls, before the trees
    createSasquatch(assets),
    deer,                             // the deer at the pool, behind the near forest like the sasquatch
    createNearForest(assets),
    treeSnow,                         // snow on the front trees, at the same stage as the far ones
    createTreetops(assets),
    createBird(assets),
    createPrecipitation(assets, weather),
    createWind(assets),
    createWindowFrame(assets),
    createBoard(assets, board),       // hangs on the right-hand log; click it for the achievements
    // ── sill items ──
    mug,
    createTrophy(assets),
    createFolder(assets),             // `whoami`; click it to open
    createCigarette(assets),          // easter egg; the smoking is drawn over everything
    mug.overlay,                      // a sip from the mug, over everything
  ];
}

// Every element's `events` merged into one { name: trigger } table.
export function collectEvents(layers) {
  return Object.assign({}, ...layers.map((layer) => layer.events ?? {}));
}

// Every element's `running` merged into one { name: () => boolean } table:
// whether that event's visit is still on, for the scheduler's skipWhile.
export function collectRunning(layers) {
  return Object.assign({}, ...layers.map((layer) => layer.running ?? {}));
}
