import { SnakeGame } from './snake.js';
import { Renderer } from './render.js';

export function start() {
  const canvas = tt.createCanvas();
  const ctx = canvas.getContext('2d');
  const game = new SnakeGame({ cols: 20, rows: 20 });
  const renderer = new Renderer(ctx, game, canvas);
  let last = 0;

  function frame(now) {
    if (game.state === 'running' && now - last >= game.speed) {
      last = now;
      game.step();
    }
    renderer.draw();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  tt.onTouchStart((e) => {
    if (game.state === 'over') {
      game.reset();
      return;
    }
    if (game.state === 'paused') {
      game.resume();
      return;
    }
    const t = e.touches[0];
    const w = canvas.width / 3;
    const h = canvas.height / 3;
    const x = t.clientX;
    const y = t.clientY;
    if (x >= w && x <= w * 2 && y >= h && y <= h * 2) {
      game.pause();
    } else if (x < w) game.turn(-1, 0);
    else if (x > w * 2) game.turn(1, 0);
    else if (y < h) game.turn(0, -1);
    else if (y > h * 2) game.turn(0, 1);
  });
}