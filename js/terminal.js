// terminal.js — the one-line command prompt at the bottom of the page, and
// the speech bubble above it that shows a command's reply. Each command
// replaces the previous bubble; a command that prints nothing leaves none.
// The prompt keeps focus and recalls earlier commands with up/down arrows.
// It knows nothing about what commands do; it hands each line to onCommand.
// On a phone held sideways (compactLandscape matches) the keyboard covers
// nearly everything, so there it comes up only when the prompt is tapped,
// goes away after each command, and the prompt rides just above it.
// Exports: createTerminal(elements, { onCommand, maxHistory, compactLandscape })
//            compactLandscape: a MediaQueryList (config.compactLandscape.query)
//          -> { print, say, announce, clear, focus, setTheme, prefill }
//   prefill(text) puts text on the prompt, ready to send, and focuses it.

export function createTerminal({ bubble, form, input }, { onCommand, maxHistory, compactLandscape }) {
  const terminal = form.parentElement;
  const history = [];
  let historyIndex = 0;   // history.length means "the line being typed"
  let running = false;    // a command is running: its reply is being written

  // Adds a line to the current bubble, showing it if it was hidden.
  function print(text, kind = 'out') {
    const line = document.createElement('div');
    line.className = `line ${kind}`;
    line.textContent = text;
    bubble.append(line);
    bubble.hidden = false;
  }

  function clear() {
    bubble.replaceChildren();
    bubble.hidden = true;
  }

  // A one-line reply to something other than a command (like a sip of coffee).
  function say(text) {
    clear();
    print(text);
  }

  // Something that happened (an achievement): it replaces whatever bubble is
  // showing, unless a command is running, whose reply it then joins.
  function announce(text) {
    if (running) print(text);
    else say(text);
  }

  // colours: { background, text, dim, cursor }, or null for the wood theme.
  function setTheme(colours) {
    const vars = { '--terminal-bg': 'background', '--text': 'text', '--prompt': 'dim', '--rule': 'dim', '--caret': 'cursor' };
    for (const [cssVar, key] of Object.entries(vars)) {
      if (colours) terminal.style.setProperty(cssVar, colours[key]);
      else terminal.style.removeProperty(cssVar);
    }
  }

  function focus() {
    input.focus({ preventScroll: true });
  }

  function prefill(text) {
    input.value = text;
    focus();
    input.setSelectionRange(text.length, text.length);
  }

  function remember(line) {
    if (line && history[history.length - 1] !== line) history.push(line);
    if (history.length > maxHistory) history.shift();
    historyIndex = history.length;
  }

  function recall(step) {
    historyIndex = Math.max(0, Math.min(history.length, historyIndex + step));
    input.value = history[historyIndex] ?? '';
    input.setSelectionRange(input.value.length, input.value.length);
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const line = input.value;
    input.value = '';
    clear();
    remember(line.trim());
    running = true;
    try {
      onCommand(line);
    } finally {
      running = false;
    }
    if (compactLandscape.matches) input.blur();   // put the keyboard away to show what happened
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp') { event.preventDefault(); recall(-1); }
    if (event.key === 'ArrowDown') { event.preventDefault(); recall(+1); }
  });

  // Keep focus so a visitor can just start typing: any click or key press
  // elsewhere on the page sends focus back to the input. Anything marked
  // data-keep-focus (like the folder pop-up) is left alone.
  const elsewhere = (node) => node instanceof Element && node.closest('[data-keep-focus]');
  // On a sideways phone only a tap on the prompt itself does: focus brings
  // up the keyboard, and a tap on the scene is meant for the scene.
  document.addEventListener('pointerup', (event) => {
    if (compactLandscape.matches && !terminal.contains(event.target)) return;
    if (!elsewhere(event.target) && !window.getSelection()?.toString()) focus();
  });
  document.addEventListener('keydown', (event) => {
    if (elsewhere(document.activeElement) || elsewhere(event.target)) return;
    if (document.activeElement !== input && !event.ctrlKey && !event.metaKey && !event.altKey) focus();
  });

  // Sideways phone: while the keyboard is up, keep the prompt (and its
  // bubble) on the bottom edge of what is still visible, and when it goes
  // away undo any scrolling the browser did to show the input.
  const viewport = window.visualViewport;
  function rideAboveKeyboard() {
    const covered = compactLandscape.matches && viewport
      ? Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop) : 0;
    terminal.style.transform = covered ? `translateY(${-covered}px)` : '';
  }
  viewport?.addEventListener('resize', rideAboveKeyboard);
  viewport?.addEventListener('scroll', rideAboveKeyboard);
  compactLandscape.addEventListener('change', rideAboveKeyboard);
  input.addEventListener('blur', () => {
    if (compactLandscape.matches) window.scrollTo(0, 0);
  });

  return { print, say, announce, clear, focus, setTheme, prefill };
}
