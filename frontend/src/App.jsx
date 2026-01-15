import { useEffect, useRef, useState } from "react";
import TetrisBoard from "./components/TetrisBoard";
import StatsPanel from "./components/StatsPanel";
import RewardChart from "./components/RewardChart";
import LinesChart from "./components/LinesChart";
import EpisodeRewardChart from "./components/EpisodeRewardChart";




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

  const [history, setHistory] = useState([]); // { step, reward, score, lines }
  const [episodeHistory, setEpisodeHistory] = useState([]); // { episode, totalReward, lines }
  
  const episodeRewardRef = useRef(0);
  const lastChartUpdateRef = useRef(0);
  const lastEpisodeRef = useRef(0);
  const episodeStartLinesRef = useRef(0);
  const episodeMaxLinesRef = useRef(0);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");

    ws.onopen = () => setStatus("Connected");
    ws.onclose = () => setStatus("Disconnected");
    ws.onerror = () => setStatus("Error");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus("Connected");

      // ────────────────────────────────
      // EPISODE CHANGE = FINALIZE PREVIOUS EPISODE
      // ────────────────────────────────
      if (data.episode !== undefined && data.episode !== lastEpisodeRef.current) {
        const episodeLinesCleared = episodeMaxLinesRef.current - episodeStartLinesRef.current;

        setEpisodeHistory((prev) => [
          ...prev.slice(-100),
          {
            episode: lastEpisodeRef.current,
            totalReward: episodeRewardRef.current,
            lines: episodeLinesCleared,
          },
        ]);

        // reset accumulators for new episode
        episodeRewardRef.current = 0;
        episodeStartLinesRef.current = 0;
        episodeMaxLinesRef.current = 0;

        lastEpisodeRef.current = data.episode;
      }

      // ────────────────────────────────
      // TELEMETRY
      // ────────────────────────────────
      if (data.aiAction !== undefined) setAiAction(data.aiAction);
      if (data.reward !== undefined) setReward(data.reward);
      if (data.episode !== undefined) setEpisode(data.episode);
      if (data.step !== undefined) setStep(data.step);
      if (data.gameOver !== undefined) setGameOver(data.gameOver);

      // accumulate reward for this episode
      if (data.reward !== undefined) {
        episodeRewardRef.current += data.reward;
      }

      // track max cumulative lines in this episode
      if (data.lines !== undefined) {
        if (data.lines > episodeMaxLinesRef.current) {
          episodeMaxLinesRef.current = data.lines;
        }
      }

      // ────────────────────────────────
      // MAIN GAME STATE
      // ────────────────────────────────
      if (data.type === "state") {
        if (data.board) setBoard(data.board);
        if (data.score !== undefined) setScore(data.score);
        if (data.lines !== undefined) setLines(data.lines);
        if (data.nextPiece !== undefined) setNextPiece(data.nextPiece);
        if (data.gameOver !== undefined) setGameOver(data.gameOver);
      }

      // ────────────────────────────────
      // CHART HISTORY (THROTTLED)
      // ────────────────────────────────
      if (data.reward !== undefined && data.step !== undefined) {
        const now = performance.now();
        if (now - lastChartUpdateRef.current > 100) { // 10 FPS charts
          lastChartUpdateRef.current = now;

          setHistory((prev) => {
            const next = [
              ...prev,
              {
                step: data.step,
                reward: data.reward,
                score: data.score ?? score,
                lines: data.lines ?? lines,
              },
            ];
            return next.slice(-200);
          });
        }
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
        <div style={{ display: "grid", gap: 12 }}>
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
        <div style={{display: "grid", gap: 12  }}>
          <RewardChart history={history} />
          <LinesChart history={history} />
          <EpisodeRewardChart data={episodeHistory} />
          <div style={{ fontSize: 12, opacity: 0.8 }}>
            episodeHistory points: {episodeHistory.length}{" "}
            | last:{" "}
            {episodeHistory.length
              ? `${episodeHistory[episodeHistory.length - 1].totalReward.toFixed(2)} (lines ${episodeHistory[episodeHistory.length - 1].lines})`
              : "-"}
          </div>

        </div>
        </div>

        <div>
          <TetrisBoard board={board} />
        </div>
      </div>
    </div>
  );
}
