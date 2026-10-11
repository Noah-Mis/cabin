"""sound.py — checks for the ambient sound.

1. The waterfall loop, rendered offline through the site's own createLoop()
   for 60 s: the level must stay steady across seams (no gaps, no pulsing),
   compared with simply looping the whole file. And the level it plays at.
2. The live page: nothing is created before the first click (browsers warn
   otherwise); after it, the waterfall loops; a spawned bird plays the bird
   sound from the side it enters on (the far bird is silent); a gust plays
   the wind; `sound off` / `on`; a hidden tab pauses sound; test mode is
   silent; the console stays clean.

Writes tests/results/sound.md.   Run:  python tests/sound.py
"""
import re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from harness import ROOT, RESULTS, serve_site, open_browser, watch_page

CONFIG = (ROOT / 'js' / 'config.js').read_text()
report, failures = [], []


def check(ok, what):
    report.append(f"- {'PASS' if ok else 'FAIL'}: {what}")
    if not ok:
        failures.append(what)
    print(report[-1].encode('ascii', 'replace').decode())


OFFLINE = """async () => {
  const { config } = await import('./js/config.js');
  const { createLoop } = await import('./js/sound.js');
  const w = config.sound.sounds.waterfall;
  const seconds = 60, rate = 44100;
  const render = async (loopSettings, volumeDb) => {
    const ctx = new OfflineAudioContext(2, seconds * rate, rate);
    const buffer = await ctx.decodeAudioData(await (await fetch(config.sound.dir + w.file)).arrayBuffer());
    const gain = ctx.createGain();
    gain.gain.value = 10 ** (volumeDb / 20);
    gain.connect(ctx.destination);
    createLoop(ctx, buffer, gain, loopSettings).extend(seconds);
    const out = (await ctx.startRendering()).getChannelData(0);
    const win = rate / 2, levels = [];
    for (let i = rate * 2; i + win <= out.length; i += win) {   // skip the first 2 s (the fade in)
      let s = 0; for (let j = 0; j < win; j++) s += out[i + j] ** 2;
      levels.push(10 * Math.log10(s / win));
    }
    const mean = 10 * Math.log10(levels.reduce((a, l) => a + 10 ** (l / 10), 0) / levels.length);
    return { min: Math.min(...levels), max: Math.max(...levels), mean, duration: buffer.duration };
  };
  const site = await render(w.loop, w.volumeDb);
  const naive = await render({ startSec: 0, crossfadeSec: 0.02 }, w.volumeDb);
  return { site, naive, settings: w };
}"""

DISTANCE = """async () => {
  const { config } = await import('./js/config.js');
  const { createLoop, createDistance } = await import('./js/sound.js');
  const w = config.sound.sounds.waterfall, rate = 44100, seconds = 9, stopAt = 6;   // the loop section is about 7 s
  const render = async (withDistance, bandFilter) => {
    const ctx = new OfflineAudioContext(2, seconds * rate, rate);
    const buffer = await ctx.decodeAudioData(await (await fetch(config.sound.dir + w.file)).arrayBuffer());
    let out = ctx.destination;
    if (bandFilter) {   // a steep measuring filter: three stages, so it hears only that band
      for (let stage = 0; stage < 3; stage++) {
        const f = ctx.createBiquadFilter(); f.type = bandFilter[0]; f.frequency.value = bandFilter[1];
        f.connect(out); out = f;
      }
    }
    const into = withDistance ? createDistance(ctx, w.distance, out).input : out;
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(into);
    src.start(0, w.loop.startSec, stopAt);
    const r = await ctx.startRendering();
    return [r.getChannelData(0), r.getChannelData(1)];
  };
  const energy = (ch, from, to) => { let s = 0; for (let i = from * rate; i < to * rate; i++) s += ch[i] ** 2; return s; };
  const db = (x) => 10 * Math.log10(x);
  const correlation = ([l, r]) => { let lr = 0, ll = 0, rr = 0;
    for (let i = rate; i < stopAt * rate; i++) { lr += l[i] * r[i]; ll += l[i] ** 2; rr += r[i] ** 2; } return lr / Math.sqrt(ll * rr); };
  const near = await render(false), far = await render(true);
  const nearHigh = await render(false, ['highpass', 4000]), farHigh = await render(true, ['highpass', 4000]);
  const nearLow = await render(false, ['lowpass', 100]), farLow = await render(true, ['lowpass', 100]);
  const level = (ch) => db(energy(ch[0], 1, stopAt) / ((stopAt - 1) * rate));
  return {
    highDropDb: level(nearHigh) - level(farHigh),   // how much quieter each band is, in absolute terms
    lowDropDb: level(nearLow) - level(farLow),
    corrNear: correlation(near), corrFar: correlation(far),
    // Echo: energy 0.3-1.3 s after the sound stops, relative to while it played.
    tailNearDb: db(energy(near[0], stopAt + 0.3, stopAt + 1.3)) - db(energy(near[0], stopAt - 1, stopAt)),
    tailFarDb: db(energy(far[0], stopAt + 0.3, stopAt + 1.3)) - db(energy(far[0], stopAt - 1, stopAt)),
    loudnessChangeDb: level(far) - level(near),
  };
}"""


