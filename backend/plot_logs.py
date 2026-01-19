import argparse
import os
from glob import glob

import pandas as pd
import matplotlib.pyplot as plt


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def moving_avg(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


def list_runs(runs_root: str) -> list[str]:
    if not os.path.isdir(runs_root):
        return []
    runs = [d for d in os.listdir(runs_root) if os.path.isdir(os.path.join(runs_root, d))]
    runs.sort()
    return runs


def load_episodes_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        return df
    # Sort by time then episode
    if "wall_time" in df.columns:
        df = df.sort_values(["wall_time", "episode"]).reset_index(drop=True)
    else:
        df = df.sort_values(["episode"]).reset_index(drop=True)
    return df


def save_plots(df: pd.DataFrame, out_dir: str, ma: int, label: str, xaxis: str = "episode") -> None:
    ensure_dir(out_dir)

    df = df.copy()

    # Choose x-axis
    if xaxis == "time":
        if "wall_time" not in df.columns:
            raise ValueError("wall_time column missing; cannot use --xaxis time")
        t0 = float(df["wall_time"].iloc[0])
        df["t_min"] = (df["wall_time"] - t0) / 60.0
        x = df["t_min"]
        xlabel = "Minutes since run start"
    else:
        x = df["episode"]
        xlabel = "Episode"

    df["reward_ma"] = moving_avg(df["total_reward"], ma)
    df["lines_ma"] = moving_avg(df["lines"], ma)
    df["score_ma"] = moving_avg(df["score"], ma)
    df["steps_ma"] = moving_avg(df["steps"], ma)

    # Reward
    plt.figure()
    plt.plot(x, df["total_reward"], alpha=0.25)
    plt.plot(x, df["reward_ma"])
    plt.title(f"Episode Reward {label} (MA={ma})")
    plt.xlabel(xlabel)
    plt.ylabel("Total reward")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "reward.png"))
    plt.close()

    # Lines
    plt.figure()
    plt.plot(x, df["lines"], alpha=0.25)
    plt.plot(x, df["lines_ma"])
    plt.title(f"Lines per Episode {label} (MA={ma})")
    plt.xlabel(xlabel)
    plt.ylabel("Lines")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "lines.png"))
    plt.close()

    # Score
    plt.figure()
    plt.plot(x, df["score"], alpha=0.25)
    plt.plot(x, df["score_ma"])
    plt.title(f"Score per Episode {label} (MA={ma})")
    plt.xlabel(xlabel)
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "score.png"))
    plt.close()

    # Steps
    plt.figure()
    plt.plot(x, df["steps"], alpha=0.25)
    plt.plot(x, df["steps_ma"])
    plt.title(f"Steps per Episode {label} (MA={ma})")
    plt.xlabel(xlabel)
    plt.ylabel("Steps")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "steps.png"))
    plt.close()

def summarize_run(df: pd.DataFrame) -> dict:
    return {
        "episodes": len(df),
        "avg_lines": float(df["lines"].mean()),
        "max_lines": int(df["lines"].max()),
        "avg_reward": float(df["total_reward"].mean()),
        "max_reward": float(df["total_reward"].max()),
        "avg_score": float(df["score"].mean()),
        "max_score": int(df["score"].max()),
    }
def build_summary_table(runs_root: str) -> pd.DataFrame:
    runs = list_runs(runs_root)
    rows = []
    for rid in runs:
        ep_path = os.path.join(runs_root, rid, "episodes.csv")
        if not os.path.exists(ep_path):
            continue
        df = load_episodes_csv(ep_path)
        if df.empty:
            continue
        s = summarize_run(df)
        s["run_id"] = rid
        rows.append(s)

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    out = out.sort_values(["avg_lines", "max_lines", "avg_score"], ascending=False).reset_index(drop=True)
    return out


