#!/usr/bin/env python3
"""测试数量与 skip 数量检查：与 main 上的基线比较。
地板检查：只防“删用例/标 skip”，不防“断言弱化”（后者靠闭卷套件与变异测试）。
退出码：0 通过；1 数量违规；2 测试本身失败；3 runner 错误。
用法：
  人工在 main 上生成基线：python check_counts.py --runner unittest --write-baseline --baseline guard/baseline.json
  CI 中比较：            python check_counts.py --runner unittest --baseline guard/baseline.json
支持 runner：unittest（标准库，零依赖）、pytest、jest。
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_unittest(out: str) -> dict:
    m = re.search(r"Ran (\d+) test", out)
    total = int(m.group(1)) if m else None
    skipped = sum(int(x) for x in re.findall(r"skipped=(\d+)", out))
    xfail = sum(int(x) for x in re.findall(r"expected failures=(\d+)", out))
    failed = 0
    if not re.search(r"^OK", out, re.M):
        nums = re.findall(r"failures=(\d+)", out) + re.findall(r"errors=(\d+)", out)
        failed = sum(map(int, nums)) or 1
    return {"total": total, "inactive": skipped + xfail, "failed": failed}


def parse_pytest_collect(out: str) -> int:
    m = re.search(r"(\d+) tests? collected", out)
    return int(m.group(1)) if m else 0


def parse_pytest_run(out: str) -> dict:
    counts = {}
    for n, word in re.findall(r"(\d+) (passed|failed|skipped|xfailed|xpassed|errors?)", out):
        counts[word] = counts.get(word, 0) + int(n)
    failed = counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)
    inactive = counts.get("skipped", 0) + counts.get("xfailed", 0)
    passed = counts.get("passed", 0) + counts.get("xpassed", 0)
    return {"failed": failed, "inactive": inactive, "passed": passed}


def parse_jest_json(data: dict) -> dict:
    return {
        "total": data.get("numTotalTests"),
        "inactive": data.get("numPendingTests", 0) + data.get("numTodoTests", 0),
        "failed": data.get("numFailedTests", 0),
    }


def parse_node_test(out: str) -> dict:
    def grab(key: str) -> int:
        m = re.search(rf"# {key} (\d+)", out)
        return int(m.group(1)) if m else 0
    return {"total": grab("tests"), "inactive": grab("skipped") + grab("todo"),
            "failed": grab("fail"), "passed": grab("pass")}


def run_cmd(cmd, workdir: str, shell: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=workdir, shell=shell, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=1800)


def measure(runner: str, workdir: str, tests_dir: str) -> dict:
    if runner == "unittest":
        p = run_cmd([sys.executable, "-m", "unittest", "discover", "-s", tests_dir, "-v"], workdir)
        return parse_unittest(p.stdout + p.stderr)
    if runner == "pytest":
        c = run_cmd([sys.executable, "-m", "pytest", "--collect-only", "-q"], workdir)
        total = parse_pytest_collect(c.stdout + c.stderr)
        r = run_cmd([sys.executable, "-m", "pytest", "-q", "--tb=no"], workdir)
        stats = parse_pytest_run(r.stdout + r.stderr)
        return {"total": total, **stats}
    if runner == "node-test":
        p = run_cmd("node --test", workdir, shell=True)
        return parse_node_test(p.stdout + p.stderr)
    if runner == "jest":
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            out_file = tf.name
        run_cmd(f"npx jest --json --outputFile={out_file}", workdir, shell=True)
        try:
            data = json.loads(Path(out_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"total": None, "inactive": 0, "failed": 0}
        return parse_jest_json(data)
    raise ValueError(f"未知 runner: {runner}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True, choices=["unittest", "pytest", "jest", "node-test"])
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--tests-dir", default="tests")
    args = ap.parse_args()

    stats = measure(args.runner, args.workdir, args.tests_dir)
    if stats.get("total") is None:
        print("无法从 runner 输出解析测试数量，按 runner 错误处理")
        sys.exit(3)

    if args.write_baseline:
        Path(args.baseline).write_text(
            json.dumps({"runner": args.runner, "total": stats["total"],
                        "inactive": stats["inactive"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"基线已写入 {args.baseline}：total={stats['total']} inactive={stats['inactive']}")
        sys.exit(2 if stats.get("failed", 0) > 0 else 0)

    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    if stats.get("failed", 0) > 0:
        print(f"测试本身失败 {stats['failed']} 个，先修测试")
        sys.exit(2)
    problems = []
    if stats["total"] < base["total"]:
        problems.append(f"测试总数减少：{base['total']} → {stats['total']}")
    if stats["inactive"] > base["inactive"]:
        problems.append(f"skip/xfail/todo 增加：{base['inactive']} → {stats['inactive']}")
    if problems:
        for p in problems:
            print(p)
        print("数量检查失败。如属合理变动，由人工在 main 上更新基线，不要在本 PR 里改。")
        sys.exit(1)
    print(f"数量检查通过：total={stats['total']}（基线 {base['total']}），"
          f"inactive={stats['inactive']}（基线 {base['inactive']}）")


if __name__ == "__main__":
    main()