import { useEffect, useState } from "react";
import TetrisBoard from "./components/TetrisBoard";
import StatsPanel from "./components/StatsPanel";

const emptyBoard = () => Array.from({ length: 20 }, () => Array(10).fill(0));

export default function App() {
  const [board, setBoard] = useState(emptyBoard());
  const [score, setScore] = useState(0);
  const [lines, setLines] = useState(0);
  const [nextPiece, setNextPiece] = useState(null);
  const [status, setStatus] = useState("Disconnected");

  const [aiAction, setAiAction] = useState(null);
  const [reward, setReward] = useState(0);
  const [episode, setEpisode] = useState(0);
  const [step, setStep] = useState(0);
  const [gameOver, setGameOver] = useState(false);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");

    ws.onopen = () => setStatus("Connected");
    ws.onclose = () => setStatus("Disconnected");
    ws.onerror = () => setStatus("Error");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // optional AI telemetry
      if (data.aiAction !== undefined) setAiAction(data.aiAction);
      if (data.reward !== undefined) setReward(data.reward);
      if (data.episode !== undefined) setEpisode(data.episode);
      if (data.step !== undefined) setStep(data.step);
      if (data.gameOver !== undefined) setGameOver(data.gameOver);

      // main state updates
      if (data.type === "state") {
        if (data.board) setBoard(data.board);
        if (data.score !== undefined) setScore(data.score);
        if (data.lines !== undefined) setLines(data.lines);
        if (data.nextPiece !== undefined) setNextPiece(data.nextPiece);
        if (data.gameOver !== undefined) setGameOver(data.gameOver);
      }
    };

    // Keyboard controls for human play (still useful)
    const send = (action) => {
      ws.send(JSON.stringify({ type: "input", action }));
    };

    const keyDown = (e) => {
      if (e.repeat) return;

      if (e.key === "ArrowLeft") send("left");
      if (e.key === "ArrowRight") send("right");
      if (e.key === "ArrowUp") send("rotate");
      if (e.key === "ArrowDown") send("soft_drop_on");
      if (e.key === " ") send("hard_drop");
    };

    const keyUp = (e) => {
      if (e.key === "ArrowDown") send("soft_drop_off");
    };

    window.addEventListener("keydown", keyDown);
    window.addEventListener("keyup", keyUp);

    return () => {
      ws.close();
      window.removeEventListener("keydown", keyDown);
      window.removeEventListener("keyup", keyUp);
    };
  }, []);

  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <h1 style={{ margin: 0 }}>Tetris RL Project</h1>
      <div style={{ opacity: 0.7, marginTop: 6 }}>
        Live PPO demo (WebSocket → Python → React)
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "320px 1fr",
          gap: 16,
          marginTop: 16,
          alignItems: "start",
        }}
      >
        <StatsPanel
          status={status}
          score={score}
          lines={lines}
          episode={episode}
          step={step}
          aiAction={aiAction}
          reward={reward}
          nextPiece={nextPiece}
          gameOver={gameOver}
        />

        <div>
          <TetrisBoard board={board} />
        </div>
      </div>
    </div>
  );
}
