#!/usr/bin/env python3
"""
从 Experiment 看板拉取图表时序数据并生成供 single_analysis / cross_curve_analysis 使用的 CSV。

依赖 merlin-cli，内部会调用：
- merlin-cli tracking search-panel：获取每个图表的 legends 列表
- merlin-cli tracking get-timeseries：获取每条曲线的 (x, y) 数据点

输出 CSV 表头：insight_sid, legend, x, y, is_new
- insight_sid：图表的 experiment_group_insight_sid（如 8puzm1u1qe697c293f）。
- is_new 规则：
  - 第一次调用（不传 --baseline-csv）：每条 legend 按 x 排序后，后 30% 的点标 is_new=1（新增），前 70% 标 is_new=0（历史）；可用 --first-new-ratio 调整比例。
  - 第二次及以后（传 --baseline-csv 指向上次输出的 CSV）：上次 CSV 里已有的点标 is_new=0（存量），本次新出现的点标 is_new=1（增量）。
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, List, Dict, Optional


def run_merlin_cli(subcommand: str, json_payload: dict) -> str:
    """执行 merlin-cli 命令并返回 stdout。"""
    cmd = ["merlin-cli", "tracking", subcommand, "--json", json.dumps(json_payload)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"merlin-cli 执行失败 (exit {result.returncode}): {result.stderr or result.stdout}"
            )
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError(
            "未找到 merlin-cli，请先安装： "
            "curl -fsSL https://ml.bytedance.net/api/agent/system/tos-proxy/merlin-cli/latest/install.sh | bash"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("merlin-cli 执行超时 (120s)")


def search_panel(experiment_group_sid: str, insight_sids: List[str]) -> List[Dict[str, Any]]:
    """
    调用 search-panel 获取每个 insight 的 legends。
    返回形如 [{"insight_sid": "...", "legends": ["a","b"], "error": null}, ...]
    """
    insights = [
        {"insight_sid": sid, "experiment_group_sid": experiment_group_sid}
        for sid in insight_sids
    ]
    payload = {"insights": insights}
    out = run_merlin_cli("search-panel", payload)
    data = json.loads(out)
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    if isinstance(data, list):
        return data
    raise ValueError(f"search-panel 返回格式无法解析: {out[:500]}")


def get_timeseries(
    experiment_group_sid: str,
    insight_sid: str,
    legends: List[str],
) -> Dict[str, Any]:
    """
    调用 get-timeseries 获取指定 insight 下若干 legend 的时序数据。
    返回形如 {"series": [{"legend": "xxx", "points": [{"value": [x,y], ...}]}]}
    """
    payload = {
        "insight_sid": insight_sid,
        "experiment_group_sid": experiment_group_sid,
        "filters": {"legends": legends},
    }
    out = run_merlin_cli("get-timeseries", payload)
    data = json.loads(out)
    if isinstance(data, dict) and "content" in data and len(data["content"]) > 0:
        text = data["content"][0].get("text", "{}")
        return json.loads(text)
    if isinstance(data, dict) and "series" in data:
        return data
    if isinstance(data, str):
        return json.loads(data)
    raise ValueError(f"get-timeseries 返回格式无法解析: {out[:500]}")


def load_baseline_keys(baseline_csv_path: Path, x_round: int = 4) -> set:
    """
    从上次输出的 CSV 加载 (insight_sid, legend, rounded_x)，用于判断存量点。
    返回 set of (insight_sid, legend, round(x, x_round))。
    """
    keys = set()
    with open(baseline_csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for col in ["insight_sid", "legend", "x"]:
            if col not in (reader.fieldnames or []):
                return keys
        for row in reader:
            try:
                x = float(row["x"])
            except (ValueError, TypeError):
                continue
            keys.add((row["insight_sid"], row["legend"], round(x, x_round)))
    return keys


def build_rows(
    experiment_group_sid: str,
    panel_results: List[Dict[str, Any]],
    baseline_keys: Optional[set] = None,
    x_round: int = 4,
    first_new_ratio: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    根据 search-panel 结果逐个拉取 get-timeseries，组装 (insight_sid, legend, x, y, is_new)。
    baseline_keys 为 None 时（首次拉取）：每条 legend 按 x 排序，后 first_new_ratio 比例的点为 is_new=1；
    否则与 baseline 比对，已在 baseline 中的点为 is_new=0。
    """
    rows: List[Dict[str, Any]] = []
    for item in panel_results:
        insight_sid = item.get("insight_sid", "")
        if item.get("error"):
            sys.stderr.write(
                f"跳过 insight_sid={insight_sid}, 错误: {item.get('error')}\n"
            )
            continue
        legends = item.get("legends") or []
        if not legends:
            continue
        try:
            ts = get_timeseries(experiment_group_sid, insight_sid, legends)
        except Exception as e:
            sys.stderr.write(f"get-timeseries 失败 insight_sid={insight_sid}: {e}\n")
            continue
        series_list = ts.get("series") or []
        for s in series_list:
            legend = s.get("legend", "")
            points = s.get("points") or []
            # 按 x 排序，保证顺序一致
            point_list = []
            for pt in points:
                val = pt.get("value") if isinstance(pt.get("value"), list) else []
                if len(val) < 2:
                    continue
                point_list.append((val[0], val[1]))
            point_list.sort(key=lambda p: (float(p[0]), float(p[1])))
            n = len(point_list)
            for i, (x_val, y_val) in enumerate(point_list):
                if baseline_keys is None:
                    # 首次拉取：后 first_new_ratio 比例的点为新增
                    cutoff = max(0, n - max(1, int(round(n * first_new_ratio))))
                    is_new = 1 if i >= cutoff else 0
                else:
                    key = (insight_sid, legend, round(float(x_val), x_round))
                    is_new = 0 if key in baseline_keys else 1
                rows.append({
                    "insight_sid": insight_sid,
                    "legend": legend,
                    "x": x_val,
                    "y": y_val,
                    "is_new": is_new,
                })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="通过 merlin-cli tracking search-panel 与 get-timeseries 拉取看板数据并生成 case.csv"
    )
    parser.add_argument(
        "--experiment-group-sid",
        "-g",
        required=True,
        help="实验组 ID（可从看板 URL 中 experiment/dashboard/<id> 获取）",
    )
    parser.add_argument(
        "--insight-sids",
        "-i",
        required=True,
        nargs="+",
        help="要拉取的图表 insight_sid 列表（可从看板 URL experiment_group_insight 或页面获取）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="case.csv",
        help="输出 CSV 路径 (默认: case.csv)",
    )
    parser.add_argument(
        "--baseline-csv",
        "-b",
        default=None,
        metavar="PATH",
        help="上次输出的 CSV 路径。不传则首次拉取（每条 legend 后 30%% 为 is_new=1）；传入则与上次对比，存量 is_new=0，增量 is_new=1",
    )
    parser.add_argument(
        "--first-new-ratio",
        type=float,
        default=0.3,
        metavar="R",
        help="首次拉取时每条 legend 末尾视为新增点的比例 (默认: 0.3 即 30%%)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="仅写 CSV，不打印进度",
    )
    args = parser.parse_args()

    experiment_group_sid = args.experiment_group_sid.strip()
    insight_sids = [s.strip() for s in args.insight_sids if s.strip()]
    if not insight_sids:
        print("错误: 至少提供一个 --insight-sids", file=sys.stderr)
        return 1

    baseline_keys: Optional[set] = None
    if args.baseline_csv:
        baseline_path = Path(args.baseline_csv).resolve()
        if not baseline_path.exists():
            print(f"错误: baseline CSV 不存在: {baseline_path}", file=sys.stderr)
            return 1
        baseline_keys = load_baseline_keys(baseline_path)
        if not args.quiet:
            print(f"已加载 baseline: {baseline_path} ({len(baseline_keys)} 个存量点)")

    if not args.quiet:
        print("调用 merlin-cli tracking search-panel ...")
    panel_results = search_panel(experiment_group_sid, insight_sids)
    if not args.quiet:
        print(f"已获取 {len(panel_results)} 个图表的 legends，正在拉取 get-timeseries ...")

    rows = build_rows(
        experiment_group_sid,
        panel_results,
        baseline_keys=baseline_keys,
        first_new_ratio=args.first_new_ratio,
    )
    if not rows:
        print("未获取到任何数据点", file=sys.stderr)
        return 1

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["insight_sid", "legend", "x", "y", "is_new"],
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)

    if not args.quiet:
        print(f"已写入 {len(rows)} 行 -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
