/**
 * 贪吃蛇纯逻辑层（不依赖渲染 / 平台 API，Node 可直接测试）
 */
export class SnakeGame {
  constructor({ cols = 20, rows = 20, wrap = false } = {}) {
    this.cols = cols;
    this.rows = rows;
    this.wrap = wrap;
    this.reset();
  }

  reset() {
    const cx = Math.floor(this.cols / 2);
    const cy = Math.floor(this.rows / 2);
    this.snake = [
      { x: cx, y: cy },
      { x: cx - 1, y: cy },
      { x: cx - 2, y: cy }
    ];
    this.dir = { x: 1, y: 0 };
    this.score = 0;
    this.state = 'running';
    this.lastEvent = null;
    this.food = this._spawnFood();
  }

  _occupied(x, y) {
    return this.snake.some((s) => s.x === x && s.y === y);
  }

  _spawnFood() {
    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        if (!this._occupied(x, y)) return { x, y };
      }
    }
    return null;
  }

  setFood(x, y) {
    if (x < 0 || y < 0 || x >= this.cols || y >= this.rows) return false;
    if (this._occupied(x, y)) return false;
    this.food = { x, y };
    return true;
  }

  /** 转向：只接受轴向单位向量；反向掉头忽略 */
  turn(dx, dy) {
    if (Math.abs(dx) + Math.abs(dy) !== 1) return;
    if (dx === -this.dir.x && dy === -this.dir.y) return;
    this.dir = { x: dx, y: dy };
  }

  step() {
    if (this.state !== 'running') return this.lastEvent;
    let hx = this.snake[0].x + this.dir.x;
    let hy = this.snake[0].y + this.dir.y;

    if (this.wrap) {
      hx = (hx + this.cols) % this.cols;
      hy = (hy + this.rows) % this.rows;
    } else if (hx < 0 || hy < 0 || hx >= this.cols || hy >= this.rows) {
      return this._die();
    }

    // 尾巴会在这一步移开，所以不把自己最后一节算作障碍
    const body = this.snake.slice(0, -1);
    if (body.some((s) => s.x === hx && s.y === hy)) return this._die();

    const eat = this.food && this.food.x === hx && this.food.y === hy;
    this.snake.unshift({ x: hx, y: hy });
    if (eat) {
      this.score += 10;
      this.food = this._spawnFood();
      this.lastEvent = 'eat';
    } else {
      this.snake.pop();
      this.lastEvent = 'move';
    }
    return this.lastEvent;
  }

  _die() {
    this.state = 'over';
    this.lastEvent = 'die';
    return 'die';
  }

  /** 暂停：仅运行中可暂停；暂停期间 step 不动 */
  pause() {
    if (this.state === 'running') this.state = 'paused';
  }

  /** 继续：仅暂停中可继续 */
  resume() {
    if (this.state === 'paused') this.state = 'running';
  }

  /** 每 10 分提速 20ms，下限 70ms */
  get speed() {
    return Math.max(70, 200 - 20 * Math.floor(this.score / 10));
  }
}