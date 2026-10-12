"""terrarium.py — checks for the terrarium mini-game (anim/terrarium/terrarium_brief.md).

1. The rules, through js/terrarium.js with a fake clock and fixed dice, under
   a test storage key: the starter set, growth over real hours, the 48-hour
   offline cap (thirsty, never dead), dying only of thirst while visited,
   watering (debounce, saturation, wilting cleared), trimming, harvesting
   (seeds by vigor, the one-time gift, the codex), crossing (odds, pity +5
   up to +25, a seed back on a miss, same-species crosses), the stack of
   tiles per stage, saving, and bad saved data starting fresh.
2. Every string the journal draws fits its line (33 characters from x 12).
3. The live page: the pot on the wall opens the journal, which is drawn
   over everything; on the Pot tab, the seed tray and the tool rail
   (terrarium_tools_plan.md): a seed dragged to the pot is planted, the can
   picked up with a click and clicked on the pot waters it (the soil
   darkens with the meter), a drag let go off the pot puts the tool back,
   the rail shows only tools that would do something, the basket
   harvests, and the keyboard plays it too; the Seeds tab has no Plant
   button; the crossing bench; terminal commands change an open journal
   without switching its tab; every time of day; closing; the console.
   The journal's hints show on a first visit and each goes once its step
   has been done, for good (they are saved).

Writes tests/results/terrarium.md and screens/terrarium_*.png.
Run:  python tests/terrarium.py
"""
import base64, io, json, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from harness import ROOT, RESULTS, serve_site, open_browser, watch_page

SCREENS = RESULTS / 'screens'
MANIFEST = json.loads((ROOT / 'anim' / 'terrarium' / 'terrarium_manifest.json').read_text(encoding='utf-8'))['animations']
report, failures = [], []


def check(ok, what):
    report.append(f"- {'PASS' if ok else 'FAIL'}: {what}")
    if not ok:
        failures.append(what)
    print(report[-1].encode('ascii', 'replace').decode())


