"""compare.py — pixel-for-pixel comparison of the site against compose().

Two passes, each over every tick from 0 to 47 (the length of the preview GIFs):

A. Reference pass. The site runs with ?test&timing=reference&demo=reference
   (plus &wind=1 for day and afternoon, as in the previews), which plays every
   sheet at compose()'s speed and replays its bird, far bird, sasquatch and
   wind at its demo positions. Every layer is compared except the waterfall's
   rectangle: compose() predates the redrawn waterfall (scripts/waterfall.py)
   and still draws the old one. Pass B checks the new waterfall exactly.

B. Manifest pass. The site runs with ?test only: the speeds in manifest.json
   times config.animationSlowdown (as on the live site), and no events. compose() hard-codes different speeds for some sheets, so
   the expected frame is built from compose()'s own sheets and layer order
   with the frame index the manifest implies:
   floor(elapsed / (ms_per_frame * slowdown)). This proves the site plays the
   always-on loops at the manifest's speeds, slowed by exactly that factor.

Writes tests/results/comparison.md, comparison.json, frames/ and diffs/.
Run:  python tests/compare.py
"""
import json, math, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from reference import load_reference
from harness import RESULTS, serve_site, open_browser, watch_page, canvas_pixels

TICKS = range(48)
ANIM_DIR = Path(__file__).parent.parent / 'anim'
# The live site (and test mode without timing=reference) plays every sheet
# config.animationSlowdown times slower than the manifest says.
SLOWDOWN = float(re.search(r'animationSlowdown:\s*([\d.]+)',
                           (Path(__file__).parent.parent / 'js' / 'config.js').read_text()).group(1))
TIMES = ['morning', 'day', 'afternoon', 'night']
CASES = ([(t, None) for t in TIMES] + [(t, 'rain') for t in TIMES] + [(t, 'snow') for t in TIMES])


def use_window_for(ns, manifest, t):
    """compose() predates the night window and always draws cabin_window.png.
    The manifest's "window" entry now gives a night version, so swap the
    window compose() reads (its global WIN) to the one for this time of day."""
    files = manifest['window']['files']
    night = next(f for f in files if f.endswith('_night.png'))
    day = next(f for f in files if f != night)
    ns['WIN'] = Image.open(Path(__file__).parent.parent / 'anim' / (night if t == 'night' else day)).convert('RGBA')


def manifest_compose(ns, manifest, t, k, weather):
    """compose() with manifest timing and without the demo characters."""
    use_window_for(ns, manifest, t)
    W, H, fr = ns['W'], ns['H'], ns['fr']
    anim = manifest['animations']
    ms = k * 100

    def frame(name):
        a = anim[name]
        return math.floor(ms / (a['ms_per_frame'] * SLOWDOWN)) % a['frames']

    c = ns['BG'][t].copy()
    sl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if t == 'night':
        sl.alpha_composite(fr(ns['STARS'], W, frame('stars')))
    for nm, x, y, sp in (('a', 52, 30, 0.5), ('c', 196, 40, 0.3), ('b', 128, 60, 0.4), ('d', 236, 70, 0.25)):
        sl.alpha_composite(ns['CL'][(nm, t)], (int(x + k * sp), y))
    c.alpha_composite(Image.composite(sl, Image.new('RGBA', (W, H), (0, 0, 0, 0)), ns['sky'].split()[3]))
    # The waterfall was redrawn after anim.py (scripts/waterfall.py): draw it
    # from its own sheets, at the manifest's size, place and frame timing.
    wf = anim['waterfall']
    sheet = Image.open(ANIM_DIR / next(f for f in wf['files'] if f.endswith(f'_{t}.png'))).convert('RGBA')
    c.alpha_composite(fr(sheet, wf['frame_w'], frame('waterfall')), (wf['placement']['x'], wf['placement']['y']))
    c.alpha_composite(ns['NEAR'][t])
    c.alpha_composite(fr(ns['SHEETS'][('treetops', t)], W, frame('treetops')))
    if weather:
        tile = fr(ns['SHEETS'][(weather, t)], 64, frame(weather))
        for ty in range(0, H, 64):
            for tx in range(0, W, 64):
                c.alpha_composite(tile, (tx, ty))
    c.alpha_composite(ns['WIN'])
    mug = ns['SHEETS']['mug_night' if t == 'night' else 'mug']
    c.alpha_composite(fr(mug, ns['MW'], frame('mug')), (ns['MUG_AT'][0] - ns['MCX'], ns['MUG_AT'][1] - 40))
    return c


def waterfall_rect(manifest):
    """Where the current waterfall patch, and compose()'s older one, are drawn."""
    wf = manifest['animations']['waterfall']
    x, y = wf['placement']['x'], wf['placement']['y']
    old_x, old_y, old_w, old_h = 148, 96, 25, 44          # compose()'s waterfall (anim.py X0, Y0, PW, PH)
    x0, y0 = min(x, old_x), min(y, old_y)
    x1, y1 = max(x + wf['frame_w'], old_x + old_w), max(y + wf['frame_h'], old_y + old_h)
    return (slice(y0, y1), slice(x0, x1))


def diff_stats(site, ref, skip=None):
    delta = np.abs(site.astype(np.int16) - ref.astype(np.int16))
    if skip is not None:
        delta[skip] = 0
    differing = np.any(delta > 0, axis=2)
    return int(differing.sum()), int(delta.max()), differing


