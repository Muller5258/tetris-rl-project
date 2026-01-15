export default function LinesChart({ history, height = 120, width = 320 }) {
  if (!history || history.length < 2) {
    return <div style={{ opacity: 0.7, fontSize: 12 }}>Waiting for data…</div>;
  }

  const values = history.map((h) => h.lines ?? 0);
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const range = maxV - minV || 1;

  const points = history
    .map((h, i) => {
      const x = (i / (history.length - 1)) * (width - 10) + 5;
      const v = h.lines ?? 0;
      const yNorm = (v - minV) / range; // 0..1
      const y = (1 - yNorm) * (height - 10) + 5;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div style={{ border: "1px solid #333", borderRadius: 12, padding: 10 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>
        Lines (last {history.length})
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
        <span>min: {minV}</span>
        <span>max: {maxV}</span>
      </div>
    </div>
  );
}
