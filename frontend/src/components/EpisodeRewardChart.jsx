import React, { useMemo } from "react";

function EpisodeRewardChart({ data, height = 120, width = 320 }) {
  const computed = useMemo(() => {
    if (!data || data.length < 2) return null;

    const values = data.map((d) => d.totalReward);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    const range = maxV - minV || 1;

    const points = data
      .map((d, i) => {
        const x = (i / (data.length - 1)) * (width - 10) + 5;
        const yNorm = (d.totalReward - minV) / range;
        const y = (1 - yNorm) * (height - 10) + 5;
        return `${x},${y}`;
      })
      .join(" ");

    return { points, minV, maxV };
  }, [data, height, width]);

  if (!computed) {
    return (
      <div style={{ border: "1px solid #333", borderRadius: 12, padding: 10 }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>
          Episode Reward (last {data?.length ?? 0})
        </div>
        <div style={{ opacity: 0.7, fontSize: 12 }}>Waiting for episodes…</div>
      </div>
    );
  }

  const { points, minV, maxV } = computed;

  return (
    <div style={{ border: "1px solid #333", borderRadius: 12, padding: 10 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>
        Episode Reward (last {data.length})
      </div>

      <svg width={width} height={height} style={{ display: "block" }}>
        <polyline fill="none" stroke="#3fb950" strokeWidth="2" points={points} />
      </svg>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, opacity: 0.8 }}>
        <span>min: {minV.toFixed(2)}</span>
        <span>max: {maxV.toFixed(2)}</span>
      </div>
    </div>
  );
}

export default React.memo(EpisodeRewardChart);

