import { useState, useEffect, useRef } from "react";

const AGENTS = [
  { id: "concept", icon: "✦", label: "Concept Agent", desc: "Generates story concept & world" },
  { id: "script", icon: "✿", label: "Script Agent", desc: "Writes narration & scene descriptions" },
  { id: "visuals", icon: "◈", label: "Visual Agent", desc: "Creates Ghibli-style image prompts" },
  { id: "metadata", icon: "❋", label: "Metadata Agent", desc: "SEO title, description & tags" },
];

const THEMES = ["Enchanted Forest", "Seaside Village", "Sky Castle", "Mountain Spirit", "Abandoned Station", "Rainy Rooftop"];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const GhibliBackground = () => (
  <div style={{ position: "fixed", inset: 0, zIndex: 0, overflow: "hidden", pointerEvents: "none" }}>
    <div style={{
      position: "absolute", inset: 0,
      background: "linear-gradient(180deg, #0a1628 0%, #0d2240 30%, #1a3a2a 70%, #0f2318 100%)"
    }} />
    {/* Stars */}
    {Array.from({ length: 60 }).map((_, i) => (
      <div key={i} style={{
        position: "absolute",
        width: i % 5 === 0 ? 3 : 1.5,
        height: i % 5 === 0 ? 3 : 1.5,
        borderRadius: "50%",
        background: `rgba(255,255,220,${0.3 + Math.random() * 0.7})`,
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 55}%`,
        animation: `twinkle ${2 + Math.random() * 3}s ease-in-out infinite`,
        animationDelay: `${Math.random() * 4}s`,
      }} />
    ))}
    {/* Moon */}
    <div style={{
      position: "absolute", top: "6%", right: "12%",
      width: 80, height: 80, borderRadius: "50%",
      background: "radial-gradient(circle at 35% 35%, #fffde0, #f5d97a)",
      boxShadow: "0 0 40px 15px rgba(245,217,122,0.25), 0 0 80px 30px rgba(245,217,122,0.1)",
    }} />
    {/* Rolling hills */}
    <svg style={{ position: "absolute", bottom: 0, width: "100%", height: "45%" }} viewBox="0 0 1440 300" preserveAspectRatio="none">
      <path d="M0,200 Q200,120 400,180 Q600,240 800,160 Q1000,80 1200,150 Q1350,200 1440,140 L1440,300 L0,300 Z" fill="#0d2a1a" opacity="0.9" />
      <path d="M0,240 Q180,190 360,220 Q540,250 720,200 Q900,150 1080,210 Q1260,260 1440,220 L1440,300 L0,300 Z" fill="#0a1f14" opacity="1" />
      {/* Trees */}
      {[80, 200, 340, 520, 680, 820, 960, 1100, 1280, 1400].map((x, i) => (
        <g key={i} transform={`translate(${x}, ${180 + (i % 3) * 15})`}>
          <polygon points="0,-45 -18,0 18,0" fill={i % 2 === 0 ? "#0f3d1f" : "#163d28"} />
          <polygon points="0,-65 -14,-20 14,-20" fill={i % 2 === 0 ? "#155a2a" : "#1a4a2e"} />
          <rect x="-4" y="0" width="8" height="20" fill="#0a2010" />
        </g>
      ))}
    </svg>
    {/* Fireflies */}
    {Array.from({ length: 12 }).map((_, i) => (
      <div key={i} style={{
        position: "absolute",
        width: 4, height: 4, borderRadius: "50%",
        background: "rgba(180,255,120,0.9)",
        boxShadow: "0 0 8px 3px rgba(180,255,120,0.5)",
        left: `${10 + Math.random() * 80}%`,
        bottom: `${15 + Math.random() * 25}%`,
        animation: `firefly ${3 + Math.random() * 4}s ease-in-out infinite`,
        animationDelay: `${Math.random() * 5}s`,
      }} />
    ))}
    <style>{`
      @keyframes twinkle { 0%,100%{opacity:0.3} 50%{opacity:1} }
      @keyframes firefly { 0%,100%{opacity:0;transform:translate(0,0)} 30%{opacity:1} 50%{opacity:0.8;transform:translate(${Math.random()>0.5?'':'-'}${10+Math.random()*20}px,${-10-Math.random()*20}px)} 70%{opacity:0.5} }
    `}</style>
  </div>
);

const AgentCard = ({ agent, status, output }) => {
  const colors = { idle: "#2a4a3a", running: "#1a4a6a", done: "#1a5a2a", error: "#5a1a1a" };
  const icons = { idle: "○", running: "◌", done: "●", error: "✕" };
  return (
    <div style={{
      background: `linear-gradient(135deg, ${colors[status]}cc, ${colors[status]}88)`,
      border: `1px solid ${status === "done" ? "#4aff8a44" : status === "running" ? "#4ab8ff44" : "#ffffff11"}`,
      borderRadius: 16,
      padding: "18px 20px",
      transition: "all 0.5s ease",
      position: "relative",
      overflow: "hidden",
    }}>
      {status === "running" && (
        <div style={{
          position: "absolute", top: 0, left: "-100%", width: "100%", height: "100%",
          background: "linear-gradient(90deg, transparent, rgba(74,184,255,0.08), transparent)",
          animation: "shimmer 1.5s infinite",
        }} />
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <span style={{ fontSize: 20, filter: status === "running" ? "drop-shadow(0 0 6px #4ab8ff)" : "none" }}>{agent.icon}</span>
        <div>
          <div style={{ fontFamily: "'Crimson Text', Georgia, serif", fontSize: 15, color: "#e8f4e8", fontWeight: 600 }}>{agent.label}</div>
          <div style={{ fontSize: 11, color: "#88aa88", fontFamily: "monospace" }}>{agent.desc}</div>
        </div>
        <span style={{ marginLeft: "auto", fontSize: 14, color: status === "done" ? "#4aff8a" : status === "running" ? "#4ab8ff" : "#445544" }}>
          {icons[status]}
        </span>
      </div>
      {output && (
        <div style={{
          marginTop: 10, fontSize: 12, color: "#aaccaa", fontFamily: "'Crimson Text', Georgia, serif",
          lineHeight: 1.6, borderTop: "1px solid #ffffff11", paddingTop: 10,
          maxHeight: 120, overflowY: "auto",
        }}>
          {output}
        </div>
      )}
      <style>{`@keyframes shimmer { to { left: 100% } }`}</style>
    </div>
  );
};

export default function GhibliAutomation() {
  const [theme, setTheme] = useState("");
  const [customTheme, setCustomTheme] = useState("");
  const [running, setRunning] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState({ concept: "idle", script: "idle", visuals: "idle", metadata: "idle" });
  const [agentOutputs, setAgentOutputs] = useState({});
  const [finalResult, setFinalResult] = useState(null);
  const [phase, setPhase] = useState("input"); // input | pipeline | result
  const [logLines, setLogLines] = useState([]);
  const logRef = useRef(null);

  const addLog = (msg) => setLogLines(l => [...l, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logLines]);

  const setStatus = (id, s) => setAgentStatuses(prev => ({ ...prev, [id]: s }));
  const setOutput = (id, o) => setAgentOutputs(prev => ({ ...prev, [id]: o }));

  const runPipeline = async () => {
    const topic = customTheme || theme;
    if (!topic) return;
    setRunning(true);
    setPhase("pipeline");
    setLogLines([]);
    setFinalResult(null);
    setAgentOutputs({});
    setAgentStatuses({ concept: "idle", script: "idle", visuals: "idle", metadata: "idle" });

    try {
      addLog(`🎬 Pipeline started for topic: '${topic}'`);
      
      const response = await fetch("https://ghibli-backend-748780382992.us-central1.run.app/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep the last partial line in the buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.replace("data: ", ""));
            
            if (data.status === "done") {
               // The final state will be in the last update before "done"
               // Or we can just wait for it.
            } else if (data.error) {
              throw new Error(data.error);
            } else {
              // LangGraph sends updates per node
              // data = { "node_name": { ...updated_state } }
              const nodeName = Object.keys(data)[0];
              const state = data[nodeName];

              if (nodeName && state) {
                setStatus(nodeName, "done");
                if (state[nodeName]) {
                  setOutput(nodeName, state[nodeName]);
                }
                if (state.logs && state.logs.length > 0) {
                  // Only add the last log if it's new
                  const lastLog = state.logs[state.logs.length - 1];
                  addLog(lastLog);
                }

                // If it's the last agent, set final result
                if (nodeName === "metadata") {
                  setFinalResult({
                    topic,
                    concept: state.concept,
                    script: state.script,
                    visuals: state.visuals,
                    metadata: state.metadata
                  });
                } else {
                  // Set next agent to running
                  const nextAgentMap = { concept: "script", script: "visuals", visuals: "metadata" };
                  if (nextAgentMap[nodeName]) {
                    setStatus(nextAgentMap[nodeName], "running");
                  }
                }
              }
            }
          }
        }
      }

      addLog("🎬 Pipeline complete! Your Ghibli video is ready.");
      await sleep(800);
      setPhase("result");

    } catch (e) {
      console.error("Pipeline error:", e);
      addLog("⚠ Error: " + e.message);
      AGENTS.forEach(a => { if (agentStatuses[a.id] === "running") setStatus(a.id, "error"); });
    }
    setRunning(false);
  };

  const reset = () => {
    setPhase("input");
    setFinalResult(null);
    setAgentOutputs({});
    setAgentStatuses({ concept: "idle", script: "idle", visuals: "idle", metadata: "idle" });
    setLogLines([]);
    setCustomTheme("");
    setTheme("");
  };

  const parseMetadata = (raw) => {
    if (!raw) return {};
    const title = raw.match(/TITLE[:\s]+(.+)/i)?.[1]?.trim() || "";
    const tags = raw.match(/TAGS[:\s]+(.+)/i)?.[1]?.trim() || "";
    const thumbnail = raw.match(/THUMBNAIL[^\n:]*:[:\s]+(.+)/i)?.[1]?.trim() || "";
    return { title, tags, thumbnail };
  };

  return (
    <div style={{ minHeight: "100vh", position: "relative", fontFamily: "'Crimson Text', Georgia, serif" }}>
      <GhibliBackground />

      {/* Google Font */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=Cormorant+Garamond:wght@300;400;600&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a5a3a; border-radius: 2px; }
        .theme-btn:hover { background: rgba(100,200,120,0.15) !important; transform: translateY(-1px); }
        .theme-btn.selected { background: rgba(74,255,138,0.15) !important; border-color: #4aff8a88 !important; }
        .run-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(74,200,100,0.4) !important; }
        .tab-btn:hover { color: #aaddaa !important; }
      `}</style>

      <div style={{ position: "relative", zIndex: 1, maxWidth: 860, margin: "0 auto", padding: "30px 20px 60px" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 13, letterSpacing: 6, color: "#5a9a6a", textTransform: "uppercase", marginBottom: 8, fontFamily: "monospace" }}>
            ✦ AI Video Automation ✦
          </div>
          <h1 style={{
            fontFamily: "'Cormorant Garamond', serif", fontSize: "clamp(2rem, 5vw, 3.2rem)",
            fontWeight: 300, color: "#e8f8e0", margin: "0 0 10px",
            textShadow: "0 0 40px rgba(100,220,120,0.3)",
            letterSpacing: 2,
          }}>
            Ghibli Video Studio
          </h1>
          <p style={{ color: "#6a9a7a", fontSize: 15, margin: 0, fontStyle: "italic" }}>
            Multi-agent pipeline · Concept → Script → Visuals → YouTube
          </p>
        </div>

        {/* INPUT PHASE */}
        {phase === "input" && (
          <div style={{ animation: "fadeIn 0.6s ease" }}>
            <div style={{
              background: "rgba(10,25,18,0.7)", border: "1px solid #1a4a2a",
              borderRadius: 20, padding: 30, backdropFilter: "blur(10px)", marginBottom: 20,
            }}>
              <div style={{ fontSize: 13, color: "#5a9a6a", letterSpacing: 3, textTransform: "uppercase", marginBottom: 16, fontFamily: "monospace" }}>
                Choose Your World
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 20 }}>
                {THEMES.map(t => (
                  <button key={t} className={`theme-btn${theme === t ? " selected" : ""}`} onClick={() => { setTheme(t); setCustomTheme(""); }}
                    style={{
                      background: "rgba(20,50,30,0.6)", border: `1px solid ${theme === t ? "#4aff8a44" : "#1a4a2a"}`,
                      color: theme === t ? "#4aff8a" : "#88bb88", borderRadius: 100, padding: "8px 16px",
                      fontSize: 13, cursor: "pointer", transition: "all 0.2s", fontFamily: "'Crimson Text', serif",
                    }}>
                    {t}
                  </button>
                ))}
              </div>
              <div style={{ fontSize: 12, color: "#4a7a5a", marginBottom: 8, fontFamily: "monospace" }}>— or describe your own —</div>
              <input
                value={customTheme}
                onChange={e => { setCustomTheme(e.target.value); setTheme(""); }}
                placeholder="e.g. A lonely lighthouse keeper who befriends sea spirits..."
                style={{
                  width: "100%", background: "rgba(10,30,18,0.8)", border: "1px solid #1a4a2a",
                  borderRadius: 12, padding: "12px 16px", color: "#c8e8c8", fontSize: 14,
                  fontFamily: "'Crimson Text', serif", outline: "none",
                }}
              />
            </div>

            {/* Agent preview */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 24 }}>
              {AGENTS.map(a => <AgentCard key={a.id} agent={a} status="idle" output={null} />)}
            </div>

            <button className="run-btn" onClick={runPipeline} disabled={!theme && !customTheme}
              style={{
                width: "100%", padding: "16px", borderRadius: 14,
                background: (theme || customTheme) ? "linear-gradient(135deg, #1a5a2a, #2a7a3a)" : "rgba(20,40,25,0.5)",
                border: `1px solid ${(theme || customTheme) ? "#4aff8a33" : "#1a3a1a"}`,
                color: (theme || customTheme) ? "#c8ffd0" : "#3a6a4a",
                fontSize: 16, cursor: (theme || customTheme) ? "pointer" : "not-allowed",
                fontFamily: "'Cormorant Garamond', serif", letterSpacing: 2,
                transition: "all 0.3s", boxShadow: "0 4px 20px rgba(74,200,100,0.2)",
              }}>
              ✦ Begin the Journey ✦
            </button>
            <style>{`@keyframes fadeIn { from { opacity:0; transform: translateY(10px) } to { opacity:1; transform: translateY(0) } }`}</style>
          </div>
        )}

        {/* PIPELINE PHASE */}
        {phase === "pipeline" && (
          <div style={{ animation: "fadeIn 0.5s ease" }}>
            <div style={{ textAlign: "center", marginBottom: 24 }}>
              <div style={{ fontSize: 18, color: "#88cc88", fontStyle: "italic" }}>
                ✦ The spirits are at work... ✦
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14, marginBottom: 20 }}>
              {AGENTS.map(a => (
                <AgentCard key={a.id} agent={a} status={agentStatuses[a.id]} output={agentOutputs[a.id]} />
              ))}
            </div>
            {/* Log */}
            <div ref={logRef} style={{
              background: "rgba(5,15,8,0.9)", border: "1px solid #0a2a14",
              borderRadius: 12, padding: "14px 16px", height: 130, overflowY: "auto",
              fontFamily: "monospace", fontSize: 12, color: "#4a8a5a",
            }}>
              {logLines.map((l, i) => <div key={i} style={{ marginBottom: 4 }}>{l}</div>)}
              {running && <div style={{ color: "#4aff8a", animation: "blink 1s infinite" }}>▌</div>}
            </div>
            <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`}</style>
          </div>
        )}

        {/* RESULT PHASE */}
        {phase === "result" && finalResult && (
          <ResultPanel result={finalResult} onReset={reset} parseMetadata={parseMetadata} />
        )}
      </div>
    </div>
  );
}

function ResultPanel({ result, onReset, parseMetadata }) {
  const [tab, setTab] = useState("script");
  const meta = parseMetadata(result.metadata);
  const tabs = [
    { id: "script", label: "✿ Script" },
    { id: "visuals", label: "◈ Visuals" },
    { id: "metadata", label: "❋ YouTube" },
  ];

  return (
    <div style={{ animation: "fadeIn 0.6s ease" }}>
      {/* Hero card */}
      <div style={{
        background: "linear-gradient(135deg, rgba(20,60,30,0.9), rgba(10,30,20,0.9))",
        border: "1px solid #2a6a3a", borderRadius: 20, padding: "24px 28px", marginBottom: 20,
        backdropFilter: "blur(10px)",
      }}>
        <div style={{ fontSize: 11, color: "#4a8a5a", letterSpacing: 4, textTransform: "uppercase", fontFamily: "monospace", marginBottom: 6 }}>
          ✦ Video Ready
        </div>
        <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "1.6rem", color: "#d0ffd8", fontWeight: 400, marginBottom: 6 }}>
          {meta.title || result.topic}
        </div>
        {meta.thumbnail && (
          <div style={{
            display: "inline-block", background: "rgba(74,255,138,0.12)", border: "1px solid #4aff8a33",
            borderRadius: 8, padding: "4px 12px", fontSize: 13, color: "#4aff8a", marginBottom: 10,
          }}>
            🖼 Thumbnail: {meta.thumbnail}
          </div>
        )}
        <div style={{ fontSize: 13, color: "#6a9a7a", fontStyle: "italic" }}>{result.concept?.slice(0, 140)}...</div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 16 }}>
        {tabs.map(t => (
          <button key={t.id} className="tab-btn" onClick={() => setTab(t.id)} style={{
            flex: 1, padding: "10px", borderRadius: 10,
            background: tab === t.id ? "rgba(40,100,50,0.5)" : "rgba(10,25,15,0.5)",
            border: `1px solid ${tab === t.id ? "#3a8a4a" : "#1a3a1a"}`,
            color: tab === t.id ? "#9aee9a" : "#4a7a5a",
            fontSize: 13, cursor: "pointer", fontFamily: "'Crimson Text', serif",
            transition: "all 0.2s",
          }}>{t.label}</button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{
        background: "rgba(8,20,12,0.85)", border: "1px solid #1a4a2a",
        borderRadius: 16, padding: 24, minHeight: 280, backdropFilter: "blur(8px)",
        marginBottom: 20,
      }}>
        {tab === "script" && (
          <pre style={{ whiteSpace: "pre-wrap", color: "#b8e8b8", fontSize: 13, lineHeight: 1.8, margin: 0, fontFamily: "'Crimson Text', serif" }}>
            {result.script}
          </pre>
        )}
        {tab === "visuals" && (
          <div>
            <div style={{ fontSize: 12, color: "#4a8a5a", fontFamily: "monospace", marginBottom: 16 }}>
              ◈ Copy these prompts into Midjourney, DALL-E, or Stable Diffusion
            </div>
            <pre style={{ whiteSpace: "pre-wrap", color: "#b8e8b8", fontSize: 13, lineHeight: 1.8, margin: 0, fontFamily: "'Crimson Text', serif" }}>
              {result.visuals}
            </pre>
          </div>
        )}
        {tab === "metadata" && (
          <pre style={{ whiteSpace: "pre-wrap", color: "#b8e8b8", fontSize: 13, lineHeight: 1.8, margin: 0, fontFamily: "'Crimson Text', serif" }}>
            {result.metadata}
          </pre>
        )}
      </div>

      {/* Next steps */}
      <div style={{
        background: "rgba(8,20,12,0.7)", border: "1px solid #1a3a2a",
        borderRadius: 16, padding: "18px 22px", marginBottom: 20,
      }}>
        <div style={{ fontSize: 12, color: "#4a8a5a", letterSpacing: 3, textTransform: "uppercase", fontFamily: "monospace", marginBottom: 12 }}>
          Next Steps
        </div>
        {[
          ["1", "Generate images", "Use the Visual Agent prompts in Midjourney or DALL-E 3"],
          ["2", "Add narration", "Run the script through ElevenLabs or OpenAI TTS"],
          ["3", "Assemble video", "Combine images + audio in CapCut, Premiere, or RunwayML"],
          ["4", "Upload", "Paste the metadata directly into YouTube Studio"],
        ].map(([n, title, desc]) => (
          <div key={n} style={{ display: "flex", gap: 14, marginBottom: 12, alignItems: "flex-start" }}>
            <div style={{
              width: 24, height: 24, borderRadius: "50%", background: "rgba(74,200,100,0.2)",
              border: "1px solid #2a6a3a", display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, color: "#4aff8a", flexShrink: 0, fontFamily: "monospace",
            }}>{n}</div>
            <div>
              <div style={{ color: "#9add9a", fontSize: 14, fontWeight: 600 }}>{title}</div>
              <div style={{ color: "#5a8a6a", fontSize: 12 }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      <button onClick={onReset} style={{
        width: "100%", padding: 14, borderRadius: 12,
        background: "rgba(15,35,20,0.8)", border: "1px solid #2a5a3a",
        color: "#6a9a7a", fontSize: 15, cursor: "pointer",
        fontFamily: "'Cormorant Garamond', serif", letterSpacing: 2,
        transition: "all 0.2s",
      }}>
        ✦ Create Another Video ✦
      </button>
      <style>{`@keyframes fadeIn { from { opacity:0; transform: translateY(12px) } to { opacity:1; transform: translateY(0) } }`}</style>
    </div>
  );
}
