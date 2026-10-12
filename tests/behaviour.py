"""behaviour.py — exercises the site the way a visitor would and records proof.

1. Layout at several browser sizes: whole-number scale in device pixels,
   the scene fills the screen with the window and sill fully visible above
   the one-line prompt, and crisp (every visible art pixel is a uniform
   scale x scale block equal to the native canvas pixel). Saves screenshots.
2. Commands typed into the real terminal, in test mode so each effect can be
   compared pixel for pixel with a page that did not run the command.
   `time X` must end up identical to a page that started at X: proof that
   every layer swapped palette and nothing was left behind.
3. Terminal behaviour: focus, history recall, the reply bubble (one at a
   time, replaced by each command, removed by `clear`), unknown / empty /
   repeated input, and that creatures and wind are no longer commands.
4. The scheduler: with config.js swapped for one with short timers (via a
   network route, so no source file changes), every event must fire by itself.
5. The cigarette easter egg: hidden `cig` command places the pack; hover
   outlines it; a click plays the whole smoking sequence over everything.
6. The folder: `whoami` places it; hover outlines it (closed or open); a
   click opens it and calls js/folder-contents.js open(), another click closes
   it and calls close().
7. The folder pop-up: art pixel-exact at a whole-number scale, every word
   from content/folder_content.json shown as written, tabs, scrolling, the
   resume download, closing (X, Escape, outside click), and the plain
   single-column panel on a phone.
8. A phone held sideways: both pop-ups drawn as art (not the plain panel)
   with no text spilling out of its region, turning the phone with one open,
   the keyboard coming up only from the prompt and going away after a
   command, and a desktop window of the same size left exactly as it was.
9. No console errors or warnings, no failed requests, anywhere above.

Writes tests/results/behaviour.md and tests/results/screens/.
Run:  python tests/behaviour.py
"""
import io, json, math, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from harness import ROOT, RESULTS, BOARD, serve_site, open_browser, watch_page, canvas_pixels

SCREENS = RESULTS / 'screens'
report, failures = [], []


def check(ok, what):
    report.append(f"- {'PASS' if ok else 'FAIL'}: {what}")
    if not ok:
        failures.append(what)
    print(report[-1])


def open_page(browser, base, query, problems, **context):
    ctx = browser.new_context(**context)
    page = ctx.new_page()
    page_problems = watch_page(page)
    page.goto(base + 'index.html' + query)
    try:
        page.wait_for_function('window.cabin && window.cabin.app', timeout=15000)
    except Exception:
        loaded = page.evaluate('performance.getEntriesByType("resource").length')
        raise RuntimeError(f'page did not start: {loaded} resources loaded, problems {page_problems}, '
                           f'bubble {page.text_content("#bubble")!r}')
    return page, page_problems


def type_command(page, line):
    page.keyboard.type(line)
    page.keyboard.press('Enter')


def output_lines(page):
    """The lines in the reply bubble, or [] when no bubble is showing."""
    return page.eval_on_selector_all('#bubble:not([hidden]) .line', 'els => els.map(e => e.textContent)')


def bubble_visible(page):
    return page.evaluate("!document.getElementById('bubble').hidden")


