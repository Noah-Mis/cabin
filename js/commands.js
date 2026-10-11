// commands.js — the terminal's command table and the code that runs a line.
// To add a command, add one entry to `commands`. Each entry gets the words
// after the command name and the app: { events, timeOfDay, weather, print,
// clearOutput, setTheme, resetProgress, debug, theme }. Whatever a command
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
// So `badges` counts; `reset` doesn't (it would wipe the very progress it
// completes); `sound` doesn't (muting shouldn't be a chore); `theme` doesn't (it only appears once the achievement is
// earned). everyDayCommands() below computes the list.
//
// Exports: commands, runCommand(line, app), everyDayCommands()

import { track, isUnlocked, listAchievements, debugSetStat, debugUnlock } from './achievements.js';
import { setMuted, isMuted, soundState, outputLevelDb, soundLog } from './sound.js';

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
  badges: {
    usage: 'badges',
    about: 'your achievements',
    run(args, app) {
      const all = listAchievements();
      app.print(`${all.filter((a) => a.unlocked).length} of ${all.length} earned:`);
      for (const { definition, unlocked, count } of all) app.print(describeBadge(definition, unlocked, count));
    },
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

// Earned: name, what it is, and what it changed. Not earned: "???", or the
// name and a count once there is some progress. Rewards stay secret.
function describeBadge(definition, unlocked, count) {
  if (unlocked) return `★ ${definition.name}: ${definition.desc}. ${definition.reward}.`;
  if (count && count.value > 0) return `· ${definition.name} ${count.value}/${count.goal}`;
  return '· ???';
}
