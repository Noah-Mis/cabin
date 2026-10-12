// commands.js — the terminal's command table and the code that runs a line.
// To add a command, add one entry to `commands`. Each entry gets the words
// after the command name and the app: { events, timeOfDay, weather, print,
// clearOutput, setTheme, resetProgress, debug, theme, terrarium, journal }. Whatever a command
// prints appears together in one speech bubble. Creatures and wind are not
// commands; they only come on their timers.
//
// Flags on an entry:
//   hidden: true          works, but `help` leaves it out
//   available(app)        listed and usable only while this returns true
//   everyCommand: false   doesn't count toward "use every command"
//
// THE "USE EVERY COMMAND" RULE (the power_user achievement): it needs every
// command `help` lists from the start, which is every entry that is not
// hidden, has no `available` test, and isn't marked everyCommand: false.
// So `reset` doesn't count (it would wipe the very progress it completes);
// `sound` doesn't (muting shouldn't be a chore); `theme` doesn't (it only
// appears once the achievement is earned); `badges` no longer does (the board
// by the window replaced it). The hidden sill commands (`ls`, `rm`, `touch`) don't,
// and neither do the terrarium's (all hidden: the pot on the wall opens it). The rule only asks that every listed command
// was used, so retiring a command never sets anyone back: an old mark for it
// is simply ignored. everyDayCommands() below computes the list.
//
// Exports: commands, runCommand(line, app), everyDayCommands()

import { track, isUnlocked, listAchievements, debugSetStat, debugUnlock } from './achievements.js';
import { setMuted, isMuted, soundState, outputLevelDb, soundLog } from './sound.js';
import { sillItems, putAway, findSillItem, putOnSill, takeOffSill } from './sill.js';
import { SPECIES, speciesIndex } from './terrarium-species.js';

