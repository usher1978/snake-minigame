#!/usr/bin/env python3
"""保护文件检查：测试、检查配置、检查脚本、基线不得在 PR/暂存区中被改动。
退出码：0 通过；1 有保护文件被改动。
用法：
  python check_protected.py --base origin/main
  python check_protected.py --staged          # pre-commit 模式
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def glob_to_regex(g: str) -> re.Pattern:
    g = g.replace("\\", "/")
    out, i = [], 0
    while i < len(g):
        if g[i:i + 3] == "**/":
            out.append("(?:.*/)?")
            i += 3
        elif g[i:i + 2] == "**":
            out.append(".*")
            i += 2
        elif g[i] == "*":
            out.append("[^/]*")
            i += 1
        elif g[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(g[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def changed_files(repo: str, base: str, staged: bool) -> list[str]:
    cmd = ["git", "-C", repo, "diff", "--name-only"]
    cmd += ["--cached"] if staged else [f"{base}...HEAD"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("git diff 失败：" + p.stderr.strip())
        sys.exit(3)
    return [f.strip().replace("\\", "/") for f in p.stdout.splitlines() if f.strip()]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--config", default=str(Path(__file__).parent / "config.json"))
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    patterns = [glob_to_regex(g) for g in cfg["protected_globs"]]
    hits = [f for f in changed_files(args.repo, args.base, args.staged)
            if any(p.match(f) for p in patterns)]
    if hits:
        print("保护文件被改动（测试/检查配置/检查脚本/基线），拒绝：")
        for f in hits:
            print("  " + f)
        print("如确需改动：停下报告，由人工在 main 上修改，不要在本 PR 里动。")
        sys.exit(1)
    print("保护文件检查通过")


if __name__ == "__main__":
    main()