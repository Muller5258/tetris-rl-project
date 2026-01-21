import { useEffect, useRef, useState } from "react";
import TetrisBoard from "./components/TetrisBoard";
import StatsPanel from "./components/StatsPanel";
import RewardChart from "./components/RewardChart";
import LinesChart from "./components/LinesChart";
import EpisodeRewardChart from "./components/EpisodeRewardChart";

const emptyBoard = () => Array.from({ length: 20 }, () => Array(10).fill(0));

export default function App() {
  // Core game state
  const [board, setBoard] = useState(emptyBoard());
  const [score, setScore] = useState(0);
  const [lines, setLines] = useState(0);
  const [nextPiece, setNextPiece] = useState(null);
  const [status, setStatus] = useState("Disconnected");

  // AI telemetry
  const [aiAction, setAiAction] = useState(null);
  const [reward, setReward] = useState(0);
  const [episode, setEpisode] = useState(0);
  const [step, setStep] = useState(0);
  const [gameOver, setGameOver] = useState(false);

  // Charts
  const [history, setHistory] = useState([]); // { step, reward, score, lines }
  const [episodeHistory, setEpisodeHistory] = useState([]); // { episode, totalReward, lines }

  // FPS control (backend streaming rate)
  const [fps, setFps] = useState(30);
  const [modelName, setModelName] = useState("phase2")
  const [lastAck, setLastAck] = useState(null);
  // WebSocket ref
  const wsRef = useRef(null);

  // Episode accumulation refs
  const episodeRewardRef = useRef(0);
  const episodeStartLinesRef = useRef(0);
  const episodeMaxLinesRef = useRef(0);
  const lastEpisodeRef = useRef(null);

  // Throttle chart updates
  const lastChartUpdateRef = useRef(0);

  // Keep latest score/lines in refs so history writes don't use stale state
  const scoreRef = useRef(0);
  const linesRef = useRef(0);

  const sendConfig = (nextModel, nextFps) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    ws.send(
      JSON.stringify({
        type: "config",
        model: nextModel,
        fps: nextFps,
      })
    );
  };

  useEffect(() => {
    scoreRef.current = score;
  }, [score]);

  useEffect(() => {
    linesRef.current = lines;
  }, [lines]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("Connected");
      // send initial FPS config
      ws.send(JSON.stringify({ type: "config", fps }));
    };

    ws.onclose = () => setStatus("Disconnected");
    ws.onerror = () => setStatus("Error");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "config_ack") {
          setLastAck(data);
        }

      // ---- telemetry fields ----
      if (data.aiAction !== undefined) setAiAction(data.aiAction);
      if (data.reward !== undefined) setReward(data.reward);
      if (data.episode !== undefined) setEpisode(data.episode);
      if (data.step !== undefined) setStep(data.step);
      if (data.gameOver !== undefined) setGameOver(data.gameOver);

      // ---- episode tracking (finalize when episode changes) ----
      if (data.episode !== undefined) {
        if (lastEpisodeRef.current === null) {
          // first ever message containing episode
          lastEpisodeRef.current = data.episode;
          episodeRewardRef.current = 0;
          episodeStartLinesRef.current = data.lines ?? 0;
          episodeMaxLinesRef.current = episodeStartLinesRef.current;
        } else if (data.episode !== lastEpisodeRef.current) {
          // episode changed -> finalize previous episode
          const linesClearedThisEpisode =
            episodeMaxLinesRef.current - episodeStartLinesRef.current;

          setEpisodeHistory((prev) => {
            const next = [
              ...prev,
              {
                episode: lastEpisodeRef.current,
                totalReward: episodeRewardRef.current,
                lines: linesClearedThisEpisode,
              },
            ];
            return next.slice(-120);
          });

          // reset for new episode
          lastEpisodeRef.current = data.episode;
          episodeRewardRef.current = 0;
          episodeStartLinesRef.current = data.lines ?? 0;
          episodeMaxLinesRef.current = episodeStartLinesRef.current;
        }
      }

      // accumulate reward for current episode
      if (data.reward !== undefined) {
        episodeRewardRef.current += data.reward;
      }

      // track max cumulative lines during current episode
      if (data.lines !== undefined) {
        if (data.lines > episodeMaxLinesRef.current) {
          episodeMaxLinesRef.current = data.lines;
        }
      }

      // ---- main state updates ----
      if (data.type === "state") {
        if (data.board) setBoard(data.board);
        if (data.score !== undefined) setScore(data.score);
        if (data.lines !== undefined) setLines(data.lines);
        if (data.nextPiece !== undefined) setNextPiece(data.nextPiece);
        if (data.gameOver !== undefined) setGameOver(data.gameOver);
      }

      // ---- chart history (throttled) ----
      if (data.reward !== undefined && data.step !== undefined) {
        const now = performance.now();
        if (now - lastChartUpdateRef.current > 100) {
          // 100ms = 10fps chart updates
          lastChartUpdateRef.current = now;

          setHistory((prev) => {
            const next = [
              ...prev,
              {
                step: data.step,
                reward: data.reward,
                score: data.score ?? scoreRef.current,
                lines: data.lines ?? linesRef.current,
              },
            ];
            return next.slice(-250);
          });
        }
      }
    };

    // keyboard controls (optional)
    const send = (action) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "input", action }));
      }
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // create WS once

  // send fps config whenever slider changes
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");
    wsRef.current = ws;

    ws.onopen = () => {
        ws.send(
          JSON.stringify({
            type: "config",
            fps: fps,
            model: modelName,
          })
        );
      };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, []);
  useEffect(() => {
  const ws = wsRef.current;
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  ws.send(JSON.stringify({
    type: "config",
    fps,
  }));
}, [fps]);

  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <h1 style={{ margin: 0 }}>Tetris RL Project</h1>
      <div style={{ opacity: 0.7, marginTop: 6 }}>
        Live PPO demo (WebSocket → Python → React)
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "340px 1fr",
          gap: 16,
          marginTop: 16,
          alignItems: "start",
        }}
      >
        {/* Left panel */}
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

          {/* FPS slider */}
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 10,
              padding: 12,
              background: "#fff",
            }}
          >
            <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 6 }}>
              Stream FPS: <b>{fps}</b>
            </div>
            <input
              type="range"
              min="1"
              max="60"
              value={fps}
              onChange={(e) => setFps(Number(e.target.value))}
              style={{ width: "100%" }}
            />
            <div style={{ fontSize: 12, opacity: 0.65, marginTop: 6 }}>
              Lower FPS = smoother charts + less CPU. Higher FPS = more responsive board.
            </div>
          </div>
          {/* Model selector */}
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 10,
              padding: 12,
              background: "#fff",
            }}
          >
            <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 6 }}>
              Model: <b>{modelName}</b>
            </div>

            <select
              value={modelName}
              onChange={(e) => {
                const m = e.target.value;
                setModelName(m);
                sendConfig(m, fps);
              }}
              style={{ width: "100%", padding: 8, borderRadius: 8 }}
            >
              <option value="phase2">phase2</option>
              <option value="phase25">phase25</option>
              <option value="masked_v5">masked_v5</option>
              <option value="masked_v6">masked_v6</option>
              <option value="latest">latest</option>
            </select>
            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <button
                onClick={() => sendConfig(modelName, fps)}
                style={{
                  padding: "8px 10px",
                  borderRadius: 8,
                  border: "1px solid #ddd",
                  cursor: "pointer",
                  background: "#fff",
                }}
              >
                Apply
              </button>

              <button
                onClick={() => sendConfig("phase2", fps)}
                style={{
                  padding: "8px 10px",
                  borderRadius: 8,
                  border: "1px solid #ddd",
                  cursor: "pointer",
                  background: "#fff",
                }}
              >
                Reset to phase2
              </button>
            </div>

            <div style={{ fontSize: 12, opacity: 0.7, marginTop: 8 }}>
              {lastAck
                ? `Backend ack: model=${lastAck.received?.model ?? "-"}, fps=${lastAck.received?.fps ?? "-"}`
                : "No ack yet (change model/FPS to test)."}
            </div>
          </div>

          {/* Charts */}
          <div style={{ display: "grid", gap: 12 }}>
            <RewardChart history={history} />
            <LinesChart history={history} />
            <EpisodeRewardChart data={episodeHistory} />

            <div style={{ fontSize: 12, opacity: 0.8 }}>
              episodeHistory points: {episodeHistory.length}{" "}
              {episodeHistory.length ? (
                <>
                  | last:{" "}
                  {episodeHistory[episodeHistory.length - 1].totalReward.toFixed(2)}{" "}
                  (lines {episodeHistory[episodeHistory.length - 1].lines})
                </>
              ) : (
                "| -"
              )}
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div>
          <TetrisBoard board={board} />
        </div>
      </div>
    </div>
  );
}