export const commands = {
  help: {
    usage: 'help',
    about: 'list the commands',
    run(args, app) {
      const shown = Object.values(commands).filter((command) => isListed(command, app));
      const width = Math.max(...shown.map((command) => command.usage.length));
      for (const command of shown) app.print(`${command.usage.padEnd(width)}  ${command.about}`);
    },
  },
  time: {
    usage: 'time morning|day|afternoon|night|auto',
    about: 'change the time of day',
    hidden: true,
    run([name], app) {
      if (!name) return app.print(`it is ${app.timeOfDay.current()} (${app.timeOfDay.mode()}).`);
      if (!app.timeOfDay.set(name)) return app.print(`usage: ${commands.time.usage}`);
      app.print(name === 'auto' ? 'following your clock again.' : `it is now ${name}.`);
    },
  },
  weather: {
    usage: 'weather rain|snow|clear',
    about: 'change the weather',
    hidden: true,
    run([name], app) {
      if (!name) return app.print(`the weather is ${app.weather.get()}.`);
      if (!app.weather.set(name)) return app.print(`usage: ${commands.weather.usage}`);
      app.print(name === 'clear' ? 'the sky clears.' : `it starts to ${name}.`);
    },
  },
  clear: {
    usage: 'clear',
    about: 'hide this bubble',
    run(args, app) { app.clearOutput(); },
  },
  whoami: {
    usage: 'whoami',
    about: 'take out my folder',
    run(args, app) {
      app.print(app.events.folder()
        ? 'you take out the folder. click it to open it.'
        : 'the folder is already on the sill. click it to open it.');
    },
  },
  // The sill (js/sill.js): what is on it, taking things off, putting them back.
  // Hidden, for visitors who think to try them; not part of Power User.
  ls: {
    usage: 'ls',
    about: 'list what is on the sill',
    hidden: true,
    everyCommand: false,
    run(args, app) {
      const items = sillItems();
      app.print(items.length ? items.join('  ') : 'the sill is empty.');
      const away = putAway();
      if (away.length) app.print(`put away: ${away.join('  ')}`);
    },
  },
  rm: {
    usage: 'rm <item>',
    about: 'take something off the sill',
    hidden: true,
    everyCommand: false,
    run([word], app) {
      if (!word) return app.print(`usage: ${commands.rm.usage}`);
      const name = findSillItem(word);
      const result = name ? takeOffSill(name) : 'absent';
      if (result === 'absent') return app.print(`rm: cannot remove '${word}': not on the sill`);
      if (result === 'busy') return app.print(`rm: cannot remove '${name}': it's in use`);
      app.print(`you take the ${name} off the sill.`);
    },
  },
  touch: {
    usage: 'touch <item>',
    about: 'put something of yours on the sill',
    hidden: true,
    everyCommand: false,
    run([word], app) {
      if (!word) return app.print(`usage: ${commands.touch.usage}`);
      const name = findSillItem(word);
      const result = name ? putOnSill(name) : 'missing';
      if (result === 'missing') return app.print(`touch: cannot touch '${word}': you don't have one`);
      if (result === 'already') return app.print(`the ${name} is already on the sill.`);
      app.print(`you put the ${name} on the sill.`);
    },
  },
  // The terrarium (js/terrarium.js): the journal's actions without a pointer.
  // The pot on the wall opens the journal; an open journal shows the change at
  // once, on whatever tab it is.
  water: {
    usage: 'water',
    about: 'water the terrarium pot',
    hidden: true,
    everyCommand: false,
    run(args, app) {
      app.journal.drop();   // a command puts down whatever the journal had in hand
      const result = app.terrarium.water();
      if (result.reason === 'empty') return app.print("there's nothing in the pot to water.");
      if (result.reason === 'dead') return app.print(`the ${nameOf(result.species)} is past watering. "harvest" clears the pot.`);
      if (result.reason === 'wait') return app.print('give it a moment to soak in.');
      app.print(result.saturated
        ? `you water the ${nameOf(result.species)}. the soil is saturated; the extra drains away.`
        : `you water the ${nameOf(result.species)}.`);
    },
  },
  trim: {
    usage: 'trim',
    about: 'trim the plant in the pot',
    hidden: true,
    everyCommand: false,
    run(args, app) {
      app.journal.drop();
      const result = app.terrarium.trim();
      if (result.reason === 'empty') return app.print("there's nothing in the pot to trim.");
      if (result.reason === 'dead') return app.print(`the ${nameOf(result.species)} has withered. "harvest" clears the pot.`);
      if (result.reason === 'healthy') return app.print(`the ${nameOf(result.species)} doesn't need trimming. trim a plant that has wilted to get it growing at full speed again.`);
      app.print(`you trim the ${nameOf(result.species)} back. it looks healthier.`);
    },
  },
  harvest: {
    usage: 'harvest',
    about: 'harvest the plant for seeds',
    hidden: true,
    everyCommand: false,
    run(args, app) {
      app.journal.drop();
      const result = app.terrarium.harvest();
      if (result.reason === 'empty') return app.print('the pot is empty. "plant <seed>" to start something.');
      if (result.reason === 'unripe') {
        return app.print(`the ${nameOf(result.species)} isn't ready yet (growth ${percent(result.growth)}).`);
      }
      if (result.cleared) return app.print(`you clear out the withered ${nameOf(result.species)}. the pot is empty.`);
      app.print(`you harvest the ${nameOf(result.species)}: ${result.seeds} seed${result.seeds > 1 ? 's' : ''}.`);
    },
  },
  plant: {
    usage: 'plant <seed>',
    about: 'plant a seed in the pot',
    hidden: true,
    everyCommand: false,
    run(words, app) {
      if (!words.length) return app.print(`usage: ${commands.plant.usage}`);
      app.journal.drop();
      const id = app.terrarium.find(words.join(' '));
      if (!id) return app.print(`there's no such seed as "${words.join(' ')}".`);
      const result = app.terrarium.plant(id);
      if (result.reason === 'occupied') return app.print(`the pot's already got ${aOrAn(nameOf(result.species))} in it.`);
      if (result.reason === 'none') return app.print(`you don't have any ${nameOf(id)} seeds.`);
      app.print(`you plant ${aOrAn(nameOf(id))} seed. water it now and then.`);
    },
  },
  seeds: {
    usage: 'seeds',
    about: 'list your seeds',
    hidden: true,
    everyCommand: false,
    run(args, app) {
      const owned = SPECIES.filter((s) => app.terrarium.count(s.id)).map((s) => `${nameOf(s.id)} ${app.terrarium.count(s.id)}`);
      app.print(owned.length ? owned.join('  ') : 'you have no seeds.');
    },
  },
  cross: {
    usage: 'cross <seed> <seed>',
    about: 'cross two seeds for a new one',
    hidden: true,
    everyCommand: false,
    run(words, app) {
      const [a, b] = splitPair(words, app.terrarium.find);
      if (!a || !b) return app.print(`usage: ${commands.cross.usage}`);
      const result = app.terrarium.cross(a, b);
      if (result.reason === 'last') {
        const two = a === b;
        return app.print(`your last ${nameOf(result.species)} seed stays for planting. you need ${two ? 'two spare ones' : 'a spare one'} to cross.`);
      }
      if (!result.ok) return app.print(`you need ${a === b ? `two ${nameOf(a)} seeds` : `${aOrAn(nameOf(result.species))} seed`} for that.`);
      const odds = result.hybrid ? `chance ${percent(result.chance)} - new species.` : 'no new species from this pair.';
      app.print(result.hit ? `${odds} new species: ${nameOf(result.species)}!` : `${odds} you got ${aOrAn(nameOf(result.species))} seed.`);
    },
  },
  codex: {
    usage: 'codex',
    about: 'which species you have found',
    hidden: true,
    everyCommand: false,
    run(args, app) {
      const found = app.terrarium.get().codex;
      app.print(`${found.length} / ${SPECIES.length} discovered.`);
      const missing = SPECIES.filter((s) => !found.includes(s.id)).map((s) => nameOf(s.id));
      if (missing.length) app.print(`missing: ${missing.join(', ')}`);
    },
  },
  // Retired: the achievement board on the window's right-hand log replaced
  // it. Old habits and old screenshots still send people here.
  badges: {
    usage: 'badges',
    about: 'where your achievements went',
    hidden: true,
    everyCommand: false,
    run(args, app) { app.print('your achievements are on the board by the window now. click it to see them.'); },
  },
  reset: {
    usage: 'reset',
    about: 'forget all achievements and progress',
    everyCommand: false,
    hidden: true,
    run([answer], app) {
      if (answer !== 'yes') return app.print('this erases every achievement and all progress. type "reset yes" to confirm.');
      app.resetProgress();
      app.print('all progress erased. the cabin is as you found it.');
    },
  },
  theme: {
    usage: 'theme green|wood',
    about: 'change the terminal colours',
    available: () => isUnlocked('power_user'),
    run([name], app) {
      if (name === 'green') { app.setTheme(app.theme.green); return app.print('green screen on.'); }
      if (name === 'wood') { app.setTheme(null); return app.print('back to wood.'); }
      app.print(`usage: ${commands.theme.usage}`);
    },
  },
  sound: {
    usage: 'sound on|off',
    about: 'the waterfall, birds and wind',
    everyCommand: false,
    run([choice], app) {
      if (choice === 'off') { setMuted(true); return app.print('sound off.'); }
      if (choice === 'on') { setMuted(false); return app.print('sound on.'); }
      app.print(`sound is ${isMuted() ? 'off' : 'on'}. usage: ${commands.sound.usage}`);
    },
  },
  // Easter egg: `hidden` keeps it out of `help`.
  cig: {
    usage: 'cig',
    about: 'put the pack of cigarettes on the sill',
    hidden: true,
    run(args, app) {
      app.print(app.events.cig() ? 'you set your pack down on the sill.' : 'your pack is already on the sill.');
    },
  },
  // Testing without grinding; only exists with ?debug in the URL.
  debug: {
    usage: 'debug unlock <id|all> | set <stat> <number|a,b,c> | event <name> [key=value ...] | stats | sound',
    about: 'test achievements',
    hidden: true,
    available: (app) => app.debug,
    run([action, name, value, ...rest], app) {
      if (action === 'unlock' && name === 'all') {
        for (const { definition } of listAchievements()) debugUnlock(definition.id);
        return app.print('unlocked everything.');
      }
      if (action === 'unlock') return app.print(debugUnlock(name) ? `unlocked ${name}.` : `no locked achievement "${name}".`);
      if (action === 'set' && name && value !== undefined) {
        // Typed lower-case; match it to the stat's real name (birdclicks -> birdClicks).
        const stat = listAchievements().map((a) => a.definition.stat).find((s) => s.toLowerCase() === name) ?? name;
        debugSetStat(stat, /^\d+(\.\d+)?$/.test(value) ? Number(value) : value.split(','));
        return app.print(`${stat} = ${value}`);
      }
      if (action === 'event' && app.events[name]) {
        const options = Object.fromEntries([value, ...rest].filter(Boolean).map((pair) => {
          const [key, raw] = pair.split('=');
          return [CAMEL_CASE_OPTIONS[key] ?? key, /^-?\d+(\.\d+)?$/.test(raw) ? Number(raw) : raw];
        }));
        return app.print(`${name}: ${app.events[name](options) === false ? 'did nothing' : 'fired'}.`);
      }
      if (action === 'stats') return app.print(JSON.stringify(app.progressStats()));
      if (action === 'sound') {
        const playing = [...new Set(soundLog.map((entry) => entry.name))].join(', ') || 'nothing yet';
        return app.print(`sound ${soundState()}, output ${outputLevelDb().toFixed(1)} dBFS, played: ${playing}`);
      }
      app.print(`usage: ${commands.debug.usage}`);
    },
  },
};

