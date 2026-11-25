export class Renderer {
  constructor(ctx, game, canvas) {
    this.ctx = ctx;
    this.game = game;
    this.canvas = canvas;
  }

  draw() {
    const { ctx, canvas, game } = this;
    const w = canvas.width;
    const h = canvas.height;
    const cell = Math.min(w / game.cols, h / game.rows);
    const ox = (w - cell * game.cols) / 2;
    const oy = (h - cell * game.rows) / 2;

    ctx.fillStyle = '#101820';
    ctx.fillRect(0, 0, w, h);

    // 棋盘格子
    for (let y = 0; y < game.rows; y++) {
      for (let x = 0; x < game.cols; x++) {
        if ((x + y) % 2 === 0) {
          ctx.fillStyle = '#16232e';
          ctx.fillRect(ox + x * cell, oy + y * cell, cell, cell);
        }
      }
    }

    // 食物
    if (game.food) {
      ctx.fillStyle = '#ff5c5c';
      ctx.beginPath();
      ctx.arc(ox + (game.food.x + 0.5) * cell, oy + (game.food.y + 0.5) * cell,
              cell * 0.36, 0, Math.PI * 2);
      ctx.fill();
    }

    // 蛇：头亮尾暗
    game.snake.forEach((s, i) => {
      ctx.fillStyle = i === 0 ? '#7cf0a8' : '#3ecf7a';
      const pad = i === 0 ? cell * 0.14 : cell * 0.2;
      ctx.fillRect(ox + s.x * cell + pad, oy + s.y * cell + pad,
                   cell - pad * 2, cell - pad * 2);
    });

    // 分数
    ctx.fillStyle = '#e8f1f8';
    ctx.font = `${Math.round(cell * 1.2)}px sans-serif`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(`得分 ${game.score}`, ox + 6, oy - cell * 1.6);

    if (game.state === 'over') {
      ctx.fillStyle = 'rgba(0,0,0,0.62)';
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#fff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = `${Math.round(cell * 2)}px sans-serif`;
      ctx.fillText('撞到了！', w / 2, h / 2 - cell * 1.4);
      ctx.font = `${Math.round(cell * 1.1)}px sans-serif`;
      ctx.fillText(`得分 ${game.score} · 点击重新开始`, w / 2, h / 2 + cell);
    }
  }
}