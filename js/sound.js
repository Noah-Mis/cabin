// sound.js — quiet ambient sound: a looping waterfall, and one-shot sounds
// for things that happen (a bird, a gust). Scene elements call play() or
// loop() and never deal with the Web Audio API themselves.
//
// Browsers only allow sound after the visitor interacts with the page, so
// nothing is heard until the first click or key press; loops asked for
// before then start at that moment, one-shots asked for before then are
// skipped. Sound pauses while the tab is hidden.
//
// Exports: startSound(settings), play(name, { pan, panTo, durationSec }),
//          loop(name), setMuted(on), isMuted(), soundState(), outputLevelDb(), soundLog,
//          createLoop, createDistance (exported for the tests)

let audio = null;            // { ctx, master, buffers: { name: AudioBuffer } } once started
let settings = null;
let muted = false;
const wantedLoops = new Set();
const runningLoops = new Map();
export const soundLog = [];  // what played, for inspection and tests

export async function startSound(soundSettings) {
  settings = soundSettings;
  const AudioContextClass = window.AudioContext ?? window.webkitAudioContext;
  if (!AudioContextClass) return;   // no Web Audio: the site stays silent
  // Download now, but create the audio system only on the first gesture:
  // browsers warn about (and refuse) sound started before one.
  const files = {};
  await Promise.all(Object.entries(settings.sounds).map(async ([name, sound]) => {
    try {
      const response = await fetch(settings.dir + sound.file);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      files[name] = await response.arrayBuffer();
    } catch (error) {
      console.error(`could not load sound ${sound.file}:`, error);
    }
  }));

  let starting = null;   // shared, so two quick clicks don't build it twice
  async function unlock() {
    if (muted || document.visibilityState !== 'visible') return;
    starting ??= createAudio(AudioContextClass, files);
    audio = await starting;
    resume();
  }
  for (const type of ['pointerdown', 'keydown']) document.addEventListener(type, unlock);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') unlock();
    else audio?.ctx.suspend();
  });
}

async function createAudio(AudioContextClass, files) {
  const ctx = new AudioContextClass();
  const master = ctx.createGain();
  master.gain.value = dbToGain(settings.masterVolumeDb);
  master.connect(ctx.destination);
  // A meter on the final mix, so `debug sound` (and the tests) can confirm
  // something is actually coming out, not just scheduled.
  const meter = ctx.createAnalyser();
  meter.fftSize = 8192;
  master.connect(meter);
  const buffers = {};
  await Promise.all(Object.entries(files).map(async ([name, data]) => {
    try {
      buffers[name] = await ctx.decodeAudioData(data);
    } catch (error) {
      console.error(`could not decode sound ${settings.sounds[name].file}:`, error);
    }
  }));
  return { ctx, master, meter, buffers };
}

function resume() {
  audio.ctx.resume().then(startWantedLoops);
}

// Keeps `name` playing for as long as the page is open.
export function loop(name) {
  wantedLoops.add(name);
  if (audio?.ctx.state === 'running') startWantedLoops();
}

function startWantedLoops() {
  for (const name of wantedLoops) {
    if (runningLoops.has(name) || !audio.buffers[name]) continue;
    const sound = settings.sounds[name];
    const output = gainNode(sound.volumeDb, sound.pan ?? 0);
    // A far-off sound goes through the distance effect first.
    const into = sound.distance ? createDistance(audio.ctx, sound.distance, output.input).input : output.input;
    const looper = createLoop(audio.ctx, audio.buffers[name], into, sound.loop);
    looper.extend(audio.ctx.currentTime + settings.loopLookaheadSec);
    // Keep scheduling ahead; timers are slowed in hidden tabs, which is fine
    // because the context is suspended then.
    const timer = setInterval(() => looper.extend(audio.ctx.currentTime + settings.loopLookaheadSec), 1000);
    runningLoops.set(name, { looper, timer });
    soundLog.push({ name, loop: true, volumeDb: sound.volumeDb, at: audio.ctx.currentTime });
  }
}