// ── terrarium helpers ──
function nameOf(id) {
  return SPECIES[speciesIndex(id)].name.toLowerCase();
}

function aOrAn(word) {
  return `${/^[aeiou]/i.test(word) ? 'an' : 'a'} ${word}`;
}

function percent(fraction) {
  return `${Math.round(fraction * 100)}%`;
}

// Two species from the words after `cross`, names of two words included
// ("cross aurora bloom fern"): the first split where both halves are seeds.
function splitPair(words, find) {
  for (let i = 1; i < words.length; i++) {
    const a = find(words.slice(0, i).join(' '));
    const b = find(words.slice(i).join(' '));
    if (a && b) return [a, b];
  }
  return [null, null];
}

// Commands arrive lower-cased; event options that aren't single words.
const CAMEL_CASE_OPTIONS = { spotindex: 'spotIndex', speedpxpersec: 'speedPxPerSec' };

export function runCommand(line, app) {
  const [name, ...args] = line.trim().toLowerCase().split(/\s+/);
  if (!name) return;
  const command = Object.hasOwn(commands, name) ? commands[name] : null;
  if (!command || (command.available && !command.available(app))) {
    app.print(`no such command "${name}". type "help" to see what you can do.`);
    return;
  }
  track('commandsUsed', name);   // before running, so `reset` wipes its own mark too
  command.run(args, app);
}

// The commands "use every command" asks for (see the rule at the top).
export function everyDayCommands() {
  return Object.entries(commands)
    .filter(([, command]) => !command.hidden && !command.available && command.everyCommand !== false)
    .map(([name]) => name);
}

function isListed(command, app) {
  return !command.hidden && (!command.available || command.available(app));
}
