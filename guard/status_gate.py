#!/usr/bin/env python3
"""状态报告校验 + 编排层停止规则。
从报告中提取 ```status 围栏里的 JSON，校验格式，输出机器可执行的决策。
重试次数由编排层传入（--attempt），模型无权自报；超过上限强制受阻。
决策与退出码：auto_merge_candidate=0；human_review=10；stop=20；报告不合规=2。
注意：auto_merge_candidate 只是“允许进入自动合并流程”，仍须 required CI 全绿 + 平台审批规则。
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_KEYS = ["status", "changed_files", "evidence", "assumptions",
                 "not_verified", "blockers", "next_step"]
VALID_STATUS = {"完成", "部分完成", "受阻"}


def validate(report: dict) -> list[str]:
    errors = []
    for k in REQUIRED_KEYS:
        if k not in report:
            errors.append(f"缺少字段 {k}")
    if errors:
        return errors
    st = report["status"]
    if st not in VALID_STATUS:
        errors.append(f"status 非法：{st}")
        return errors
    for k in REQUIRED_KEYS[1:-1]:
        if not isinstance(report[k], list):
            errors.append(f"{k} 必须是数组")
    if not isinstance(report["next_step"], str):
        errors.append("next_step 必须是字符串")
    if errors:
        return errors
    if st == "完成":
        if not report["changed_files"]:
            errors.append("完成必须列出 changed_files")
        if not report["evidence"]:
            errors.append("完成必须附 evidence（命令+原始输出）")
        for i, ev in enumerate(report["evidence"]):
            if not (isinstance(ev, dict) and ev.get("command") and ev.get("output")):
                errors.append(f"evidence[{i}] 必须含非空的 command 和 output")
        if report["blockers"]:
            errors.append("完成不得有 blockers")
    if st == "部分完成" and not (report["not_verified"] or report["blockers"]):
        errors.append("部分完成必须说明 not_verified 或 blockers")
    if st == "受阻" and not report["blockers"]:
        errors.append("受阻必须写明 blockers")
    return errors


def decide(report: dict, errors: list[str], attempt: int, max_attempts: int, ci: str) -> dict:
    if attempt > max_attempts:
        return {"decision": "stop", "reason": f"重试 {attempt} 次超过上限 {max_attempts}，强制受阻，转人工"}
    if errors:
        return {"decision": "human_review", "reason": "状态块不合规", "errors": errors}
    st = report["status"]
    if st == "受阻":
        return {"decision": "stop", "reason": "模型报告受阻，转人工", "blockers": report["blockers"]}
    if st == "部分完成":
        return {"decision": "human_review", "reason": "部分完成一律人工审查，不得自动合并"}
    if ci != "green":
        return {"decision": "human_review", "reason": f"声称完成但 CI 状态为 {ci}，不得自动合并"}
    return {"decision": "auto_merge_candidate", "reason": "完成且 CI 绿，进入自动合并流程（仍受平台审批规则约束）"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--max-attempts", type=int, default=2)
    ap.add_argument("--ci", choices=["green", "red", "unknown"], default="unknown")
    args = ap.parse_args()

    text = Path(args.report).read_text(encoding="utf-8")
    m = re.search(r"```status\s*\n(.*?)```", text, re.S)
    if not m:
        print(json.dumps({"decision": "human_review", "reason": "报告中没有 ```status 状态块"}, ensure_ascii=False))
        sys.exit(2)
    try:
        report = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(json.dumps({"decision": "human_review", "reason": f"状态块不是合法 JSON：{e}"}, ensure_ascii=False))
        sys.exit(2)

    errors = validate(report)
    result = decide(report, errors, args.attempt, args.max_attempts, args.ci)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit({"auto_merge_candidate": 0, "human_review": 10, "stop": 20}[result["decision"]])


if __name__ == "__main__":
    main()