// Plays `name` once. pan: -1 (left) to 1 (right); panTo: glide there over the
// sound. durationSec: stop early, with a short fade.
export function play(name, { pan = 0, panTo = pan, durationSec } = {}) {
  if (!audio || muted || audio.ctx.state !== 'running' || !audio.buffers[name]) return false;
  const sound = settings.sounds[name];
  const { ctx } = audio;
  const buffer = audio.buffers[name];
  const startAt = sound.startAtSec ?? 0;
  const length = Math.min(durationSec ?? Infinity, (sound.stopAtSec ?? buffer.duration) - startAt);
  const now = ctx.currentTime;
  const output = gainNode(sound.volumeDb, pan);
  output.panner.pan.linearRampToValueAtTime(panTo, now + length);
  // A short fade at the end, so a trimmed sound doesn't click.
  output.gain.gain.setValueAtTime(output.gain.gain.value, now + Math.max(0, length - settings.endFadeSec));
  output.gain.gain.linearRampToValueAtTime(0, now + length);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(output.input);
  source.start(now, startAt, length);
  source.onended = () => output.disconnect();
  soundLog.push({ name, loop: false, volumeDb: sound.volumeDb, pan, panTo, seconds: +length.toFixed(2), at: now });
  return true;
}

export function setMuted(on) {
  muted = on;
  if (!audio) return;   // not started yet: the next gesture starts it (unless muted)
  if (on) audio.ctx.suspend();
  else resume();
}

export const isMuted = () => muted;

// The level coming out right now, in dBFS (about -100 is silence).
export function outputLevelDb() {
  if (!audio || audio.ctx.state !== 'running') return -Infinity;
  const samples = new Float32Array(audio.meter.fftSize);
  audio.meter.getFloatTimeDomainData(samples);
  const meanSquare = samples.reduce((sum, s) => sum + s * s, 0) / samples.length;
  return 10 * Math.log10(Math.max(meanSquare, 1e-12));
}

// 'not started' until the first gesture, then the audio system's state.
export const soundState = () => audio?.ctx.state ?? 'not started';

// volume (dB) -> stereo pan -> master. Returns the nodes so callers can automate them.
function gainNode(volumeDb, pan) {
  const { ctx, master } = audio;
  const gain = ctx.createGain();
  gain.gain.value = dbToGain(volumeDb);
  const panner = ctx.createStereoPanner();
  panner.pan.value = pan;
  gain.connect(panner).connect(master);
  return { input: gain, gain, panner, disconnect: () => { gain.disconnect(); panner.disconnect(); } };
}

// Makes a sound seem far away, the way distance changes it:
//   lowpassHz     air soaks up high frequencies, so it sounds duller
//   highpassHz    close-up rumble falls away
//   stereoWidth   0 = a single point, 1 = as recorded: distant things are narrow
//   reverbMix     0-1: how much of it reaches you as echo off the valley
//   reverbSec     how long that echo takes to die away
// Connects into `destination`; returns { input }.
export function createDistance(ctx, distance, destination) {
  const highpass = ctx.createBiquadFilter();
  highpass.type = 'highpass';
  highpass.frequency.value = distance.highpassHz;
  const lowpass = ctx.createBiquadFilter();
  lowpass.type = 'lowpass';
  lowpass.frequency.value = distance.lowpassHz;
  highpass.connect(lowpass);
  const narrow = stereoWidth(ctx, distance.stereoWidth);
  lowpass.connect(narrow.input);

  const dry = ctx.createGain();
  dry.gain.value = Math.cos(distance.reverbMix * Math.PI / 2);
  const wet = ctx.createGain();
  wet.gain.value = Math.sin(distance.reverbMix * Math.PI / 2);
  const echo = ctx.createConvolver();
  echo.buffer = valleyEcho(ctx, distance.reverbSec);
  narrow.output.connect(dry).connect(destination);
  narrow.output.connect(echo).connect(wet).connect(destination);
  return { input: highpass };
}