def save_diff(path, site, ref, differing):
    """Site | reference | differing pixels in magenta, at 3x."""
    h, w = differing.shape
    marked = site.copy()
    marked[differing] = (255, 0, 255, 255)
    strip = np.concatenate([site, ref, marked], axis=1)
    Image.fromarray(strip).resize((w * 9, h * 3), Image.NEAREST).save(path)


def run_pass(page, base, ns, manifest, label, query_for, expected_for):
    rows = []
    for t, weather in CASES:
        wind = label == 'A' and weather is None and t in ('day', 'afternoon')
        page.goto(base + 'index.html?' + query_for(t, weather, wind))
        page.wait_for_function('window.cabin && window.cabin.test')
        per_tick = []
        for k in TICKS:
            page.evaluate(f'cabin.test.advanceTo({k})')
            site = canvas_pixels(page)
            ref = np.asarray(expected_for(t, k, weather, wind).convert('RGBA'))
            n, max_delta, differing = diff_stats(site, ref, waterfall_rect(manifest) if label == 'A' else None)
            per_tick.append({'tick': k, 'differing_pixels': n, 'max_channel_delta': max_delta})
            if n:
                save_diff(RESULTS / 'diffs' / f'{label}_{t}_{weather or "clear"}_{k:02d}.png', site, ref, differing)
            if label == 'A' and k == 11:
                Image.fromarray(site).save(RESULTS / 'frames' / f'{t}_{weather or "clear"}_tick11.png')
        rows.append({'pass': label, 'time': t, 'weather': weather or 'clear', 'wind': wind, 'ticks': per_tick})
        bad = [p for p in per_tick if p['differing_pixels']]
        print(f'{label} {t:9} {weather or "clear":5} wind={int(wind)}: '
              f'{len(per_tick) - len(bad)}/{len(per_tick)} ticks exact, '
              f'{sum(p["differing_pixels"] for p in per_tick)} differing pixels in total')
    return rows


def write_report(rows, problems):
    lines = ['# Pixel comparison: site vs compose()', '',
             'Each row is one page load, compared at ticks 0-47 (100 ms each) on the native 320x180 canvas.',
             'Pass A leaves out the waterfall rectangle (compose() draws the old waterfall); pass B includes the new one.', '',
             '| pass | time | weather | wind | ticks exact | differing pixels (total) | worst tick | max channel delta |',
             '|---|---|---|---|---|---|---|---|']
    for r in rows:
        ticks = r['ticks']
        exact = sum(1 for p in ticks if p['differing_pixels'] == 0)
        worst = max(ticks, key=lambda p: p['differing_pixels'])
        lines.append(f"| {r['pass']} | {r['time']} | {r['weather']} | {'yes' if r['wind'] else 'no'} | "
                     f"{exact}/{len(ticks)} | {sum(p['differing_pixels'] for p in ticks)} | "
                     f"{worst['tick'] if worst['differing_pixels'] else '-'} | "
                     f"{max(p['max_channel_delta'] for p in ticks)} |")
    lines += ['', f'Browser console problems during the run: {len(problems)}']
    lines += [f'- {p}' for p in problems]
    (RESULTS / 'comparison.md').write_text('\n'.join(lines) + '\n')
    (RESULTS / 'comparison.json').write_text(json.dumps(rows, indent=1))


def main():
    for sub in ('frames', 'diffs'):
        (RESULTS / sub).mkdir(parents=True, exist_ok=True)
        for old in (RESULTS / sub).glob('*.png'):
            old.unlink()
    ns = load_reference()
    manifest = json.loads((Path(__file__).parent.parent / 'anim' / 'manifest.json').read_text())
    base, stop = serve_site()
    with sync_playwright() as p:
        browser = open_browser(p)
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        problems = watch_page(page)

        def query(extra):
            return lambda t, w, wind: f'test&time={t}&weather={w or "clear"}' + extra + ('&wind=1' if wind else '')

        rows = run_pass(page, base, ns, manifest, 'A', query('&timing=reference&demo=reference'),
                        lambda t, k, w, wind: (use_window_for(ns, manifest, t), ns['compose'](t, k, weather=w, wind=wind))[1])
        rows += run_pass(page, base, ns, manifest, 'B', query(''),
                         lambda t, k, w, wind: manifest_compose(ns, manifest, t, k, w))
        browser.close()
    stop()
    write_report(rows, problems)
    total = sum(p['differing_pixels'] for r in rows for p in r['ticks'])
    print(f'\n{len(rows)} cases, {sum(len(r["ticks"]) for r in rows)} frames, {total} differing pixels; '
          f'{len(problems)} console problems')
    for pr in problems:
        print('  ', pr)
    # Known and accepted: the browser keeps canvas pixels premultiplied by
    # alpha, so blending the semi-transparent coloured rain can round one
    # channel by 1 compared with PIL. Everything else must be exact.
    exact_elsewhere = all(p['differing_pixels'] == 0 for r in rows if r['weather'] != 'rain' for p in r['ticks'])
    rain_rounding_only = all(p['max_channel_delta'] <= 1 for r in rows for p in r['ticks'])
    return 0 if exact_elsewhere and rain_rounding_only and not problems else 1


if __name__ == '__main__':
    sys.exit(main())
