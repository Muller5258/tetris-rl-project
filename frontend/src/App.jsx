import { useEffect, useState } from "react";
import TetrisBoard from "./components/TetrisBoard";

const emptyBoard = () => Array.from({ length: 20 }, () => Array(10).fill(0));

export default function App() {
  const [board, setBoard] = useState(emptyBoard());
  const [score, setScore] = useState(0);
  const [nextPiece, setNextPiece] = useState(null);
  const [status, setStatus] = useState("Disconnected");

  // AI-only extras (watch mode)
  const [aiAction, setAiAction] = useState(null);
  const [reward, setReward] = useState(0);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");

    ws.onopen = () => setStatus("Connected");
    ws.onclose = () => setStatus("Disconnected");
    ws.onerror = () => setStatus("Error");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // AI extras (only present in watch mode)
      if (data.aiAction !== undefined) setAiAction(data.aiAction);
      if (data.reward !== undefined) setReward(data.reward);

      if (data.type === "state") {
        setBoard(data.board);
        setScore(data.score);
        setNextPiece(data.nextPiece);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <h1>Tetris RL Project</h1>

      <div>Status: {status}</div>
      <div>Score: {score}</div>
      <div>Next piece (0-6): {nextPiece}</div>

      <div style={{ marginTop: 8 }}>
        <div>AI action: {aiAction}</div>
        <div>Reward: {reward}</div>
      </div>

      <div style={{ marginTop: 16 }}>
        <TetrisBoard board={board} />
      </div>
    </div>
  );
}