def main():
    base, stop = serve_site()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True, args=['--autoplay-policy=user-gesture-required'])
        page = browser.new_page(viewport={'width': 1280, 'height': 752})
        problems = watch_page(page)
        page.goto(base + 'index.html?debug')
        page.wait_for_function('window.cabin && window.cabin.scheduler')

        r = page.evaluate(OFFLINE)
        s, n = r['site'], r['naive']
        check(s['max'] - s['min'] <= 1.5 and s['min'] > s['mean'] - 1.5,
              f"waterfall loop over 60 s: level stays within {s['max'] - s['min']:.1f} dB "
              f"({s['min']:.1f} to {s['max']:.1f} dBFS in half-second steps), no gaps; "
              f"looping the whole file instead would swing {n['max'] - n['min']:.1f} dB every {n['duration']:.0f} s")
        check(-50 < s['mean'] < -38, f"waterfall plays at {s['mean']:.1f} dBFS on average (quiet; full scale is 0)")

        d = page.evaluate(DISTANCE)
        check(d['highDropDb'] >= 6 and d['lowDropDb'] >= 3 and d['corrFar'] > d['corrNear'] + 0.1 and d['tailFarDb'] > -40,
              f"waterfall sounds distant: the crisp top end (above 4 kHz) is {d['highDropDb']:.1f} dB quieter, "
              f"close-up rumble (below 100 Hz) {d['lowDropDb']:.1f} dB quieter; stereo narrower (left/right correlation "
              f"{d['corrNear']:.2f} -> {d['corrFar']:.2f}); a soft echo lingers after it stops ({d['tailFarDb']:.0f} dB vs "
              f"{d['tailNearDb']:.0f} dB without); overall {d['loudnessChangeDb']:+.1f} dB from the effect")

        page.wait_for_timeout(1500)
        before = page.evaluate('cabin.sound.state()')
        logged_before = page.evaluate('cabin.sound.log.length')
        check(before == 'not started' and logged_before == 0 and not problems,
              f'before any click: audio {before!r}, nothing played ({logged_before}), console clean ({problems})')

        page.mouse.click(640, 300)
        page.wait_for_function("cabin.sound.state() === 'running'", timeout=10000)
        page.wait_for_timeout(300)
        log = page.evaluate('cabin.sound.log')
        water = [e for e in log if e['name'] == 'waterfall']
        check(len(water) == 1 and water[0]['loop'],
              f"first click starts the waterfall loop (state running, at {water[0]['volumeDb'] if water else '?'} dB)")

        # Listen to what actually comes out: a meter on the final mix.
        def levels(seconds, every=0.1):
            out = []
            for _ in range(int(seconds / every)):
                page.wait_for_timeout(int(every * 1000))
                out.append(page.evaluate('cabin.sound.levelDb()'))
            return out
        bed = levels(3)
        bed_db = sorted(bed)[len(bed) // 2]
        # No dropouts: the meter never falls far below the waterfall's own level.
        check(-56 < bed_db < -40 and min(bed) > bed_db - 12,
              f"the live page really outputs the waterfall: {bed_db:.1f} dBFS (median over 3 s, lowest {min(bed):.1f}); "
              f"silence would read about -120")
        page.focus('#input'); page.keyboard.type('debug event wind'); page.keyboard.press('Enter')
        gust = levels(4)
        rise = max(gust) - bed_db
        check(rise >= 4, f"a gust rises {rise:.1f} dB above the waterfall at its loudest ({max(gust):.1f} dBFS), so it is heard over it")
        page.focus('#input'); page.keyboard.type('debug sound'); page.keyboard.press('Enter')
        page.wait_for_timeout(100)
        readout = page.eval_on_selector_all('#bubble .line', 'e => e.map(x => x.textContent)')[-1]
        check(readout.startswith('sound running, output -'), f'`debug sound` reports what is playing: "{readout}"')
        page.wait_for_timeout(2000)   # let the gust finish before the next checks

        def cmd(line):
            page.focus('#input'); page.keyboard.type(line); page.keyboard.press('Enter')
            page.wait_for_timeout(150)
            return page.evaluate('cabin.sound.log')

        log = cmd('debug event bird direction=1')
        right = cmd('debug event bird direction=-1')
        birds = [e for e in right if e['name'] == 'bird']
        far = cmd('debug event farbird')
        far_sounds = len([e for e in far if e['name'] == 'bird']) - len(birds)
        check(len(birds) == 2 and birds[0]['pan'] < 0 < birds[1]['pan'] and far_sounds == 0,
              f"a bird entering from the left is heard on the left (pan {birds[0]['pan'] if birds else '?'}), "
              f"from the right on the right ({birds[1]['pan'] if len(birds) > 1 else '?'}), once each; "
              f"the far-off bird makes no sound ({far_sounds})")
        before_wind = len([e for e in page.evaluate('cabin.sound.log') if e['name'] == 'wind'])
        wind = [e for e in cmd('debug event wind') if e['name'] == 'wind'][before_wind:]
        check(len(wind) == 1 and wind[0]['pan'] < 0 < wind[0]['panTo'],
              f"a gust plays the wind once, sweeping {wind[0]['pan'] if wind else '?'} -> {wind[0]['panTo'] if wind else '?'} "
              f"over {wind[0]['seconds'] if wind else '?'} s (the file's silent start and end trimmed)")

        cmd('sound off')
        off_state = page.evaluate('cabin.sound.state()')
        count = len(page.evaluate('cabin.sound.log'))
        cmd('debug event bird direction=1')
        page.wait_for_timeout(1200)   # let that bird clear before the next
        silent = len(page.evaluate('cabin.sound.log')) == count
        cmd('sound on')
        page.wait_for_function("cabin.sound.state() === 'running'", timeout=5000)
        check(off_state == 'suspended' and silent, f'`sound off`: audio {off_state}, a bird spawned silently; `sound on` resumes')

        page.evaluate("""() => { Object.defineProperty(document, 'visibilityState', { get: () => 'hidden', configurable: true });
                                 document.dispatchEvent(new Event('visibilitychange')); }""")
        page.wait_for_timeout(300)
        hidden = page.evaluate('cabin.sound.state()')
        page.evaluate("""() => { Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
                                 document.dispatchEvent(new Event('visibilitychange')); }""")
        page.wait_for_function("cabin.sound.state() === 'running'", timeout=5000)
        check(hidden == 'suspended', f'a hidden tab pauses sound ({hidden}); coming back resumes it')

        help_text = '\n'.join(cmd('help') and page.eval_on_selector_all('#bubble .line', 'e => e.map(x => x.textContent)'))
        check('sound on|off' in help_text, '`help` lists `sound on|off`')

        test_page = browser.new_page()
        tp = watch_page(test_page)
        test_page.goto(base + 'index.html?test&debug')
        test_page.wait_for_function('window.cabin && window.cabin.test')
        test_page.mouse.click(300, 300)
        test_page.focus('#input'); test_page.keyboard.type('debug event bird'); test_page.keyboard.press('Enter')
        test_page.wait_for_timeout(500)
        check(test_page.evaluate('cabin.sound.state()') == 'not started' and not tp,
              'test mode stays silent (deterministic pixel tests are unaffected)')
        check(not problems, f'no console errors or warnings on the live page ({problems})')
        browser.close()
    stop()
    (RESULTS / 'sound.md').write_text('# Sound checks\n' + '\n'.join(report) + '\n', encoding='utf-8')
    print(f'\n{len(failures)} failures')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