# A terrarium on a clock the test moves (clock.t, in ms) and dice it loads
# (dice.queue, used first to last; then dice.rest). Its own storage key.
RULES = """async () => {
  const { config } = await import('./js/config.js');
  const { createTerrarium } = await import('./js/terrarium.js');
  const HOUR = 3600 * 1000;
  const settings = { ...config.terrarium, storageKey: 'terrarium-test' };
  const clock = { t: 1e12 };
  const dice = { queue: [], rest: 0.5 };
  const make = () => createTerrarium(settings, { now: () => clock.t, random: () => (dice.queue.length ? dice.queue.shift() : dice.rest) });
  const genome = (g) => ({ height: 3, bloom: 2, vigor: 3, hue: 3, hardiness: 3, ...g });
  const out = {};
  localStorage.removeItem('terrarium-test');

  let t = make();
  const s = () => t.get();
  out.fresh = { seeds: Object.fromEntries(Object.entries(s().seeds).map(([k, v]) => [k, v.length])), codex: [...s().codex], pot: s().pot,
    hues: Object.values(s().seeds).flat().map((g) => g.hue) };

  // Growth: a daisy (two stars), vigor 3, hardiness 3, watered to full, 2 hours.
  s().seeds.daisy = [genome()];
  t.plant('daisy');
  s().pot.hydration = 1;
  clock.t += 2 * HOUR;
  t.tick();
  out.grow2h = { growth: s().pot.growth, hydration: s().pot.hydration, stage: t.stage(s().pot), stack: s().pot.stack };
  // Water runs out partway through 10 more hours: growth only while above wiltBelow.
  s().pot.hydration = 0.2;
  clock.t += 10 * HOUR;
  t.tick();
  out.grow12h = { growth: s().pot.growth, hydration: s().pot.hydration, wilting: s().pot.wilting, health: s().pot.health, stack: s().pot.stack };
  // Water: clears wilting at once, debounced, health stays until a trim.
  const w1 = t.water();
  const w2 = t.water();
  clock.t += 600;
  const w3 = t.water();
  out.water = { w1, w2, w3, wilting: s().pot.wilting, health: s().pot.health, hydration: s().pot.hydration };
  // Saturation: past full the extra drains, and the status says so.
  s().pot.hydration = 0.9;
  clock.t += 600;
  const w4 = t.water();
  out.saturated = { w4, hydration: s().pot.hydration, status: t.status(s().pot) };
  clock.t += config.terrarium.saturatedShowSec * 1000 + 1;
  out.saturatedLater = t.status(s().pot);
  // Trim: needs growth 0.35, costs 0.05, restores health.
  const g0 = s().pot.growth;
  out.trim = { result: t.trim(), drop: g0 - s().pot.growth, health: s().pot.health };

  // A week away: clamped to 48 h; thirsty, not dead.
  s().pot.hydration = 1;
  clock.t += 7 * 24 * HOUR;
  t.tick();
  out.week = { dead: s().pot.dead, wilting: s().pot.wilting, hydration: s().pot.hydration, dryMs: s().pot.dryMs };
  // Watched: dry and visited (a tick a minute) for 23 h lives; past 24 h dies.
  for (let i = 0; i < 23 * 60; i++) { clock.t += 60 * 1000; t.tick(); }
  out.watched23h = s().pot.dead;
  for (let i = 0; i < 2 * 60; i++) { clock.t += 60 * 1000; t.tick(); }
  out.watched25h = { dead: s().pot.dead, stack: s().pot.stack, status: t.status(s().pot), water: t.water() };
  // Dead: harvest clears, no seeds.
  const before = t.count('daisy');
  out.clear = { result: t.harvest(), pot: s().pot, seeds: t.count('daisy') - before };

  // Harvest: 1 seed at vigor 3, 2 at vigor 4; the first harvest's gift, once.
  s().seeds.bluebell = [genome({ vigor: 3 }), genome({ vigor: 4 })];
  t.plant('bluebell');
  out.unripe = t.harvest();
  s().pot.growth = 1;
  s().pot.hydration = 1;
  t.tick();
  out.readyStack = s().pot.stack;
  const h1 = t.harvest();
  t.plant('bluebell');
  s().pot.growth = 1;
  const h2 = t.harvest();
  out.harvest = { h1, h2, codex: s().codex, bluebells: t.count('bluebell'), gifted: s().gifted };

  // Crossing: no hit (dice 0.99), pity rises 5 points a miss up to +25,
  // a parent comes back; then a hit resets it.
  s().seeds.daisy = Array.from({ length: 20 }, () => genome());
  s().seeds.wildflower = Array.from({ length: 20 }, () => genome());
  const chances = [];
  dice.rest = 0.99;
  for (let i = 0; i < 7; i++) { chances.push(t.predict('daisy', 'wildflower').chance); t.cross('daisy', 'wildflower'); }
  out.pity = { chances, stored: s().pity['daisy|wildflower'] };
  dice.rest = 0.5;
  dice.queue = [0];
  const hit = t.cross('wildflower', 'daisy');
  out.hit = { hit, pityAfter: s().pity['daisy|wildflower'] ?? 0, codex: s().codex.includes('bluebell') };
  // No hybrid for the pair; the same species twice needs two.
  out.noHybrid = { predict: t.predict('moss', 'daisy'), result: t.cross('moss', 'daisy') };
  s().seeds.ivy = [genome({ bloom: 0 })];
  out.sameOne = t.cross('ivy', 'ivy');
  s().seeds.ivy.push(genome({ bloom: 0 }));
  out.sameTwo = { result: t.cross('ivy', 'ivy'), bloom: s().seeds.ivy?.at(-1)?.bloom };
  // Hybrids that flower always get a bloom gene.
  s().seeds.moonflower = [genome({ bloom: 0 })];
  s().seeds.suncap = [genome({ bloom: 0 })];
  dice.queue = [0];
  out.aurora = { result: t.cross('moonflower', 'suncap'), bloom: s().seeds.aurora?.[0]?.bloom };

  // Stacks per stage for a flowering and a non-flowering species.
  const stacks = {};
  for (const id of ['bluebell', 'fern']) {
    s().pot = null;
    s().seeds[id] = [genome({ bloom: id === 'fern' ? 0 : 2 })];
    t.plant(id);
    stacks[id] = [0, 0.2, 0.4, 0.7, 0.86, 0.95, 1].map((g) => { s().pot.growth = g; clock.t += 1; t.tick(); return s().pot.stack.join(' '); });
  }
  out.stacks = stacks;
  // Time to full by rarity, for the slowest seed (vigor 1), kept wet.
  const fullAfter = (id) => {
    s().pot = null;
    s().seeds[id] = [genome({ vigor: 1, hardiness: 5 })];
    t.plant(id);
    s().pot.hydration = 1;
    const hours = config.terrarium.growHoursByRarity[{ moss: 0, aurora: 4 }[id]];
    clock.t += (hours - 0.1) * HOUR;
    t.tick();
    const before = s().pot.growth;
    clock.t += 0.1 * HOUR + 1000;
    t.tick();
    return { hours, before, after: s().pot.growth };
  };
  out.fullTime = { moss: fullAfter('moss'), aurora: fullAfter('aurora') };
  out.sameDraw = (() => { const a = s().pot.stack.join(); s().pot.growth = 0.7; t.tick(); const b = s().pot.stack.join(); t.tick(); return b === s().pot.stack.join() && !!a; })();

  // Saved: a new instance reads the same state back.
  const saved = JSON.stringify(s());
  t = make();
  out.reload = JSON.stringify(t.get()) === saved;
  // Bad or other-version data starts fresh (with the starter seeds).
  for (const [name, raw] of [['garbage', '{nope'], ['version', JSON.stringify({ ...JSON.parse(saved), version: 99 })],
      ['badGenome', JSON.stringify({ ...JSON.parse(saved), seeds: { moss: [{ height: 9 }] } })]]) {
    localStorage.setItem('terrarium-test', raw);
    const fresh = make().get();
    out[name] = { codex: fresh.codex.length, moss: fresh.seeds.moss?.length ?? 0, pot: fresh.pot };
  }
  // Zero seeds and an empty pot on load: the starter set again.
  localStorage.setItem('terrarium-test', JSON.stringify({ ...JSON.parse(saved), pot: null, seeds: {} }));
  out.restock = Object.fromEntries(Object.entries(make().get().seeds).map(([k, v]) => [k, v.length]));
  localStorage.removeItem('terrarium-test');
  return out;
}"""

