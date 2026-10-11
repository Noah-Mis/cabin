"""achievements.py — checks for the 13 achievements, their rewards and the edges.

1. Each achievement, from a fresh (reset) browser profile: earned the real
   way at least once (real clicks on the real sasquatch, birds, stars, cup,
   pack, folder tabs; real commands; real visible time), using ?debug only to
   skip grinding (e.g. set birdClicks to 49 and click the 50th). Then: the
   sign and the terminal line appear exactly once, the reward is on screen,
   and after a reload both the unlock and the reward persist with no new sign.
2. Rewards drawn in the right place and layer: the site's pixels are compared
   with a reference built the way anim/achievements/achieve.py composes its
   preview (background, sky layer clipped by the sky mask, creatures, near
   forest, window, sill items), by day and by night.
3. Edges: two unlocks at once; clicking where a creature was; a star by day;
   reset then earn again; storage disabled; hand-edited and older saved data;
   the tab hidden not counting as time on the page.
4. Screenshots of the scene with every reward on, by day and by night.
5. The deer's visit (anim/achievements/deer_brief.md): the pond bank for
   everyone; the tree cover invisible on its own; a whole visit by day and
   night, measuring how far right and down the deer reaches and that each act
   starts and ends hidden; each stage against deer_route_check.png; rain, a
   click and night falling mid-visit; never alongside the sasquatch.
6. The achievement board: idle, hovered and night pixel-exact against
   anim/board's mockups; each unlock lights its own pin (with a sparkle);
   the pop-up's art against its mockup; nothing earned, partway, unlocking
   while open, everything earned; arrow keys, X, Escape, click outside;
   keyboard only from the terminal; touch on a phone; `badges` retired.

Writes tests/results/achievements.md and tests/results/achievements/.
Run:  python tests/achievements.py
"""
import base64, io, json, os, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from harness import ROOT, RESULTS, BOARD, serve_site, open_browser, watch_page, canvas_pixels, add_board, add_pond_bank

ANIM = ROOT / 'anim'
ACH_DIR = ANIM / 'achievements'
ACH = json.loads((ACH_DIR / 'achievements.json').read_text())
DEFS = {a['id']: a for a in ACH['achievements']}
SPRITES = ACH['animations']
MAIN = json.loads((ANIM / 'manifest.json').read_text())
CONFIG = (ROOT / 'js' / 'config.js').read_text()
OUT = RESULTS / 'achievements'
TEST = '?test&debug&timing=reference'   # deterministic, sheets at their JSON speeds
report, failures = [], []

# Records every unlock sign shown and every "achievement unlocked" terminal
# line, across the whole page life, with timestamps.
WATCH = """
window.__signs = []; window.__unlockLines = [];
new MutationObserver((records) => {
  for (const r of records) {
    const node = r.target.nodeType === 1 ? r.target : r.target.parentElement;
    if (node && node.classList.contains('us-name') && node.textContent)
      __signs.push({ name: node.textContent, t: performance.now() });
    for (const added of r.addedNodes) {
      if (added.nodeType === 1 && added.classList.contains('line') && added.textContent.startsWith('achievement unlocked:'))
        __unlockLines.push(added.textContent);
    }
  }
}).observe(document, { subtree: true, childList: true, characterData: true });
"""


def check(ok, what):
    report.append(f"- {'PASS' if ok else 'FAIL'}: {what}")
    if not ok:
        failures.append(what)
    print(report[-1].encode('ascii', 'replace').decode())


def config_number(name):
    """A number from js/config.js, e.g. `showMs: 4000,` or `auroraChancePerNight: 1 / 3,`."""
    raw = re.search(r'\b' + name + r':\s*([^,\n]+)', CONFIG).group(1).split('//')[0].strip()
    top, _, bottom = raw.partition('/')
    return float(top) / float(bottom) if bottom else float(top)


class Visit:
    """One page of the site, with helpers. Reusing `context` keeps localStorage."""

    def __init__(self, browser, base, query, context=None, init_script=None, **context_options):
        self.context = context or browser.new_context(viewport={'width': 1280, 'height': 752}, **context_options)
        if init_script and context is None:
            self.context.add_init_script(init_script)
        self.page = self.context.new_page()
        self.page.add_init_script(WATCH)
        self.problems = watch_page(self.page)
        self.query, self.base, self.browser = query, base, browser
        self.page.goto(base + 'index.html' + query)
        self.page.wait_for_function('window.cabin && window.cabin.app')
        self.tick = 0
        if 'test' in query:
            self.page.wait_for_function('window.cabin.test')

    def reload(self):
        return Visit(self.browser, self.base, self.query, context=self.context)

    def close(self):
        self.context.close()

    def cmd(self, line):
        self.page.focus('#input')
        self.page.keyboard.type(line)
        self.page.keyboard.press('Enter')
        return self.page.eval_on_selector_all('#bubble:not([hidden]) .line', 'e => e.map(x => x.textContent)')

    def to(self, tick):
        self.tick = max(self.tick, tick)
        self.page.evaluate(f'cabin.test.advanceTo({self.tick})')

    def frame(self, tick=None):
        self.to(self.tick if tick is None else tick)
        return canvas_pixels(self.page)

    def screen(self, x, y):
        r = self.page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        return r[0] + (x + 0.5) * r[2] / 320, r[1] + (y + 0.5) * r[3] / 180

    def click(self, x, y):
        self.page.mouse.click(*self.screen(x, y))
        self.to(self.tick)

    def stats(self):
        return self.page.evaluate('cabin.app.progressStats()')

    def unlocked(self, id_):
        return self.page.evaluate(f"cabin.achievements.isUnlocked('{id_}')")

    def signs(self):
        return [s['name'] for s in self.page.evaluate('__signs')]

    def lines(self):
        return self.page.evaluate('__unlockLines')

    def shot(self, name):
        self.page.screenshot(path=str(OUT / f'{name}.png'))


BOARD_DIR = ANIM / 'board'
BOARD_LAYOUT = json.loads((BOARD_DIR / 'board_layout.json').read_text())
BX, BY = BOARD['canvas_x'], BOARD['canvas_y']
BOARD_BOX = (slice(BY - 1, BY + BOARD['h'] + 1), slice(BX - 1, BX + BOARD['w'] + 1))   # with its outline
ORDER = [a['id'] for a in ACH['achievements']]


def diff(a, b):
    return np.any(a != b, axis=2)


# ── reference composition (achieve.py's preview layering) ──────────────────
def sheet_frame(name, frame, time):
    if name in SPRITES:
        info, base = SPRITES[name], ACH_DIR
    elif name in MAIN['animations']:
        info, base = MAIN['animations'][name], ANIM
    else:
        info, base = FOLDER['animations'][name], ANIM / 'folder'
    files = info['files']
    pick = next((f for f in files if f.endswith(f'_{time}.png')), None) or next(
        f for f in files if not any(f.endswith(f'_{t}.png') for t in ('morning', 'day', 'afternoon', 'night')))
    im = Image.open(base / pick).convert('RGBA')
    return im.crop((frame * info['frame_w'], 0, (frame + 1) * info['frame_w'], info['frame_h'])), info


def reference(time, layers):
    """layers: list of (group, sprite name, frame, anchor x, anchor y, mirrored)."""
    c = Image.open(ANIM / 'scene' / f'bg_{time}.png').convert('RGBA')
    sky = Image.new('RGBA', (320, 180), (0, 0, 0, 0))
    front, sill = [], []
    for group, name, frame, x, y, mirrored in layers:
        im, info = sheet_frame(name, frame, time)
        ax, ay = info['anchor']
        if mirrored:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            pos = (x - (info['frame_w'] - 1 - ax), y - ay)
        else:
            pos = (x - ax, y - ay)
        {'sky': lambda: sky.alpha_composite(im, pos), 'front': lambda: front.append((im, pos)),
         'sill': lambda: sill.append((im, pos))}[group]()
    mask = Image.open(ANIM / 'scene' / 'sky_mask.png').convert('RGBA').split()[3]
    c.alpha_composite(Image.composite(sky, Image.new('RGBA', (320, 180), (0, 0, 0, 0)), mask))
    add_pond_bank(c, time)   # scenery, under the creatures
    for im, pos in front:
        c.alpha_composite(im, pos)
    c.alpha_composite(Image.open(ANIM / 'scene' / f'near_forest_{time}.png').convert('RGBA'))
    window = 'cabin_window_night.png' if time == 'night' else 'cabin_window.png'   # manifest "window" entry
    c.alpha_composite(Image.open(ANIM / 'scene' / window).convert('RGBA'))
    add_board(c, time)   # empty: unlocks also light pins there, which check_board() covers
    for im, pos in sill:
        c.alpha_composite(im, pos)
    return np.asarray(c)


