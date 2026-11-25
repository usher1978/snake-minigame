# 贪吃蛇 · 抖音小游戏

原生 JavaScript + Canvas 2D 的 20×20 贪吃蛇，竖屏，触摸九宫格控制方向；撞墙/撞自己结束，点击重开。

## 结构

```
snake-minigame/
├── game.js                # 入口
├── game.json              # 小游戏配置（竖屏）
├── project.config.json    # 工程配置（compileType: game，appid 待填）
├── js/
│   ├── snake.js           # 纯逻辑层（Node 可测）
│   ├── main.js            # 主控：循环、触摸
│   └── render.js          # Canvas 渲染
├── tests/snake.test.js    # 测试合同（node --test）
├── guard/                 # 防线脚本
└── rules/AGENTS.md        # 编码规则
```

## 运行

- 测试：`node --test`（或 `npm test`）
- 抖音开发者工具：导入项目，类型选小游戏；appid 填自己的。

## 防线段（guard）

- 派活：按 `rules/AGENTS.md`；任务合同见 `templates/task-contract.md`
- 验收：`python guard/check_protected.py --base <基线分支>`、`python guard/scan_diff.py --base <基线分支>`、`python guard/check_counts.py --runner node-test --baseline guard/baseline.json`
- 状态门：`python guard/status_gate.py --report report.md --ci green`
- 测试与基线受保护：只由人工在基线分支上改。
