import React, { useMemo } from "react";

function RewardChart({ history, height = 120, width = 320 }) {
  const computed = useMemo(() => {
    if (!history || history.length < 2) return null;

    const rewards = history.map((h) => h.reward ?? 0);
    const minR = Math.min(...rewards);
    const maxR = Math.max(...rewards);
    const range = maxR - minR || 1;

    const points = history
      .map((h, i) => {
        const x = (i / (history.length - 1)) * (width - 10) + 5;
        const yNorm = ((h.reward ?? 0) - minR) / range; // 0..1
        const y = (1 - yNorm) * (height - 10) + 5;
        return `${x},${y}`;
      })
      .join(" ");

    return { points, minR, maxR };
  }, [history, height, width]);

  if (!computed) {
    return (
      <div style={{ border: "1px solid #333", borderRadius: 12, padding: 10 }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>
          Reward (last {history?.length ?? 0})
        </div>
        <div style={{ opacity: 0.7, fontSize: 12 }}>Waiting for data…</div>
      </div>
    );
  }

  const { points, minR, maxR } = computed;

  return (
    <div style={{ border: "1px solid #333", borderRadius: 12, padding: 10 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>
        Reward (last {history.length})
      </div>

      <svg width={width} height={height} style={{ display: "block" }}>
        <polyline fill="none" stroke="white" strokeWidth="2" points={points} />
      </svg>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          opacity: 0.8,
        }}
      >
        <span>min: {minR.toFixed(2)}</span>
        <span>max: {maxR.toFixed(2)}</span>
      </div>
    </div>
  );
}

export default React.memo(RewardChart);