def compare_reward(label, time, site_with, site_without, layer, note='', base=(), replaces=None):
    """Do the pixels the reward changes on the site match the reference's?
    base: layers already in the scene (e.g. the folder under its seal);
    replaces: the layer the reward is drawn instead of (the old mug)."""
    ref_with = reference(time, [*base, layer])
    ref_without = reference(time, [*base, *([replaces] if replaces else [])])
    behind_agree = ~diff(site_without, ref_without)
    behind_agree[BOARD_BOX] = False   # the unlock also lights a pin on the board; check_board() covers that
    site_d = diff(site_with, site_without) & behind_agree
    ref_d = diff(ref_with, ref_without) & behind_agree
    covered = int((diff(ref_with, ref_without) & ~behind_agree).sum())
    both = site_d & ref_d
    same_bg = both
    delta = np.abs(site_with.astype(int) - ref_with.astype(int)).max(axis=2)
    exact = int((same_bg & (delta == 0)).sum())
    near = int((same_bg & (delta <= 1)).sum())
    agree = both.sum() / max(1, max(site_d.sum(), ref_d.sum()))
    if covered:
        note = (note + '; ' if note else '') + f'{covered} reward px are under things the site draws in front (e.g. clouds), not compared'

    Image.fromarray(np.concatenate([site_with, ref_with], axis=1)).resize((1280, 360), Image.NEAREST) \
        .save(OUT / f'reward_{label}.png')
    ok = agree >= 0.9 and same_bg.sum() > 0 and near == same_bg.sum()
    check(ok, f'{label} ({time}): {site_d.sum()} px changed on the site, {ref_d.sum()} in the reference, '
              f'{agree:.0%} in the same place; colours where the scenes behind agree: {exact}/{same_bg.sum()} '
              f'exact, {near}/{same_bg.sum()} within 1{(" - " + note) if note else ""}')
    return ok


def run_script(v, script):
    for tick, line in sorted(script, key=lambda s: s[0]):
        v.to(tick)
        v.cmd(line)


def pair(browser, base, time, script, tick, reward_script):
    """The same deterministic scene at `tick`, with and without the reward."""
    shots = []
    for extra in (reward_script, []):
        v = Visit(browser, base, f'{TEST}&time={time}')
        run_script(v, script + extra)
        shots.append(v.frame(tick))
        v.close()
    return shots


