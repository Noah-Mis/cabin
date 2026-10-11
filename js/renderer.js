// renderer.js — draws the layer stack, back to front, onto the scene canvas.
// During a time-of-day change it draws the whole stack twice, once per time,
// and blends the second over the first. This works because every time-of-day
// version of an asset has the same shape.
// Exports: createRenderer(canvas, layers) -> { render(view) }
//   view = { from, to, mix } from timeofday.js

export function createRenderer(canvas, layers) {
  const ctx = canvas.getContext('2d');
  const fadeBuffer = document.createElement('canvas');
  fadeBuffer.width = canvas.width;
  fadeBuffer.height = canvas.height;
  const fadeCtx = fadeBuffer.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  fadeCtx.imageSmoothingEnabled = false;

  function drawStack(target, time) {
    target.clearRect(0, 0, canvas.width, canvas.height);
    for (const layer of layers) {
      target.save();
      layer.draw(target, time);
      target.restore();
    }
  }

  function render({ from, to, mix }) {
    drawStack(ctx, from);
    if (to === from || mix <= 0) return;
    drawStack(fadeCtx, to);
    ctx.globalAlpha = mix;
    ctx.drawImage(fadeBuffer, 0, 0);
    ctx.globalAlpha = 1;
  }

  return { render };
}