def diff_box(a, b):
    m = np.any(a != b, axis=2)
    if not m.any():
        return 0, None
    ys, xs = np.nonzero(m)
    return int(m.sum()), (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def save_pair(name, before, after):
    strip = np.concatenate([before, after], axis=1)
    Image.fromarray(strip).resize((strip.shape[1] * 3, strip.shape[0] * 3), Image.NEAREST).save(SCREENS / name)


# ── 1. layout ─────────────────────────────────────────────────────────────
SIZES = [
    ('desktop_1920x1080', dict(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1)),
    ('fullscreen_1920x1200', dict(viewport={'width': 1920, 'height': 1200}, device_scale_factor=1)),   # 16:10
    ('laptop_1366x768', dict(viewport={'width': 1366, 'height': 768}, device_scale_factor=1)),
    ('hidpi_1440x900_dpr2', dict(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)),
    ('odd_1000x700_dpr1.25', dict(viewport={'width': 1000, 'height': 700}, device_scale_factor=1.25)),
    ('phone_390x844_dpr3', dict(viewport={'width': 390, 'height': 844}, device_scale_factor=3,
                                is_mobile=True, has_touch=True)),
    ('phone_landscape_844x390_dpr3', dict(viewport={'width': 844, 'height': 390}, device_scale_factor=3,
                                          is_mobile=True, has_touch=True)),
    ('phone_landscape_667x320_dpr2', dict(viewport={'width': 667, 'height': 320}, device_scale_factor=2,
                                          is_mobile=True, has_touch=True)),
    ('phone_landscape_915x360_dpr2.625', dict(viewport={'width': 915, 'height': 360}, device_scale_factor=2.625,
                                              is_mobile=True, has_touch=True)),
]


def check_layout(browser, base, problems):
    report.append('\n## Layout and crispness\n')
    for name, ctx in SIZES:
        page, pp = open_page(browser, base, '?test&time=day&timing=reference&demo=reference', problems, **ctx)
        page.evaluate('cabin.test.advanceTo(11)')
        g = page.evaluate('''() => {
            const c = document.getElementById('scene').getBoundingClientRect();
            const s = document.getElementById('stage').getBoundingClientRect();
            const t = document.getElementById('terminal').getBoundingClientRect();
            return { c: [c.left, c.top, c.width, c.height], s: [s.left, s.top, s.width, s.height],
                     t: [t.left, t.top, t.width, t.height], dpr: devicePixelRatio,
                     scale: cabin.display.scale(), vw: innerWidth, vh: innerHeight };
        }''')
        dpr, scale = g['dpr'], g['scale']
        cw, ch = g['c'][2] * dpr, g['c'][3] * dpr
        whole = abs(cw - 320 * scale) < 0.01 and abs(ch - 180 * scale) < 0.01
        # Fills the screen: the canvas reaches every edge of the viewport.
        fills = (g['c'][0] <= 0.01 and g['c'][1] <= 0.01 and g['c'][0] + g['c'][2] >= g['vw'] - 0.01
                 and g['c'][1] + g['c'][3] >= g['vh'] - 0.01)
        # The window opening down to the bottom of the sill (art x 40-279,
        # y 24-149) is fully on screen and above the prompt line.
        kx0 = g['c'][0] + 40 * scale / dpr; kx1 = g['c'][0] + 280 * scale / dpr
        ky0 = g['c'][1] + 24 * scale / dpr; ky1 = g['c'][1] + 150 * scale / dpr
        window_visible = kx0 >= -0.01 and kx1 <= g['vw'] + 0.01 and ky0 >= -0.01 and ky1 <= g['t'][1] + 0.01
        # The achievement board on the right-hand log (and its hover outline) too.
        bx0 = g['c'][0] + (BOARD['canvas_x'] - 1) * scale / dpr; bx1 = g['c'][0] + (BOARD['canvas_x'] + BOARD['w'] + 1) * scale / dpr
        by1 = g['c'][1] + (BOARD['canvas_y'] + BOARD['h'] + 1) * scale / dpr
        board_visible = bx0 >= -0.01 and bx1 <= g['vw'] + 0.01 and by1 <= g['t'][1] + 0.01
        # The window stays centred left to right (the board never pulls the picture
        # sideways): its middle is within a device pixel of the screen's.
        off_centre = (kx0 + kx1) / 2 - g['vw'] / 2
        centred = abs(off_centre) * dpr <= 1
        one_line = g['t'][3] <= 40   # the prompt is a single line
        page.screenshot(path=str(SCREENS / f'layout_{name}.png'))
        # Crispness: everything visible above the prompt must be exactly the
        # native image with each pixel repeated scale x scale times.
        full = np.asarray(Image.open(SCREENS / f'layout_{name}.png').convert('RGB'))
        big = np.repeat(np.repeat(canvas_pixels(page)[..., :3], scale, axis=0), scale, axis=1)
        x0, y0 = round(g['c'][0] * dpr), round(g['c'][1] * dpr)
        vx0, vy0 = max(0, x0), max(0, y0)
        # Stop a row short of the prompt: its fractional top edge may snap up a pixel.
        vx1 = min(full.shape[1], x0 + big.shape[1]); vy1 = min(int(g['t'][1] * dpr) - 1, y0 + big.shape[0])
        crisp = np.array_equal(full[vy0:vy1, vx0:vx1], big[vy0 - y0:vy1 - y0, vx0 - x0:vx1 - x0])
        # The scene fills the screen unless that would cut into the window, sill
        # or board: then the largest whole scale that keeps them in view wins
        # (a tall phone; some sizes since the board, like 1000x700 at 1.25x).
        cover = math.ceil(max(g['vw'] * dpr / 320, g['vh'] * dpr / 180) - 1e-9)
        expect_fill = scale >= cover
        check(whole and window_visible and board_visible and centred and one_line and crisp and fills == expect_fill and not pp,
              f'{name}: scale {scale} (filling needs {cover}), whole-number={whole}, fills the screen={fills}, '
              f'window centred={centred} ({off_centre:+.1f} px), '
              f'window, sill and board fully visible above the prompt={window_visible and board_visible}, '
              f'prompt {g["t"][3]:.0f} px tall={one_line}, every visible pixel a clean {scale}x{scale} block={crisp}'
              + (f', console: {pp}' if pp else ''))
        problems.extend(pp)
        page.context.close()


# ── 2. commands ──────────────────────────────────────────────────────────
def capture_at(browser, base, query, tick, problems, commands=(), command_tick=0):
    page, pp = open_page(browser, base, query, problems)
    page.evaluate(f'cabin.test.advanceTo({command_tick})')
    for c in commands:
        type_command(page, c)
    page.evaluate(f'cabin.test.advanceTo({tick})')
    img = canvas_pixels(page)
    lines = output_lines(page)
    problems.extend(pp)
    page.context.close()
    return img, lines


def check_commands(browser, base, problems):
    report.append('\n## Commands (typed into the terminal, test mode, compared with a page that did not run them)\n')
    q = '?test&time=day'
    # Creatures and wind come only from the timers now; typing them does nothing.
    for cmd in ('bird', 'sasquatch', 'wind', 'farbird'):
        before, _ = capture_at(browser, base, q, 25, problems)
        after, lines = capture_at(browser, base, q, 25, problems, [cmd])
        n, _ = diff_box(before, after)
        check(n == 0 and len(lines) == 1 and 'no such command' in lines[0],
              f'`{cmd}` is not a command any more: scene unchanged ({n} differing pixels), bubble said "{lines[0]}"')

    for target in ('morning', 'afternoon', 'night'):
        switched, lines = capture_at(browser, base, q, 40, problems, [f'time {target}'], command_tick=5)
        fresh, _ = capture_at(browser, base, f'?test&time={target}', 40, problems)
        mid, _ = capture_at(browser, base, q, 12, problems, [f'time {target}'], command_tick=5)
        day12, _ = capture_at(browser, base, q, 12, problems)
        night12, _ = capture_at(browser, base, f'?test&time={target}', 12, problems)
        n_after, _ = diff_box(switched, fresh)
        save_pair(f'command_time_{target}.png', day12, mid)
        check(n_after == 0 and diff_box(mid, day12)[0] > 0 and diff_box(mid, night12)[0] > 0,
              f'`time {target}`: mid-fade frame differs from both palettes; 3.5 s later the frame is '
              f'identical to a page started at {target} ({n_after} differing pixels), so every layer swapped')

    # Snow settles on the trees the longer it falls, so a page that started
    # snowing earlier has more of it: leave those pixels out (check_tree_snow tests them).
    snow_on_trees = tree_snow_mask()
    for target in ('rain', 'snow', 'clear'):
        start = '&weather=rain' if target == 'clear' else ''
        switched, lines = capture_at(browser, base, q + start, 20, problems, [f'weather {target}'], command_tick=5)
        fresh, _ = capture_at(browser, base, f'{q}&weather={target}', 20, problems)
        save_pair(f'command_weather_{target}.png', fresh, switched)
        if target == 'snow':
            switched, fresh = switched.copy(), fresh.copy()
            switched[snow_on_trees] = fresh[snow_on_trees] = 0
        check(diff_box(switched, fresh)[0] == 0,
              f'`weather {target}`: identical to a page started with {target}'
              f'{" (apart from how much snow has settled on the trees)" if target == "snow" else ""}; terminal said "{lines[-1]}"')


# ── 3. terminal ──────────────────────────────────────────────────────────
def check_terminal(browser, base, problems):
    report.append('\n## Terminal\n')
    page, pp = open_page(browser, base, '?test&time=day', problems)
    focused = lambda: page.evaluate('document.activeElement && document.activeElement.id')
    check(focused() == 'input', 'input has focus on load, so typing works straight away')
    page.mouse.click(300, 200)
    check(focused() == 'input', 'clicking the scene keeps focus in the input')

    check(not bubble_visible(page), 'no bubble before anything is typed (test mode has no greeting)')
    type_command(page, 'help')
    help_lines = len(output_lines(page))
    out = '\n'.join(output_lines(page))
    names = ['help', 'clear', 'whoami']
    gone = ['bird', 'wind', 'sasquatch', 'cig', 'time', 'weather', 'reset', 'badges', 'ls', 'rm', 'touch']   # removed, or hidden from help
    check(all(re.search(rf'^{n}\b', out, re.M) for n in names)
          and not any(re.search(rf'^{n}\b', out, re.M) for n in gone),
          f'`help` shows one bubble listing {", ".join(names)} and not {", ".join(gone)}')
    page.wait_for_timeout(300)   # let the pop-in finish before the screenshot
    page.screenshot(path=str(SCREENS / 'bubble_help.png'))

    type_command(page, 'dance')
    lines = output_lines(page)
    check(lines == ['no such command "dance". type "help" to see what you can do.'],
          f'unknown command replaces the help bubble with one hint line: {lines}')
    check(page.evaluate("document.querySelectorAll('#bubble').length") == 1, 'there is only ever one bubble')

    type_command(page, 'weather snow')
    check(output_lines(page) == ['it starts to snow.'], f'a new command replaces the bubble: {output_lines(page)}')
    page.evaluate('cabin.test.advanceTo(5)')
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENS / 'bubble_reply.png'))

    type_command(page, '')
    check(not bubble_visible(page), 'an empty command removes the bubble and shows nothing else')
    type_command(page, '   ')
    check(not bubble_visible(page), 'a blank command does the same')

    for bad in ('time noon', 'weather fog'):
        type_command(page, bad)
        check(len(output_lines(page)) == 1 and 'usage' in output_lines(page)[0],
              f'`{bad}` shows its usage: "{output_lines(page)[0]}"')

    for _ in range(20):
        type_command(page, 'time night')
        type_command(page, 'time day')
        type_command(page, 'help')
    page.evaluate('cabin.test.advanceTo(200)')
    check(page.evaluate("document.querySelectorAll('#bubble .line').length") == help_lines and not pp,
          '60 rapid commands: still one bubble holding only the last reply, scene kept running, no errors')
    check(page.evaluate('cabin.app.timeOfDay.current()') == 'day', 'after the last `time day` the scene is day')

    page.keyboard.press('ArrowUp')
    v1 = page.input_value('#input')
    page.keyboard.press('ArrowUp')
    v2 = page.input_value('#input')
    page.keyboard.press('ArrowDown')
    page.keyboard.press('ArrowDown')
    v3 = page.input_value('#input')
    check((v1, v2, v3) == ('help', 'time day', ''), f'up/down recall: {v1!r}, {v2!r}, back to {v3!r}')

    type_command(page, 'time auto')
    hour = page.evaluate('new Date().getHours()')
    check(page.evaluate('cabin.app.timeOfDay.mode()') == 'auto',
          f'`time auto` returns to the clock (local hour {hour} -> {page.evaluate("cabin.app.timeOfDay.current()")})')

    check(bubble_visible(page), 'the `time auto` reply is showing')
    type_command(page, 'clear')
    check(not bubble_visible(page) and output_lines(page) == [], '`clear` removes the bubble')
    problems.extend(pp)
    page.context.close()


