export default function StatsPanel({
  status,
  score,
  lines,
  episode,
  step,
  aiAction,
  reward,
  nextPiece,
  gameOver,
}) {
  const pillStyle = (bg) => ({
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 12,
    background: bg,
  });

  return (
    <div
      style={{
        border: "1px solid #333",
        borderRadius: 12,
        padding: 12,
        display: "grid",
        gap: 8,
        minWidth: 280,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <div style={{ fontWeight: 700 }}>AI Panel</div>
        <span
          style={pillStyle(
            status === "Connected"
              ? "#1f6f3b"
              : status === "Error"
              ? "#7a1f1f"
              : "#444"
          )}
        >
          {status}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Score</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{score ?? "-"}</div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Lines</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{lines ?? "-"}</div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Episode</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{episode ?? "-"}</div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Step</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{step ?? "-"}</div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Last Action</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{aiAction ?? "-"}</div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Reward</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {reward ?? "-"}
          </div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Next Piece</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {nextPiece ?? "-"}
          </div>
        </div>

        <div>
          <div style={{ opacity: 0.7, fontSize: 12 }}>Game Over</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {gameOver ? "Yes" : "No"}
          </div>
        </div>
      </div>
    </div>
  );
}
