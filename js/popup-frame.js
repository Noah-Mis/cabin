// popup-frame.js — what every pop-up over the scene shares: the dimmed
// backdrop, a dialog drawn at the canvas's whole-number pixel scale (shrunk
// if needed to fit above the prompt line, and centred there), a plain
// single-column fallback when that would be too small to read, the fade in
// and out, and closing on Escape or a click outside. The folder pop-up and
// the achievement board fill it with their own art and text.
// Exports: createPopupFrame(canvas, options)
//            options: { bottomInset(), className, w, h, label, backdrop, fadeMs, minCssPxPerArtPx }
//            -> { backdrop, popup, art, show(onRequestClose), hide(), isShown(), requestClose() }
//   art is a w x h box in art pixels, scaled up with the dialog; put images
//   there. Text goes on the dialog itself, sized with --u (one art pixel in
//   CSS pixels). onRequestClose() is called on Escape or a click outside;
//   the caller decides when to actually hide().

export function createPopupFrame(canvas, { bottomInset, className, w, h, label, backdrop: backdropColour, fadeMs, minCssPxPerArtPx }) {
  const backdrop = el('div', `popup-backdrop ${className}-backdrop`);
  backdrop.hidden = true;
  backdrop.dataset.keepFocus = '';   // the terminal leaves focus alone in here
  backdrop.style.setProperty('--popup-backdrop', backdropColour);
  backdrop.style.setProperty('--popup-fade', `${fadeMs}ms`);

  const popup = el('div', `popup ${className}`);
  popup.setAttribute('role', 'dialog');
  popup.setAttribute('aria-modal', 'true');
  popup.setAttribute('aria-label', label);
  popup.tabIndex = -1;
  popup.style.setProperty('--w', w);
  popup.style.setProperty('--h', h);

  const art = el('div', `popup-art ${className}-art`);
  popup.append(art);
  backdrop.append(popup);
  document.body.append(backdrop);

  let shown = false;
  let onRequestClose = () => {};
  const requestClose = () => onRequestClose();

  backdrop.addEventListener('click', (event) => { if (event.target === backdrop) requestClose(); });
  document.addEventListener('keydown', (event) => {
    if (shown && event.key === 'Escape') requestClose();
  });
  window.addEventListener('resize', () => { if (shown) place(); });

  // Same whole-number scale as the canvas (device pixels per art pixel),
  // shrunk if needed to fit above the prompt line, and centred there.
  function place() {
    const dpr = window.devicePixelRatio || 1;
    const canvasScale = Math.round(canvas.getBoundingClientRect().width * dpr / canvas.width);
    const availW = window.innerWidth * dpr;
    const availH = (window.innerHeight - bottomInset()) * dpr;
    const scale = Math.min(canvasScale, Math.floor(availW / w), Math.floor(availH / h));
    const cssPerArtPx = scale / dpr;
    const plain = scale < 1 || cssPerArtPx < minCssPxPerArtPx;

    popup.classList.toggle('is-plain', plain);
    backdrop.style.setProperty('--prompt-h', `${bottomInset()}px`);
    if (plain) {
      popup.style.transform = '';
      return;
    }
    const left = Math.floor((availW - w * scale) / 2);
    const top = Math.floor((availH - h * scale) / 2);
    // Transforms, not left/top, so the art lands exactly on device pixels.
    popup.style.transform = `translate(${left / dpr}px, ${top / dpr}px)`;
    popup.style.setProperty('--u', `${cssPerArtPx}px`);
    art.style.transform = `scale(${cssPerArtPx})`;
  }

  function show(onClose) {
    onRequestClose = onClose;
    shown = true;
    backdrop.hidden = false;
    place();
    requestAnimationFrame(() => backdrop.classList.add('is-visible'));
    popup.focus({ preventScroll: true });
  }

  function hide() {
    shown = false;
    backdrop.classList.remove('is-visible');
    setTimeout(() => { if (!shown) backdrop.hidden = true; }, fadeMs);
  }

  return { backdrop, popup, art, show, hide, isShown: () => shown, requestClose };
}

function el(tag, className) {
  const node = document.createElement(tag);
  node.className = className;
  return node;
}
