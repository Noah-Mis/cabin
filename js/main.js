// main.js — starts the site: loads the art, builds the scene, wires up the
// terminal and the event timers, and runs the animation loop.
// Everything is created here and handed to the modules that need it, so no
// module reaches into another.
// Exports: nothing. Exposes window.cabin for inspection and automated tests.

import { config } from './config.js';
import { loadAssets } from './assets.js';
import { fitCanvasToStage } from './display.js';
import { createRenderer } from './renderer.js';
import { createTimeOfDay } from './timeofday.js';
import { createWeather } from './weather.js';
import { createScheduler } from './scheduler.js';
import { createTerminal } from './terminal.js';
import { runCommand, everyDayCommands } from './commands.js';
import { createProgress } from './progress.js';
import { startAchievements, track, resetAchievements, listAchievements, isUnlocked } from './achievements.js';
import { createUnlockSign } from './unlock-sign.js';
import { createBoardPopup } from './board-popup.js';
import { loadBoardArt } from './scene/board.js';
import { startSound, soundLog, soundState, outputLevelDb } from './sound.js';
import { trackPointer } from './pointer.js';
import { buildLayers, collectEvents, collectRunning } from './scene/layers.js';
import { readTestOptions, startTestMode, useReferenceTiming, useTestSettings } from './testmode.js';

async function boot() {
  const canvas = document.getElementById('scene');
  const testOptions = readTestOptions(location.search);
  const debug = new URLSearchParams(location.search).has('debug');
  let app = null;

  const terminal = createTerminal(
    {
      bubble: document.getElementById('bubble'),
      form: document.getElementById('prompt'),
      input: document.getElementById('input'),
    },
    {
      onCommand: (line) => app && runCommand(line, app),
      maxHistory: config.terminal.maxHistory,
    },
  );
  terminal.focus();

  const [assets, boardArt] = await Promise.all([loadAssets(config), loadBoardArt()]);
  if (assets.failures.length) {
    console.error('could not load:', assets.failures.join(', '));
    terminal.print(`some pictures failed to load: ${assets.failures.join(', ')}`, 'error');
  }
  [canvas.width, canvas.height] = assets.manifest.canvas;
  if (testOptions?.referenceTiming) useReferenceTiming(assets.manifest, config.test.referenceMsPerFrame);
  else assets.slowDown(config.animationSlowdown);
  if (testOptions) useTestSettings(config);

  // The window opening down to the bottom of the sill, and the achievement
  // board on the log beside it (with its hover outline), must always be in view.
  const { window_opening: opening, sill_band: sill } = assets.manifest;
  const { board } = boardArt.layout;
  const left = Math.min(opening.x, board.canvas_x - 1);
  const right = Math.max(opening.x + opening.w, board.canvas_x + board.w + 1);
  const display = fitCanvasToStage(canvas, document.getElementById('stage'), {
    keepVisible: { x: left, y: opening.y, w: right - left, h: sill.y1 + 1 - opening.y },
    bottomInset: () => document.getElementById('terminal').offsetHeight,
  });

  // Achievements start before time of day and weather exist, because those
  // report what they show from the moment they are created.
  const achievementData = assets.packManifest(config.achievements.artDir);
  const progress = createProgress({ storageKey: config.achievements.storageKey, version: config.achievements.storageVersion });
  const sign = createUnlockSign(canvas, { manifest: achievementData, openingY: opening.y });
  const boardPopup = createBoardPopup(canvas, {
    bottomInset: () => document.getElementById('terminal').offsetHeight,
    layout: boardArt.layout,
    badges: achievementData.badges,
  });
  startAchievements({
    definitions: achievementData.achievements,
    progress,
    universes: { commandsUsed: everyDayCommands() },
    onUnlock(earned) {
      for (const definition of earned) {
        sign.show(definition);
        terminal.print(`achievement unlocked: ${definition.name}. ${definition.reward}.`);
      }
      if (boardPopup.isShown()) boardPopup.refresh(earned.at(-1).id);   // the board's pins update themselves
    },
  });

  const weather = createWeather(config);
  const timeOfDay = createTimeOfDay(config, testOptions?.time);
  const layers = buildLayers(assets, { weather, timeOfDay, board: { ...boardArt, popup: boardPopup } });
  const events = collectEvents(layers);
  const renderer = createRenderer(canvas, layers);

  trackPointer(canvas, layers);

  // Back to a first visit: no progress, wood terminal, and whatever is on
  // screen right now counts as seen again.
  function resetProgress() {
    resetAchievements();
    sign.clear();
    boardPopup.refresh();
    terminal.setTheme(null);
    track('timesSeen', timeOfDay.current());
    if (weather.get() !== config.defaultWeather) track('weatherSeen', weather.get());
  }

  app = {
    events, timeOfDay, weather, debug, resetProgress,
    print: terminal.print, clearOutput: terminal.clear, setTheme: terminal.setTheme,
    theme: { green: achievementData.terminal_theme_green },
    progressStats: () => ({ stats: progress.stats(), unlocked: progress.unlocked(), saved: progress.persistent() }),
  };
  window.cabin = {
    app, layers, display, run: (line) => runCommand(line, app),
    achievements: { list: listAchievements, isUnlocked },   // read-only, for inspection
    sound: { log: soundLog, state: soundState, levelDb: outputLevelDb },
  };

  function update(dtMs) {
    timeOfDay.update(dtMs);
    for (const layer of layers) layer.update?.(dtMs);
  }
  function render() {
    renderer.render(timeOfDay.view());
  }

  if (testOptions) {
    timeOfDay.set(testOptions.time, { instant: true });
    weather.set(testOptions.weather);
    startTestMode({ update, render, events, canvas, tickMs: config.test.tickMs }, testOptions);
    return;
  }

  startSound(config.sound);   // test mode stays silent
  const scheduler = createScheduler(config.events, events, Math.random, collectRunning(layers));
  window.cabin.scheduler = scheduler;
  terminal.print(config.terminal.greeting);

  let lastFrameMs = performance.now();
  let visibleMs = 0;   // time on the page counts only while the tab is visible
  function frame(nowMs) {
    const dtMs = Math.max(0, Math.min(nowMs - lastFrameMs, config.maxFrameDtMs));
    lastFrameMs = nowMs;
    if (document.visibilityState === 'visible') visibleMs += dtMs;
    for (; visibleMs >= 1000; visibleMs -= 1000) track('secondsOpen', 1);
    update(dtMs);
    scheduler.update(dtMs);
    render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

boot().catch((error) => {
  console.error(error);
  const bubble = document.getElementById('bubble');
  bubble.textContent = `the cabin could not start: ${error.message}`;
  bubble.hidden = false;
});
