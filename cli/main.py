#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cli/main.py — smartpickcore 命令行入口

命令：
    validate   校验契约（schema / 红线 / 外键 / 双向取代 / 文件存在性 / 版本一致性）
    index      从 FACTS.jsonl 重生成 memory/facts/INDEX.md
    versions   ★ 版本一致性检查（文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md）
    strategy   重新生成 games/<game>/strategy/strategy.json
    games      列出彩种
    facts      列结论（可筛选）
    questions  列开放问题
    todo       从 caveats 生成待办建议
    caveats    列某条结论的减损项
    info       仓库概览
    new-game   从 _template 创建新彩种骨架
    pick       生成合规号码（按单注层规则过滤）
    eval       求一注号码的特征并按规则判定

用法示例：
    python cli/main.py validate --all
    python cli/main.py validate --facts
    python cli/main.py index
    python cli/main.py versions
    python cli/main.py facts --status established --game dlt
    python cli/main.py caves F-0004
    python cli/main.py strategy --game dlt --dry-run

设计约定：**未实现的命令必须明确报"未实现"，不得静默成功。**
"""
from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from smartpickcore import __version__  # noqa: E402
from smartpickcore.api import SmartPick  # noqa: E402
from smartpickcore.memory import Memory  # noqa: E402
from smartpickcore.validate import (  # noqa: E402
    validate_all,
    validate_facts,
    validate_game,
    validate_iterations,
    validate_strategy,
)

# framework/core 是彩种无关的计算核心，不在 src/ 包内
sys.path.insert(0, os.path.join(_ROOT, "framework"))
from core import Ticket  # noqa: E402

STARS = lambda c: "★" * c + "☆" * (5 - c)


def _smartpick(game: str) -> SmartPick:
    """统一的 SmartPick 构造 + 友好错误。"""
    try:
        return SmartPick.for_game(game, _ROOT)
    except ValueError as e:
        print(f"✗ {e}")
        raise SystemExit(1)


# ---------------------------------------------------------------- validate

def cmd_validate(args) -> int:
    if args.facts:
        rep = validate_facts(_ROOT)
    elif args.game:
        rep = validate_game(args.game, _ROOT)
        validate_strategy(args.game, _ROOT, rep)
        validate_iterations(args.game, _ROOT, rep)
    else:
        rep = validate_all(_ROOT, verbose=args.verbose)

    print(rep.render(verbose=args.verbose))
    return 0 if rep.passed else 1


# ---------------------------------------------------------------- index

def cmd_index(args) -> int:
    mem = Memory(_ROOT)
    errs = mem.validate_facts()
    if errs:
        print(f"✗ 结论台账有 {len(errs)} 项问题，拒绝生成 INDEX：")
        for e in errs:
            print("  ✗", e)
        return 1
    path = mem.write_index()
    rel = os.path.relpath(path, _ROOT)
    n = len(mem.load_facts())
    print(f"✓ 已从 FACTS.jsonl（{n} 条）重新生成 {rel}")
    return 0


def cmd_versions(args) -> int:
    """版本一致性检查。"""
    from smartpickcore.versions import (
        VersionsError,
        render_versions_summary,
        verify_versions,
    )

    try:
        r = verify_versions(_ROOT)
    except VersionsError as e:
        print(f"✗ {e}")
        return 1

    if args.summary:
        print(render_versions_summary(_ROOT))
        return 0

    s = r["stats"]
    if args.verbose or args.summary:
        print(render_versions_summary(_ROOT))
        print()

    print(f"登记条目 {s.get('total')} 个  "
          f"(A={s['by_level'].get('A', 0)} B={s['by_level'].get('B', 0)} "
          f"C={s['by_level'].get('C', 0)} D={s['by_level'].get('D', 0)})")
    print(f"文件内版本行 {s.get('file_version_lines_ok')}/{s.get('file_version_lines_needed')} 一致")
    print(f"C 级版本字段 {s.get('c_level_checked_ok')} 一致"
          + (f"，{s['c_level_mismatch']} 不一致" if s.get("c_level_mismatch") else ""))
    print()

    if r["warnings"]:
        print(f"⚠ {len(r['warnings'])} 项警告：")
        for w in r["warnings"]:
            print(f"  ! {w}")
        print()

    if r["errors"]:
        print(f"✗ {len(r['errors'])} 项错误：")
        for e in r["errors"]:
            print(f"  ✗ {e}")
        return 1

    print("✓ 版本一致性检查通过")
    return 0


# ---------------------------------------------------------------- strategy

def cmd_strategy(args) -> int:
    from smartpickcore.strategy import StrategyError, build_strategy

    try:
        st = build_strategy(args.game, _ROOT, iteration=args.iteration,
                            generator=f"smartpickcore-cli/{__version__}")
    except StrategyError as e:
        print(f"✗ {e}")
        return 1

    import json
    text = json.dumps(st, ensure_ascii=False, indent=2) + "\n"

    if args.dry_run:
        print(f"--- dry-run：将写入 games/{args.game}/strategy/strategy.json ---")
        print(text[:3000])
        if len(text) > 3000:
            print(f"...（共 {len(text)} 字符，已截断）")
        return 0

    p = os.path.join(_ROOT, "games", args.game, "strategy", "strategy.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"✓ 已写入 {os.path.relpath(p, _ROOT)}")

    # 立即校验
    rep = validate_strategy(args.game, _ROOT)
    if not rep.passed:
        print(rep.render())
        return 1
    print("✓ 策略校验通过")
    return 0


# ---------------------------------------------------------------- games

def cmd_games(args) -> int:
    games = SmartPick.games(_ROOT)
    if not games:
        print("（games/ 下未发现彩种）")
        return 0
    print(f"{'id':10s}  {'T（单注组合数）':>15s}  {'一等奖概率':>12s}  "
          f"{'返奖率':>6s}  {'结论':>4s}  {'规则':>4s}")
    print("-" * 70)
    for g in games:
        try:
            print(SmartPick.for_game(g, _ROOT).summary())
        except Exception as e:
            print(f"{g:10s}  ✗ 装载失败: {e}")
    return 0


# ---------------------------------------------------------------- facts

def cmd_facts(args) -> int:
    mem = Memory(_ROOT)
    facts = mem.load_facts()

    if args.game:
        facts = [f for f in facts if f["game"] == args.game]
    if args.status:
        facts = [f for f in facts if f["status"] == args.status]
    if args.category:
        facts = [f for f in facts if f["category"] == args.category]
    if args.min_confidence:
        facts = [f for f in facts if f["confidence"] >= args.min_confidence]

    if not facts:
        print("（无匹配结论）")
        return 0

    for f in sorted(facts, key=lambda x: x["id"]):
        print(f"{f['id']}  {f['game']:7s} {STARS(f['confidence'])}  "
              f"[{f['status']}]  {f['claim']}")
    print(f"\n共 {len(facts)} 条。权威源：memory/facts/FACTS.jsonl")
    return 0


def cmd_caveats(args) -> int:
    mem = Memory(_ROOT)
    f = mem.fact(args.fact_id)
    if f is None:
        print(f"✗ 结论 {args.fact_id} 不存在")
        return 1
    print(f"{f['id']}  {STARS(f['confidence'])}  [{f['status']}]")
    print(f"  {f['claim']}")
    print(f"\n  类别: {f['category']}   轮次: {f['established_in']}")
    print(f"  红线: affects_win_probability = {f['affects_win_probability']}")
    print(f"  来源: {f['source']}")
    if f.get("confidence_basis"):
        print(f"  置信依据: {f['confidence_basis']}")
    ev = f.get("evidence") or {}
    print(f"\n  方法: {ev.get('method')}")
    print(f"  结果: {ev.get('result_summary')}")
    if ev.get("ci95"):
        print(f"  95%CI: {ev['ci95']}")
    if ev.get("rules_epoch"):
        print(f"  规则 epoch: {ev['rules_epoch']}")
    if ev.get("script"):
        print(f"  脚本: {ev['script']}")
    print(f"\n  ★ 减损项（{len(f.get('caveats') or [])} 条）—— 引用前必读：")
    for i, c in enumerate(f.get("caveats") or [], 1):
        print(f"    {i}. {c}")
    if f.get("supersedes"):
        print(f"\n  ← 取代了 {f['supersedes']}")
    if f.get("superseded_by"):
        print(f"\n  → 已被 {f['superseded_by']} 取代（禁止引用）")
    return 0


# ---------------------------------------------------------------- questions

def cmd_questions(args) -> int:
    mem = Memory(_ROOT)
    qs = mem.open_questions()
    if not qs:
        print("（未解析到开放问题；检查 memory/workbench/OPEN_QUESTIONS.md 格式）")
        return 0
    open_only = [q for q in qs if q[1] == "open"]
    for qid, status, title in qs:
        mark = "○" if status == "open" else "●"
        print(f"{mark} {qid}  [{status}]  {title}")
    print(f"\n共 {len(qs)} 个，其中 open {len(open_only)} 个。")
    print("文件：memory/workbench/OPEN_QUESTIONS.md")
    return 0


def cmd_todo(args) -> int:
    mem = Memory(_ROOT)
    print(mem.render_todo_from_caveats())
    return 0


# ---------------------------------------------------------------- info

def cmd_info(args) -> int:
    print(f"smartpickcore {__version__}")
    print(f"仓库根: {_ROOT}")
    print()

    mem = Memory(_ROOT)
    facts = mem.load_facts()
    print(f"结论台账: {len(facts)} 条")
    by_status: dict[str, int] = {}
    for f in facts:
        by_status[f["status"]] = by_status.get(f["status"], 0) + 1
    if by_status:
        print("  " + "  ".join(f"{k}={v}" for k, v in sorted(by_status.items())))

    qs = mem.open_questions()
    print(f"开放问题: {len(qs)} 个（open {len([q for q in qs if q[1] == 'open'])}）")
    print(f"教训库:   {mem.lessons_path.replace(_ROOT + os.sep, '') if os.path.exists(mem.lessons_path) else '不存在'}")
    print()

    games = SmartPick.games(_ROOT)
    print(f"彩种: {len(games)}")
    for g in games:
        try:
            print("  " + SmartPick.for_game(g, _ROOT).summary())
        except Exception as e:
            print(f"  {g}: ✗ {e}")
    print()
    print("单一入口: AI_CONTEXT.md")
    print("契约:     spec/*.schema.json")
    return 0


# ---------------------------------------------------------------- new-game

def cmd_new_game(args) -> int:
    import shutil

    src = os.path.join(_ROOT, "games", "_template")
    dst = os.path.join(_ROOT, "games", args.game_id)

    if not os.path.isdir(src):
        print(f"✗ 模板不存在: {os.path.relpath(src, _ROOT)}")
        print("  请先创建 games/_template/（见 games/_template/README.md）")
        return 1
    if os.path.exists(dst):
        print(f"✗ 目标已存在: {os.path.relpath(dst, _ROOT)}")
        return 1

    shutil.copytree(src, dst)
    print(f"✓ 已创建 {os.path.relpath(dst, _ROOT)}")
    print()
    print("下一步：")
    print(f"  1. 编辑 games/{args.game_id}/game.yaml（machine / features / prize_model / data）")
    print(f"  2. 放置数据到 games/{args.game_id}/data/raw/ 并算 SHA256")
    print(f"  3. 建 games/{args.game_id}/iterations/round01/TASK_BRIEF.md")
    print(f"  4. python cli/main.py validate --game {args.game_id}")
    print()
    print("⚠️ 不要修改 framework/ 与 src/ 的任何一行 —— 若需要改，说明框架分离没做好。")
    return 0


# ---------------------------------------------------------------- pick

def cmd_pick(args) -> int:
    from core import GenerateError

    sp = _smartpick(args.game)
    if args.n < 1:
        print("✗ --n 必须是正整数")
        return 1

    try:
        res = sp.pick(
            n=args.n,
            seed=args.seed,
            use_rules=not args.no_rules,
            spread=not args.no_spread,
        )
    except GenerateError as e:
        print(f"✗ {e}")
        return 1

    if args.json:
        import json
        print(json.dumps(
            {
                "game": args.game,
                "n": len(res),
                "attempts": res.attempts,
                "stats": res.stats,
                "tickets": [t.to_json() for t in res],
            },
            ensure_ascii=False, indent=2,
        ))
        return 0

    if args.quiet:
        for t in res:
            print(t.render())
        return 0

    # 表头
    print(f"smartpickcore pick — game={args.game}  n={len(res)}"
          f"  seed={args.seed if args.seed is not None else '随机'}")
    print()

    scopes = sp.rule_scopes()
    if scopes["single"]:
        print(f"已应用单注层规则: {scopes['single']}")
    if scopes["cross"]:
        print(f"⚠️ 跨注层规则已跳过（单注无法判定）: {scopes['cross']}")
        for rid, why in scopes["cross_reasons"].items():
            print(f"     {rid}: {why}")
    print()

    feats = sp.evaluable_features()
    show = [k for k in ("adjacent_pairs", "has_run_ge2", "front_sum", "front_odd")
            if k in feats]

    if show:
        head = f"{'#':>3}  {'号码':<32}  " + "  ".join(f"{k:>15s}" for k in show)
    else:
        head = f"{'#':>3}  {'号码':<32}"
    print(head)
    print("-" * len(head))

    for i, t in enumerate(res, 1):
        fv = sp.evaluate(t)
        row = f"{i:>3}  {t.render():<32}  " + "  ".join(
            f"{str(fv.get(k)):>15s}" for k in show
        )
        print(row)

    print()
    s = res.stats
    print(f"尝试 {s.get('attempts', '?')} 次"
          f"  接受率 {s.get('acceptance_rate', 0):.3f}"
          f"  被 exclude {s.get('excluded', 0)} 次")
    if "spread_penalty" in s:
        print(f"结构分散惩罚 {s['spread_penalty']:.4f}"
              f"  ⚠️ 该指标未量化（见 OPEN_QUESTIONS 的 Q-009 提案）")

    print()
    print("⚠️ 本命令不改变中奖概率（恒为 1/T）。产出的号码只是满足规则，")
    print("   不代表更容易中奖。请理性购彩，量力而行。")
    return 0


# ---------------------------------------------------------------- eval

def cmd_eval(args) -> int:
    """求一注号码的特征并按规则判定。"""
    from core import PredicateError, TicketError

    sp = _smartpick(args.game)

    # 号码来源：--ticket "03 11 17 24 32 + 04 09" 或 --front/--back
    zones: dict[str, list[int]] = {}
    if args.ticket:
        text = args.ticket
        if "+" in text:
            parts = [p.strip() for p in text.split("+")]
        else:
            parts = [text]
        keys = [z["key"] for z in sp.config["machine"]["zones"]]
        if len(parts) != len(keys):
            print(f"✗ 号码需要 {len(keys)} 个区（{keys}），用 + 分隔；"
                  f"你给了 {len(parts)} 段")
            return 1
        for k, p in zip(keys, parts):
            try:
                zones[k] = [int(x) for x in p.replace(",", " ").split()]
            except ValueError:
                print(f"✗ 区 {k} 的号码无法解析为整数: {p!r}")
                return 1
    else:
        print("✗ 需要 --ticket；例如 "
              '--ticket "03 11 17 24 32 + 04 09"')
        return 1

    try:
        t = Ticket(zones).check(sp.config)
    except TicketError as e:
        print(f"✗ 号码不合法: {e}")
        return 1

    feats = sp.evaluate(t)
    print(f"号码: {t.render()}")
    print()
    print("特征：")
    for k in sorted(feats):
        print(f"  {k:24s} = {feats[k]}")

    print()
    scopes = sp.rule_scopes()
    if scopes["cross"]:
        print(f"⚠️ 跨注层规则不参与判定（单注无法算）: {scopes['cross']}")

    try:
        r = sp.judge(t)
    except PredicateError as e:
        print(f"✗ 规则求值失败: {e}")
        return 1

    print(f"判定: {r.explain()}")
    print(f"  excluded={r.excluded}  required_failed={r.required_failed}"
          f"  weight={r.weight:.3f}  matched={r.matched}")
    print()
    print("⚠️ 该判定只反映「号码与规则的契合度」，不代表中奖概率。")
    return 0


# ---------------------------------------------------------------- parsers

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="smartpickcore",
        description="彩票投注策略研究框架 CLI",
        epilog="未实现的命令会明确报错，不会静默成功。",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    # validate
    sp = sub.add_parser("validate", help="校验契约")
    sp.add_argument("--all", action="store_true", default=False,
                    help="全量校验（默认行为）")
    sp.add_argument("--facts", action="store_true", help="只校验结论台账")
    sp.add_argument("--game", metavar="ID", help="只校验某彩种（含 strategy 与 iterations）")
    sp.add_argument("-v", "--verbose", action="store_true", help="打印通过项")
    sp.set_defaults(func=cmd_validate)

    # index
    sp = sub.add_parser("index", help="从 FACTS.jsonl 重生成 INDEX.md")
    sp.set_defaults(func=cmd_index)

    # versions
    sp = sub.add_parser("versions", help="版本一致性检查（文件内版本行 ↔ versions.json ↔ VERSION_INDEX.md）")
    sp.add_argument("--summary", action="store_true", help="打印版本概览")
    sp.add_argument("-v", "--verbose", action="store_true", help="打印通过项")
    sp.set_defaults(func=cmd_versions)

    # strategy
    sp = sub.add_parser("strategy", help="重新生成 strategy.json")
    sp.add_argument("--game", required=True, metavar="ID")
    sp.add_argument("--iteration", metavar="roundNN", default=None)
    sp.add_argument("--dry-run", action="store_true", help="只打印，不写盘")
    sp.set_defaults(func=cmd_strategy)

    # games
    sp = sub.add_parser("games", help="列出彩种")
    sp.set_defaults(func=cmd_games)

    # facts
    sp = sub.add_parser("facts", help="列结论")
    sp.add_argument("--game", metavar="ID")
    sp.add_argument("--status", choices=["established", "tentative", "refuted", "superseded"])
    sp.add_argument("--category")
    sp.add_argument("--min-confidence", type=int, metavar="N")
    sp.set_defaults(func=cmd_facts)

    # caveats
    sp = sub.add_parser("caveats", aliases=["caves"], help="列某条结论的减损项")
    sp.add_argument("fact_id", metavar="F-XXXX")
    sp.set_defaults(func=cmd_caveats)

    # questions
    sp = sub.add_parser("questions", help="列开放问题")
    sp.set_defaults(func=cmd_questions)

    # todo
    sp = sub.add_parser("todo", help="从 caveats 生成待办建议")
    sp.set_defaults(func=cmd_todo)

    # info
    sp = sub.add_parser("info", help="仓库概览")
    sp.set_defaults(func=cmd_info)

    # new-game
    sp = sub.add_parser("new-game", help="从 _template 创建新彩种骨架")
    sp.add_argument("game_id", metavar="ID")
    sp.set_defaults(func=cmd_new_game)

    # pick
    sp = sub.add_parser("pick", help="生成合规号码（按单注层规则过滤）")
    sp.add_argument("--game", required=True, metavar="ID")
    sp.add_argument("-n", "--n", type=int, default=1, help="生成注数（默认 1）")
    sp.add_argument("--seed", type=int, default=None, help="随机种子（固定后可复现）")
    sp.add_argument("--no-rules", action="store_true",
                    help="不过滤规则（等价于均匀随机，用于对照）")
    sp.add_argument("--no-spread", action="store_true",
                    help="不做注间结构分散（只看单注是否合规）")
    sp.add_argument("--json", action="store_true", help="输出 JSON")
    sp.add_argument("-q", "--quiet", action="store_true", help="只输出号码")
    sp.set_defaults(func=cmd_pick)

    # eval
    sp = sub.add_parser("eval", help="求一注号码的特征并按规则判定")
    sp.add_argument("--game", required=True, metavar="ID")
    sp.add_argument("--ticket", required=True, metavar="TXT",
                    help='号码，如 "03 11 17 24 32 + 04 09"')
    sp.set_defaults(func=cmd_eval)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n中断")
        return 130
    except Exception as e:
        print(f"✗ 未预期的错误: {type(e).__name__}: {e}")
        if os.environ.get("SMARTPICK_DEBUG"):
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
