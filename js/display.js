// display.js — scales the native-resolution canvas up to fill the stage.
// The scale is always a whole number of *device* pixels per art pixel, which
// is what keeps it crisp on high-density screens. It picks the smallest such
// scale that covers the whole stage, letting the log wall at the edges
// overflow, but never so large that the important part of the picture (the
// window and sill) is cut off or hidden behind the bottom overlay.
// Exports: fitCanvasToStage(canvas, stage, { keepVisible, bottomInset })
//            keepVisible: {x, y, w, h} in art pixels
//            bottomInset(): CSS px covered at the bottom (the prompt line)
//          -> { scale() }

export function fitCanvasToStage(canvas, stage, { keepVisible: keep, bottomInset }) {
  let currentScale = 1;

  function fit() {
    const dpr = window.devicePixelRatio || 1;
    const stageW = stage.getBoundingClientRect().width * dpr;
    const stageH = stage.getBoundingClientRect().height * dpr;
    const usableH = stageH - bottomInset() * dpr;

    const coverScale = Math.ceil(Math.max(stageW / canvas.width, stageH / canvas.height));
    const largestShowingKeep = Math.floor(Math.min(stageW / keep.w, usableH / keep.h));
    currentScale = Math.max(1, Math.min(coverScale, largestShowingKeep));

    // Centre the picture, then slide it just enough to bring the important
    // part fully on screen. Whole device pixels, or it would be resampled.
    const s = currentScale;
    const left = clamp(Math.floor((stageW - canvas.width * s) / 2),
      -keep.x * s, stageW - (keep.x + keep.w) * s);
    const top = clamp(Math.floor((stageH - canvas.height * s) / 2),
      -keep.y * s, usableH - (keep.y + keep.h) * s);

    // A transform rather than width/left: layout rounds sizes to 1/64 of a
    // CSS pixel, which at ratios like 1.25 or 1.5 lands between device
    // pixels. Transforms keep full precision.
    Object.assign(canvas.style, {
      width: `${canvas.width}px`,
      height: `${canvas.height}px`,
      transformOrigin: '0 0',
      transform: `translate(${Math.floor(left) / dpr}px, ${Math.floor(top) / dpr}px) scale(${s / dpr})`,
    });
  }

  new ResizeObserver(fit).observe(stage);
  window.addEventListener('resize', fit);   // also fires when zoom changes devicePixelRatio
  fit();
  return { scale: () => currentScale };
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
