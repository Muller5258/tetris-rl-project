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


def save_plots(df: pd.DataFrame, out_dir: str, ma: int, label: str) -> None:
    ensure_dir(out_dir)

    df["reward_ma"] = moving_avg(df["total_reward"], ma)
    df["lines_ma"] = moving_avg(df["lines"], ma)
    df["score_ma"] = moving_avg(df["score"], ma)
    df["steps_ma"] = moving_avg(df["steps"], ma)

    # Reward
    plt.figure()
    plt.plot(df["episode"], df["total_reward"])
    plt.plot(df["episode"], df["reward_ma"])
    plt.title(f"Episode Reward {label} (MA={ma})")
    plt.xlabel("Episode")
    plt.ylabel("Total reward")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "reward.png"))
    plt.close()

    # Lines
    plt.figure()
    plt.plot(df["episode"], df["lines"])
    plt.plot(df["episode"], df["lines_ma"])
    plt.title(f"Lines per Episode {label} (MA={ma})")
    plt.xlabel("Episode")
    plt.ylabel("Lines")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "lines.png"))
    plt.close()

    # Score
    plt.figure()
    plt.plot(df["episode"], df["score"])
    plt.plot(df["episode"], df["score_ma"])
    plt.title(f"Score per Episode {label} (MA={ma})")
    plt.xlabel("Episode")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "score.png"))
    plt.close()

    # Steps
    plt.figure()
    plt.plot(df["episode"], df["steps"])
    plt.plot(df["episode"], df["steps_ma"])
    plt.title(f"Steps per Episode {label} (MA={ma})")
    plt.xlabel("Episode")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ma", type=int, default=20, help="Moving average window")
    parser.add_argument("--runs-root", type=str, default="logs/runs", help="Root folder that contains run_id folders")
    parser.add_argument("--run-id", type=str, default="", help="Specific run_id to plot (folder name)")
    parser.add_argument("--latest", action="store_true", help="Plot the latest run_id")
    parser.add_argument("--summary", action="store_true", help="Print summary table of all runs")
    args = parser.parse_args()

    runs = list_runs(args.runs_root)

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
        save_plots(df, out_dir, args.ma, label="(flat)")
        print("Saved plots to:", out_dir)
        print("Summary:", summarize_run(df))
        return

    ep_path = os.path.join(args.runs_root, run_id, "episodes.csv")
    if not os.path.exists(ep_path):
        raise SystemExit(f"episodes.csv not found for run_id={run_id}: {ep_path}")

    df = load_episodes_csv(ep_path)
    out_dir = os.path.join(args.runs_root, run_id, "plots")
    save_plots(df, out_dir, args.ma, label=run_id)

    print("Saved plots to:", out_dir)
    print("Summary:", summarize_run(df))


if __name__ == "__main__":
    main()
