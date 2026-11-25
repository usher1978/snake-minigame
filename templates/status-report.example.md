# 状态报告示例

交付报告末尾必须附 ```status 围栏块，内容为合法 JSON，供 guard/status_gate.py 机器解析。

## 示例：完成

```status
{
  "status": "完成",
  "changed_files": ["src/app.py", "src/util.py"],
  "evidence": [
    {"command": "python -m unittest discover -s tests -v", "output": "Ran 4 tests in 0.002s\n\nOK"}
  ],
  "assumptions": ["输入由调用方保证非空"],
  "not_verified": ["并发下的性能未测"],
  "blockers": [],
  "next_step": "无"
}
```

## 示例：受阻

```status
{
  "status": "受阻",
  "changed_files": [],
  "evidence": [],
  "assumptions": [],
  "not_verified": ["全部"],
  "blockers": ["接口契约不明确：userId 是否允许为空"],
  "next_step": "等人工确认契约后继续"
}
```

## 字段规则

- status 只允许：完成 / 部分完成 / 受阻
- changed_files、evidence、assumptions、not_verified、blockers 为数组；next_step 为字符串
- 完成：changed_files 与 evidence 非空，evidence 每项含非空 command 和 output，blockers 必须为空
- 部分完成：not_verified 或 blockers 至少一项非空
- 受阻：blockers 非空
- 重试次数由编排层计数（status_gate.py --attempt），模型自报无效