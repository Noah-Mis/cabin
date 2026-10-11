// terminal.js — the one-line command prompt at the bottom of the page, and
// the speech bubble above it that shows a command's reply. Each command
// replaces the previous bubble; a command that prints nothing leaves none.
// The prompt keeps focus and recalls earlier commands with up/down arrows.
// It knows nothing about what commands do; it hands each line to onCommand.
// Exports: createTerminal(elements, { onCommand, maxHistory })
//          -> { print, say, clear, focus, setTheme }

export function createTerminal({ bubble, form, input }, { onCommand, maxHistory }) {
  const history = [];
  let historyIndex = 0;   // history.length means "the line being typed"

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

  // colours: { background, text, dim, cursor }, or null for the wood theme.
  function setTheme(colours) {
    const terminal = form.parentElement;
    const vars = { '--terminal-bg': 'background', '--text': 'text', '--prompt': 'dim', '--rule': 'dim', '--caret': 'cursor' };
    for (const [cssVar, key] of Object.entries(vars)) {
      if (colours) terminal.style.setProperty(cssVar, colours[key]);
      else terminal.style.removeProperty(cssVar);
    }
  }

  function focus() {
    input.focus({ preventScroll: true });
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
    onCommand(line);
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp') { event.preventDefault(); recall(-1); }
    if (event.key === 'ArrowDown') { event.preventDefault(); recall(+1); }
  });

  // Keep focus so a visitor can just start typing: any click or key press
  // elsewhere on the page sends focus back to the input. Anything marked
  // data-keep-focus (like the folder pop-up) is left alone.
  const elsewhere = (node) => node instanceof Element && node.closest('[data-keep-focus]');
  document.addEventListener('pointerup', (event) => {
    if (!elsewhere(event.target) && !window.getSelection()?.toString()) focus();
  });
  document.addEventListener('keydown', (event) => {
    if (elsewhere(document.activeElement) || elsewhere(event.target)) return;
    if (document.activeElement !== input && !event.ctrlKey && !event.metaKey && !event.altKey) focus();
  });

  return { print, say, clear, focus, setTheme };
}
