#!/usr/bin/env python3
"""
研究更新驱动器 - 驱动 CC CLI 进行 StockMoney 模块迭代

闭环流程：
  1. 收集当前系统状态（周期定位、市场判断、政策判断）
  2. 对比外部输入的新信息，生成具体修改清单
  3. 调用 CC CLI 执行代码修改
  4. 运行验证脚本
  5. git commit/push
  6. 输出更新报告

用法：
  python scripts/research_driver.py --auto           # 自动模式（定时任务用）
  python scripts/research_driver.py --manual         # 手动模式（交互式）
  python scripts/research_driver.py --prompt "更新美联储利率判断为3.25-3.50%"

作者：Claude Code
日期：2026-05-01
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR / "scripts"))

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def run_shell(cmd: str, cwd: str = None, timeout: int = 300) -> tuple[int, str, str]:
    """执行 shell 命令，返回 (exit_code, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or str(BASE_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


def get_current_state() -> dict:
    """收集当前系统各模块的关键判断状态"""
    state = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "modules": {},
    }

    # 1. 策略引擎决策摘要
    try:
        from strategy_engine import StrategyEngine
        engine = StrategyEngine()
        decision = engine.evaluate_all()
        state["modules"]["strategy"] = {
            "cycle_position": decision.cycle_position,
            "resonance": decision.resonance_strength,
            "market_signal": decision.market_signal,
            "overall_position": f"{decision.overall_position:.0%}",
            "position_range": f"{decision.position_range[0]:.0%}-{decision.position_range[1]:.0%}",
            "four_percent_enabled": decision.four_percent_enabled,
            "policy_score": decision.policy_score,
            "policy_trend": decision.policy_trend,
        }
    except Exception as e:
        state["modules"]["strategy"] = {"error": str(e)}

    # 2. 政策分析摘要
    try:
        from policy_analyzer import PolicyAnalyzer
        analyzer = PolicyAnalyzer()
        analysis = analyzer.run_full_analysis()
        state["modules"]["policy"] = {
            "overall_score": analysis.overall_policy_score,
            "trend": analysis.overall_trend,
            "next_review": analysis.next_review_date,
        }
    except Exception as e:
        state["modules"]["policy"] = {"error": str(e)}

    # 3. 康波周期定位
    try:
        from kondratiev_model import KondratievModel
        model = KondratievModel()
        phase_name = model.get_current_phase()
        pos = model.get_cycle_position()
        state["modules"]["kondratiev"] = {
            "wave": pos.kondratiev_round,
            "phase": pos.kondratiev_phase,
            "year": pos.current_year,
            "progress": f"{pos.kondratiev_progress:.0%}",
        }
    except Exception as e:
        state["modules"]["kondratiev"] = {"error": str(e)}

    return state


def build_iteration_prompt(state: dict, user_input: str = "") -> str:
    """构建给 CC CLI 的迭代 prompt"""

    prompt_parts = [
        "# StockMoney 研究更新任务",
        "",
        f"当前日期：{state['date']}",
        "",
        "## 当前系统状态",
        json.dumps(state["modules"], ensure_ascii=False, indent=2),
        "",
        "## 你的工作",
        "你是 StockMoney 投资研究系统的维护者。请根据最新信息更新以下模块中的判断和数据：",
        "",
        "### 允许修改的文件范围",
        "1. `scripts/kondratiev_model.py` - 康波周期定位数据（当前阶段、技术驱动、年份判断）",
        "2. `scripts/cycle_phase_evaluator.py` - 周期共振判断（朱格拉/基钦周期阶段）",
        "3. `scripts/market_indicators.py` - 市场指标数据（PE/PB、股债利差、情绪指标）",
        "4. `scripts/policy_analyzer.py` - 政策分析（美联储、中国央行、十五五、大宗商品）",
        "5. `scripts/asset_allocator.py` - 资产配置矩阵",
        "",
        "### 修改原则",
        "- 只更新事实性数据和判断，不改动架构和算法",
        "- 保留原有代码结构，只修改具体数值和字符串",
        "- 如果某项判断没有新变化，不要修改",
        "- 确保修改后的代码可以正常执行",
        "",
    ]

    if user_input:
        prompt_parts.extend([
            "## 用户提供的最新信息",
            user_input,
            "",
        ])
    else:
        prompt_parts.extend([
            "## 自动更新指令",
            "请检查各模块中的日期标记（如 '2026-05-01'），如果判断已经过时（超过2周未更新），",
            "请根据你对当前宏观经济、政策环境、市场状况的理解进行合理更新。",
            "",
            "重点检查：",
            "1. 美联储利率判断是否合理",
            "2. 中国货币政策描述是否最新",
            "3. 大宗商品价格预测是否需要调整",
            "4. 十五五规划相关产业是否有新的政策动向",
            "5. 市场估值指标（PE/PB分位数）是否需要更新",
            "",
        ])

    prompt_parts.extend([
        "## 输出要求",
        "1. 列出你修改了哪些文件、哪些具体数值",
        "2. 说明每项修改的理由",
        "3. 最后运行 `python scripts/strategy_engine.py --decision` 验证系统能正常输出",
    ])

    return "\n".join(prompt_parts)


def call_cc_cli(prompt: str) -> tuple[int, str]:
    """调用 CC CLI 执行迭代任务"""
    cmd = (
        f'claude --print --permission-mode bypassPermissions '
        f'--output-format text '
        f'"{prompt.replace(chr(34), chr(92)+chr(34))}"'
    )
    print(f"[ResearchDriver] 调用 CC CLI...")
    print(f"[ResearchDriver] 工作目录: {BASE_DIR}")

    code, out, err = run_shell(cmd, cwd=str(BASE_DIR), timeout=600)

    # 合并输出
    full_output = out
    if err:
        full_output += "\n\n[STDERR]\n" + err

    return code, full_output


def validate_changes() -> dict:
    """验证修改后的系统是否正常运行"""
    results = {}

    # 1. 策略引擎
    code, out, err = run_shell(
        "python scripts/strategy_engine.py --decision",
        cwd=str(BASE_DIR),
        timeout=60,
    )
    results["strategy_engine"] = {
        "ok": code == 0,
        "output": out[:500] if code == 0 else err[:500],
    }

    # 2. 政策分析
    code, out, err = run_shell(
        "python scripts/policy_analyzer.py --summary",
        cwd=str(BASE_DIR),
        timeout=60,
    )
    results["policy_analyzer"] = {
        "ok": code == 0,
        "output": out[:500] if code == 0 else err[:500],
    }

    # 3. git diff 查看修改内容
    code, out, err = run_shell("git diff --stat", cwd=str(BASE_DIR))
    results["git_diff"] = {
        "ok": code == 0,
        "output": out,
    }

    return results


def git_commit_and_push(message: str) -> tuple[bool, str]:
    """git 提交并推送到 GitHub"""
    steps = [
        ("git add -A", "暂存修改"),
        (f'git commit -m "{message}"', "提交"),
        ("git push origin main", "推送"),
    ]

    logs = []
    for cmd, desc in steps:
        code, out, err = run_shell(cmd, cwd=str(BASE_DIR))
        if code != 0:
            logs.append(f"[FAIL] {desc}: {err or out}")
            return False, "\n".join(logs)
        logs.append(f"[OK] {desc}")

    return True, "\n".join(logs)


def generate_report(state: dict, cc_output: str, validation: dict, git_result: str) -> str:
    """生成更新报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# StockMoney 研究更新报告",
        f"",
        f"**更新时间**: {now}",
        f"",
        f"## 更新前状态",
        f"",
        "```json",
        json.dumps(state["modules"], ensure_ascii=False, indent=2),
        "```",
        f"",
        f"## CC CLI 迭代输出",
        f"",
        "```",
        cc_output[:3000],
        "```",
        f"",
        f"## 验证结果",
        f"",
    ]

    for name, result in validation.items():
        status = "✅ 通过" if result["ok"] else "❌ 失败"
        lines.append(f"- **{name}**: {status}")
        if not result["ok"]:
            lines.append(f"  ```")
            lines.append(f"  {result['output'][:200]}")
            lines.append(f"  ```")

    lines.extend([
        f"",
        f"## Git 同步",
        f"",
        "```",
        git_result,
        "```",
        f"",
        f"---",
        f"*本报告由 StockMoney Research Driver 自动生成*",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="StockMoney 研究更新驱动器")
    parser.add_argument("--auto", action="store_true", help="自动模式（定时任务用）")
    parser.add_argument("--manual", action="store_true", help="手动模式")
    parser.add_argument("--prompt", type=str, default="", help="直接提供更新指令")
    parser.add_argument("--dry-run", action="store_true", help="仅生成 prompt，不调用 CC CLI")
    args = parser.parse_args()

    print("=" * 60)
    print("StockMoney Research Driver")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 收集当前状态
    print("\n[1/5] 收集当前系统状态...")
    state = get_current_state()
    print(json.dumps(state, ensure_ascii=False, indent=2))

    # 2. 构建 prompt
    print("\n[2/5] 构建迭代 prompt...")
    user_input = args.prompt
    if args.manual and not user_input:
        user_input = input("请输入最新研究信息（或直接回车进入自动模式）:\n")

    prompt = build_iteration_prompt(state, user_input)

    if args.dry_run:
        print("\n[Dry Run] Prompt 内容:\n")
        print(prompt)
        return

    # 3. 调用 CC CLI
    print("\n[3/5] 调用 CC CLI 执行迭代...")
    cc_code, cc_output = call_cc_cli(prompt)
    print(f"CC CLI 退出码: {cc_code}")
    print(f"CC CLI 输出（前1000字）:\n{cc_output[:1000]}")

    # 4. 验证修改
    print("\n[4/5] 验证修改...")
    validation = validate_changes()
    all_ok = all(r["ok"] for r in validation.values())

    if not all_ok:
        print("[WARNING] 验证未完全通过，跳过 Git 提交")
        git_ok = False
        git_result = "验证失败，未提交"
    else:
        # 5. Git 提交
        print("\n[5/5] Git 提交并推送...")
        commit_msg = f"Research update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if user_input:
            commit_msg += f" | {user_input[:50]}"
        git_ok, git_result = git_commit_and_push(commit_msg)

    # 6. 生成报告
    report = generate_report(state, cc_output, validation, git_result)
    report_path = REPORTS_DIR / f"research_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n报告已保存: {report_path}")

    # 7. 输出摘要
    print("\n" + "=" * 60)
    print("更新摘要")
    print("=" * 60)
    print(f"CC CLI 执行: {'成功' if cc_code == 0 else '失败'}")
    print(f"验证通过: {'是' if all_ok else '否'}")
    print(f"Git 同步: {'成功' if git_ok else '失败/跳过'}")
    print(f"报告: {report_path}")


if __name__ == "__main__":
    main()