def plot_compare_runs(
    runs_root: str,
    out_dir: str,
    ma: int,
    metric: str,
    top_k: int,
    xaxis: str = "episode",
) -> None:
    ensure_dir(out_dir)

    summary = build_summary_table(runs_root)
    if summary.empty:
        print("No runs to compare.")
        return

    # choose top K runs by avg_lines primarily (already sorted)
    chosen = summary.head(top_k)["run_id"].tolist()

    plt.figure()
    for rid in chosen:
        ep_path = os.path.join(runs_root, rid, "episodes.csv")
        df = load_episodes_csv(ep_path)
        if df.empty:
            continue

        if metric == "reward":
            y = df["total_reward"]
            y_ma = moving_avg(y, ma)
            ylabel = "Total reward"
        elif metric == "score":
            y = df["score"]
            y_ma = moving_avg(y, ma)
            ylabel = "Score"
        else:
            y = df["lines"]
            y_ma = moving_avg(y, ma)
            ylabel = "Lines"

        # MA line only (cleaner than raw)
        if xaxis == "time":
            if "wall_time" not in df.columns:
                continue
            t0 = float(df["wall_time"].iloc[0])
            x = (df["wall_time"] - t0) / 60.0
            xlabel = "Minutes since run start"
        else:
            x = df["episode"]
            xlabel = "Episode"

        plt.plot(x, y_ma, label=rid)

    plt.title(f"Compare runs: {metric} (MA={ma}) | top_k={top_k} | x={xaxis}")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f"compare_{metric}.png"))
    plt.close()

    # also export a leaderboard table for convenience
    summary.to_csv(os.path.join(out_dir, "summary.csv"), index=False)
    print("Saved compare plot + summary.csv to:", out_dir)
    print(summary[["run_id", "episodes", "avg_lines", "max_lines", "avg_score", "max_score", "avg_reward"]].head(top_k).to_string(index=False))



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ma", type=int, default=20, help="Moving average window")
    parser.add_argument("--runs-root", type=str, default="backend/logs/runs", help="Root folder that contains run_id folders")
    parser.add_argument("--run-id", type=str, default="", help="Specific run_id to plot (folder name)")
    parser.add_argument("--latest", action="store_true", help="Plot the latest run_id")
    parser.add_argument("--summary", action="store_true", help="Print summary table of all runs")
    parser.add_argument("--compare", action="store_true", help="Compare runs on one set of plots")
    parser.add_argument("--metric", type=str, default="lines", choices=["lines", "reward", "score"], help="Metric for compare plot")
    parser.add_argument("--top-k", type=int, default=5, help="Top K runs to include in compare plots")
    parser.add_argument("--out", type=str, default="logs/compare", help="Output folder for compare plots and summary csv")
    parser.add_argument("--export-summary", action="store_true", help="Write summary.csv into --out folder")
    parser.add_argument("--xaxis", type=str, default="episode", choices=["episode", "time"], help="X-axis for plots")

    args = parser.parse_args()

    runs = list_runs(args.runs_root)
    if args.export_summary:
        ensure_dir(args.out)
        summary = build_summary_table(args.runs_root)
        if summary.empty:
            print("No runs found to export.")
            return
        summary.to_csv(os.path.join(args.out, "summary.csv"), index=False)
        print("Wrote:", os.path.join(args.out, "summary.csv"))

    if args.compare:
        plot_compare_runs(
        runs_root=args.runs_root,
        out_dir=args.out,
        ma=args.ma,
        metric=args.metric,
        top_k=args.top_k,
        xaxis=args.xaxis,
        )
        return


    if args.summary:
        if not runs:
            print("No runs found in", args.runs_root)
            return
        rows = []
        for rid in runs:
            ep_path = os.path.join(args.runs_root, rid, "episodes.csv")
            if not os.path.exists(ep_path):
                continue
            df = load_episodes_csv(ep_path)
            if df.empty:
                continue
            s = summarize_run(df)
            s["run_id"] = rid
            rows.append(s)

        if not rows:
            print("No usable episodes.csv files found.")
            return

        out = pd.DataFrame(rows)
        out = out.sort_values(["avg_lines", "max_lines", "avg_score"], ascending=False)

        print(out[["run_id", "episodes", "avg_lines", "max_lines", "avg_score", "max_score", "avg_reward"]].to_string(index=False))
        return

    # Decide which run to plot
    run_id = args.run_id
    if args.latest:
        if not runs:
            raise SystemExit(f"No runs found in {args.runs_root}")
        run_id = runs[-1]

    if not run_id:
        # fallback: plot "flat" logs if you still use logs/episodes.csv
        flat_path = "logs/episodes.csv"
        if not os.path.exists(flat_path):
            raise SystemExit("No run selected and logs/episodes.csv not found. Use --latest or --run-id.")
        df = load_episodes_csv(flat_path)
        out_dir = "logs/plots"
        save_plots(df, out_dir, args.ma, label="(flat)", xaxis=args.xaxis)
        print("Saved plots to:", out_dir)
        print("Summary:", summarize_run(df))
        return

    ep_path = os.path.join(args.runs_root, run_id, "episodes.csv")
    if not os.path.exists(ep_path):
        raise SystemExit(f"episodes.csv not found for run_id={run_id}: {ep_path}")

    df = load_episodes_csv(ep_path)
    out_dir = os.path.join(args.runs_root, run_id, "plots")
    save_plots(df, out_dir, args.ma, label=run_id, xaxis=args.xaxis)

    print("Saved plots to:", out_dir)
    print("Summary:", summarize_run(df))


if __name__ == "__main__":
    main()
