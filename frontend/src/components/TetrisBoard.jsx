export default function TetrisBoard({ board }) {
  return (
    <div style={{ display: "inline-block", background: "#111", padding: 6 }}>
      {board.map((row, r) => (
        <div key={r} style={{ display: "flex" }}>
          {row.map((cell, c) => (
            <div
              key={c}
              style={{
                width: 20,
                height: 20,
                border: "1px solid #222",
                background: cell === 0 ? "#111" : "white",
              }}
              title={`r${r} c${c} = ${cell}`}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
