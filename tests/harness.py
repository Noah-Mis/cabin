"""harness.py — shared helpers for the browser tests.

Serves the site folder over HTTP (ES modules do not load from file://) and
opens it in headless Chrome through Playwright, recording every console
message, page error and failed request so tests can assert there were none.

Exports:
    serve_site() -> (base_url, stop)
    open_browser(playwright) -> browser
    watch_page(page) -> problems list (filled in as the page runs)
    canvas_pixels(page) -> numpy array (H, W, 4) of the native canvas
"""
import base64, functools, io, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'tests' / 'results'


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