STRINGS = """async () => {
  const { SPECIES } = await import('./js/terrarium-species.js');
  const { STAGES } = await import('./js/terrarium.js');
  const { config } = await import('./js/config.js');
  return { species: SPECIES, statuses: STAGES.map((s) => s.status), titles: config.terrarium.words.titles };
}"""


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def check_rules(page):
    r = page.evaluate(RULES)
    check(r['fresh']['seeds'] == {'moss': 3, 'fern': 2, 'clover': 2} and r['fresh']['codex'] == [] and r['fresh']['pot'] is None
          and set(r['fresh']['hues']) == {3},
          f"a fresh start: 3 moss, 2 fern, 2 clover, hue 3, empty codex and pot ({r['fresh']['seeds']})")
    evap = 0.08 / (0.6 + 3 * 0.15)
    rate = (1 / 5.5) * (0.8 + 0.3) / 0.9   # a daisy (two stars) at vigor 3
    g = r['grow2h']
    check(approx(g['growth'], 2 * rate) and approx(g['hydration'], 1 - 2 * evap) and g['stage'] == 'young',
          f"2 hours, a daisy at vigor 3 / hardiness 3: growth {g['growth']:.4f} (expect {2 * rate:.4f}), "
          f"water {g['hydration']:.4f} (expect {1 - 2 * evap:.4f}), stage {g['stage']} {g['stack']}")
    wet = (0.2 - 0.10) / evap
    g = r['grow12h']
    check(approx(g['growth'], (2 + wet) * rate) and g['hydration'] == 0 and g['wilting'] and g['health'] == 0.5
          and g['stack'][0] == 'wilt',
          f"10 more hours from 20% water: grew only the {wet:.2f} h the soil stayed above 10% ({g['growth']:.4f}), "
          f"dry and wilting at health 0.5, wilt tiles {g['stack']}")
    ft = r['fullTime']
    check(all(ft[k]['before'] < 1 and ft[k]['after'] == 1 for k in ft) and ft['moss']['hours'] == 4 and ft['aurora']['hours'] == 10,
          f"growth time scales with rarity: the slowest moss is ready at {ft['moss']['hours']} h, the slowest aurora bloom at "
          f"{ft['aurora']['hours']} h, not before ({ft})")
    w = r['water']
    check(w['w1']['ok'] and w['w2'] == {'ok': False, 'reason': 'wait'} and w['w3']['ok'] and not w['wilting']
          and w['health'] == 0.5 and approx(w['hydration'], 0.5, 1e-3),
          f"watering clears wilting at once, +25% each, a second within 500 ms is ignored ({w['w2']}); health waits for a trim")
    sat = r['saturated']
    check(sat['w4']['saturated'] and sat['hydration'] == 1 and sat['status'] == 'Saturated!' and r['saturatedLater'] != 'Saturated!',
          f"watering past full: capped at 100%, \"{sat['status']}\" for a moment, then \"{r['saturatedLater']}\"")
    tr = r['trim']
    check(tr['result']['ok'] and approx(tr['drop'], 0.05, 1e-3) and tr['health'] == 1,
          f"trim: -0.05 growth ({tr['drop']:.3f}), health back to 1")
    wk = r['week']
    check(not wk['dead'] and wk['wilting'] and wk['hydration'] == 0 and wk['dryMs'] == 0,
          f"a week away counts as 48 h: thirsty and wilting, not dead, no dry time counted ({wk})")
    d = r['watched25h']
    check(r['watched23h'] is False and d['dead'] and set(d['stack']) == {'dead'} and d['status'] == 'Withered.'
          and d['water']['reason'] == 'dead',
          f"bone dry while visited: alive at 23 h, withered past 24 h ({d['stack']}), water refused")
    c = r['clear']
    check(c['result']['cleared'] and c['pot'] is None and c['seeds'] == 0,
          'a withered plant: harvest becomes Clear, empties the pot, no seeds')
    h = r['harvest']
    check(r['unripe']['reason'] == 'unripe' and h['h1']['seeds'] == 1 and h['h2']['seeds'] == 2 and h['h1']['gift'] in ('daisy', 'wildflower', 'mushroom')
          and h['h2']['gift'] is None and h['h1']['discovered'] and not h['h2']['discovered'] and h['codex'][:1] == ['bluebell'] and h['bluebells'] == 3 and h['gifted'],
          f"harvest: refused before 1.0; 1 seed at vigor 3, 2 at vigor 4; a flowering starter ({h['h1']['gift']}) on the first harvest "
          f"only; codex {h['codex']} (the first says it is new, the second not)")
    check(r['readyStack'] == ['stem_leaves', 'full'], f"a ready bluebell with bloom 2: {r['readyStack']}")
    p = r['pity']
    expect = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.40]
    check(all(approx(a, b) for a, b in zip(p['chances'], expect)) and p['stored'] == 7,
          f"failed crosses raise the chance 5 points each, capped at +25: {[round(c, 2) for c in p['chances']]}")
    hit = r['hit']
    check(hit['hit']['hit'] and hit['hit']['species'] == 'bluebell' and hit['pityAfter'] == 0 and hit['codex'],
          'a hit gives the hybrid, puts it in the codex and resets the pity')
    nh = r['noHybrid']
    check(nh['predict']['hybrid'] is None and nh['predict']['chance'] == 0 and nh['result']['ok']
          and nh['result']['species'] in ('moss', 'daisy'),
          f"a pair with no hybrid still crosses and gives a parent back ({nh['result']['species']})")
    check(not r['sameOne']['ok'] and r['sameTwo']['result']['ok'] and r['sameTwo']['result']['species'] == 'ivy'
          and r['sameTwo']['bloom'] == 0,
          'the same species twice needs two seeds, and gives that species back (a non-flowering one keeps bloom 0)')
    check(r['aurora']['result']['hit'] and r['aurora']['bloom'] >= 1,
          f"a flowering hybrid gets a bloom gene even from bloom-0 parents (aurora bloom {r['aurora']['bloom']})")
    st = r['stacks']
    expect_bluebell = ['seed', 'sprout', 'stem_leaves crown', 'stem_leaves * crown', 'stem_leaves bud', 'stem_leaves opening', 'stem_leaves full']
    ok_bb = all(e == a or (e.replace('*', a.split()[1]) == a and a.split()[1] in ('stem_leaves', 'stem_leaf_l', 'stem_leaf_r'))
                for e, a in zip(expect_bluebell, st['bluebell']))
    check(ok_bb and st['fern'][-1].endswith('crown') and len(st['fern'][-1].split()) == 3 and r['sameDraw'],
          f"tile stacks by stage, always ending in a crown or bloom: bluebell {st['bluebell']}; fern ends {st['fern'][-1]!r}; "
          'the same every redraw')
    check(r['reload'], 'a new page reads the same state back')
    check(all(r[k]['codex'] == 0 and r[k]['moss'] == 3 and r[k]['pot'] is None for k in ('garbage', 'version', 'badGenome')),
          'unreadable data, another version, or a malformed seed: a fresh start with the starter seeds')
    check(r['restock'] == {'moss': 3, 'fern': 2, 'clover': 2}, f"no seeds and an empty pot on load: the starter set again ({r['restock']})")