def check_reward_rendering(browser, base):
    report.append('\n## Rewards drawn in place (site vs achieve.py-style reference)\n')
    spots = MAIN['animations']['sasquatch_peek']['placement']['spots']
    fold = ['whoami']
    for time in ('day', 'night'):
        # Sill items: the same tick with and without the unlock.
        for rid, name, pre in (('caffeinated', 'mug_camp', []), ('smoke_break', 'ashtray', []),
                               ('woodsman', 'trophy', []), ('case_closed', 'folder_reviewed', fold)):
            p = SPRITES[name]['placement']
            w, wo = pair(browser, base, time, [(0, c) for c in pre], 18, [(15, f'debug unlock {rid}')])
            extra = {}
            if name == 'mug_camp':      # 1800 ms: the camp mug (150 ms) is on frame 0, the mug (200 ms in test timing) on 3
                extra['replaces'] = ('sill', 'mug', (1800 // 200) % 6, p['x'], p['y'], False)
            if name == 'folder_reviewed':
                extra['replaces'] = ('sill', 'folder', 0, p['x'], p['y'], False)
            frame = (1800 // SPRITES[name]['ms_per_frame']) % SPRITES[name]['frames'] if SPRITES[name]['ms_per_frame'] else 0
            compare_reward(f'{name}_{time}', time, w, wo, ('sill', name, frame, p['x'], p['y'], False), **extra)
    # Night sky: constellation and aurora (under the stars), shooting star.
    p = SPRITES['constellation_sasquatch']['placement']
    w, wo = pair(browser, base, 'night', [], 12, [(0, 'debug unlock stargazer')])
    compare_reward('constellation', 'night', w, wo, ('sky', 'constellation_sasquatch', 0, p['x'], p['y'], False),
                   'the site also twinkles stars on top')
    tick = 72   # more than the 6000 ms fade after the event at tick 2; treetops at rest (7200 % 1200 = 0)
    frame = (tick * 100 // SPRITES['aurora']['ms_per_frame']) % SPRITES['aurora']['frames']
    p = SPRITES['aurora']['placement']
    w, wo = pair(browser, base, 'night', [(0, 'debug unlock around_the_clock')], tick, [(2, 'debug event aurora')])
    compare_reward('aurora', 'night', w, wo, ('sky', 'aurora', frame, p['x'], p['y'], False),
                   'translucent; the site draws stars and clouds over it')
    w, wo = pair(browser, base, 'night', [(0, 'debug unlock night_owl')], 26,
                 [(24, 'debug event shootingstar x=170 y=30')])
    compare_reward('shooting_star', 'night', w, wo, ('sky', 'shooting_star', 3, 170, 30, False))   # 200 ms / 60 ms = frame 3
    # The gold-seal folder sliding onto the sill (whoami after Case Closed),
    # half a second in: frame 4 at 120 ms a frame, in place of the plain slide-in.
    p = SPRITES['folder_reviewed_place']['placement']
    w, wo = pair(browser, base, 'day', [(1, 'whoami')], 6, [(0, 'debug unlock case_closed')])
    compare_reward('folder_reviewed_place', 'day', w, wo, ('sill', 'folder_reviewed_place', 4, p['x'], p['y'], False),
                   replaces=('sill', 'folder_place', 4, p['x'], p['y'], False))
    # Rainbow after rain, at full strength.
    p = SPRITES['rainbow']['placement']
    w, wo = pair(browser, base, 'day', [(0, 'debug unlock storm_chaser')], 36, [(0, 'weather rain'), (2, 'weather clear')])
    compare_reward('rainbow', 'day', w, wo, ('front', 'rainbow', 0, p['x'], p['y'], False), 'translucent')
    # Sasquatch wave, yeti wave and yeti peek at manifest spots.
    for label, time, unlocks, creature, spot, sheet, start, tick in (
            ('sasquatch_wave', 'day', ['first_sighting'], 'sasquatch', 0, 'sasquatch_wave', 2, 12),
            ('yeti_wave', 'night', ['first_sighting', 'cryptid_hunter'], 'yeti', 5, 'yeti_wave', 4, 12),
            ('yeti_peek', 'day', ['cryptid_hunter'], 'yeti', 2, 'yeti_peek', 4, 12)):
        script = [(0, f'debug unlock {u}') for u in unlocks]
        w, wo = pair(browser, base, time, script, tick,
                     [(start, f'debug event sasquatch spotindex={spot} creature={creature}')])
        f = (tick - start) * 100 // SPRITES[sheet]['ms_per_frame']
        compare_reward(label, time, w, wo, ('front', sheet, f, spots[spot]['x'], spots[spot]['y'], False),
                       'behind the near forest')
    # The deer has its own section: check_deer().
    # Golden birds, on the frame they appear (no trail yet).
    w, wo = pair(browser, base, 'day', [(0, 'debug unlock bird_watcher')], 12, [(12, 'debug event bird x=128 y=56 direction=1')])
    compare_reward('bird_flap_shiny', 'day', w, wo, ('front', 'bird_flap_shiny', 0, 128, 56, False))
    w, wo = pair(browser, base, 'day', [(0, 'debug unlock bird_watcher')], 12, [(12, 'debug event farbird x=233 y=43 direction=-1')])
    compare_reward('bird_far_shiny', 'day', w, wo, ('sky', 'bird_far_shiny', 0, 233, 43, True))


def check_sign_art(browser, base):
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('debug unlock bird_watcher')
    v.page.wait_for_function("document.querySelector('.us').classList.contains('is-down')")
    v.page.wait_for_timeout(700)   # slide finished
    v.page.add_style_tag(content='.us-text { visibility: hidden !important; }')
    v.page.wait_for_timeout(50)
    shot = np.asarray(Image.open(io.BytesIO(v.page.screenshot())).convert('RGBA')).astype(int)
    g = v.page.evaluate("(() => { const r = document.querySelector('.us-board').getBoundingClientRect(); return [r.left, r.top, r.width]; })()")
    scale = round(g[2] / ACH['sign']['w'])
    art = Image.open(ACH_DIR / ACH['sign']['file']).convert('RGBA')
    badge = Image.open(ACH_DIR / ACH['badges']['file']).convert('RGBA').crop((16, 0, 32, 16))   # bird_watcher = frame 1
    art.alpha_composite(badge, (ACH['sign']['badge_slot']['x'], ACH['sign']['badge_slot']['y']))
    big = np.repeat(np.repeat(np.asarray(art).astype(int), scale, 0), scale, 1)
    x0, y0 = round(g[0]), round(g[1])
    region = shot[y0:y0 + big.shape[0], x0:x0 + big.shape[1]]
    opaque = big[..., 3] == 255
    exact = region.shape == big.shape and bool(np.all(region[opaque][:, :3] == big[opaque][:, :3]))
    canvas_y = v.page.evaluate("document.getElementById('scene').getBoundingClientRect().top")
    sign_art_y = (g[1] - canvas_y) / scale
    check(exact and abs(sign_art_y - (MAIN['window_opening']['y'] + 4)) < 0.01,
          f'unlock sign: art and badge pixel-exact at {scale}x, at art y {sign_art_y:g} (4 below the window opening), '
          f'name as real text: "{v.page.text_content(".us-name")}"')
    v.close()


# ── the 13, each from a fresh profile ──────────────────────────────────────
def earn_each(browser, base):
    report.append('\n## Each achievement, earned from a reset state, then reloaded\n')
    spots = MAIN['animations']['sasquatch_peek']['placement']['spots']
    opening = MAIN['window_opening']

    def click_sasquatch(v, spot):
        v.cmd(f'debug event sasquatch spotindex={spot}')
        v.to(v.tick + 8)   # risen
        v.click(spots[spot]['x'], spots[spot]['y'] - 8)
        v.click(spots[spot]['x'], spots[spot]['y'] - 8)   # a second click on the same appearance
        return v.stats()['stats'].get('sasquatchClicks')

    flows = []

    def flow(id_, time='day'):
        def wrap(fn):
            flows.append((id_, time, fn))
            return fn
        return wrap

    @flow('first_sighting')
    def _(v):
        n = click_sasquatch(v, 1)
        return f'clicked the real sasquatch twice in one appearance: sasquatchClicks = {n}', n == 1

    @flow('bird_watcher')
    def _(v):
        for i, y in enumerate((50, 64, 72)):
            v.cmd(f'debug event bird x={60 + 50 * i} y={y} direction=1')
        v.to(v.tick + 1)
        for i, y in enumerate((50, 64, 72)):
            v.click(60 + 50 * i + 5, y)        # where each bird is one tick (5 px) later
        real = v.stats()['stats'].get('birdClicks')
        v.cmd('debug set birdclicks 49')
        v.cmd('debug event bird x=200 y=60 direction=-1')
        v.to(v.tick + 1)
        v.click(195, 60)
        return f'3 real bird clicks counted ({real}), set to 49, the 50th clicked for real', real == 3

    @flow('cryptid_hunter')
    def _(v):
        v.cmd('debug set sasquatchclicks 9')
        n = click_sasquatch(v, 3)
        return f'sasquatchClicks 9 -> {n} by clicking the real sasquatch', n == 10

    @flow('caffeinated')
    def _(v):
        mug = MAIN['animations']['mug']['placement']
        sip = MAIN['animations']['mug_sip']
        sip_ticks = sip['frames'] * sip['ms_per_frame'] // 100 + 1
        v.click(mug['x'], mug['y'] - 10)
        v.click(mug['x'], mug['y'] - 10)      # mid-sip: the cup is in the visitor's hand
        during = v.stats()['stats'].get('mugClicks')
        for _ in range(24):
            v.to(v.tick + sip_ticks)
            v.click(mug['x'], mug['y'] - 10)
        n = v.stats()['stats'].get('mugClicks')
        return f'25 real sips from the cup ({n}); a click mid-sip did not count ({during})', n == 25 and during == 1

    @flow('smoke_break')
    def _(v):
        v.cmd('cig')
        v.to(v.tick + 15)
        pk = SPRITES_SMOKE['cig_pack']
        v.click(pk['placement']['x'] + 2, pk['placement']['y'] - 6)
        smoke = sum(SMOKE['animations'][s.get('play') or s['loop']]['frames'] * 120 * s.get('times', 1)
                    for s in SMOKE['sequences']['smoke']['steps']) + SMOKE['animations']['cig_pick']['frames'] * 120
        mid = v.unlocked('smoke_break')
        v.to(v.tick + smoke // 100 + 2)
        return f'cig, clicked the pack, let all {smoke / 1000:.1f} s play (not earned half-way: {not mid})', not mid

    @flow('case_closed')
    def _(v):
        v.cmd('whoami')
        v.to(v.tick + 15)
        v.click(160, 140)
        v.to(v.tick + 15)
        v.page.wait_for_selector('.fp-backdrop.is-visible')
        for tab in ('resume', 'projects', 'contact'):
            v.page.evaluate(f"[...document.querySelectorAll('.fp-tab')].find(b => b.textContent === '{tab}').click()")
        seen = v.stats()['stats'].get('tabsSeen')
        v.page.keyboard.press('Escape')
        v.to(v.tick + 15)
        v.page.mouse.move(2, 2)
        return f'opened the folder and clicked the other three tabs: tabsSeen = {seen}', sorted(seen or []) == sorted(['about', 'resume', 'projects', 'contact'])

    @flow('night_owl')
    def _(v):
        before = v.unlocked('night_owl')
        v.cmd('time night')
        mid = v.unlocked('night_owl')
        v.to(v.tick + 20)   # the fade finishes
        return f'`time night`: not earned mid-fade ({not mid}), earned once night is shown', not before and not mid

    @flow('around_the_clock', 'morning')
    def _(v):
        for t in ('day', 'afternoon', 'night'):
            v.cmd(f'time {t}')
            v.to(v.tick + 20)
        return f'morning (start) then day, afternoon, night: timesSeen = {v.stats()["stats"].get("timesSeen")}', True

    @flow('storm_chaser')
    def _(v):
        v.cmd('weather rain')
        half = v.unlocked('storm_chaser')
        v.cmd('weather clear')
        v.cmd('weather snow')
        return f'rain (not enough on its own: {not half}), clear, snow: weatherSeen = {v.stats()["stats"].get("weatherSeen")}', not half

    @flow('stargazer')
    def _(v):
        v.cmd('time night')
        v.to(v.tick + 20)
        stars = ACH['star_click_targets']
        v.click(*stars[0])
        v.click(*stars[0])   # the same star twice counts once
        once = v.stats()['stats'].get('starClicks')
        for sx, sy in stars[1:10]:
            v.click(sx, sy)
        return f'10 real star clicks (the same star twice counted {once})', once == 1

    @flow('power_user')
    def _(v):
        before = v.page.evaluate("getComputedStyle(document.getElementById('terminal')).backgroundColor")
        for line in ('help', 'time day', 'weather clear', 'clear', 'badges', 'ls', 'rm mug', 'touch mug'):   # hidden ones don't count
            v.cmd(line)
        almost = v.unlocked('power_user')
        theme_before = v.cmd('theme green')
        v.cmd('whoami')
        after = v.cmd('theme green')
        bg = v.page.evaluate("getComputedStyle(document.getElementById('terminal')).backgroundColor")
        want = ACH['terminal_theme_green']['background']
        want_rgb = 'rgb(%d, %d, %d)' % tuple(int(want[i:i + 2], 16) for i in (1, 3, 5))
        return (f'help, clear, and the hidden `badges`, `ls`, `rm`, `touch`: not yet ({not almost}); `theme` unknown before ({theme_before[0][:25]}...); '
                f'after `whoami`: `theme green` -> {after[-1]!r}, terminal background {bg} (JSON {want})',
                not almost and 'no such command' in theme_before[0] and bg == want_rgb and before != bg)

    @flow('woodsman')
    def _(v):
        for id_ in list(DEFS)[:-1]:
            if id_ != 'night_owl':
                v.cmd(f'debug unlock {id_}')
        eleven = v.unlocked('woodsman')
        v.cmd('time night')           # night_owl for real, the 12th
        v.to(v.tick + 20)
        return f'11 unlocked by debug (no trophy yet: {not eleven}), the 12th (Night Owl) for real', not eleven

    for id_, time, fn in flows:
        d = DEFS[id_]
        v = Visit(browser, base, f'{TEST}&time={time}')
        fresh = v.stats()['unlocked'] == [] and v.signs() == []
        detail, real_ok = fn(v)
        earned = v.unlocked(id_)
        if earned:
            v.page.wait_for_function(f"__signs.some(s => s.name === {json.dumps(d['name'])})", timeout=120000)
            v.page.wait_for_timeout(500)
        signs_for = [s for s in v.signs() if s == d['name']]
        line = f'achievement unlocked: {d["name"]}. {d["reward"]}.'
        lines_for = [l for l in v.lines() if l == line]
        reward_ok, reward_note = reward_on_screen(v, id_)
        v.shot(f'earned_{id_}')
        again = v.reload()
        persists = again.unlocked(id_)
        reward_again, _ = reward_on_screen(again, id_)
        no_new_sign = d['name'] not in again.signs()
        problems = v.problems + again.problems
        if not fresh:
            detail += f' (NOT a fresh start: {v.stats()})'
        check(fresh and real_ok and earned and len(signs_for) == 1 and len(lines_for) == 1 and reward_ok
              and persists and reward_again and no_new_sign and not problems,
              f'**{d["name"]}** (`{id_}`): {detail}. Earned: {earned}; sign shown {len(signs_for)}x, terminal line '
              f'{len(lines_for)}x; reward: {reward_note}; after reload: still earned {persists}, reward {reward_again}, '
              f'no new sign {no_new_sign}' + (f'; console: {problems}' if problems else ''))
        v.close()


def folder_sheets_used(v):
    """Closed, opening and closing all use the gold-seal sheets, pixel for pixel."""
    t = v.page.evaluate("cabin.app.timeOfDay.current()")
    results = []
    for name, frame, ticks_in in (('folder_reviewed', 0, None), ('folder_reviewed_open', 4, 5),
                                  ('folder_reviewed_close', 4, 5)):
        im, info = sheet_frame(name, frame, t)
        p = info['placement']
        left, top = p['x'] - info['anchor'][0], p['y'] - info['anchor'][1]
        if ticks_in is not None:
            if name == 'folder_reviewed_open':
                v.click(160, 140)
            else:
                v.page.keyboard.press('Escape')   # closes the pop-up and the folder
            start = v.tick
            v.to(start + ticks_in)                # 500 ms in: frame 4 at 110 ms a frame
        v.page.mouse.move(2, 2)
        f = v.frame()
        a = np.asarray(im)
        solid = a[..., 3] == 255
        region = f[top:top + a.shape[0], left:left + a.shape[1]]
        results.append(bool(np.all(region[solid][:, :3] == a[solid][:, :3])))
        if name == 'folder_reviewed_open':
            v.to(v.tick + 15)
            v.page.wait_for_selector('.fp-backdrop.is-visible')
    v.to(v.tick + 15)
    ok = all(results)
    return ok, f'gold-seal folder at rest / opening / closing pixel-exact: {results}'


def config_text(name):
    return re.search(rf"{name}:\s*'([^']*)'", CONFIG).group(1)


FOLDER = json.loads((ANIM / 'folder' / 'folder_manifest.json').read_text())
SMOKE = json.loads((ANIM / 'smoke' / 'smoke_manifest.json').read_text())
SPRITES_SMOKE = SMOKE['animations']


def reward_on_screen(v, id_):
    """Is this achievement's reward visible / in effect on this page right now?"""
    spots = MAIN['animations']['sasquatch_peek']['placement']['spots']
    v.to(v.tick + 150)   # 15 s: earlier birds and appearances have left, clouds have drifted on
    if id_ in ('caffeinated', 'smoke_break', 'woodsman', 'case_closed'):
        name = {'caffeinated': 'mug_camp', 'smoke_break': 'ashtray', 'woodsman': 'trophy', 'case_closed': 'folder_reviewed'}[id_]
        if id_ == 'case_closed':
            v.cmd('whoami')
            v.to(v.tick + 15)
        v.page.mouse.move(2, 2)
        t = v.page.evaluate("cabin.app.timeOfDay.current()")
        im, info = sheet_frame(name, 0, t)
        a = np.asarray(im)
        p = info['placement']
        left, top = p['x'] - info['anchor'][0], p['y'] - info['anchor'][1]
        if id_ == 'case_closed':
            return folder_sheets_used(v)
        solid = a[..., 3] == 255
        if name == 'mug_camp':
            solid[:20] = False   # skip the steam, which moves
        # The trophy sparkles now and then (a third of a second at a time), so
        # look over a few frames for one where it is bare.
        match = False
        for _ in range(8):
            f = v.frame(v.tick + 1)   # the cup body is the same on every frame; only the steam moves
            region = f[top:top + a.shape[0], left:left + a.shape[1]]
            if np.all(region[solid][:, :3] == a[solid][:, :3]):
                match = True
                break
        return match, f'{name} drawn pixel-exact at its JSON placement' if match else f'{name} NOT found'
    if id_ in ('first_sighting', 'cryptid_hunter'):
        sheet = 'sasquatch_wave' if id_ == 'first_sighting' else 'yeti_wave'
        extra = '' if id_ == 'first_sighting' else ' creature=yeti'
        # Look 10 ticks after he appears, at a moment the treetops are at rest
        # (test mode sways them every 300 ms per frame; frame 0 is empty).
        start = v.tick
        while (start + 10) % 12 not in (0, 1, 2):
            start += 1
        v.to(start)
        v.cmd(f'debug event sasquatch spotindex=0{extra}')
        after = v.frame(start + 10)
        f = 10 * 100 // SPRITES[sheet]['ms_per_frame']
        im, info = sheet_frame(sheet, f, v.page.evaluate("cabin.app.timeOfDay.current()"))
        a = np.asarray(im)
        left, top = spots[0]['x'] - info['anchor'][0], spots[0]['y'] - info['anchor'][1]
        near = np.asarray(Image.open(ANIM / 'scene' / f'near_forest_{v.page.evaluate("cabin.app.timeOfDay.current()")}.png'))[..., 3]
        region = after[top:top + a.shape[0], left:left + a.shape[1]]
        vis = (a[..., 3] == 255) & (near[top:top + a.shape[0], left:left + a.shape[1]] == 0)
        same = np.all(region[vis][:, :3] == a[vis][:, :3], axis=1)
        match = bool(vis.any() and same.all())
        v.to(v.tick + 30)
        return match, f'next appearance uses {sheet} ({int(same.sum())}/{int(vis.sum())} visible px match)'
    if id_ == 'bird_watcher':
        v.cmd('debug event bird x=100 y=100 direction=1')
        f = v.frame()
        im, info = sheet_frame('bird_flap_shiny', 0, v.page.evaluate("cabin.app.timeOfDay.current()"))
        a = np.asarray(im)
        region = f[100 - 6:100 + 6, 100 - 8:100 + 8]
        solid = a[..., 3] == 255
        match = bool(np.all(region[solid][:, :3] == a[solid][:, :3]))
        v.to(v.tick + 10)
        return match, f'birds use bird_flap_shiny (exact: {match})'
    if id_ == 'night_owl':
        v.cmd('time night'); v.to(v.tick + 20)
        r = v.cmd('debug event shootingstar')
        return 'fired' in r[-1], f'shooting stars fire at night ({r[-1]})'
    if id_ == 'around_the_clock':
        v.cmd('time night'); v.to(v.tick + 20)
        r = v.cmd('debug event aurora')
        before = v.frame()
        after = v.frame(v.tick + 45)
        changed = int(diff(before, after)[24:70, 40:280].sum())
        return 'fired' in r[-1] and changed > 500, f'aurora shows on a night it is rolled ({changed} sky px change)'
    if id_ == 'storm_chaser':
        v.cmd('weather rain'); v.to(v.tick + 1); v.cmd('weather clear')
        before = v.frame()
        after = v.frame(v.tick + 30)
        changed = int(diff(before, after)[60:124, 96:224].sum())
        return changed > 300, f'rainbow fades in when rain ends ({changed} px)'
    if id_ == 'stargazer':
        v.cmd('time night'); v.to(v.tick + 20)
        f = v.frame()
        p = SPRITES['constellation_sasquatch']['placement']
        a = np.asarray(sheet_frame('constellation_sasquatch', 0, 'night')[0])
        sky = np.asarray(Image.open(ANIM / 'scene' / 'sky_mask.png'))[..., 3]
        region = f[p['y']:p['y'] + 34, p['x']:p['x'] + 34]
        solid = (a[..., 3] == 255) & (sky[p['y']:p['y'] + 34, p['x']:p['x'] + 34] > 0)
        same = np.all(region[solid][:, :3] == a[solid][:, :3], axis=1)
        match = bool(solid.any() and same.all())
        return match, f'constellation in the night sky ({int(same.sum())}/{int(solid.sum())} px exact)'
    if id_ == 'power_user':
        r = v.cmd('theme green')
        return 'green' in r[-1], f'`theme green` available ({r[-1]!r})'
    return True, ''


# ── edges ──────────────────────────────────────────────────────────────────
def edges(browser, base):
    report.append('\n## Edges\n')
    # Two at once: the 12th unlock completes Woodsman too.
    key = re.search(r"storageKey: '([^']+)'", CONFIG).group(1)
    eleven = [i for i in list(DEFS)[:-1] if i != 'storm_chaser']
    saved = json.dumps({'version': 1, 'stats': {}, 'unlocked': eleven})
    ctx = browser.new_context(viewport={'width': 1280, 'height': 752})
    ctx.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ sessionStorage.setItem('seeded', 1); "
                        f"localStorage.setItem({json.dumps(key)}, {json.dumps(saved)}); }}")
    v = Visit(browser, base, f'{TEST}&time=day', context=ctx)
    start = len(v.page.evaluate('__signs'))
    v.cmd('weather rain')
    v.cmd('weather snow')                       # Storm Chaser, then Woodsman, in one moment
    both = v.lines()[-2:]
    shown_now = v.page.text_content('.us-name')
    v.page.wait_for_function(f"__signs.length >= {start + 2}", timeout=200000)
    signs = v.page.evaluate('__signs')
    tail = [s['name'] for s in signs[-2:]]
    gap = signs[-1]['t'] - signs[-2]['t']
    show_ms = config_number('showMs') + 2 * config_number('slideMs')
    check(tail == ['Storm Chaser', 'Woodsman'] and gap >= show_ms - 50 and len(both) == 2,
          f'two unlocks at once: terminal lines {both}; signs shown one after the other ({tail}), '
          f'{gap:.0f} ms apart (each takes {show_ms:.0f} ms)')
    v.close()

    # Clicking where a bird was a moment ago doesn't count.
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('debug event bird x=100 y=60 direction=1')
    v.to(v.tick + 6)                            # it has moved 30 px on
    v.click(100, 60)
    v.click(100, 30)                            # empty sky
    stale = v.stats()['stats'].get('birdClicks', 0)
    v.click(130, 60)
    fresh = v.stats()['stats'].get('birdClicks', 0)
    check(stale == 0 and fresh == 1, f'clicking where the bird was 0.6 s ago, or on empty sky: {stale} counted; on the bird now: {fresh}')
    v.close()

    # A star by day.
    v = Visit(browser, base, f'{TEST}&time=day')
    for sx, sy in ACH['star_click_targets'][:5]:
        v.click(sx, sy)
    day = v.stats()['stats'].get('starClicks', 0)
    v.cmd('time night'); v.to(v.tick + 20)
    v.click(*ACH['star_click_targets'][0])
    v.cmd('time day'); v.to(v.tick + 20)
    v.cmd('time night'); v.to(v.tick + 20)
    v.click(*ACH['star_click_targets'][0])
    check(day == 0 and v.stats()['stats'].get('starClicks') == 2,
          f'stars by day: {day} counted; the same star on two different nights: {v.stats()["stats"].get("starClicks")} (once per night)')
    v.close()

    # Reset, then earn again.
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('debug unlock all')
    v.cmd('whoami')
    v.to(v.tick + 15)
    asked = v.cmd('reset')
    still = len(v.stats()['unlocked'])
    done = v.cmd('reset yes')
    after = v.stats()
    v.page.mouse.move(2, 2)
    frame_after = v.frame(v.tick + 1)
    fresh_v = Visit(browser, base, f'{TEST}&time=day')
    fresh_v.cmd('whoami')
    fresh_frame = fresh_v.frame(v.tick)
    fresh_v.close()
    clean = int(diff(frame_after, fresh_frame).sum())
    n_before = len(v.signs())
    v.cmd('debug event sasquatch spotindex=1')
    v.to(v.tick + 8)
    v.click(spots_xy(1)[0], spots_xy(1)[1] - 8)
    v.page.wait_for_timeout(200)
    regained = v.signs()[n_before:]
    check(still == 13 and 'reset yes' in asked[0] and after['unlocked'] == [] and clean == 0
          and regained == ['Something in the Trees'],
          f'`reset` asks first ({asked[0][:40]}...; still 13 earned); `reset yes`: {len(after["unlocked"])} earned, '
          f'stats {after["stats"]}; the scene matches a first visit ({clean} px differ); earning again shows its sign: {regained}')
    v.close()

    # Storage disabled: everything works for the visit, nothing persists.
    throw = "Object.defineProperty(window, 'localStorage', { get() { throw new Error('denied'); } });"
    v = Visit(browser, base, f'{TEST}&time=day', init_script=throw)
    v.cmd('time night'); v.to(v.tick + 20)
    works = v.unlocked('night_owl')
    saved = v.stats()['saved']
    again = v.reload()
    check(works and not saved and not again.unlocked('night_owl') and not v.problems and not again.problems,
          f'storage throws: achievements still work in the visit ({works}), saved={saved}, gone after reload '
          f'({not again.unlocked("night_owl")}), console clean ({v.problems + again.problems})')
    v.close()

    # Hand-edited or older saved data.
    key = re.search(r"storageKey: '([^']+)'", CONFIG).group(1)
    cases = {
        'not JSON': '{oops',
        'older version': json.dumps({'version': 0, 'stats': {'birdClicks': 49}, 'unlocked': ['woodsman']}),
        'wrong types': json.dumps({'version': 1, 'stats': {'birdClicks': 'lots', 'mugClicks': 24, 'tabsSeen': [1, 2],
                                                          'timesSeen': ['day']}, 'unlocked': 'everything'}),
        'a number': '42',
    }
    for label, raw in cases.items():
        seed = f"localStorage.setItem({json.dumps(key)}, {json.dumps(raw)});"
        ctx = browser.new_context(viewport={'width': 1280, 'height': 752})
        ctx.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ sessionStorage.setItem('seeded', 1); {seed} }}")
        v = Visit(browser, base, f'{TEST}&time=day', context=ctx)
        st = v.stats()
        kept = st['stats'].get('mugClicks')
        ok = not v.problems and st['unlocked'] == [] and 'birdClicks' not in st['stats']
        if label == 'wrong types':
            ok = ok and kept == 24 and st['stats'].get('timesSeen') == ['day'] and 'tabsSeen' not in st['stats']
        check(ok, f'saved data "{label}": starts cleanly (unlocked {st["unlocked"]}, stats {st["stats"]}), console clean')
        v.close()

    # Time on the page: counts while visible, across visits; not while hidden.
    ctx = browser.new_context(viewport={'width': 1280, 'height': 752})
    v = Visit(browser, base, '?debug', context=ctx)
    v.page.wait_for_timeout(3200)
    first = v.stats()['stats'].get('secondsOpen', 0)
    v.page.evaluate("Object.defineProperty(document, 'visibilityState', { get: () => 'hidden', configurable: true })")
    v.page.wait_for_timeout(2500)
    hidden = v.stats()['stats'].get('secondsOpen', 0) - first
    again = v.reload()
    again.page.wait_for_timeout(2200)
    total = again.stats()['stats'].get('secondsOpen', 0)
    again.cmd('debug set secondsopen 597')
    again.page.wait_for_timeout(3600)
    earned = again.unlocked('cabin_fever')
    check(first >= 2 and hidden == 0 and total >= first + 1 and earned,
          f'visible time: {first} s counted in ~3 s; {hidden} s while the tab was hidden; {total} s after a reload '
          f'(adds up across visits); 597 s + 3 real seconds earns Cabin Fever: {earned}')
    v.close()


def spots_xy(i):
    s = MAIN['animations']['sasquatch_peek']['placement']['spots'][i]
    return s['x'], s['y']


def everything_on(browser, base):
    report.append('\n## Every reward on\n')
    for time in ('day', 'night'):
        v = Visit(browser, base, f'{TEST}&time={time}')
        v.cmd('debug unlock all')
        for line in ('whoami', 'cig', 'debug event farbird x=233 y=43 direction=-1'):
            v.cmd(line)
        if time == 'day':
            v.cmd('weather rain'); v.to(v.tick + 1); v.cmd('weather clear')
        else:
            v.cmd('debug event aurora')
        v.to(v.tick + 32)
        v.cmd('debug event deer start=pool')         # at the pool, walking in, by the time of the shot
        v.to(v.tick + 32)                              # aurora and rainbow fully faded in
        # Timed so each is on screen together, as in the preview: the sasquatch
        # (or yeti) waving, a golden bird, and at night a shooting star.
        v.cmd('debug event sasquatch spotindex=0 creature=sasquatch' if time == 'day'
              else 'debug event sasquatch spotindex=5 creature=yeti')
        v.cmd('debug event bird x=78 y=56 direction=1')
        v.to(v.tick + 8)
        if time == 'night':
            v.cmd('debug event shootingstar x=170 y=30')
        v.to(v.tick + 2)
        v.page.mouse.move(2, 2)
        v.cmd('clear')
        v.page.wait_for_timeout(500)
        v.shot(f'everything_{time}')
        Image.fromarray(v.frame()).resize((1280, 720), Image.NEAREST).save(OUT / f'everything_{time}_native4x.png')
        check(not v.problems, f'{time}: every reward on at once, screenshot saved (console: {v.problems or "clean"})')
        v.close()
    preview = Image.open(ACH_DIR / 'achievements_preview.png').convert('RGB')
    day = Image.open(OUT / 'everything_day_native4x.png').convert('RGB')
    night = Image.open(OUT / 'everything_night_native4x.png').convert('RGB')
    side = Image.new('RGB', (2560, 1440))
    side.paste(preview.crop((0, 0, 2560, 720)), (0, 0))
    side.paste(day, (0, 720)); side.paste(night, (1280, 720))
    side.save(OUT / 'preview_vs_site.png')


DEER_ALONE = """(which) => {
  const deer = cabin.layers.find((l) => l.events && l.events.deer);
  const c = document.createElement('canvas'); c.width = 320; c.height = 180;
  const ctx = c.getContext('2d'); ctx.imageSmoothingEnabled = false;
  (which === 'far' ? deer.far : deer).draw(ctx, cabin.app.timeOfDay.current());
  return c.toDataURL().split(',')[1];
}"""
DEER_STAGE = "cabin.layers.find((l) => l.events && l.events.deer).stage()"
ACT_ONE = ('clifftopOut', 'clifftopPause', 'clifftopBack')
ACT_TWO = ('approach', 'pause', 'drink', 'leave')


def deer_alone(v, which):
    """One deer layer drawn alone on a blank canvas: exactly the pixels the deer covers."""
    data = v.page.evaluate(DEER_ALONE, which)
    return np.asarray(Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA'))


def box_of(mask):
    if not mask.any():
        return None
    xs, ys = np.nonzero(mask.any(0))[0], np.nonzero(mask.any(1))[0]
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def check_deer(browser, base):
    report.append('\n## Deer (Cabin Fever)\n')
    deer_info = SPRITES['deer_walk']['placement']
    forbidden = deer_info['forbidden_x'][0]
    cover_info = SPRITES['far_trees_cover']
    cx, cy = cover_info['placement']['x'], cover_info['placement']['y']
    cover_box = (slice(cy, cy + cover_info['frame_h']), slice(cx, cx + cover_info['frame_w']))
    bank_info = SPRITES['pond_bank']
    bx, by = bank_info['placement']['x'], bank_info['placement']['y']
    bank_box = (slice(by, by + bank_info['frame_h']), slice(bx, bx + bank_info['frame_w']))

    # The bank: scenery for everyone, at every time of day, steady while the waterfall runs.
    bad = []
    for time in ('morning', 'day', 'afternoon', 'night'):
        v = Visit(browser, base, f'{TEST}&time={time}')
        frames = [v.frame(t)[bank_box] for t in range(0, 24)]
        bank = np.asarray(Image.open(ACH_DIR / f'pond_bank_{time}.png').convert('RGBA'))
        near = np.asarray(Image.open(ANIM / 'scene' / f'near_forest_{time}.png').convert('RGBA'))[bank_box][..., 3] > 0
        tops = np.asarray(Image.open(ANIM / next(f for f in MAIN['animations']['treetops']['files'] if f.endswith(f'_{time}.png'))).convert('RGBA'))
        tops_any = np.zeros(near.shape, bool)
        for i in range(MAIN['animations']['treetops']['frames']):
            tops_any |= tops[:, i * 320:(i + 1) * 320][bank_box][..., 3] > 0
        open_bank = (bank[..., 3] == 255) & ~near & ~tops_any   # bank pixels nothing is drawn over
        shown = all(np.array_equal(f[open_bank][:, :3], bank[open_bank][:, :3]) for f in frames)
        # Its own pixels hold still (the water may show through its gaps, and the treetops sway over it).
        solid = (bank[..., 3] == 255) & ~tops_any
        steady = all(np.array_equal(f[solid], frames[0][solid]) for f in frames)
        if not (shown and steady and not v.unlocked('cabin_fever') and not v.problems):
            bad.append(time)
        v.close()
    check(not bad, f'the pond bank is drawn for a visitor without Cabin Fever at all four times of day, '
                   f'and stays put while the waterfall runs ({bad or "all four"})')

    # The tree cover is invisible on its own: drawing it with no deer changes nothing.
    changed = []
    for time in ('morning', 'day', 'afternoon', 'night'):
        v = Visit(browser, base, f'{TEST}&time={time}')
        before = v.frame(5)
        v.page.evaluate(f"""async () => {{
            const img = new Image(); img.src = 'anim/achievements/far_trees_cover_{time}.png'; await img.decode();
            const far = cabin.layers.find((l) => l.events && l.events.deer).far;
            cabin.layers.splice(cabin.layers.indexOf(far) + 1, 0, {{ draw: (ctx) => ctx.drawImage(img, {cx}, {cy}) }});
        }}""")
        after = v.frame(5)
        changed.append(int(np.any(after != before, axis=2).sum()))
        v.close()
    check(not any(changed), f'with no visit, drawing the far-trees cover changes nothing on screen ({changed} px at morning, day, afternoon, night)')

    # Not before it is earned, and not in rain or snow.
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('reset yes')
    early = v.page.evaluate('cabin.app.events.deer()')
    v.cmd('debug unlock cabin_fever')
    v.cmd('weather rain')
    in_rain = v.page.evaluate('cabin.app.events.deer()')
    check(early is False and in_rain is False and v.page.evaluate(DEER_STAGE) == 'hidden',
          f'no deer before Cabin Fever ({early}) or in rain ({in_rain})')
    v.close()

    # A whole visit, by day and by night, beside the same scene without one.
    for time in ('day', 'night'):
        v, plain = Visit(browser, base, f'{TEST}&time={time}'), Visit(browser, base, f'{TEST}&time={time}')
        for page in (v, plain):
            page.cmd('debug unlock cabin_fever')
            page.cmd('clear')
            page.to(1)
        v.page.evaluate('cabin.app.events.deer()')
        rows = []
        for tick in range(2, 1500):
            v.to(tick)
            plain.to(tick)
            stage = v.page.evaluate(DEER_STAGE)
            frame = v.frame()
            visible = np.any(frame[..., :3] != plain.frame()[..., :3], axis=2)
            near, far = deer_alone(v, 'near')[..., 3] > 0, deer_alone(v, 'far')[..., 3] > 0
            far_deer = far.copy()
            far_deer[cover_box] = False
            rows.append((tick, stage, int(visible.sum()), box_of(near), box_of(far_deer), near.any() and far_deer.any(), frame))
            if stage == 'hidden':
                break
        order = [s for i, (_, s, *_) in enumerate(rows) if i == 0 or rows[i - 1][1] != s]
        near_boxes = [r[3] for r in rows if r[3]]
        max_x, max_y = max(b[2] for b in near_boxes), max(b[3] for b in near_boxes)
        far_x = max((r[4][2] for r in rows if r[4]), default=None)
        ends = {}
        for name, act in (('act one', ACT_ONE), ('act two', ACT_TWO)):
            ticks = [r for r in rows if r[1] in act]
            ends[name] = (ticks[0][2], ticks[-1][2])
        both = sum(r[5] for r in rows)
        # One picture per stage, the middle of each, 4x, for the record.
        stages = []
        for r in rows:
            if not stages or stages[-1][0] != r[1]:
                stages.append([r[1], []])
            stages[-1][1].append(r[6])
        strip = np.concatenate([frames[len(frames) // 2][80:136, 96:176] for name, frames in stages if name != 'hidden'], axis=1)
        Image.fromarray(strip).resize((strip.shape[1] * 4, strip.shape[0] * 4), Image.NEAREST).save(OUT / f'deer_stages_{time}.png')
        hidden_ends = all(n == 0 for pair_ in ends.values() for n in pair_)
        check(order == ['clifftopOut', 'clifftopPause', 'clifftopBack', 'intermission', 'approach', 'pause', 'approach',
                        'drink', 'leave', 'hidden']
              and max_x < forbidden and max_y == deer_info['feet_y'] and far_x is not None and far_x < forbidden
              and hidden_ends and both == 0 and not v.problems,
              f'{time}: one visit, {len(rows) / 10:.1f} s: {" -> ".join(order)}; the deer at the pool covers at most '
              f'x {max_x} and y {max_y} (water and bank from y {by}; nothing from x {forbidden}); on the clifftop at most x {far_x}; '
              f'visible px on the first and last frame of each act: {ends}; both deer drawn at once on {both} frames')
        v.close()
        plain.close()

    # Against deer_route_check.png: what each stage adds to the scene, there and here.
    ref = np.asarray(Image.open(ACH_DIR / 'deer_route_check.png').convert('RGB'))
    tile = lambda i: ref[(i // 4) * 368:(i // 4 + 1) * 368, (i % 4) * 640:(i % 4 + 1) * 640][::8, ::8]
    crop = (slice(88, 134), slice(104, 184))
    # The reference has no treetops; on the site they sway over the near deer now and then.
    tt = MAIN['animations']['treetops']
    tops = np.asarray(Image.open(ANIM / next(f for f in tt['files'] if f.endswith('_day.png'))).convert('RGBA'))
    swaying = np.zeros((180, 320), bool)
    for i in range(tt['frames']):
        swaying |= tops[:, i * 320:(i + 1) * 320][..., 3] > 0
    swaying = swaying[crop]
    path = dict((x, y) for x, y in SPRITES['deer_far']['placement']['path'])
    poses = [(0, 'far', 'deer_far', 0, 138, False), (1, 'far', 'deer_far', 1, 149, False), (2, 'far', 'deer_far', 1, 133, True),
             (4, 'near', 'deer_walk', 0, 128, False), (5, 'near', 'deer_graze', 0, 144, False), (6, 'near', 'deer_graze', 2, 144, False)]

    def drawn(layer, sheet, frame, x, mirrored):
        info = SPRITES[sheet]
        im = Image.open(ACH_DIR / f'{sheet}_day.png').convert('RGBA').crop((frame * info['frame_w'], 0, (frame + 1) * info['frame_w'], info['frame_h']))
        ax, ay = info['anchor']
        if mirrored:
            im, ax = im.transpose(Image.FLIP_LEFT_RIGHT), info['frame_w'] - 1 - ax
        c = Image.new('RGBA', (320, 180))
        c.alpha_composite(im, (x - ax, (path[x] if layer == 'far' else deer_info['feet_y']) - ay))
        if layer == 'far':
            c.alpha_composite(Image.open(ACH_DIR / 'far_trees_cover_day.png').convert('RGBA'), (cx, cy))
        return np.asarray(c)

    v, plain = Visit(browser, base, f'{TEST}&time=day'), Visit(browser, base, f'{TEST}&time=day')
    for page in (v, plain):
        page.cmd('debug unlock cabin_fever')
        page.cmd('clear')
        page.to(1)
    v.page.evaluate('cabin.app.events.deer()')
    expected = {p[0]: drawn(*p[1:]) for p in poses}
    seen = {}
    for tick in range(2, 1500):
        v.to(tick)
        plain.to(tick)
        if v.page.evaluate(DEER_STAGE) == 'hidden':
            break
        layers = {'far': deer_alone(v, 'far'), 'near': deer_alone(v, 'near')}
        for i, layer, *_ in poses:
            if i not in seen and np.array_equal(layers[layer], expected[i]):
                site_vis = np.any(v.frame()[crop][..., :3] != plain.frame()[crop][..., :3], axis=2)
                seen[i] = (site_vis, v.frame()[crop][..., :3])
    # Tile 1 stands the deer at x 149, which puts its nose on x 152, so the walk
    # stops a step sooner. Tile 4 shows walk frame 0 at x 128: with the start
    # moved from x 100 to 97 (an ear showed at 100), that frame lands there
    # only when the random pause on the way in falls just right.
    unreachable = {1, 4}
    results, ok = [], True
    for i, *_ in poses:
        if i not in seen:
            results.append(f'tile {i}: never happens')
            ok &= i in unreachable
            continue
        site_vis, site = seen[i]
        ref_vis = np.any(tile(i) != tile(3), axis=2)
        site_vis, ref_vis = site_vis & ~swaying, ref_vis & ~swaying
        moved, recoloured = int((site_vis != ref_vis).sum()), int(np.any(site[ref_vis] != tile(i)[ref_vis], axis=1).sum())
        ok &= moved == 0 and recoloured == 0
        results.append(f'tile {i}: {int(ref_vis.sum())} px, {moved} misplaced, {recoloured} recoloured')
    v.close()
    plain.close()
    check(ok, f'stages against deer_route_check.png, deer pixels only: {"; ".join(results)} '
              f'(tile 1 has it at x 149, past x {forbidden - 1}, so here it stops one step sooner; '
              f'tile 4\'s exact pose happens only on some visits since the start moved from x 100 to 97)')

    # Rain mid-visit ends it after the current act; clicking startles it home; the time of day can change.
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('debug unlock cabin_fever')
    v.page.evaluate('cabin.app.events.deer()')
    v.to(10)
    v.cmd('weather rain')
    stages = []
    while v.page.evaluate(DEER_STAGE) != 'hidden' and v.tick < 400:
        v.to(v.tick + 1)
        stages.append(v.page.evaluate(DEER_STAGE))
    rain_ends_act = 'intermission' not in stages and 'approach' not in stages
    v.cmd('weather clear')
    v.page.evaluate("cabin.app.events.deer({ start: 'pool' })")
    v.to(v.tick + 60)
    v.cmd('weather snow')
    act_two = []
    while v.page.evaluate(DEER_STAGE) != 'hidden' and v.tick < 1200:
        v.to(v.tick + 1)
        act_two.append(v.page.evaluate(DEER_STAGE))
    finishes = 'drink' in act_two and act_two[-1] == 'hidden'
    v.cmd('weather clear')
    v.page.evaluate('cabin.app.events.deer()')
    v.to(v.tick + 40)
    day_far = deer_alone(v, 'far')
    v.cmd('time night')
    v.to(v.tick + 1)
    night_far = deer_alone(v, 'far')
    swaps = v.page.evaluate(DEER_STAGE).startswith('clifftop') and not np.array_equal(day_far, night_far)
    v.cmd('time day')
    v.to(v.tick + 30)   # the night palette has faded back out; still on the clifftop
    far_deer = deer_alone(v, 'far')[..., 3] > 0
    far_deer[cover_box] = False
    target = box_of(far_deer)
    stage_before = v.page.evaluate(DEER_STAGE)
    if target:
        v.click((target[0] + target[2]) // 2, (target[1] + target[3]) // 2)
    startled = []
    while v.page.evaluate(DEER_STAGE) != 'hidden' and v.tick < 2000:
        v.to(v.tick + 1)
        startled.append(v.page.evaluate(DEER_STAGE))
    check(rain_ends_act and finishes and swaps and stage_before.startswith('clifftop')
          and set(startled) <= {'clifftopBack', 'hidden'} and not v.problems,
          f'rain during act one: it finishes the act and the visit ends there ({rain_ends_act}); snow during act two: it '
          f'finishes drinking and leaves ({finishes}); night falling mid-visit swaps its colours without restarting ({swaps}); '
          f'clicked on the clifftop ({stage_before}), it turns back into the trees and the visit ends ({len(startled)} ticks, '
          f'stages {sorted(set(startled))})')
    v.close()

    # It shares the forest with the sasquatch: the scheduler never starts one while the other is out.
    v = Visit(browser, base, f'{TEST}&time=day')
    fired = v.page.evaluate("""async () => {
        const { createScheduler } = await import('./js/scheduler.js');
        const { config } = await import('./js/config.js');
        const timings = { deer: config.events.deer, sasquatch: config.events.sasquatch };
        const out = {};
        for (const busy of ['deer', 'sasquatch']) {
            const fired = { deer: 0, sasquatch: 0 };
            const events = { deer: () => { fired.deer += 1; }, sasquatch: () => { fired.sasquatch += 1; } };
            const s = createScheduler(timings, events, Math.random, { [busy]: () => true });
            for (let i = 0; i < 6000; i++) s.update(1000);   // 100 minutes
            out[busy] = fired;
        }
        return out;
    }""")
    check(fired['deer']['sasquatch'] == 0 and fired['deer']['deer'] > 0
          and fired['sasquatch']['deer'] == 0 and fired['sasquatch']['sasquatch'] > 0,
          f'sasquatch and deer never overlap: over 100 minutes with a deer out the whole time, the sasquatch came '
          f'{fired["deer"]["sasquatch"]} times; with the sasquatch out, the deer came {fired["sasquatch"]["deer"]} times')
    v.close()


def check_board(browser, base):
    report.append('\n## Achievement board\n')
    art = lambda name: np.asarray(Image.open(BOARD_DIR / name).convert('RGBA'))
    mock = art('board_mockup_scene.png')
    panel = lambda i: mock[:, i * 960:(i + 1) * 960][::3, ::3][BOARD_BOX]   # idle, hovered, night at 3x
    holes = np.zeros((BOARD['h'] + 2, BOARD['w'] + 2), bool)   # the mockup has some pins in; compare the rest
    spots = {}                                                 # id -> (image, x, y) on the board
    pins = [i for i in ORDER if i != BOARD['star']['for']]
    for i, (x, y) in zip(pins, BOARD['pin']['positions']):
        spots[i] = (art(BOARD['pin']['file']), x, y)
    spots[BOARD['star']['for']] = (art(BOARD['star']['file']), *BOARD['star']['position'])
    for im, x, y in spots.values():
        holes[y + 1:y + 1 + im.shape[0], x + 1:x + 1 + im.shape[1]] = True
    near = lambda a, b: int(np.any(a[..., :3] != b[..., :3], axis=2)[~holes].sum())
    centre = (BX + BOARD['w'] // 2, BY + BOARD['h'] // 2)

    # In the scene: idle and hovered by day, and at night, against the mockup.
    v = Visit(browser, base, f'{TEST}&time=day')
    idle = v.frame(1)[BOARD_BOX]
    v.page.mouse.move(*v.screen(*centre))
    hovered = v.frame(2)[BOARD_BOX]
    cursor = v.page.evaluate("getComputedStyle(document.getElementById('scene')).cursor")
    v.shot('board_hovered')
    v.page.mouse.move(2, 2)
    after = v.frame(3)[BOARD_BOX]
    outline = np.any(hovered[..., :3] != idle[..., :3], axis=2)
    supplied = art(BOARD['outline_file'])[..., 3] > 0
    check(near(idle, panel(0)) == 0 and near(hovered, panel(1)) == 0 and cursor == 'pointer'
          and np.array_equal(outline, supplied) and np.all(hovered[outline][:, :3] == 0)
          and np.array_equal(after, idle) and not v.problems,
          f'board by day matches the mockup idle ({near(idle, panel(0))} px off) and hovered ({near(hovered, panel(1))} px off); '
          f'the hover outline is black, the same pixels as {BOARD["outline_file"]} ({int((outline != supplied).sum())} off), '
          f'the board under it does not move, the cursor is a {cursor}, and it goes cleanly ({int(np.any(after != idle, axis=2).sum())} px left)')
    v.close()
    v = Visit(browser, base, f'{TEST}&time=night')
    night = v.frame(1)[BOARD_BOX]
    v.shot('board_night')
    check(near(night, panel(2)) == 0 and not v.problems, f'board at night matches the mockup ({near(night, panel(2))} px off)')
    v.close()

    # Each unlock lights its own spot, with a sparkle; reset empties the board without a reload.
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('reset yes')
    prev, wrong, sparkled, earned = v.frame(1)[BOARD_BOX], [], 0, set()
    for id_ in ORDER:
        v.cmd(f'debug unlock {id_}')
        sparkle = v.frame(v.tick + 2)[BOARD_BOX]
        now = v.frame(v.tick + 10)[BOARD_BOX]
        new = set(v.stats()['unlocked']) - earned   # the twelfth also earns Woodsman
        earned |= new
        expect = np.zeros(holes.shape, bool)
        for i in new:
            im, x, y = spots[i]
            h, w = im.shape[:2]
            solid = im[..., 3] == 255
            if not np.array_equal(now[y + 1:y + 1 + h, x + 1:x + 1 + w][solid][:, :3], im[solid][:, :3]):
                wrong.append(i)
            expect[y + 1:y + 1 + h, x + 1:x + 1 + w] = im[..., 3] > 0
        if (np.any(now[..., :3] != prev[..., :3], axis=2) & ~expect).any():
            wrong.append(f'{id_} (changed more than its spot)')
        sparkled += bool(np.any(sparkle[..., :3] != now[..., :3]))
        prev = now
    v.shot('board_all')
    v.cmd('reset yes')
    empty = v.frame(v.tick + 1)[BOARD_BOX]
    check(not wrong and sparkled == len(ORDER) - 1 and near(empty, idle) == 0 and np.array_equal(empty[holes], idle[holes]),
          f'each of the {len(ORDER)} achievements lights its own pin or the star, and nothing else ({wrong or "all in place"}); '
          f'each new pin sparkles ({sparkled} sparkles for {len(ORDER) - 1} unlocks, Woodsman arriving with the twelfth); '
          f'`reset` empties the board at once')
    v.close()

    # The pop-up against the mockup: six earned, the second selected, words hidden.
    def open_board(v):
        v.page.mouse.click(*v.screen(*centre))
        v.page.wait_for_selector('.ab-backdrop.is-visible')
        v.page.wait_for_timeout(250)

    note = lambda v: v.page.evaluate("document.querySelector('.ab-note').innerText.replace(/\\n+/g, ' | ')")
    chosen = lambda v: v.page.evaluate("[...document.querySelectorAll('.ab-slot')].findIndex(b => b.getAttribute('aria-selected') === 'true')")
    bar = lambda v: v.page.evaluate("document.querySelector('.ab-progress').textContent + ', fill ' + document.querySelector('.ab-fill').style.width")
    shown = lambda v: v.page.evaluate("!document.querySelector('.ab-backdrop').hidden")
    pp = BOARD_LAYOUT['popup']
    v = Visit(browser, base, f'{TEST}&time=day')
    for i in (0, 1, 3, 5, 6, 8):
        v.cmd(f'debug unlock {ORDER[i]}')
    v.cmd('clear')
    v.to(12)
    open_board(v)
    latest = chosen(v)
    v.page.click('.ab-slot >> nth=1')
    v.page.mouse.move(2, 2)
    v.shot('board_popup_some')
    v.page.add_style_tag(content='.ab-region, .ab-close, .ab-slot { visibility: hidden !important; }')
    r = v.page.evaluate("(() => { const r = document.querySelector('.ab-art').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    s = round(r[2] / pp['w'])
    shot = v.page.screenshot(clip={'x': r[0], 'y': r[1], 'width': r[2], 'height': r[3]})
    site = np.asarray(Image.open(io.BytesIO(shot)).convert('RGBA'))[::s, ::s][:pp['h'], :pp['w']]
    want = art('board_mockup_popup.png')
    m = want.shape[1] // 320
    want = want[::m, ::m][pp['canvas_y']:pp['canvas_y'] + pp['h'], pp['canvas_x']:pp['canvas_x'] + pp['w']]
    words = np.zeros(site.shape[:2], bool)
    for k in ('detail_name', 'detail_description', 'detail_reward', 'progress_text'):
        g = pp['regions'][k]
        words[g['y']:g['y'] + g['h'], g['x']:g['x'] + g['w']] = True
    # The mockup's progress fill has a two-pixel light line; the brief asks for one.
    g = pp['regions']['progress_bar']
    light_row2 = np.zeros_like(words)
    light_row2[g['y'] + 1, g['x']:g['x'] + g['w']] = True
    off = np.any(site[..., :3] != want[..., :3], axis=2) & ~words
    check(int((off & ~light_row2).sum()) == 0 and latest == 8 and not v.problems,
          f'pop-up art at {s}x matches the mockup with the same six earned and the second selected: slots, badges, '
          f'selection frame, big badge and progress fill line up ({int((off & ~light_row2).sum())} px off, words not compared; '
          f'{int((off & light_row2).sum())} px are the mockup\'s second light row on the fill, which the brief makes one pixel); '
          f'it opened on the latest earned (slot {latest})')
    v.close()

    # States: nothing earned, partway, unlocking while open, everything earned.
    v = Visit(browser, base, f'{TEST}&time=day')
    v.cmd('reset yes')
    v.cmd('clear')
    open_board(v)
    v.shot('board_popup_none')
    nothing = (chosen(v), note(v), bar(v))
    v.page.keyboard.press('Escape')
    v.page.wait_for_timeout(300)
    v.cmd('debug set birdclicks 17')
    open_board(v)
    v.page.click('.ab-slot >> nth=1')
    partway = note(v)
    v.cmd('debug set birdclicks 50')
    live = (chosen(v), note(v), bar(v), v.frame(v.tick + 10)[BOARD_BOX])
    _, x, y = spots['bird_watcher']
    pin_lit = not np.array_equal(live[3][y + 1:y + 3, x + 1:x + 3], idle[y + 1:y + 3, x + 1:x + 3])
    check(nothing == (0, '??? | HOW | Not yet discovered. | REWARD | ???', '0 of 13 earned, fill 0px')
          and partway == '??? | HOW | Click 50 birds | 17 / 50 | REWARD | ???'
          and live[0] == 1 and live[1].startswith('Bird Watcher | HOW | Click 50 birds | REWARD | All birds')
          and live[2] == '1 of 13 earned, fill 10px' and pin_lit,
          f'nothing earned: slot {nothing[0]}, "{nothing[1]}", {nothing[2]}; 17 of 50 birds: "{partway}"; '
          f'the 50th while open: slot {live[0]}, "{live[1][:40]}...", {live[2]}, pin lit {pin_lit} (no reopening)')
    v.page.keyboard.press('Escape')
    v.page.wait_for_timeout(300)
    v.cmd('debug unlock all')
    v.cmd('clear')
    open_board(v)
    v.shot('board_popup_all')
    check(chosen(v) == 12 and bar(v) == '13 of 13 earned, fill 141px', f'everything earned: opens on Woodsman (slot {chosen(v)}), {bar(v)}')

    # Arrow keys, then the three ways to close.
    keys = []
    for key in ('ArrowLeft', 'ArrowUp', 'ArrowUp', 'ArrowRight', 'ArrowDown', 'ArrowDown', 'Home', 'End'):
        v.page.keyboard.press(key)
        keys.append(chosen(v))
    v.page.click('.ab-close')
    v.page.wait_for_timeout(300)
    by_x = not shown(v)
    open_board(v)
    v.page.mouse.click(5, 5)
    v.page.wait_for_timeout(300)
    by_outside = not shown(v)
    check(keys == [11, 7, 2, 3, 8, 12, 0, 12] and by_x and by_outside and not v.problems,
          f'arrow keys from Woodsman (left, up, up, right, down, down, Home, End): slots {keys}; '
          f'the X closes it ({by_x}), so does a click outside ({by_outside})')
    v.close()

    # Keyboard only on the live page, and the retired `badges` command.
    v = Visit(browser, base, '?debug')
    v.page.wait_for_timeout(300)
    start = v.page.evaluate('document.activeElement.id')
    v.page.keyboard.press('Tab')
    target = v.page.evaluate('document.activeElement.textContent')
    v.page.keyboard.press('Enter')
    v.page.wait_for_selector('.ab-backdrop.is-visible')
    v.page.wait_for_timeout(250)
    v.page.keyboard.press('Escape')
    v.page.wait_for_timeout(300)
    v.page.keyboard.type('badges')
    typed_into = v.page.evaluate('document.activeElement.id')
    v.page.keyboard.press('Enter')
    reply = v.page.eval_on_selector_all('#bubble:not([hidden]) .line', 'e => e.map(x => x.textContent)')
    help_lines = v.cmd('help')
    check(start == 'input' and target == 'Achievements' and not shown(v) and typed_into == 'input'
          and reply == ['your achievements are on the board by the window now. click it to see them.']
          and not any(line.startswith('badges') for line in help_lines) and not v.problems,
          f'keyboard only: Tab from the terminal reaches "{target}", Enter opens the board, Escape closes it, '
          f'and typing goes back to the {typed_into}; `badges` now says {reply}; `help` no longer lists it')
    v.close()

    # Touch, on a phone: the plain panel.
    phone = browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=3)
    v = Visit(browser, base, '?debug', context=phone)
    v.page.wait_for_timeout(300)
    v.page.touchscreen.tap(*v.screen(*centre))
    v.page.wait_for_selector('.ab-backdrop.is-visible')
    v.page.wait_for_timeout(250)
    plain = v.page.evaluate("document.querySelector('.ab').classList.contains('is-plain')")
    v.page.locator('.ab-slot').nth(3).tap()
    tapped = chosen(v)
    v.page.screenshot(path=str(OUT / 'board_popup_phone.png'), full_page=True)
    v.page.locator('.ab-close').tap()
    v.page.wait_for_timeout(300)
    check(plain and tapped == 3 and not shown(v) and not v.problems,
          f'phone, by touch: a tap on the board opens it as the plain panel ({plain}), a tap selects a slot ({tapped}), '
          f'close closes it')
    v.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('*.png'):
        old.unlink()
    base, stop = serve_site()
    with sync_playwright() as p:
        browser = open_browser(p)
        earn_each(browser, base)
        check_reward_rendering(browser, base)
        check_sign_art(browser, base)
        edges(browser, base)
        check_deer(browser, base)
        check_board(browser, base)
        if not os.environ.get('CI'):   # screenshots for eyeballing only; skipped on GitHub Actions
            everything_on(browser, base)
        browser.close()
    stop()
    (RESULTS / 'achievements.md').write_text('# Achievement checks\n' + '\n'.join(report) + '\n', encoding='utf-8')
    print(f'\n{len(failures)} failures')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
