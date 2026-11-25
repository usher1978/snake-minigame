#!/usr/bin/env python3
"""作弊关键字扫描：只扫本次 diff 新增的行。
block 命中 → 退出 1；warn 命中 → 仅提示（--strict 时也算失败）。
这是烟雾信号，不是证明：误报由人工在 main 上调整 config.json 处理。
用法：
  python scan_diff.py --base origin/main
  python scan_diff.py --staged
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from check_protected import glob_to_regex


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--config", default=str(Path(__file__).parent / "config.json"))
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    block = [(p, re.compile(p, re.IGNORECASE)) for p in cfg["scan_block_patterns"]]
    warn = [(p, re.compile(p, re.IGNORECASE)) for p in cfg["scan_warn_patterns"]]
    exclude = [glob_to_regex(g) for g in cfg.get("scan_exclude_globs", [])]

    cmd = ["git", "-C", args.repo, "diff", "--unified=0"]
    cmd += ["--cached"] if args.staged else [f"{args.base}...HEAD"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("git diff 失败：" + p.stderr.strip())
        sys.exit(3)

    violations, warnings = [], []
    cur, lineno = None, 0
    for line in p.stdout.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:].replace("\\", "/")
            continue
        if line.startswith("+++"):
            cur = None
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
            continue
        if line.startswith("+"):
            content = line[1:]
            if cur and not any(e.match(cur) for e in exclude):
                for name, pat in block:
                    if pat.search(content):
                        violations.append(f"{cur}:{lineno}: [block] {content.strip()}  ({name})")
                for name, pat in warn:
                    if pat.search(content):
                        warnings.append(f"{cur}:{lineno}: [warn] {content.strip()}  ({name})")
            lineno += 1

    for v in violations:
        print(v)
    for w in warnings:
        print(w)
    if violations or (args.strict and warnings):
        print(f"扫描失败：block {len(violations)} 处，warn {len(warnings)} 处")
        sys.exit(1)
    print(f"扫描通过（warn {len(warnings)} 处，需人工过目）")


if __name__ == "__main__":
    main()