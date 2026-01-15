export default function RewardChart({ history, height = 120, width = 320 }) {
  if (!history || history.length < 2) {
    return (
      <div style={{ opacity: 0.7, fontSize: 12 }}>
        Waiting for data…
      </div>
    );
  }

  // Map reward values to a simple SVG polyline
  const rewards = history.map((h) => h.reward);
  const minR = Math.min(...rewards);
  const maxR = Math.max(...rewards);
  const range = maxR - minR || 1;

  const points = history
    .map((h, i) => {
      const x = (i / (history.length - 1)) * (width - 10) + 5;
      const yNorm = (h.reward - minR) / range; // 0..1
      const y = (1 - yNorm) * (height - 10) + 5;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div style={{ border: "1px solid #333", borderRadius: 12, padding: 10 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>Reward (last {history.length})</div>

      <svg width={width} height={height} style={{ display: "block" }}>
        <polyline
          fill="none"
          stroke="white"
          strokeWidth="2"
          points={points}
        />
      </svg>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, opacity: 0.8 }}>
        <span>min: {minR.toFixed(2)}</span>
        <span>max: {maxR.toFixed(2)}</span>
      </div>
    </div>
  );
}