// Mixes each side toward the other: width 1 leaves stereo alone, 0 is mono.
function stereoWidth(ctx, width) {
  const split = ctx.createChannelSplitter(2);
  const merge = ctx.createChannelMerger(2);
  const same = (1 + width) / 2, other = (1 - width) / 2;
  for (const [from, to, amount] of [[0, 0, same], [1, 0, other], [1, 1, same], [0, 1, other]]) {
    const gain = ctx.createGain();
    gain.gain.value = amount;
    split.connect(gain, from);
    gain.connect(merge, 0, to);
  }
  const input = ctx.createGain();
  input.channelCount = 2;
  input.channelCountMode = 'explicit';
  input.connect(split);
  return { input, output: merge };
}

// A soft synthetic echo: stereo noise dying away exponentially, darker as
// it fades (high frequencies die first), so no recording is needed.
function valleyEcho(ctx, seconds) {
  const length = Math.floor(ctx.sampleRate * seconds);
  const buffer = ctx.createBuffer(2, length, ctx.sampleRate);
  for (let channel = 0; channel < 2; channel++) {
    const data = buffer.getChannelData(channel);
    let smooth = 0;
    for (let i = 0; i < length; i++) {
      const t = i / length;
      const darkness = 0.2 + 0.75 * t;            // more smoothing later in the tail
      smooth = smooth * darkness + (Math.random() * 2 - 1) * (1 - darkness);
      data[i] = smooth * Math.exp(-5 * t);
    }
  }
  // Same overall energy as the dry path, so reverbMix alone sets the balance.
  let energy = 0;
  for (let channel = 0; channel < 2; channel++) for (const v of buffer.getChannelData(channel)) energy += v * v;
  const scale = 1 / Math.sqrt(energy / 2);
  for (let channel = 0; channel < 2; channel++) {
    const data = buffer.getChannelData(channel);
    for (let i = 0; i < length; i++) data[i] *= scale;
  }
  return buffer;
}

// A seamless loop of part of a recording: overlapping copies of
// [startSec, endSec], each faded in and out over crossfadeSec (equal power,
// so the level holds through the seam). levelCorrectionDb tilts each copy's
// volume to cancel a recording that gets steadily louder (negative) or
// quieter (positive) from start to end.
// Returns { extend(untilTime), stop() }.
export function createLoop(ctx, buffer, destination, { startSec, endSec, crossfadeSec, levelCorrectionDb = 0 }) {
  const end = Math.min(endSec ?? buffer.duration, buffer.duration);
  const length = end - startSec;
  const step = length - crossfadeSec;
  const curve = copyEnvelope(length, crossfadeSec, levelCorrectionDb);
  const sources = [];
  let nextAt = ctx.currentTime;

  function scheduleCopy(at) {
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    const gain = ctx.createGain();
    gain.gain.setValueCurveAtTime(curve, at, length);
    source.connect(gain).connect(destination);
    source.start(at, startSec, length);
    source.onended = () => { gain.disconnect(); sources.splice(sources.indexOf(source), 1); };
    sources.push(source);
  }

  return {
    extend(untilTime) {
      for (; nextAt < untilTime; nextAt += step) scheduleCopy(nextAt);
    },
    stop() {
      for (const source of sources) source.stop();
    },
  };
}

// One copy's volume over time: an equal-power fade in and out at the ends,
// times a straight-line tilt in dB that adds `correctionDb` from the start of
// the copy to its end (centred, so the copy's average level is unchanged).
function copyEnvelope(lengthSec, fadeSec, correctionDb, points = 512) {
  const curve = new Float32Array(points);
  for (let i = 0; i < points; i++) {
    const t = (i / (points - 1)) * lengthSec;
    let fade = 1;
    if (t < fadeSec) fade = Math.sin((t / fadeSec) * Math.PI / 2);
    else if (t > lengthSec - fadeSec) fade = Math.cos(((t - (lengthSec - fadeSec)) / fadeSec) * Math.PI / 2);
    const tiltDb = correctionDb * (t / lengthSec - 0.5);
    curve[i] = fade * dbToGain(tiltDb);
  }
  return curve;
}

function dbToGain(db) {
  return 10 ** (db / 20);
}