# ── 5b. folder (whoami) ──────────────────────────────────────────────────
def check_folder(browser, base, problems):
    report.append('\n## Folder: `whoami` (test mode)\n')
    manifest = __import__('json').loads((ROOT / 'anim' / 'folder' / 'folder_manifest.json').read_text())
    anim = manifest['animations']
    slowdown = float(re.search(r'animationSlowdown:\s*([\d.]+)', (ROOT / 'js' / 'config.js').read_text()).group(1))
    ticks = lambda n: int(anim[n]['frames'] * anim[n]['ms_per_frame'] * slowdown // 100) + 2

    def top_left(n):
        a = anim[n]
        return a['placement']['x'] - a['anchor'][0], a['placement']['y'] - a['anchor'][1]

    cl, ct = top_left('folder')
    closed_box = (cl - 1, ct - 1, cl + anim['folder']['frame_w'], ct + anim['folder']['frame_h'])
    ol, ot = top_left('folder_opened')
    open_box = (ol - 1, ot - 1, ol + anim['folder_opened']['frame_w'], ot + anim['folder_opened']['frame_h'])
    within = lambda b, box: b is not None and b[0] >= box[0] and b[1] >= box[1] and b[2] <= box[2] and b[3] <= box[3]

    def screen_point(page, x, y):
        r = page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        return r[0] + (x + 0.5) * r[2] / 320, r[1] + (y + 0.5) * r[3] / 180

    def frame(page, tick):
        page.evaluate(f'cabin.test.advanceTo({tick})')
        return canvas_pixels(page)

    def outline_check(before, after, box):
        changed = np.any(before != after, axis=2)
        n, b = diff_box(before, after)
        return n, n > 0 and bool(np.all(after[changed][:, :3] == 0)) and within(b, box)

    for t in ('day', 'night'):
        page, pp = open_page(browser, base, f'?test&time={t}', problems, viewport={'width': 1366, 'height': 768})
        page.evaluate("""async () => {
            const { folderContents } = await import('./js/folder-contents.js');
            window.hookCalls = [];
            folderContents.open = ({ close }) => { hookCalls.push('open'); window.closeFromContent = close; };
            folderContents.close = () => { hookCalls.push('close'); };
        }""")
        hooks = lambda: page.evaluate('hookCalls')
        type_command(page, 'whoami')
        said = output_lines(page)
        tick = ticks('folder_place') + 1
        plain, _ = capture_at(browser, base, f'?test&time={t}', tick, problems)
        settled = frame(page, tick)
        n, b = diff_box(plain, settled)
        check(n > 0 and within(b, closed_box) and said == ['you take out the folder. click it to open it.'],
              f'{t}: `whoami` slides the folder onto the sill, then only the closed folder remains '
              f'({n} pixels, inside its box: {within(b, closed_box)}); bubble "{said[0]}"')
        type_command(page, 'whoami')
        check(output_lines(page) == ['the folder is already on the sill. click it to open it.'],
              f'{t}: a second `whoami` says "{output_lines(page)[0]}"')

        cx, cy = screen_point(page, cl + anim['folder']['frame_w'] // 2, ct + anim['folder']['frame_h'] // 2)
        page.mouse.move(cx, cy)
        hovered = frame(page, tick)
        cursor = page.evaluate("getComputedStyle(document.getElementById('scene')).cursor")
        nh, ok = outline_check(settled, hovered, closed_box)
        check(ok and cursor == 'pointer', f'{t}: hovering the closed folder draws a black outline ({nh} pixels) and a "{cursor}" cursor')
        save_pair(f'folder_hover_{t}.png', settled[100:170, 110:210], hovered[100:170, 110:210])
        page.mouse.move(5, 5)
        check(diff_box(settled, frame(page, tick))[0] == 0, f'{t}: moving away removes the outline')

        # Open: the cover swings up, then the open hook runs.
        page.mouse.click(cx, cy)
        mid = frame(page, tick + 3)
        check(hooks() == [], f'{t}: the open hook waits until the folder has finished opening ({hooks()})')
        tick += ticks('folder_open')
        opened = frame(page, tick)
        check(hooks() == ['open'] and diff_box(settled, opened)[0] > 0 and diff_box(mid, opened)[0] > 0,
              f'{t}: clicking opens the folder, then calls folderContents.open() once ({hooks()})')
        save_pair(f'folder_open_{t}.png', settled[100:170, 110:210], opened[100:170, 110:210])

        # Hover the open folder, then click to close it.
        ox, oy = screen_point(page, ol + anim['folder_opened']['frame_w'] // 2, ot + 8)
        page.mouse.move(ox, oy)
        open_hovered = frame(page, tick)
        nh, ok = outline_check(opened, open_hovered, open_box)
        check(ok, f'{t}: hovering the open folder outlines it too ({nh} pixels)')
        page.mouse.click(ox, oy)
        check(hooks() == ['open', 'close'], f'{t}: clicking the open folder calls folderContents.close() ({hooks()})')
        tick += ticks('folder_open')
        page.mouse.move(5, 5)
        reclosed = frame(page, tick)
        just_placed = lambda at: capture_at(browser, base, f'?test&time={t}', at, problems, ['whoami'])[0]
        check(diff_box(just_placed(tick), reclosed)[0] == 0,
              f'{t}: it plays the opening backwards and ends identical to a folder that was never opened')

        # Your content can close the folder itself with the close() it is given.
        page.mouse.click(cx, cy)
        tick += ticks('folder_open')
        frame(page, tick)
        page.evaluate('closeFromContent()')
        tick += ticks('folder_open')
        page.mouse.move(5, 5)
        check(hooks() == ['open', 'close', 'open', 'close'] and diff_box(just_placed(tick), frame(page, tick))[0] == 0,
              f'{t}: calling close() from the content closes the folder ({hooks()})')

        # Pack and folder together: each highlights on its own.
        type_command(page, 'cig')
        tick += 20
        both = frame(page, tick)
        page.mouse.move(cx, cy)
        n_folder, ok_folder = outline_check(both, frame(page, tick), closed_box)
        check(ok_folder, f'{t}: with the cigarette pack also out, hovering the folder outlines only the folder')
        check(not pp, f'{t}: no console problems ({pp})')
        problems.extend(pp)
        page.context.close()



# ── 5c. folder pop-up ────────────────────────────────────────────────────
def check_folder_popup(browser, base, problems):
    report.append('\n## Folder pop-up\n')
    import json
    content = json.loads((ROOT / 'content' / 'folder_content.json').read_text(encoding='utf-8'))
    layout = json.loads((ROOT / 'anim' / 'folder' / 'popup' / 'popup_layout.json').read_text())
    art_dir = ROOT / 'anim' / 'folder' / 'popup'

    def strings(node):
        if isinstance(node, str):
            return [node]
        if isinstance(node, list):
            return [x for v in node for x in strings(v)]
        if isinstance(node, dict):
            return [x for k, v in node.items() if k != 'href' for x in strings(v)]
        return []

    def open_popup(page):
        page.focus('#input')
        type_command(page, 'whoami')
        page.evaluate('cabin.test.advanceTo(20)')
        r = page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        page.mouse.click(r[0] + 160.5 * r[2] / 320, r[1] + 140.5 * r[3] / 180)
        page.evaluate('cabin.test.advanceTo(40)')
        page.wait_for_selector('.fp-backdrop.is-visible')
        page.wait_for_timeout(400)   # fade-in

    visible = lambda page: page.evaluate("!document.querySelector('.fp-backdrop').hidden")
    click_tab = lambda page, name: page.evaluate(
        f"[...document.querySelectorAll('.fp-tab')].find(b => b.textContent === '{name}').click()")
    # textContent, not innerText: headings are shown in capitals by CSS only.
    page_text = lambda page: page.evaluate("document.querySelector('.fp').textContent")

    for name, ctx in (('1280x752', dict(viewport={'width': 1280, 'height': 752})),
                      ('1440x900_dpr2', dict(viewport={'width': 1440, 'height': 900}, device_scale_factor=2))):
        page, pp = open_page(browser, base, '?test&time=day', problems, **ctx)
        open_popup(page)
        plain = page.evaluate("document.querySelector('.fp').classList.contains('is-plain')")
        dpr = page.evaluate('devicePixelRatio')
        g = page.evaluate("""(() => { const r = document.querySelector('.fp-art').getBoundingClientRect();
                                       return [r.left, r.top, r.width, r.height]; })()""")
        scale = g[2] * dpr / layout['popup']['w']
        whole = abs(scale - round(scale)) < 1e-6
        # Art crispness: hide the text, screenshot, and compare with the art
        # scaled up by whole pixels (where the art is opaque).
        page.add_style_tag(content='.fp-region, .fp-close, .fp-tab { visibility: hidden !important; }')
        page.wait_for_timeout(50)
        shot = np.asarray(Image.open(io.BytesIO(page.screenshot())).convert('RGBA')).astype(int)
        art = Image.open(art_dir / layout['popup']['file']).convert('RGBA')
        tab = layout['tabs'][0]
        art.alpha_composite(Image.open(art_dir / tab['active_file']).convert('RGBA'), (tab['x'], tab['y']))
        s_ = int(round(scale))
        big = np.repeat(np.repeat(np.asarray(art).astype(int), s_, 0), s_, 1)
        x0, y0 = round(g[0] * dpr), round(g[1] * dpr)
        region = shot[y0:y0 + big.shape[0], x0:x0 + big.shape[1]]
        opaque = big[..., 3] == 255
        art_exact = region.shape == big.shape and bool(np.all(region[opaque][:, :3] == big[opaque][:, :3]))
        page.screenshot(path=str(SCREENS / f'popup_{name}_about.png'))
        page.add_style_tag(content='.fp-region, .fp-close, .fp-tab { visibility: visible !important; }')
        check(not plain and whole and art_exact,
              f'{name}: pop-up drawn at a whole-number scale ({scale:g} device px per art px), '
              f'art pixel-exact against popup_folder.png + active tab: {art_exact}')

        left = strings({k: v for k, v in content.items() if k != 'tabs'})
        missing_left = [t for t in left if t not in page_text(page)]
        all_missing = {}
        for tab_name, sections in content['tabs'].items():
            click_tab(page, tab_name)
            text = page_text(page)
            selected = page.evaluate("document.querySelector('.fp-tab[aria-selected=\"true\"]').textContent")
            missing = [t for t in strings(sections) if t not in text]
            if missing or selected != tab_name:
                all_missing[tab_name] = missing or [f'selected {selected}']
            page.wait_for_timeout(50)
            page.screenshot(path=str(SCREENS / f'popup_{name}_{tab_name}.png'))
        check(not missing_left and not all_missing,
              f'{name}: every string in folder_content.json appears exactly as written '
              f'(left side: {len(left)} strings; tabs: {", ".join(content["tabs"])}); missing: {missing_left or all_missing or "none"}')

        click_tab(page, 'resume')
        scroll = page.evaluate("(() => { const p = document.querySelector('.fp-page'); return [p.scrollHeight, p.clientHeight, getComputedStyle(p).overflowY]; })()")
        check(scroll[0] > scroll[1] and scroll[2] == 'auto', f'{name}: the long resume tab scrolls inside the page ({scroll[0]} px of content in {scroll[1]} px)')

        pdf = page.evaluate("""async () => { const a = [...document.querySelectorAll('.fp-link')].find(l => l.href.endsWith('.pdf'));
                                             const r = await fetch(a.href); const b = new Uint8Array(await r.arrayBuffer());
                                             return [a.hasAttribute('download'), r.status, String.fromCharCode(...b.slice(0, 5))]; }""")
        check(pdf == [True, 200, '%PDF-'], f'{name}: the resume link downloads a real PDF (download attribute, HTTP {pdf[1]}, starts {pdf[2]!r})')

        # Focus stays in the pop-up (the terminal must not steal it).
        page.click('.fp-page')
        inside = page.evaluate("!!document.activeElement.closest('.fp')")
        check(inside, f'{name}: clicking inside the pop-up keeps focus there (not the terminal input)')

        # Three ways to close; each closes the folder on the sill too.
        def closed_after(action):
            action()
            page.evaluate('cabin.test.advanceTo(200)')
            page.wait_for_timeout(400)
            return not visible(page)
        r = page.evaluate("(() => { const r = document.querySelector('.fp-close').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        by_x = closed_after(lambda: page.mouse.click(*r))
        open_again = lambda: (page.evaluate('cabin.test.advanceTo(220)'), page.mouse.click(*sill_point(page)),
                              page.evaluate('cabin.test.advanceTo(240)'), page.wait_for_selector('.fp-backdrop.is-visible'),
                              page.wait_for_timeout(300))
        def sill_point(page):
            q = page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
            return q[0] + 160.5 * q[2] / 320, q[1] + 140.5 * q[3] / 180
        open_again()
        by_escape = closed_after(lambda: page.keyboard.press('Escape'))
        page.evaluate('cabin.test.advanceTo(260)')
        page.mouse.click(*sill_point(page))
        page.evaluate('cabin.test.advanceTo(280)')
        page.wait_for_selector('.fp-backdrop.is-visible')
        page.wait_for_timeout(300)
        by_outside = closed_after(lambda: page.mouse.click(4, 4))
        page.evaluate('cabin.test.advanceTo(300)')
        page.mouse.move(2, 2)
        # All four tabs were read, so the closed folder now wears its REVIEWED seal.
        sill_closed = diff_box(capture_at(browser, base, '?test&debug&time=day', 300, problems,
                                          ['whoami', 'debug unlock case_closed'])[0],
                               canvas_pixels(page))[0] == 0
        check(by_x and by_escape and by_outside and sill_closed,
              f'{name}: closes on the X ({by_x}), Escape ({by_escape}) and a click outside ({by_outside}); '
              f'the folder on the sill closes again too ({sill_closed})')
        check(not pp, f'{name}: no console problems ({pp})')
        problems.extend(pp)
        page.context.close()

    # Phone: too small for the folder art, so the plain single-column panel.
    page, pp = open_page(browser, base, '?test&time=day', problems, viewport={'width': 390, 'height': 844},
                         device_scale_factor=3, is_mobile=True, has_touch=True)
    open_popup(page)
    plain = page.evaluate("document.querySelector('.fp').classList.contains('is-plain')")
    text = page_text(page)
    missing = [t for t in strings({k: v for k, v in content.items() if k != 'tabs'}) + strings(content['tabs']['about']) if t not in text]
    fits = page.evaluate("document.querySelector('.fp').getBoundingClientRect().width <= innerWidth")
    page.screenshot(path=str(SCREENS / 'popup_phone.png'))
    page.keyboard.press('Escape')
    page.evaluate('cabin.test.advanceTo(100)')
    page.wait_for_timeout(400)
    check(plain and not missing and fits and not visible(page) and not pp,
          f'phone 390x844: plain single-column panel ({plain}), all content shown (missing: {missing or "none"}), '
          f'fits the width ({fits}), Escape closes it ({not visible(page)})')
    problems.extend(pp)
    page.context.close()


# ── 5c. a phone held sideways ─────────────────────────────────────────────
LANDSCAPE_PHONES = [
    ('667x320_dpr2', dict(viewport={'width': 667, 'height': 320}, device_scale_factor=2)),
    ('844x340_dpr3', dict(viewport={'width': 844, 'height': 340}, device_scale_factor=3)),
    ('844x390_dpr3', dict(viewport={'width': 844, 'height': 390}, device_scale_factor=3)),
    ('915x360_dpr2.625', dict(viewport={'width': 915, 'height': 360}, device_scale_factor=2.625)),
]


def check_landscape_phone(browser, base, problems):
    report.append('\n## Phone held sideways\n')
    layout = json.loads((ROOT / 'anim' / 'folder' / 'popup' / 'popup_layout.json').read_text())

    def art_point(page, x, y):
        r = page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        return r[0] + x * r[2] / 320, r[1] + y * r[3] / 180

    def wait_shown(page, cls):
        page.wait_for_selector(f'.{cls}-backdrop.is-visible')
        page.wait_for_timeout(300)

    def close(page, cls, tick):
        page.keyboard.press('Escape')
        page.evaluate(f'cabin.test.advanceTo({tick})')
        page.wait_for_selector(f'.{cls}-backdrop', state='hidden')

    # Every piece of text that sits on the art, and whether it fits its box.
    spills = """sel => [...document.querySelectorAll(sel)]
        .filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1)
        .map(e => e.className + ': ' + e.textContent.slice(0, 30))"""
    on_folder = '.fp-card-name, .fp-card-line, .fp-sticky-links li, .fp-sticky, .fp-stamp, .fp-card'
    on_board = '.ab-name, .ab-how, .ab-reward, .ab-progress'
    input_focused = "document.activeElement === document.getElementById('input')"

    for name, ctx in LANDSCAPE_PHONES:
        page, pp = open_page(browser, base, '?test&debug&time=day', problems, is_mobile=True, has_touch=True, **ctx)
        font = page.evaluate("getComputedStyle(document.getElementById('terminal')).fontSize")

        # The keyboard: a tap on the scene leaves it down, a tap on the prompt brings it up,
        # and sending a command puts it away again with the reply showing.
        page.evaluate("document.getElementById('input').blur()")
        page.touchscreen.tap(*art_point(page, 160, 60))
        scene_tap_up = page.evaluate(input_focused)
        t = page.evaluate("(() => { const r = document.getElementById('terminal').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        page.touchscreen.tap(*t)
        prompt_tap_up = page.evaluate(input_focused)
        type_command(page, 'whoami')
        down_after = not page.evaluate(input_focused)
        replied = bubble_visible(page)
        check(font == '16px' and not scene_tap_up and prompt_tap_up and down_after and replied,
              f'{name}: prompt at 16px so the page does not zoom ({font}); a tap on the scene leaves the keyboard down '
              f'({not scene_tap_up}), a tap on the prompt brings it up ({prompt_tap_up}), sending a command puts it away '
              f'({down_after}) with the reply showing ({replied})')

        # The folder pop-up: the desktop art, not the plain panel, with every line inside its box.
        page.evaluate('cabin.test.advanceTo(40)')
        page.touchscreen.tap(*art_point(page, 160.5, 140.5))
        page.evaluate('cabin.test.advanceTo(60)')
        wait_shown(page, 'fp')
        classes = page.evaluate("document.querySelector('.fp').className")
        dpr = page.evaluate('devicePixelRatio')
        g = page.evaluate("""(() => { const r = document.querySelector('.fp-art').getBoundingClientRect();
                                       return [r.left, r.top, r.right, r.bottom, innerWidth, innerHeight]; })()""")
        scale = (g[2] - g[0]) * dpr / layout['popup']['w']
        on_screen = g[0] >= -0.01 and g[1] >= -0.01 and g[2] <= g[4] + 0.01 and g[3] <= g[5] + 0.01
        folder_spills = page.evaluate(spills, on_folder)
        gpa = page.evaluate("[...document.querySelectorAll('.fp-card-line')].some(e => e.textContent.includes('GPA') && e.scrollWidth <= e.clientWidth)")
        page.screenshot(path=str(SCREENS / f'landscape_{name}_folder.png'))
        check('is-compact' in classes and 'is-plain' not in classes and abs(scale - round(scale)) < 1e-6 and on_screen
              and not folder_spills and gpa,
              f'{name}: folder pop-up drawn as art ({classes}) at a whole-number scale ({scale:g} device px per art px), '
              f'fully on screen ({on_screen}), no text spilling out ({folder_spills or "none"}), the GPA line whole ({gpa})')

        # Turning the phone with it open: plain panel upright, the art again sideways.
        w, h = ctx['viewport']['width'], ctx['viewport']['height']
        page.set_viewport_size({'width': h, 'height': w})
        page.wait_for_timeout(100)
        upright = page.evaluate("document.querySelector('.fp').className")
        page.set_viewport_size({'width': w, 'height': h})
        page.wait_for_timeout(100)
        sideways = page.evaluate("document.querySelector('.fp').className")
        check('is-plain' in upright and 'is-compact' not in upright and 'is-compact' in sideways and 'is-plain' not in sideways,
              f'{name}: turning the phone with the folder open swaps to the plain panel ({upright}) and back to the art ({sideways})')
        close(page, 'fp', 100)

        # The board pop-up, every achievement earned so each one's longest words show.
        page.evaluate("cabin.run('debug unlock all')")
        page.touchscreen.tap(*art_point(page, BOARD['canvas_x'] + BOARD['w'] / 2, BOARD['canvas_y'] + BOARD['h'] / 2))
        wait_shown(page, 'ab')
        classes = page.evaluate("document.querySelector('.ab').className")
        board_spills = []
        for i in range(page.evaluate("document.querySelectorAll('.ab-slot').length")):
            page.evaluate(f"document.querySelectorAll('.ab-slot')[{i}].click()")
            board_spills += page.evaluate(spills, on_board)
        page.screenshot(path=str(SCREENS / f'landscape_{name}_board.png'))
        check('is-compact' in classes and 'is-plain' not in classes and not board_spills,
              f"{name}: achievement board drawn as art ({classes}), every achievement's text inside its box "
              f'({sorted(set(board_spills)) or "none"})')
        close(page, 'ab', 140)
        check(not pp, f'{name}: no console problems ({pp})')
        problems.extend(pp)
        page.context.close()

    # A desktop window the same size is not a phone: plain panels, and a click
    # anywhere still puts the cursor back in the prompt.
    page, pp = open_page(browser, base, '?test&time=day', problems, viewport={'width': 844, 'height': 390})
    page.focus('#input')
    type_command(page, 'whoami')
    page.evaluate('cabin.test.advanceTo(40)')
    page.evaluate("document.getElementById('input').blur()")
    page.mouse.click(*art_point(page, 160, 60))
    refocused = page.evaluate(input_focused)
    page.mouse.click(*art_point(page, 160.5, 140.5))
    page.evaluate('cabin.test.advanceTo(60)')
    wait_shown(page, 'fp')
    classes = page.evaluate("document.querySelector('.fp').className")
    font = page.evaluate("getComputedStyle(document.getElementById('terminal')).fontSize")
    check('is-plain' in classes and 'is-compact' not in classes and refocused and font == '14px' and not pp,
          f'desktop window 844x390: unchanged: plain panel ({classes}), a click on the scene refocuses the prompt '
          f'({refocused}), prompt at 14px ({font})')
    problems.extend(pp)
    page.context.close()


# ── 5d. the coffee mug ───────────────────────────────────────────────────
def check_mug(browser, base, problems):
    report.append('\n## Coffee mug: hover outline and sip (test mode)\n')
    import json
    manifest = json.loads((ROOT / 'anim' / 'manifest.json').read_text())
    ach = json.loads((ROOT / 'anim' / 'achievements' / 'achievements.json').read_text())
    mug = manifest['animations']['mug']
    slowdown = float(re.search(r'animationSlowdown:\s*([\d.]+)', (ROOT / 'js' / 'config.js').read_text()).group(1))
    left, top = mug['placement']['x'] - mug['anchor'][0], mug['placement']['y'] - mug['anchor'][1]
    box = (left - 1, top - 1, left + mug['frame_w'], top + mug['frame_h'])

    def sheet(info, base_dir, frame, time):
        files = info['files']
        name = next((f for f in files if f.endswith('_night.png')), None) if time == 'night' else None
        name = name or next(f for f in files if not f.endswith('_night.png'))
        im = np.asarray(Image.open(base_dir / name).convert('RGBA'))
        return im[:, frame * info['frame_w']:(frame + 1) * info['frame_w']]

    def screen_point(page, x, y):
        r = page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        return r[0] + (x + 0.5) * r[2] / 320, r[1] + (y + 0.5) * r[3] / 180

    def frame(page, tick):
        page.evaluate(f'cabin.test.advanceTo({tick})')
        return canvas_pixels(page)

    for t, unlock, sip_name, sip_info, sip_dir in (
            ('day', None, 'mug_sip', manifest['animations']['mug_sip'], ROOT / 'anim'),
            ('night', None, 'mug_sip', manifest['animations']['mug_sip'], ROOT / 'anim'),
            ('day', 'caffeinated', 'mug_camp_sip', ach['animations']['mug_camp_sip'], ROOT / 'anim' / 'achievements')):
        label = f'{t}{" (camp mug)" if unlock else ""}'
        q = f'?test&debug&time={t}'
        page, pp = open_page(browser, base, q, problems, viewport={'width': 1366, 'height': 768})
        pre = [f'debug unlock {unlock}'] if unlock else []
        for c in pre:
            type_command(page, c)
        rest = frame(page, 10)
        cx, cy = screen_point(page, mug['placement']['x'], mug['placement']['y'] - 10)
        page.mouse.move(cx, cy)
        hovered = frame(page, 10)
        changed = np.any(rest != hovered, axis=2)
        ys, xs = np.nonzero(changed)
        cursor = page.evaluate("getComputedStyle(document.getElementById('scene')).cursor")
        # Black, except where the translucent steam drifts in front of the outline.
        steam = np.zeros_like(changed)
        cup = sheet(mug, ROOT / 'anim', (10 * 100 * 1) // int(mug['ms_per_frame'] * slowdown) % mug['frames'], t)
        a = cup[..., 3]
        steam[top:top + a.shape[0], left:left + a.shape[1]] = (a > 0) & (a < 255)
        black = bool(changed.any() and np.all(hovered[changed & ~steam][:, :3] == 0))
        inside = bool(changed.any() and xs.min() >= box[0] and xs.max() <= box[2] and ys.min() >= box[1] and ys.max() <= box[3])
        # The steam's own rows are left out: the outline starts at the rim.
        below_steam = bool(changed.any() and ys.min() >= top + 18)
        check(black and inside and below_steam and cursor == 'pointer',
              f'{label}: hovering the cup draws a black outline ({int(changed.sum())} px, all black {black}, '
              f'around the cup and not the steam {below_steam}) with a "{cursor}" cursor')
        save_pair(f'mug_hover_{t}{"_camp" if unlock else ""}.png', rest[90:160, 180:260], hovered[90:160, 180:260])

        page.mouse.click(cx, cy)
        sip_ms = sip_info['ms_per_frame'] * slowdown
        k = 5                                            # 500 ms into the sip
        f = int(k * 100 // sip_ms)
        mid = frame(page, 10 + k)
        art = sheet(sip_info, sip_dir, f, t)
        sx, sy = sip_info['placement']['x'], sip_info['placement']['y']
        region = mid[sy:sy + art.shape[0], sx:sx + art.shape[1]]
        opaque = art[..., 3] == 255
        exact = bool(np.all(region[opaque][:, :3] == art[opaque][:, :3]))
        over_frame = int((opaque[min(art.shape[0], 131 - sy):, :]).sum())   # art rows below the window opening
        page.mouse.click(cx, cy)                         # mid-sip: ignored
        counted = page.evaluate('cabin.app.progressStats()')['stats'].get('mugClicks')
        check(exact and counted == 1, f'{label}: the click plays {sip_name} on top of everything '
                                      f'(frame {f} pixel-exact, {over_frame} of its px over the sill and frame); '
                                      f'a click mid-sip is ignored ({counted} sip counted)')
        Image.fromarray(mid).resize((960, 540), Image.NEAREST).save(SCREENS / f'mug_sip_{t}{"_camp" if unlock else ""}.png')

        end = 10 + int(sip_info['frames'] * sip_ms // 100) + 2
        page.mouse.move(2, 2)
        back = frame(page, end)
        never, _ = capture_at(browser, base, q, end, problems, pre)
        n = int(np.any(back != never, axis=2).sum())
        check(n == 0 and not pp, f'{label}: after {sip_info["frames"] * sip_ms / 1000:.2f} s the cup is back on the sill '
                                 f'with its steam, identical to a page where nobody sipped ({n} px differ)')
        problems.extend(pp)
        page.context.close()



# ── 5. cigarette easter egg ──────────────────────────────────────────────
def check_cigarette(browser, base, problems):
    report.append('\n## Cigarette easter egg (test mode)\n')
    manifest = __import__('json').loads((ROOT / 'anim' / 'smoke' / 'smoke_manifest.json').read_text())
    anim = manifest['animations']
    slowdown = float(re.search(r'animationSlowdown:\s*([\d.]+)', (ROOT / 'js' / 'config.js').read_text()).group(1))
    dur = lambda n: anim[n]['frames'] * anim[n]['ms_per_frame'] * slowdown
    place_ms = dur('pack_place')
    smoke_ms = dur('cig_pick') + sum(dur(st.get('play') or st['loop']) * st.get('times', 1)
                                     for st in manifest['sequences']['smoke']['steps'])
    pk = anim['cig_pack']
    left, top = pk['placement']['x'] - pk['anchor'][0], pk['placement']['y'] - pk['anchor'][1]
    box = (left - 1, top - 1, left + pk['frame_w'], top + pk['frame_h'])   # pack plus outline ring

    def screen_point(page, x, y):
        r = page.evaluate("(() => { const r = document.getElementById('scene').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        return r[0] + (x + 0.5) * r[2] / 320, r[1] + (y + 0.5) * r[3] / 180

    def frame(page, tick):
        page.evaluate(f'cabin.test.advanceTo({tick})')
        return canvas_pixels(page)

    for t in ('day', 'night'):
        page, pp = open_page(browser, base, f'?test&time={t}', problems, viewport={'width': 1366, 'height': 768})
        plain, _ = capture_at(browser, base, f'?test&time={t}', 5, problems)
        type_command(page, 'cig')
        said = output_lines(page)
        placing = frame(page, 5)
        n, b = diff_box(plain, placing)
        settled_tick = int(place_ms // 100) + 2
        settled = frame(page, settled_tick)
        plain_settled, _ = capture_at(browser, base, f'?test&time={t}', settled_tick, problems)
        n2, b2 = diff_box(plain_settled, settled)
        inside = b2 is not None and b2[0] >= box[0] and b2[1] >= box[1] and b2[2] <= box[2] and b2[3] <= box[3]
        check(n > 0 and inside and said == ['you set your pack down on the sill.'],
              f'{t}: `cig` slides the pack in ({n} pixels changing at 0.5 s), then only the pack remains '
              f'({n2} pixels, inside the pack box: {inside}); bubble "{said[0]}"')
        type_command(page, 'cig')
        check(output_lines(page) == ['your pack is already on the sill.'], f'{t}: a second `cig` says "{output_lines(page)[0]}"')

        # Hover: a black ring appears around the pack and the cursor is a hand.
        cx, cy = screen_point(page, left + pk['frame_w'] // 2, top + pk['frame_h'] // 2)
        page.mouse.move(cx, cy)
        hovered = frame(page, settled_tick)
        nh, bh = diff_box(settled, hovered)
        changed = np.any(settled != hovered, axis=2)
        all_black = bool(np.all(hovered[changed][:, :3] == 0))
        cursor = page.evaluate("getComputedStyle(document.getElementById('scene')).cursor")
        ring_inside = bh is not None and bh[0] >= box[0] and bh[1] >= box[1] and bh[2] <= box[2] and bh[3] <= box[3]
        check(nh > 0 and all_black and ring_inside and cursor == 'pointer',
              f'{t}: hovering the pack draws a black outline ({nh} pixels, all black: {all_black}, '
              f'hugging the pack: {ring_inside}) and the cursor becomes "{cursor}"')
        save_pair(f'cig_hover_{t}.png', settled[100:170, 60:160], hovered[100:170, 60:160])
        page.mouse.move(5, 5)
        unhovered = frame(page, settled_tick)
        check(diff_box(settled, unhovered)[0] == 0, f'{t}: moving the mouse away removes the outline')

        # Click: the cigarette comes out and the smoking plays over everything.
        page.mouse.move(cx, cy)
        page.mouse.click(cx, cy)
        click_tick = settled_tick
        shots = []
        for at_ms in (1000, 3500, 6000, 15000, 25000, smoke_ms - 500):
            shots.append(frame(page, click_tick + int(at_ms // 100)))
        during = shots[2]
        page.mouse.move(cx + 1, cy)   # hovering while smoking: no outline, no hand
        busy_cursor = page.evaluate("getComputedStyle(document.getElementById('scene')).cursor")
        plain_mid, _ = capture_at(browser, base, f'?test&time={t}', click_tick + 60, problems, ['cig'])
        over_frame = np.any(during != plain_mid, axis=2)
        outside_opening = over_frame.copy(); outside_opening[24:131, 40:280] = False
        page.mouse.click(cx, cy)      # ignored while smoking
        # A few ticks after the end: finishing earns Smoke Break, and its new pin
        # on the achievement board sparkles for about half a second.
        end_tick = click_tick + int(smoke_ms // 100) + 8
        after = frame(page, end_tick)
        page.mouse.move(5, 5)
        after = frame(page, end_tick)
        # A whole cigarette earns Smoke Break: the ashtray is on the sill now too.
        plain_after, _ = capture_at(browser, base, f'?test&debug&time={t}', end_tick, problems,
                                    ['cig', 'debug unlock smoke_break'])
        n_after = diff_box(plain_after, after)[0]
        check(over_frame.sum() > 0 and busy_cursor != 'pointer' and n_after == 0,
              f'{t}: clicking starts the smoking ({over_frame.sum()} pixels differ at 6 s, '
              f'{outside_opening.sum()} of them over the window frame or sill, i.e. drawn above everything); '
              f'no hand cursor mid-smoke; after {smoke_ms / 1000:.2f} s it ends and the scene is identical to '
              f'"pack on the sill" ({n_after} differing pixels)')
        strip = np.concatenate(shots[:5], axis=1)
        Image.fromarray(strip).save(SCREENS / f'cig_smoking_{t}.png')

        # Smoke again: clicking after it ends works a second time.
        page.mouse.move(cx, cy)
        page.mouse.click(cx, cy)
        again = frame(page, end_tick + 30)
        check(diff_box(plain_after, again)[0] > 0, f'{t}: the pack can be clicked again for another cigarette')
        check(not pp, f'{t}: no console problems ({pp})')
        problems.extend(pp)
        page.context.close()



# ── 4. scheduler ─────────────────────────────────────────────────────────
def check_scheduler(browser, base, problems):
    report.append('\n## Scheduler (real clock, config.js served with short timers)\n')
    source = (ROOT / 'js' / 'config.js').read_text()
    fast = re.sub(r'(\w+):\s*\{ minWaitSec: \d+,\s*maxWaitSec: \d+,\s*chance: ([\d.]+)(, [^}]*)? \}',   # keeps skipWhile
                  r'\1: { minWaitSec: 0.3, maxWaitSec: 0.6, chance: \2\3 }', source)
    assert fast != source
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    ctx.route('**/js/config.js', lambda route: route.fulfill(body=fast, content_type='text/javascript'))
    page = ctx.new_page()
    pp = watch_page(page)
    page.goto(base + 'index.html')
    page.wait_for_function('window.cabin && window.cabin.scheduler')
    page.evaluate('''() => {
        window.fired = {}; window.started = {};
        for (const [name, fn] of Object.entries(cabin.app.events)) {
            cabin.app.events[name] = (...a) => { fired[name] = (fired[name] || 0) + 1;
                                                 const ok = fn(...a); if (ok) started[name] = (started[name] || 0) + 1; return ok; };
        }
    }''')
    shots = []
    for i in range(4):
        page.wait_for_timeout(2500)
        shots.append(np.asarray(Image.open(io.BytesIO(page.locator('#scene').screenshot()))))
    fired = page.evaluate('fired')
    started = page.evaluate('started')
    for name in ('bird', 'farbird', 'wind', 'sasquatch', 'weather'):
        check(fired.get(name, 0) > 0, f'{name} fired by itself {fired.get(name, 0)} times in 10 s '
                                      f'({started.get(name, 0)} actually started)')
    rolls = 10 / 0.45
    report.append(f'  sasquatch chance check: about {rolls:.0f} rolls at chance 0.3, '
                  f'expected about {rolls * 0.3:.0f} fires, got {fired.get("sasquatch", 0)}')
    Image.fromarray(shots[-1]).save(SCREENS / 'scheduler_live.png')
    check(not pp, f'no console problems on the live (non-test) page: {pp}')
    problems.extend(pp)

    # The front trees: one full sway, then a rest of 8-20 s (config), checked
    # by driving the real treetops module for 10 simulated minutes.
    trees = page.evaluate('''async () => {
        const { config } = await import('./js/config.js');
        const { createTreetops } = await import('./js/scene/treetops.js');
        const info = { frames: 4, ms_per_frame: 300, loop: true, anchor: [0, 0], placement: { x: 0, y: 0 },
                       frame_w: 320, frame_h: 180 };
        const trees = createTreetops({ animation: () => ({ info, imageFor: () => ({}) }) });
        let shown = null;
        const ctx = { drawImage: (img, sx) => { shown = sx / 320; } };
        const sways = [], rests = []; let swayStart = null, restStart = null, last = null, order = [];
        for (let t = 0; t < 600000; t += 16) {
            shown = null; trees.draw(ctx, 'day'); trees.update(16);
            const moving = shown !== null;
            if (moving && swayStart === null) { swayStart = t; if (restStart !== null) rests.push(t - restStart); restStart = null; order = []; }
            if (moving && order[order.length - 1] !== shown) order.push(shown);
            if (!moving && swayStart !== null) { sways.push({ ms: t - swayStart, order: order.join('') }); swayStart = null; restStart = t; }
        }
        return { range: config.treetops.restBetweenSwaysSec, sways, rests };
    }''')
    rests = [r / 1000 for r in trees['rests']]
    orders = {s['order'] for s in trees['sways']}
    check(orders == {'0123'} and all(trees['range'][0] - 0.05 <= r <= trees['range'][1] + 0.05 for r in rests)
          and len(trees['sways']) > 10,
          f"front trees: {len(trees['sways'])} sways in 10 minutes (they used to sway non-stop), each a "
          f"full cycle {sorted(orders)}, rests {min(rests):.1f}-{max(rests):.1f} s (config {trees['range']})")

    # The chance and wait-range logic, statistically, with a seeded random
    # source: 20,000 rolls of a 3-10 minute, 30% timer.
    stats = page.evaluate('''async () => {
        const { createScheduler } = await import('./js/scheduler.js');
        let seed = 12345;
        const random = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
        let fires = 0;
        const s = createScheduler({ sasquatch: { minWaitSec: 180, maxWaitSec: 600, chance: 0.3 } },
                                  { sasquatch: () => { fires += 1; } }, random);
        let rolls = 0, minWait = Infinity, maxWait = 0, last = 0, clock = 0;
        while (rolls < 20000) {
            const before = s.timers.sasquatch.remainingMs;
            s.update(1000); clock += 1000;
            if (s.timers.sasquatch.remainingMs > before) {
                rolls += 1; const wait = clock - last; last = clock;
                if (rolls > 1) { minWait = Math.min(minWait, wait); maxWait = Math.max(maxWait, wait); }
            }
        }
        return { rate: fires / rolls, minWait: minWait / 1000, maxWait: maxWait / 1000 };
    }''')
    check(0.28 < stats['rate'] < 0.32 and 180 <= stats['minWait'] and stats['maxWait'] <= 601,
          f'sasquatch timer over 20,000 seeded rolls: fired {stats["rate"]:.1%} of the time (config 30%), '
          f'waits between {stats["minWait"]:.0f} s and {stats["maxWait"]:.0f} s (config 180-600 s)')
    ctx.close()


def check_sill(browser, base, problems):
    """ls, rm and touch: the sill as one list, and the pixels following it."""
    report.append('\n## The sill: ls, rm, touch (test mode)\n')
    query = '?test&debug&time=day'
    board = (slice(BOARD['canvas_y'] - 1, BOARD['canvas_y'] + BOARD['h'] + 1),
             slice(BOARD['canvas_x'] - 1, BOARD['canvas_x'] + BOARD['w'] + 1))

    def run(page, line):
        type_command(page, line)
        return output_lines(page)

    def at(page, tick):
        page.evaluate(f'cabin.test.advanceTo({tick})')
        return canvas_pixels(page)[..., :3]

    def same_as_fresh(page, tick, commands=(), skip_board=False):
        """Differing pixels against a page that ran only `commands`, at the same tick."""
        mine = at(page, tick)
        fresh, _ = capture_at(browser, base, query, tick, problems, list(commands))
        fresh = fresh[..., :3]
        if skip_board:
            mine, fresh = mine.copy(), fresh.copy()
            mine[board] = fresh[board] = 0
        return diff_box(mine, fresh)

    page, pp = open_page(browser, base, query, problems)
    start = run(page, 'ls')
    mug = __import__('json').loads((ROOT / 'anim' / 'manifest.json').read_text())['animations']['mug']
    mx0, my0 = mug['placement']['x'] - mug['anchor'][0], mug['placement']['y'] - mug['anchor'][1]
    removed = run(page, 'rm mug')
    after_rm = run(page, 'ls')
    gone, box = same_as_fresh(page, 10)
    in_mug_box = box is not None and mx0 <= box[0] and box[2] < mx0 + mug['frame_w'] and my0 <= box[1] and box[3] < my0 + mug['frame_h']
    page.mouse.click(*page.evaluate(f"""(() => {{ const r = document.getElementById('scene').getBoundingClientRect();
        return [r.left + {mug['placement']['x'] - 2} * r.width / 320, r.top + {mug['placement']['y'] - 4} * r.height / 180]; }})()"""))
    sips = page.evaluate('cabin.app.progressStats().stats.mugClicks || 0')
    back = run(page, 'touch mug')
    again = run(page, 'touch mug')
    restored, _ = same_as_fresh(page, 20)
    check(start == ['mug', 'put away: folder'] and removed == ['you take the mug off the sill.']
          and after_rm == ['the sill is empty.', 'put away: mug  folder'] and gone > 0 and in_mug_box and sips == 0
          and back == ['you put the mug on the sill.'] and again == ['the mug is already on the sill.'] and restored == 0,
          f'`ls` at the start: {start}; `rm mug`: {removed}, then `ls`: {after_rm}; the cup is gone ({gone} px, all '
          f'inside the cup: {in_mug_box}) and clicking there sips nothing ({sips}); `touch mug`: {back}, again: {again}; '
          f'afterwards the scene matches a page that never moved it ({restored} px differ)')

    # In use: a sip in progress, the folder sliding in.
    page.mouse.click(*page.evaluate(f"""(() => {{ const r = document.getElementById('scene').getBoundingClientRect();
        return [r.left + {mug['placement']['x'] - 2} * r.width / 320, r.top + {mug['placement']['y'] - 4} * r.height / 180]; }})()"""))
    mid_sip = run(page, 'rm mug')
    page.mouse.move(2, 2)
    at(page, 60)
    out = run(page, 'whoami')
    sliding = run(page, 'rm folder')
    listed = run(page, 'ls')
    at(page, 90)
    put_away = run(page, 'rm folder')
    no_folder, _ = same_as_fresh(page, 100)
    touched = run(page, 'touch folder')
    at(page, 130)
    check(mid_sip == ["rm: cannot remove 'mug': it's in use"] and sliding == ["rm: cannot remove 'folder': it's in use"]
          and listed == ['mug  folder'] and put_away == ['you take the folder off the sill.'] and no_folder == 0
          and touched == ['you put the folder on the sill.'] and run(page, 'ls') == ['mug  folder'],
          f'mid-sip `rm mug`: {mid_sip}; `whoami` then `rm folder` while it slides in: {sliding}; `ls`: {listed}; '
          f'once it rests, `rm folder`: {put_away} (the scene then matches a page without it: {no_folder} px differ); '
          f'`touch folder`: {touched}, and it slides back in')

    # Rewards: secret until earned, arrive with the achievement, leave on reset.
    early_touch = run(page, 'touch trophy')
    early_rm = run(page, 'rm trophy')
    unknown = run(page, 'rm sofa')
    run(page, 'debug unlock woodsman')   # with the twelve others it needs
    run(page, 'debug unlock all')
    at(page, 140)
    earned = run(page, 'ls')
    run(page, 'rm trophy')
    run(page, 'rm ashtray')
    at(page, 150)
    listed_away = run(page, 'ls')
    run(page, 'touch trophy')
    run(page, 'touch ashtray')
    run(page, 'reset yes')
    at(page, 151)
    after_reset = run(page, 'ls')
    check(early_touch == ["touch: cannot touch 'trophy': you don't have one"]
          and early_rm == ["rm: cannot remove 'trophy': not on the sill"] and unknown == ["rm: cannot remove 'sofa': not on the sill"]
          and earned == ['mug  folder  trophy  ashtray'] and listed_away == ['mug  folder', 'put away: trophy  ashtray']
          and after_reset == ['mug  folder'],
          f'before Woodsman: `touch trophy` {early_touch}, `rm trophy` {early_rm} (as for `rm sofa`: {unknown}); '
          f'earning everything: `ls` {earned}; after `rm` of both: {listed_away}; after `reset yes`: {after_reset}')
    page.context.close()

    # The rewards' pixels: put away, the sill matches a visitor who never earned them.
    page, pp2 = open_page(browser, base, query, problems)
    run(page, 'debug unlock smoke_break')
    run(page, 'debug unlock woodsman')
    run(page, 'rm trophy')
    run(page, 'rm ashtray')
    run(page, 'clear')
    away, _ = same_as_fresh(page, 40, skip_board=True)   # the board shows their pins either way
    page.context.close()

    # The pack stays an easter egg: unknown until `cig`, then an ordinary sill item.
    page, pp3 = open_page(browser, base, query, problems)
    hidden = run(page, 'touch pack')
    run(page, 'cig')
    at(page, 30)
    with_pack = run(page, 'ls')
    rm_pack = run(page, 'rm cigarettes')
    no_pack, _ = same_as_fresh(page, 40)
    touch_pack = run(page, 'touch cig')
    at(page, 70)
    pack_back, _ = same_as_fresh(page, 70, ['cig'])
    check(away == 0 and hidden == ["touch: cannot touch 'pack': you don't have one"] and with_pack == ['mug  pack', 'put away: folder']
          and rm_pack == ['you take the pack off the sill.'] and no_pack == 0 and touch_pack == ['you put the pack on the sill.']
          and pack_back == 0 and not pp and not pp2 and not pp3,
          f'trophy and ashtray put away: the scene matches a visitor without them ({away} px differ, board aside); '
          f'the pack before `cig`: {hidden}; after: `ls` {with_pack}; `rm cigarettes`: {rm_pack} (then {no_pack} px differ '
          f'from a page without it); `touch cig`: {touch_pack}, and it slides back in ({pack_back} px differ from a page that only ran `cig`)')
    problems.extend(pp + pp2 + pp3)
    page.context.close()


def tree_snow_mask():
    """Every pixel any stage of tree snow can cover, at any time of day."""
    info = json.loads((ROOT / 'anim' / 'manifest.json').read_text())['weather_overlays']['tree_snow']
    mask = np.zeros((180, 320), bool)
    for layer in ('far', 'near'):
        for time in ('morning', 'day', 'afternoon', 'night'):
            for n in range(1, info['stages'] + 1):
                path = ROOT / 'anim' / info[f'files_{layer}'].replace('<time>', time).replace('<N>', str(n))
                mask |= np.asarray(Image.open(path).convert('RGBA'))[..., 3] > 0
    return mask


SNOW_ALONE = """(layer) => {
  const snow = cabin.layers.find((l) => l.amount);
  const c = document.createElement('canvas'); c.width = 320; c.height = 180;
  const ctx = c.getContext('2d'); ctx.imageSmoothingEnabled = false;
  (layer === 'far' ? snow.far : snow).draw(ctx, cabin.app.timeOfDay.current());
  return c.toDataURL().split(',')[1];
}"""


def check_tree_snow(browser, base, problems):
    """Snow settles on the trees while it snows, a stage at a time, and melts off after."""
    report.append('\n## Snow on the trees (test mode)\n')
    info = json.loads((ROOT / 'anim' / 'manifest.json').read_text())['weather_overlays']['tree_snow']
    settings = {k: float(re.search(rf'{k}:\s*([\d.]+)', (ROOT / 'js' / 'config.js').read_text()).group(1))
                for k in ('fadeSec', 'stageUpSec', 'stageDownSec')}
    stage_art = lambda layer, time, n: np.asarray(Image.open(
        ROOT / 'anim' / info[f'files_{layer}'].replace('<time>', time).replace('<N>', str(n))).convert('RGBA'))
    import base64
    alone = lambda page, layer: np.asarray(Image.open(io.BytesIO(base64.b64decode(page.evaluate(SNOW_ALONE, layer)))).convert('RGBA'))
    for time in ('day', 'night'):
        page, pp = open_page(browser, base, f'?test&debug&time={time}', problems)
        amount = lambda: round(page.evaluate('cabin.layers.find((l) => l.amount).amount()'), 3)
        clear_px = int((alone(page, 'near')[..., 3] > 0).sum() + (alone(page, 'far')[..., 3] > 0).sum())
        type_command(page, 'weather snow')
        timeline, exact = [], []
        tick = 0
        fade_ticks, up_ticks = round(settings['fadeSec'] * 10), round(settings['stageUpSec'] * 10)
        for n in range(1, info['stages'] + 1):
            tick = fade_ticks + (n - 1) * up_ticks
            page.evaluate(f'cabin.test.advanceTo({tick})')
            timeline.append(amount())
            exact.append(all(np.array_equal(alone(page, layer), stage_art(layer, time, n)) for layer in ('far', 'near')))
        page.evaluate(f'cabin.test.advanceTo({tick + 300})')
        capped = amount()
        type_command(page, 'weather clear')
        down_ticks = round(settings['stageDownSec'] * 10)
        page.evaluate(f'cabin.test.advanceTo({tick + 300 + down_ticks})')
        melting = amount()
        page.evaluate(f'cabin.test.advanceTo({tick + 300 + (info["stages"] - 1) * down_ticks + fade_ticks + 1})')
        gone = amount()
        gone_px = int((alone(page, 'near')[..., 3] > 0).sum() + (alone(page, 'far')[..., 3] > 0).sum())
        check(clear_px == 0 and timeline == [1.0, 2.0, 3.0, 4.0] and all(exact) and capped == 4.0
              and melting == 3.0 and gone == 0 and gone_px == 0 and not pp,
              f'{time}: none while clear ({clear_px} px); snowing, it reaches stage {timeline} at '
              f'{settings["fadeSec"]:g} s and every {settings["stageUpSec"]:g} s after, each one the stage art exactly '
              f'(far and near: {exact}), and stops at {capped}; once it clears it melts a stage every '
              f'{settings["stageDownSec"]:g} s ({melting} after the first) and is gone ({gone}, {gone_px} px)')
        problems.extend(pp)
        page.context.close()


def check_weather_spells(browser, base, problems):
    """Rain or snow comes by itself and clears; the `weather` command overrides it."""
    report.append('\n## Weather spells (test mode)\n')
    page, pp = open_page(browser, base, '?test&debug&time=day', problems)
    now = lambda: page.evaluate('cabin.app.weather.get()')
    page.evaluate('cabin.test.advanceTo(1)')
    page.evaluate("cabin.app.events.weather({ kind: 'rain', seconds: 2 })")
    raining = now()
    page.evaluate('cabin.test.advanceTo(15)')
    still = now()
    page.evaluate('cabin.test.advanceTo(30)')
    cleared = now()
    page.evaluate("cabin.app.events.weather({ kind: 'snow', seconds: 2 })")
    earned = page.evaluate("cabin.achievements.isUnlocked('storm_chaser')")
    type_command(page, 'weather rain')        # by hand: the spell ends, rain stays
    page.evaluate('cabin.test.advanceTo(300)')
    kept = now()
    refused = page.evaluate('cabin.app.events.weather()')   # not from an overcast sky
    type_command(page, 'weather clear')
    rolled = page.evaluate('cabin.app.events.weather()')
    rolled_kind = now()
    check(raining == 'rain' and still == 'rain' and cleared == 'clear' and earned and kept == 'rain'
          and refused is False and rolled and rolled_kind in ('rain', 'snow') and not pp,
          f'a 2 s spell of rain: {raining}, still {still} at 1.4 s, {cleared} at 2.9 s; a spell of snow next earns '
          f'Storm Chaser ({earned}); `weather rain` by hand overrides the spell and stays ({kept} 30 s later); no spell '
          f'starts unless the sky is clear ({refused}); a rolled spell brings {rolled_kind}')
    problems.extend(pp)
    page.context.close()


def check_unlock_bubble(browser, base, problems):
    """An unlock replaces the bubble left by anything earlier; during a command it joins that reply."""
    report.append('\n## Unlock lines in the bubble (test mode)\n')
    page, pp = open_page(browser, base, '?test&debug&time=day', problems)
    mug = __import__('json').loads((ROOT / 'anim' / 'manifest.json').read_text())['animations']['mug']
    type_command(page, 'debug set mugclicks 24')
    before = output_lines(page)
    page.mouse.click(*page.evaluate(f"""(() => {{ const r = document.getElementById('scene').getBoundingClientRect();
        return [r.left + {mug['placement']['x'] - 2} * r.width / 320, r.top + {mug['placement']['y'] - 4} * r.height / 180]; }})()"""))
    page.evaluate('cabin.test.advanceTo(2)')
    after_sip = output_lines(page)
    type_command(page, 'weather rain')
    type_command(page, 'weather snow')
    during = output_lines(page)
    check(before == ['mugClicks = 24'] and len(after_sip) == 1 and after_sip[0].startswith('achievement unlocked: Caffeinated.')
          and len(during) == 2 and during[0].startswith('achievement unlocked: Storm Chaser.') and during[1] == 'it starts to snow.'
          and page.evaluate("document.querySelectorAll('#bubble').length") == 1 and not pp,
          f'the 25th sip replaces the bubble {before} with {after_sip}; an unlock during `weather snow` shares '
          f'its reply: {during}')
    problems.extend(pp)
    page.context.close()


def main():
    SCREENS.mkdir(parents=True, exist_ok=True)
    base, stop = serve_site()
    problems = []
    with sync_playwright() as p:
        browser = open_browser(p)
        check_layout(browser, base, problems)
        check_commands(browser, base, problems)
        check_terminal(browser, base, problems)
        check_mug(browser, base, problems)
        check_folder(browser, base, problems)
        check_folder_popup(browser, base, problems)
        check_landscape_phone(browser, base, problems)
        check_cigarette(browser, base, problems)
        check_sill(browser, base, problems)
        check_unlock_bubble(browser, base, problems)
        check_weather_spells(browser, base, problems)
        check_tree_snow(browser, base, problems)
        check_scheduler(browser, base, problems)
        browser.close()
    stop()
    report.append('\n## Console\n')
    check(not problems, f'no console errors/warnings or failed requests across every page above ({len(problems)})')
    for pr in problems:
        report.append(f'  - {pr}')
    (RESULTS / 'behaviour.md').write_text('# Behaviour checks\n' + '\n'.join(report) + '\n')
    print(f'\n{len(failures)} failures')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
