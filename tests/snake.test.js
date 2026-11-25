import test from 'node:test';
import assert from 'node:assert/strict';
import { SnakeGame } from '../js/snake.js';

function fresh(opts) {
  return new SnakeGame({ cols: 20, rows: 20, ...opts });
}

test('初始状态：长度 3，头在中心，朝右，0 分', () => {
  const g = fresh();
  assert.equal(g.snake.length, 3);
  assert.deepEqual(g.snake[0], { x: 10, y: 10 });
  assert.deepEqual(g.snake[2], { x: 8, y: 10 });
  assert.deepEqual(g.dir, { x: 1, y: 0 });
  assert.equal(g.score, 0);
  assert.equal(g.state, 'running');
});

test('直线前进：头前移一格，长度不变', () => {
  const g = fresh();
  g.setFood(0, 0);
  g.step();
  assert.deepEqual(g.snake[0], { x: 11, y: 10 });
  assert.equal(g.snake.length, 3);
  assert.equal(g.lastEvent, 'move');
});

test('吃食物：长度 +1，得分 +10', () => {
  const g = fresh();
  assert.equal(g.setFood(11, 10), true);
  g.step();
  assert.equal(g.snake.length, 4);
  assert.equal(g.score, 10);
  assert.equal(g.lastEvent, 'eat');
});

test('撞墙：游戏结束', () => {
  const g = fresh();
  g.setFood(2, 18);
  for (let i = 0; i < 15 && g.state === 'running'; i++) g.step();
  assert.equal(g.state, 'over');
  assert.equal(g.lastEvent, 'die');
});

test('撞自己：游戏结束', () => {
  const g = fresh();
  g.setFood(11, 10);
  g.step(); // 吃，长度 4
  g.setFood(12, 10);
  g.step(); // 吃，长度 5
  g.turn(0, 1);
  g.step();
  g.turn(-1, 0);
  g.step();
  g.turn(0, -1);
  g.step(); // 头咬到身体
  assert.equal(g.state, 'over');
  assert.equal(g.lastEvent, 'die');
});

test('反向掉头被拒绝', () => {
  const g = fresh();
  g.turn(-1, 0);
  assert.deepEqual(g.dir, { x: 1, y: 0 });
});

test('垂直转向有效', () => {
  const g = fresh();
  g.turn(0, 1);
  assert.deepEqual(g.dir, { x: 0, y: 1 });
  g.step();
  assert.deepEqual(g.snake[0], { x: 10, y: 11 });
});

test('重开恢复初始状态', () => {
  const g = fresh();
  g.setFood(11, 10);
  g.step();
  g.reset();
  assert.equal(g.score, 0);
  assert.equal(g.state, 'running');
  assert.equal(g.snake.length, 3);
  assert.deepEqual(g.snake[0], { x: 10, y: 10 });
});

test('食物不能落在蛇身上', () => {
  const g = fresh();
  assert.equal(g.setFood(10, 10), false);
  assert.deepEqual(g.food, { x: 0, y: 0 });
});

test('速度随得分加快：0 分 200ms，20 分 160ms，下限 70ms', () => {
  const g = fresh();
  assert.equal(g.speed, 200);
  g.setFood(11, 10);
  g.step();
  g.setFood(12, 10);
  g.step();
  assert.equal(g.score, 20);
  assert.equal(g.speed, 160);
  g.score = 60;
  assert.equal(g.speed, 80);
  g.score = 1000;
  assert.equal(g.speed, 70);
});

test('穿墙模式：从右边界穿到左边界，不结束', () => {
  const g = fresh({ wrap: true });
  g.setFood(2, 18);
  for (let i = 0; i < 10; i++) g.step();
  assert.equal(g.state, 'running');
  assert.equal(g.snake[0].x, 0);
});
test('暂停：state 变为 paused，step 不动', () => {
  const g = fresh();
  g.pause();
  assert.equal(g.state, 'paused');
  const before = { ...g.snake[0] };
  g.step();
  assert.deepEqual(g.snake[0], before);
});

test('继续：resume 后恢复前进', () => {
  const g = fresh();
  g.setFood(0, 0);
  g.pause();
  g.step();
  g.resume();
  assert.equal(g.state, 'running');
  g.step();
  assert.deepEqual(g.snake[0], { x: 11, y: 10 });
});
