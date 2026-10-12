"""harness.py — shared helpers for the browser tests.

Serves the site folder over HTTP (ES modules do not load from file://) and
opens it in headless Chrome through Playwright, recording every console
message, page error and failed request so tests can assert there were none.

Exports:
    serve_site() -> (base_url, stop)
    open_browser(playwright) -> browser
    watch_page(page) -> problems list (filled in as the page runs)
    canvas_pixels(page) -> numpy array (H, W, 4) of the native canvas
    add_board(image, time, unlocked=()) -> image with the achievement board drawn
        where the site hangs it, over the window frame, with a pin (or the
        star) for each achievement id in `unlocked`
    add_pond_bank(image, time) -> image with the grassy bank by the pool (scenery,
        drawn right after the waterfall)
    tree_snow(time, amount) -> (far, near) RGBA layers of snow on the trees, as
        js/scene/treesnow.js draws them for that `amount` (0 = none)
"""
import base64, functools, io, json, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'tests' / 'results'
BOARD = json.loads((ROOT / 'anim' / 'board' / 'board_layout.json').read_text())['board']
ACHIEVEMENT_IDS = [a['id'] for a in json.loads((ROOT / 'anim' / 'achievements' / 'achievements.json').read_text())['achievements']]


def add_pond_bank(image, time):
    info = json.loads((ROOT / 'anim' / 'achievements' / 'achievements.json').read_text())['animations']['pond_bank']
    bank = Image.open(ROOT / 'anim' / 'achievements' / f'pond_bank_{time}.png').convert('RGBA')
    image.alpha_composite(bank, (info['placement']['x'], info['placement']['y']))
    return image


def tree_snow(time, amount):
    info = json.loads((ROOT / 'anim' / 'manifest.json').read_text())['weather_overlays']['tree_snow']
    layers = []
    for layer in ('far', 'near'):
        canvas = Image.new('RGBA', (320, 180))
        stage = max(1, int(amount))
        art = lambda n: Image.open(ROOT / 'anim' / info[f'files_{layer}'].replace('<time>', time).replace('<N>', str(n))).convert('RGBA')
        def faded(im, alpha):
            a = np.asarray(im).copy()
            a[..., 3] = np.round(a[..., 3] * alpha).astype(np.uint8)
            return Image.fromarray(a)
        if amount > 0:
            canvas.alpha_composite(faded(art(stage), min(1, amount)))
            if stage < info['stages'] and amount - stage > 0:
                canvas.alpha_composite(faded(art(stage + 1), amount - stage))
        layers.append(canvas)
    return tuple(layers)


def add_board(image, time, unlocked=()):
    art = lambda name: Image.open(ROOT / 'anim' / 'board' / name).convert('RGBA')
    night = next(f for f in BOARD['files'] if f.endswith('_night.png'))
    day = next(f for f in BOARD['files'] if f != night)
    x, y = BOARD['canvas_x'], BOARD['canvas_y']
    image.alpha_composite(art(night if time == 'night' else day), (x, y))
    pins = [i for i in ACHIEVEMENT_IDS if i != BOARD['star']['for']]
    for id_ in unlocked:
        if id_ == BOARD['star']['for']:
            (dx, dy), name = BOARD['star']['position'], BOARD['star']['file']
        else:
            (dx, dy), name = BOARD['pin']['positions'][pins.index(id_)], BOARD['pin']['file']
        image.alpha_composite(art(name), (x + dx, y + dy))
    return image


class QuietHandler(SimpleHTTPRequestHandler):
    # Windows can map .js to text/plain via the registry, which browsers
    # refuse for module scripts. Static hosts like GitHub Pages get this right.
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.js': 'text/javascript'}
    # Keep-alive: one page load asks for ~90 files at once, and opening a new
    # connection for each exhausts Windows' socket buffers over a long run.
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass


class Server(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


def serve_site():
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = Server(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{server.server_address[1]}/', server.shutdown


def open_browser(playwright):
    return playwright.chromium.launch(channel='chrome', headless=True)


def watch_page(page):
    problems = []
    page.on('console', lambda m: problems.append(f'console.{m.type}: {m.text}')
            if m.type in ('error', 'warning') else None)
    page.on('pageerror', lambda e: problems.append(f'page error: {e}'))
    page.on('requestfailed', lambda r: problems.append(f'request failed: {r.url}'))
    page.on('response', lambda r: problems.append(f'HTTP {r.status}: {r.url}')
            if r.status >= 400 else None)
    return problems


def canvas_pixels(page):
    data_url = page.evaluate('cabin.test.capture()')
    png = base64.b64decode(data_url.split(',', 1)[1])
    return np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'))