def check_strings(page):
    data = page.evaluate(STRINGS)
    too_long = []
    for s in data['species']:
        for key in ('name', 'blurb', 'flavour'):
            if len(s[key]) > 33:
                too_long.append(s[key])
        if len(s.get('short', s['name'])) * 4 - 1 > 39:
            too_long.append(s.get('short', s['name']))
    too_long += [x for x in data['statuses'] + ['Thirsty. Water me!', 'Saturated!', 'Withered.', 'Empty pot'] if len(x) > 19]
    too_long += [x for x in data['titles'] if len(x) > 33]
    check(not too_long, f"every journal string fits its line (33 characters, 19 beside the pot; bench names 39 px): {too_long or 'all fit'}")


def capture(page, name):
    png = base64.b64decode(page.evaluate('cabin.test.capture()').split(',', 1)[1])
    image = Image.open(io.BytesIO(png)).convert('RGBA')
    image.resize((960, 540), Image.NEAREST).save(SCREENS / f'terrarium_{name}.png')
    return image


def check_page(browser, base):
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    problems = watch_page(page)
    page.goto(base + '?test&time=day')
    page.wait_for_function('window.cabin && window.cabin.test')
    page.evaluate("localStorage.removeItem('cabin_terrarium')")
    page.reload()
    page.wait_for_function('window.cabin && window.cabin.test')
    left, top, scale = page.evaluate('(() => { const r = document.getElementById("scene").getBoundingClientRect(); return [r.left, r.top, r.width / 320]; })()')
    tick = [0]

    def advance():
        tick[0] += 1
        page.evaluate(f'cabin.test.advanceTo({tick[0]})')

    def click(x, y):
        page.mouse.click(left + (x + .5) * scale, top + (y + .5) * scale)
        advance()

    def hover(x, y):
        page.mouse.move(left + (x + .5) * scale, top + (y + .5) * scale)
        advance()
        return page.evaluate('document.getElementById("scene").style.cursor')

    pot = MANIFEST['terrarium_potshelf']
    journal = MANIFEST['terrarium_journal']
    PX, PY = journal['placement']['x'], journal['placement']['y']
    is_open = lambda: page.evaluate('cabin.app.journal.isOpen()')
    T = 'cabin.app.terrarium'

    # The pot on the wall: exactly its sprite, a hand over it, and it opens the journal.
    advance()
    closed = capture(page, 'closed')
    sprite = Image.open(ROOT / 'anim' / 'terrarium' / 'terrarium_potshelf_day.png').convert('RGBA')
    x0, y0 = pot['placement']['x'], pot['placement']['y']
    region = closed.crop((x0, y0, x0 + pot['frame_w'], y0 + pot['frame_h']))
    alpha = sprite.split()[3]
    same = all(a == b for a, b, m in zip(region.tobytes(), sprite.tobytes(), bytes(b for b in alpha.tobytes() for _ in range(4))) if m == 255)
    cursor = hover(x0 + 16, y0 + 20)
    click(x0 + 16, y0 + 20)
    opened = is_open()
    check(same and cursor == 'pointer' and opened,
          f'the pot is on the left wall as drawn ({same}), shows a hand ({cursor}), and a click opens the journal ({opened})')

    # Drawn over everything: the panel's opaque pixels are the journal's own.
    page.evaluate("cabin.app.weather.set('snow')")
    for _ in range(5):
        advance()
    over = capture(page, 'over_snow')
    panel = Image.open(ROOT / 'anim' / 'terrarium' / 'terrarium_journal_day.png').convert('RGBA')
    # Compare the empty strip of paper before the tabs (x 145-147) and the binding margin (x 0-8).
    probe = [(x, y) for x in list(range(0, 9)) + list(range(145, 148)) for y in range(2, 120) if panel.getpixel((x, y))[3] == 255]
    covered = sum(over.getpixel((PX + x, PY + y))[:3] == panel.getpixel((x, y))[:3] for x, y in probe)
    check(covered == len(probe), f'the journal is drawn over the snow and everything else ({covered}/{len(probe)} margin pixels exact)')
    page.evaluate("cabin.app.weather.set('clear')")

    # Tabs by mouse; the Seeds tab is inventory only now.
    tabs = journal['tab_ys']
    tab_x = journal['tab_x'] + journal['tab_w'] // 2
    on_paper = hover(PX + 100, PY + 95)
    click(PX + tab_x, PY + tabs[1] + 11)
    on_tab = page.evaluate(f'{T}.get().tab')
    click(PX + 14 + 8, PY + 26 + 8)          # moss
    capture(page, 'seeds')
    click(PX + 120, PY + 112)                # where the Plant button was
    nothing = page.evaluate(f'{T}.get().pot') is None
    check(on_paper == '' and on_tab == 1 and nothing,
          f'tabs switch on a click (seeds: {on_tab}); the Seeds tab plants nothing ({nothing}); plain paper keeps the arrow ({on_paper!r})')

    # The Pot tab, empty: the strip is a tray of your seeds; drag one to the pot.
    click(PX + tab_x, PY + tabs[0] + 11)
    tray = capture(page, 'tray')
    # The hint line under the meters (panel x 66-145, y 88-92): blank is the paper's own pixels.
    paper = Image.open(ROOT / 'anim' / 'terrarium' / 'terrarium_journal_day.png').convert('RGBA')
    hint_line = lambda img: img.crop((PX + 66, PY + 88, PX + 146, PY + 93)).tobytes()
    hint_blank = lambda img: hint_line(img) == paper.crop((66, 88, 146, 93)).tobytes()
    first_hint = not hint_blank(tray)
    rail = MANIFEST['terrarium_tools']['rail']
    slot = lambda i: (PX + rail['x'][i] + 8, PY + rail['y'] + 8)
    pot_at = (PX + 36, PY + 72)
    sx, sy = slot(0)
    page.mouse.move(left + (sx + .5) * scale, top + (sy + .5) * scale)
    page.mouse.down()
    advance()
    for i in range(1, 10):
        page.mouse.move(left + (sx + .5 + i * 1.5) * scale, top + (sy + .5 - i * 4) * scale)
        advance()
    glow_on = hover(*pot_at)
    capture(page, 'drag_seed')
    page.mouse.up()
    for _ in range(7):
        advance()
    planted = page.evaluate(f'{T}.get().pot && {T}.get().pot.species')
    check(planted == 'moss' and glow_on == 'grabbing', f'a seed dragged from the tray to the pot is planted ({planted}); a closed hand while dragging ({glow_on})')
    for _ in range(25):   # past the "Planted" status line
        advance()
    after_hint = capture(page, 'hint_gone')
    learned = page.evaluate(f'{T}.get().hints')
    check(first_hint and hint_blank(after_hint) and {'pot-pickup', 'pot-use', 'seeds-pick', 'seeds-plant'} <= set(learned),
          f'hints teach each step once: the Pot tab says what to do on a first visit ({first_hint}), and is quiet once a seed '
          f'has been picked up and planted ({hint_blank(after_hint)}); learned: {sorted(learned)}')

    # The rail: only tools that do something. A seedling: just the can.
    def soil_pane():
        img = capture(page, 'soil')
        return img.getpixel((PX + 12 + 24, PY + 54 + 14))[:3]
    # Click to equip the can (press and release in place), then click the pot.
    page.evaluate(f'{T}.get().pot.hydration = 0.2')
    advance()
    dry = soil_pane()
    click(*slot(0))
    hover(PX + 120, PY + 60)
    held = page.evaluate(f'{T}.get().pot.hydration')
    click(*pot_at)
    for _ in range(3):
        advance()
    mid = page.evaluate(f'{T}.get().pot.hydration')
    capture(page, 'pouring')
    for _ in range(5):
        advance()
    wet = page.evaluate(f'{T}.get().pot.hydration')
    page.evaluate(f'{T}.get().pot.hydration = 0.8')
    advance()
    soaked = soil_pane()
    check(held == 0.2 and mid > 0.2 and abs(wet - 0.45) < 0.01 and dry != soaked,
          f'the can, clicked then clicked on the pot, waters it on its third droplet frame ({held} -> {mid:.2f}); '
          f'the soil shows how wet it is ({dry} dry, {soaked} wet)')

    # A drag let go off the pot puts the tool back.
    sx, sy = slot(0)
    page.mouse.move(left + (sx + .5) * scale, top + (sy + .5) * scale)
    page.mouse.down()
    advance()
    page.mouse.move(left + (sx + 60.5) * scale, top + (sy - 40.5) * scale)
    advance()
    page.mouse.up()
    advance()
    click(*pot_at)
    for _ in range(8):
        advance()
    unchanged = page.evaluate(f'{T}.get().pot.hydration')
    check(abs(unchanged - 0.8) < 0.01, f'a drag let go off the pot puts the can back: a later click on the pot does nothing ({unchanged:.2f})')

    # Ripe: can, shears, basket; the basket harvests and the tray comes back.
    page.evaluate(f'(() => {{ const p = {T}.get().pot; p.growth = 1; {T}.tick(); }})()')
    advance()
    capture(page, 'ripe')
    click(*slot(2))
    click(*pot_at)
    for _ in range(9):
        advance()
    harvested = page.evaluate(f'({{ pot: {T}.get().pot, moss: {T}.count("moss"), codex: {T}.get().codex }})')
    check(harvested['pot'] is None and 'moss' in harvested['codex'],
          f'the basket, the third tool on a ripe plant, harvests it ({harvested})')

    # The keyboard: Tab to the first tray seed, Enter, Tab round to the pot, Enter.
    page.focus('#input')
    page.keyboard.press('Tab')
    page.keyboard.press('Enter')
    targets = page.evaluate(f'Object.keys({T}.get().seeds).length') + 1
    for _ in range(targets - 1):
        page.keyboard.press('Tab')
    page.keyboard.press('Enter')
    for _ in range(7):
        advance()
    by_keys = page.evaluate(f'{T}.get().pot && {T}.get().pot.species')
    typed = page.input_value('#input')
    check(by_keys is not None and typed == '', f'the keyboard plants a seed: Tab, Enter, Tab to the pot, Enter ({by_keys}); nothing typed on the prompt ({typed!r})')
    page.evaluate(f'(() => {{ const s = {T}.get(); s.pot = null; }})()')
    page.evaluate('cabin.app.journal.close()')
    page.evaluate('cabin.app.journal.open(0)')
    advance()

    # The crossing bench: pick two parents from the seed grid, cross.
    page.evaluate(f"{T}.plant('moss')")
    click(PX + tab_x, PY + tabs[2] + 11)
    click(PX + 30, PY + 42)                  # parent A
    picking = capture(page, 'picker')
    click(PX + 14 + 22 + 8, PY + 26 + 8)     # fern
    click(PX + 70, PY + 42)                  # parent B
    click(PX + 14 + 44 + 8, PY + 26 + 8)     # clover
    capture(page, 'bench')
    before = page.evaluate(f'({T}.count("fern") + {T}.count("clover") + {T}.count("ivy"))')
    click(PX + 76, PY + 112)                 # Cross
    after = page.evaluate(f'({T}.count("fern") + {T}.count("clover") + {T}.count("ivy"))')
    capture(page, 'crossed')
    check(before - after == 1, f'the bench crosses fern x clover: two seeds in, one back ({before} -> {after})')
    page.reload()
    page.wait_for_function('window.cabin && window.cabin.test')
    kept = page.evaluate(f'{T}.get().hints')
    page.evaluate('cabin.app.journal.open(2)')
    advance()
    check({'cross-pick', 'cross-cancel', 'cross-go'} <= set(kept) and set(learned) <= set(kept),
          f'the crossing bench hints are learned by using it, and every learned hint stays learned after a reload ({sorted(kept)})')

    # The terminal changes the open journal without switching its tab.
    page.wait_for_timeout(600)   # watering is debounced 500 ms in real time; the can was used moments ago
    page.evaluate("cabin.run('water')")
    advance()
    tab = page.evaluate(f'{T}.get().tab')
    water = page.evaluate(f'{T}.get().pot.hydration')
    check(tab == 2 and water > 0.5, f'`water` with the journal open: the pot is watered ({water:.2f}), the tab stays ({tab})')

    # Every time of day, and the codex, with a grown, flowering plant.
    page.evaluate(f"""(() => {{ const s = {T}.get(); s.pot = null; s.seeds.aurora = [{{ height: 3, bloom: 2, vigor: 3, hue: 4, hardiness: 3 }}];
                      {T}.plant('aurora'); s.pot.growth = 1; s.pot.hydration = 1; {T}.tick(); s.codex.push('moss', 'aurora'); }})()""")
    page.evaluate(f'{T}.setTab(0)')
    for time in ('morning', 'day', 'afternoon', 'night'):
        page.evaluate(f"cabin.app.timeOfDay.set('{time}', {{ instant: true }})")
        advance()
        capture(page, f'pot_{time}')
    page.evaluate("cabin.app.timeOfDay.set('day', { instant: true })")
    click(PX + tab_x, PY + tabs[3] + 11)
    click(PX + 13 + 22 * 5 + 8, PY + 26 + 30 + 8)
    capture(page, 'codex')

    # Closing: a click outside, the pot again, Escape; the keyboard button opens it.
    click(300, 170)
    outside = not is_open()
    click(x0 + 16, y0 + 20)
    click(x0 + 16, y0 + 20)
    pot_again = not is_open()
    page.focus('button.scene-hotspot:has-text("Terrarium")')
    page.keyboard.press('Enter')
    advance()
    by_key = is_open()
    page.keyboard.press('Escape')
    advance()
    escaped = not is_open()
    # The red X at the top right, on every tab.
    close = MANIFEST['terrarium_close']['placement']
    by_x = []
    for t in range(4):
        page.evaluate(f'cabin.app.journal.open({t})')
        advance()
        cursor_x = hover(PX + close['x'] + 5, PY + close['y'] + 5)
        click(PX + close['x'] + 5, PY + close['y'] + 5)
        by_x.append(not is_open() and cursor_x == 'pointer')
    check(all(by_x), f'the close button at the top right shows a hand and closes the journal on every tab ({by_x})')
    check(outside and pot_again and by_key and escaped,
          f'closes on a click outside ({outside}), on the pot ({pot_again}), on Escape ({escaped}); the Terrarium button opens it ({by_key})')

    # Commands print in character.
    replies = {}
    for line in ('terrarium status', 'plant fern', 'seeds', 'codex', 'cross moss aurora bloom'):
        page.evaluate(f'cabin.run({line!r})')
        replies[line] = page.inner_text('#bubble').strip().splitlines()[-1]
    check(replies['plant fern'] == "the pot's already got an aurora bloom in it."
          and replies['cross moss aurora bloom'] == 'you need an aurora bloom seed for that.',
          f'commands answer in character: {replies}')
    check(not problems, f'no console problems ({problems})')
    page.close()


def main():
    SCREENS.mkdir(parents=True, exist_ok=True)
    base, stop = serve_site()
    with sync_playwright() as p:
        browser = open_browser(p)
        page = browser.new_page()
        page.goto(base + '?test')
        page.wait_for_function('window.cabin && window.cabin.test')
        check_rules(page)
        check_strings(page)
        page.close()
        check_page(browser, base)
        browser.close()
    stop()
    (RESULTS / 'terrarium.md').write_text('# Terrarium checks\n' + '\n'.join(report) + '\n', encoding='utf-8')
    print(f'{len(report) - len(failures)} / {len(report)} passed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
