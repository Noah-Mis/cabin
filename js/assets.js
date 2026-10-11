// assets.js — loads every manifest listed in config.assetPacks and every image
// they (and config.files) name. The first pack is the scene's own manifest;
// later packs (like the smoke animations) add animations and sequences.
// File names that end in _<time> belong to that time of day; a file without a
// time suffix serves every time that has no file of its own. This one rule
// covers all the variants: four palettes, the night-only stars, the plain +
// night pairs (mug, smoke), and wind's plain + morning + night.
// Exports: loadAssets(config)
//   -> Promise<{ manifest, sequences, failures, image, timeImage, animation, variants, slowDown, packManifest }>

export async function loadAssets(config) {
  const packs = await Promise.all(config.assetPacks.map(async (pack) => ({
    dir: pack.dir,
    manifest: await loadJson(pack.dir + pack.manifest),
  })));
  const manifest = packs[0].manifest;
  const animations = {};   // name -> { info, dir }
  const sequences = {};
  for (const pack of packs) {
    for (const [name, info] of Object.entries(pack.manifest.animations)) animations[name] = { info, dir: pack.dir };
    Object.assign(sequences, pack.manifest.sequences ?? {});
  }

  // Images are keyed by their path, so two packs may reuse a file name.
  const paths = new Set(Object.values(animations).flatMap(({ info, dir }) => info.files.map((f) => dir + f)));
  for (const pattern of Object.values(config.files)) {
    for (const time of config.times) paths.add(packs[0].dir + pattern.replace('<time>', time));
  }
  for (const file of manifest.window?.files ?? []) paths.add(packs[0].dir + file);   // the window frame
  const images = new Map();
  const failures = [];
  await Promise.all([...paths].map(async (path) => {
    try {
      images.set(path, await loadImage(path));
    } catch {
      failures.push(path);
    }
  }));

  // A static scene image (config.files) by its file name.
  function image(name) {
    return images.get(packs[0].dir + name) ?? null;
  }

  function timeImage(pattern, time) {
    return image(pattern.replace('<time>', time));
  }

  // The manifest entry for an animation plus imageFor(time).
  function animation(name) {
    const entry = animations[name];
    if (!entry) throw new Error(`no manifest has an animation called "${name}"`);
    const byTime = pickFilesByTime(entry.info.files, config.times);
    return { info: entry.info, imageFor: (time) => images.get(entry.dir + byTime[time]) ?? null };
  }

  // imageFor(time) over a list of scene files that follow the _<time> rule,
  // like the manifest's window entry (plain by day, _night at night).
  function variants(files) {
    const byTime = pickFilesByTime(files, config.times);
    return { imageFor: (time) => image(byTime[time]) };
  }

  // Stretches every frame of every animation by `factor` (1.2 = 20% slower).
  // Call before the scene is built; sprites read ms_per_frame from here.
  function slowDown(factor) {
    for (const { info } of Object.values(animations)) info.ms_per_frame *= factor;
  }

  // A pack's whole manifest, for packs that carry more than sprites
  // (the achievements file also lists the achievements themselves).
  function packManifest(dir) {
    return packs.find((pack) => pack.dir === dir)?.manifest ?? null;
  }

  return { manifest, sequences, failures, image, timeImage, animation, variants, slowDown, packManifest };
}

function pickFilesByTime(files, times) {
  const timeOf = (file) => times.find((t) => file.endsWith(`_${t}.png`));
  const shared = files.find((f) => !timeOf(f));
  const byTime = {};
  for (const t of times) byTime[t] = files.find((f) => timeOf(f) === t) ?? shared ?? null;
  return byTime;
}

async function loadJson(url) {
  // 'no-cache' asks the server every time (an unchanged file is a tiny "not
  // modified" reply), so an updated manifest is never paired with stale code.
  const response = await fetch(url, { cache: 'no-cache' });
  if (!response.ok) throw new Error(`could not load ${url} (${response.status})`);
  return response.json();
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`could not load ${url}`));
    img.src = url;
  });
}
