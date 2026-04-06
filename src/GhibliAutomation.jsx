import { useState, useEffect, useRef } from "react";
import { CheckCircle2, AlertCircle, Sparkles, Plus, Trash2, Layout, Video, Image as ImageIcon, Send, Clock, Play, Download, Search, Settings, User, LogOut, ExternalLink, Bookmark, Share2, Info, ChevronRight, Menu, X, Terminal, Monitor, Tablet, Phone, Type, Layers, Eye } from 'lucide-react';
import GhibliTitleCard from './components/GhibliTitleCard';

const AGENTS = [
  { id: "concept", icon: "✦", label: "Concept Agent", desc: "Generates story concept & world" },
  { id: "script", icon: "✿", label: "Script Agent", desc: "Writes narration & scene descriptions" },
  { id: "visuals", icon: "◈", label: "Visual Agent", desc: "Creates image prompts" },
  { id: "metadata", icon: "❋", label: "Metadata Agent", desc: "SEO title, description & tags" },
  { id: "production", icon: "🎬", label: "Production Agent", desc: "Generates assets and renders MP4" },
];

const THEMES = ["Enchanted Forest", "Seaside Village", "Sky Castle", "Mountain Spirit", "Abandoned Station", "Rainy Rooftop"];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const GhibliBackground = () => (
  <div style={{ position: "fixed", inset: 0, zIndex: 0, overflow: "hidden", pointerEvents: "none" }}>
    <div style={{
      position: "absolute", inset: "-5%", width: "110%", height: "110%",
      backgroundImage: "url('/ghibli_bg.png')",
      backgroundSize: "cover",
      backgroundPosition: "center",
      filter: "brightness(0.65) saturate(1.2)",
      animation: "subtlePan 30s ease-in-out infinite alternate"
    }} />
    <div style={{
      position: "absolute", inset: 0,
      background: "linear-gradient(180deg, rgba(13,34,64,0.4) 0%, rgba(15,35,24,0.7) 100%)"
    }} />
    {Array.from({ length: 40 }).map((_, i) => (
      <div key={i} style={{
        position: "absolute",
        width: 4, height: 4, borderRadius: "50%",
        background: "rgba(180,255,120,0.9)",
        boxShadow: "0 0 12px 4px rgba(180,255,120,0.6)",
        left: `${10 + Math.random() * 80}%`,
        bottom: `${5 + Math.random() * 40}%`,
        animation: `firefly ${3 + Math.random() * 4}s ease-in-out infinite`,
        animationDelay: `${Math.random() * 5}s`,
      }} />
    ))}
    <style>{`
      @keyframes subtlePan { from { transform: scale(1) translate(0, 0); } to { transform: scale(1.05) translate(-1%, 1%); } }
      @keyframes firefly { 0%,100%{opacity:0;transform:translate(0,0)} 30%{opacity:1} 50%{opacity:0.8;transform:translate(${Math.random()>0.5?'':'-'}${10+Math.random()*20}px,${-10-Math.random()*20}px)} 70%{opacity:0.5} }
    `}</style>
  </div>
);

const AgentCard = ({ agent, status, output }) => {
  const colors = { idle: "rgba(30, 50, 40, 0.4)", running: "rgba(20, 80, 120, 0.6)", done: "rgba(40, 110, 60, 0.6)", error: "rgba(120, 30, 30, 0.6)" };
  const borderColors = { idle: "rgba(255,255,255,0.08)", running: "rgba(74, 184, 255, 0.5)", done: "rgba(74, 255, 138, 0.5)", error: "rgba(255, 74, 74, 0.5)" };
  const icons = { idle: "○", running: "◌", done: "●", error: "✕" };
  
  return (
    <div style={{
      background: colors[status],
      backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
      border: `1px solid ${borderColors[status]}`,
      borderRadius: 20, padding: "20px 24px",
      transition: "all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
      position: "relative", overflow: "hidden",
      boxShadow: status === "running" ? "0 10px 40px rgba(0,0,0,0.3), inset 0 0 20px rgba(74, 184, 255, 0.2)" : "0 4px 15px rgba(0,0,0,0.2)",
      transform: status === "running" ? "translateY(-4px) scale(1.02)" : "translateY(0) scale(1)",
    }}>
      {status === "running" && (
        <div style={{
          position: "absolute", top: 0, left: "-100%", width: "100%", height: "100%",
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)",
          animation: "shimmer 2s infinite",
        }} />
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 8 }}>
        <div style={{ 
          display: "flex", alignItems: "center", justifyContent: "center",
          width: 42, height: 42, borderRadius: "50%",
          background: "rgba(0,0,0,0.2)", border: `1px solid ${borderColors[status]}`,
          fontSize: 20, textShadow: status === "running" ? "0 0 10px #4ab8ff" : "none" 
        }}>
          {agent.icon}
        </div>
        <div>
          <div style={{ fontFamily: "'Outfit', sans-serif", fontSize: 16, color: "#ffffff", fontWeight: 600, letterSpacing: 0.5 }}>{agent.label}</div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", fontFamily: "'Inter', sans-serif" }}>{agent.desc}</div>
        </div>
        <span style={{ marginLeft: "auto", fontSize: 16, color: status === "done" ? "#4aff8a" : status === "running" ? "#4ab8ff" : "rgba(255,255,255,0.3)" }}>
          {icons[status]}
        </span>
      </div>
      {output && (
        <div style={{
          marginTop: 14, fontSize: 13, color: "rgba(255,255,255,0.85)", fontFamily: "'Inter', sans-serif",
          lineHeight: 1.6, borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: 14,
          maxHeight: 140, overflowY: "auto", paddingRight: 4,
        }}>
          {output}
        </div>
      )}
      <style>{`@keyframes shimmer { to { left: 100% } }`}</style>
    </div>
  );
};

import Auth from './components/Auth';
import { supabase } from './lib/supabaseClient';

export default function GhibliAutomation() {
  const [user, setUser] = useState(null);
  const [authInitialized, setAuthInitialized] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [theme, setTheme] = useState("");
  const [customTheme, setCustomTheme] = useState("");
  const [numScenes, setNumScenes] = useState(5);
  const [generateVideo, setGenerateVideo] = useState(false);
  const [running, setRunning] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState({ concept: "idle", script: "idle", visuals: "idle", metadata: "idle", production: "idle" });
  const [agentOutputs, setAgentOutputs] = useState({});
  const [finalResult, setFinalResult] = useState(null);
  const [phase, setPhase] = useState("input");
  const [logLines, setLogLines] = useState([]);
  const logRef = useRef(null);
  const [galleryData, setGalleryData] = useState([]);
  const [loadingGallery, setLoadingGallery] = useState(false);
  const [selectedGalleryItem, setSelectedGalleryItem] = useState(null);

  const addLog = (msg) => setLogLines(l => [...l, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  useEffect(() => {
    // Check initial session
    const initAuth = async () => {
      try {
        if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
          throw new Error("Missing Supabase configuration. Check your VITE_ environment variables.");
        }
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) throw error;
        setUser(session?.user ?? null);
        setAuthInitialized(true);
      } catch (err) {
        console.error("Auth init error:", err);
        setAuthError(err.message);
        setAuthInitialized(true);
      }
    };
    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  const fetchGallery = async () => {
    setLoadingGallery(true);
    setPhase("gallery");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const response = await fetch("https://ghibli-backend-bskf4s232a-uc.a.run.app/generations", {
        headers: {
          Authorization: `Bearer ${session?.access_token}`
        }
      });
      const data = await response.json();
      setGalleryData(data.data || []);
    } catch (e) {
      console.error("Failed to fetch gallery", e);
    } finally {
      setLoadingGallery(false);
    }
  };

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
    setAgentStatuses({ concept: "idle", script: "idle", visuals: "idle", metadata: "idle", production: "idle" });

    try {
      addLog(`🎬 Pipeline started for topic: '${topic}'`);
      let accumulatedState = { topic, concept: "", script: "", visuals: "", metadata: "", image_urls: [], audio_urls: [], video_url: "" };
      
      const { data: { session } } = await supabase.auth.getSession();
      const response = await fetch("https://ghibli-backend-bskf4s232a-uc.a.run.app/generate", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({ topic, numScenes, generateVideo }),
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
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          
          try {
            const rawJson = line.replace("data: ", "").trim();
            if (!rawJson) continue;
            
            const data = JSON.parse(rawJson);
            if (data.status === "done") continue;
            if (data.error) throw new Error(data.error);

            Object.entries(data).forEach(([nodeName, delta]) => {
              if (!delta || typeof delta !== 'object') return;

              accumulatedState = { ...accumulatedState, ...delta };
              setStatus(nodeName, "done");
              
              if (delta[nodeName]) setOutput(nodeName, delta[nodeName]);
              if (Array.isArray(delta.logs)) delta.logs.forEach(l => addLog(l));

              if (nodeName === "production") {
                // Keep the final result state updated
                setFinalResult({ ...accumulatedState });
              } else {
                const nextAgentMap = { concept: "script", script: "visuals", visuals: "metadata", metadata: "production" };
                const next = nextAgentMap[nodeName];
                if (next) setStatus(next, "running");
              }
            });

          } catch (jsonErr) {
            console.error("❌ Data Processing Error:", jsonErr, "Line:", line);
          }
        }
      }

      // Important: Verify the pipeline actually finished
      // If video generation was skipped, we just check if it returned a successful status without ERROR.
      // If video generation was checked, we check if video_url exists to confirm the production node completed
      if (accumulatedState.video_url === "ERROR") {
         throw new Error("Production Agent failed to render the video. Check the logs above for API issues.");
      }
      
      const isComplete = !generateVideo || Boolean(accumulatedState.video_url);

      if (isComplete) {
         setFinalResult({ ...accumulatedState });
         addLog("🎬 Pipeline complete! Your Ghibli video is ready.");
         await sleep(1500);
         setPhase("result");
         // Default to images tab if video was not generated
         if (!generateVideo) {
            setTimeout(() => {
                const imagesTabBtn = document.getElementById("tab-btn-images");
                if (imagesTabBtn) imagesTabBtn.click();
            }, 100);
         }
      } else {
         throw new Error("Connection dropped. The server might have timed out during video generation. Please check GCP logs or try a shorter video.");
      }

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
    setSelectedGalleryItem(null);
    setAgentOutputs({});
    setAgentStatuses({ concept: "idle", script: "idle", visuals: "idle", metadata: "idle", production: "idle" });
    setLogLines([]);
    setCustomTheme("");
    setTheme("");
  };

  const parseMetadata = (raw) => {
    if (!raw) return {};
    // If it's already an object (from DB), return it
    if (typeof raw === 'object') {
      return {
        title: raw.title || "",
        tags: Array.isArray(raw.tags) ? raw.tags.join(", ") : (raw.tags || ""),
        thumbnail: raw.thumbnail || ""
      };
    }
    // Otherwise parse string from pipeline
    const title = raw.match(/TITLE[:\s]+(.+)/i)?.[1]?.trim() || "";
    const tags = raw.match(/TAGS[:\s]+(.+)/i)?.[1]?.trim() || "";
    const thumbnail = raw.match(/THUMBNAIL[^ \n:]*:[:\s]+(.+)/i)?.[1]?.trim() || "";
    return { title, tags, thumbnail };
  };

  if (!authInitialized) return null;
  if (authError) return (
    <div style={{ color: "#ff4a8a", padding: 50, textAlign: "center", background: "#0f0f1b", minHeight: "100vh", fontFamily: "'Outfit', sans-serif" }}>
      <h2 style={{ fontSize: "2rem", marginBottom: 20 }}>🚨 Studio Configuration Error</h2>
      <div style={{ background: "rgba(255,255,255,0.05)", padding: 30, borderRadius: 24, border: "1px solid rgba(255,255,255,0.1)", maxWidth: 600, margin: "0 auto" }}>
        <p style={{ fontSize: 18, marginBottom: 20 }}>{authError}</p>
        <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 14, lineHeight: 1.6 }}>
          Please check your environment variables.
        </p>
      </div>
    </div>
  );
  if (!user) return <Auth onLogin={setUser} />;

  return (
    <div style={{ minHeight: "100vh", position: "relative", color: "#fff", display: "flex", flexDirection: "column" }}>
      <div style={{ position: "absolute", top: 20, right: 30, zIndex: 10, display: "flex", alignItems: "center", gap: 15 }}>
        <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>{user.email}</div>
        <button onClick={handleSignOut} style={{
          background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
          color: "rgba(255,255,255,0.7)", padding: "8px 16px", borderRadius: 12, cursor: "pointer",
          fontSize: 13, transition: "all 0.2s"
        }} onMouseEnter={e => e.target.style.background = "rgba(255,74,138,0.1)"} onMouseLeave={e => e.target.style.background = "rgba(255,255,255,0.05)"}>
          Sign Out
        </button>
      </div>
      <GhibliBackground />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.4); }
        .theme-btn:hover { background: rgba(255,255,255,0.1) !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .theme-btn.selected { background: rgba(74,255,138,0.2) !important; border-color: rgba(74,255,138,0.5) !important; color: #fff !important; }
        .run-btn {
          background: linear-gradient(135deg, rgba(74,255,138,0.8), rgba(46,204,113,0.9));
          box-shadow: 0 4px 15px rgba(46,204,113,0.3);
        }
        .run-btn:hover:not(:disabled) { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(46,204,113,0.5); filter: brightness(1.1); }
        .tab-btn:hover { background: rgba(255,255,255,0.1) !important; }
        body { margin: 0; background: #0a0a0a; }
      `}</style>

      <div style={{ position: "relative", zIndex: 1, flex: 1, display: "flex", flexDirection: "column", maxWidth: 900, margin: "0 auto", width: "100%", padding: "40px 20px" }}>
        
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 50 }}>
          <div style={{ display: "inline-block", background: "rgba(255,255,255,0.1)", backdropFilter: "blur(8px)", padding: "6px 16px", borderRadius: 100, fontSize: 12, letterSpacing: 3, textTransform: "uppercase", marginBottom: 16, fontFamily: "'Inter', sans-serif", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>
            ✦ AI Video Automation ✦
          </div>
          <h1 style={{
            fontFamily: "'Outfit', sans-serif", fontSize: "clamp(2.5rem, 6vw, 4rem)",
            fontWeight: 700, margin: "0 0 16px", letterSpacing: -1,
            background: "linear-gradient(to right, #ffffff, #a8ffb2)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.3))"
          }}>
            Video Studio
          </h1>
          <p style={{ color: "rgba(255,255,255,0.7)", fontSize: 18, margin: 0, fontFamily: "'Inter', sans-serif", fontWeight: 300 }}>
            Multi-agent pipeline from Concept directly to YouTube.
          </p>
        </div>

        {/* INPUT PHASE */}
        {phase === "input" && (
          <div style={{ animation: "fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1)" }}>
            <div style={{
              background: "rgba(10, 15, 20, 0.5)", backdropFilter: "blur(24px)", WebkitBackdropFilter: "blur(24px)",
              border: "1px solid rgba(255,255,255,0.08)", borderRadius: 24, padding: 40, marginBottom: 30,
              boxShadow: "0 20px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
            }}>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", letterSpacing: 2, textTransform: "uppercase", marginBottom: 20, fontFamily: "'Inter', sans-serif", fontWeight: 600 }}>
                Choose Your World
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 30 }}>
                {THEMES.map(t => (
                  <button key={t} className={`theme-btn${theme === t ? " selected" : ""}`} onClick={() => { setTheme(t); setCustomTheme(""); }}
                    style={{
                      background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
                      color: "rgba(255,255,255,0.8)", borderRadius: 100, padding: "10px 20px",
                      fontSize: 14, cursor: "pointer", transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)", fontFamily: "'Inter', sans-serif", fontWeight: 500
                    }}>
                    {t}
                  </button>
                ))}
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
                <div style={{ height: 1, flex: 1, background: "rgba(255,255,255,0.1)" }} />
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", fontFamily: "'Inter', sans-serif", fontWeight: 500, textTransform: "uppercase", letterSpacing: 1 }}>Or Create Custom</div>
                <div style={{ height: 1, flex: 1, background: "rgba(255,255,255,0.1)" }} />
              </div>
              
              <input
                value={customTheme}
                onChange={e => { setCustomTheme(e.target.value); setTheme(""); }}
                placeholder="e.g. A lonely lighthouse keeper who befriends sea spirits..."
                style={{
                  width: "100%", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.15)",
                  borderRadius: 16, padding: "18px 20px", color: "#fff", fontSize: 16,
                  fontFamily: "'Inter', sans-serif", outline: "none", transition: "all 0.3s",
                  boxShadow: "inset 0 2px 10px rgba(0,0,0,0.2)", marginBottom: 20
                }}
                onFocus={(e) => e.target.style.borderColor = "rgba(74,255,138,0.5)"}
                onBlur={(e) => e.target.style.borderColor = "rgba(255,255,255,0.15)"}
              />
              
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", letterSpacing: 2, textTransform: "uppercase", marginBottom: 10, fontFamily: "'Inter', sans-serif", fontWeight: 600 }}>
                  Number of Scenes
                </div>
                <input 
                  type="number" min="1"
                  value={numScenes} 
                  onChange={e => setNumScenes(parseInt(e.target.value) || 5)} 
                  style={{ 
                    width: "100%", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.15)", 
                    borderRadius: 16, padding: "12px 20px", color: "#fff", fontSize: 16, fontFamily: "'Inter', sans-serif", outline: "none" 
                  }} 
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 40 }}>
              {AGENTS.map(a => <AgentCard key={a.id} agent={a} status="idle" output={null} />)}
            </div>

            <div style={{ display: "flex", gap: 12 }}>
              <button className="run-btn" onClick={runPipeline} disabled={!theme && !customTheme}
                style={{
                  flex: 2, padding: "20px", borderRadius: 20,
                  border: "none", color: "#000", fontSize: 18, fontWeight: 700,
                  cursor: (theme || customTheme) ? "pointer" : "not-allowed",
                  fontFamily: "'Outfit', sans-serif", letterSpacing: 1,
                  transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                  opacity: (theme || customTheme) ? 1 : 0.5,
                }}>
                Launch Mission
              </button>
              <button onClick={fetchGallery}
                style={{
                  flex: 1, padding: "20px", borderRadius: 20,
                  background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)",
                  color: "#fff", fontSize: 16, fontWeight: 600,
                  cursor: "pointer", fontFamily: "'Outfit', sans-serif",
                  transition: "all 0.3s",
                }}
                onMouseEnter={e => e.target.style.background = "rgba(255,255,255,0.15)"}
                onMouseLeave={e => e.target.style.background = "rgba(255,255,255,0.1)"}>
                Explore Gallery
              </button>
            </div>
            <style>{`@keyframes fadeInUp { from { opacity:0; transform: translateY(20px) } to { opacity:1; transform: translateY(0) } }`}</style>
          </div>
        )}

        {/* PIPELINE PHASE */}
        {phase === "pipeline" && (
          <div style={{ animation: "fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)", flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ textAlign: "center", marginBottom: 30 }}>
              <div style={{ fontSize: 20, color: "rgba(255,255,255,0.9)", fontFamily: "'Outfit', sans-serif", fontWeight: 500, display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
                {running && <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: "#4ab8ff", animation: "pulse 1.5s infinite" }} />}
                {running ? "The agents are orchestrating..." : "Pipeline execution halted"}
              </div>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20, marginBottom: 30 }}>
              {AGENTS.map(a => (
                <AgentCard key={a.id} agent={a} status={agentStatuses[a.id]} output={agentOutputs[a.id]} />
              ))}
            </div>
            
            {/* Log Window */}
            <div style={{
              background: "rgba(0,0,0,0.6)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.05)", borderRadius: 20, padding: "20px 24px",
              height: 180, overflowY: "auto", fontFamily: "'SF Mono', Consolas, monospace", fontSize: 13, color: "rgba(255,255,255,0.7)",
              marginTop: "auto", boxShadow: "inset 0 4px 20px rgba(0,0,0,0.4)"
            }}>
              <div style={{ marginBottom: 12, color: "rgba(255,255,255,0.4)", fontSize: 11, textTransform: "uppercase", letterSpacing: 2 }}>Terminal Output</div>
              {logLines.map((l, i) => <div key={i} style={{ marginBottom: 6, lineHeight: 1.5 }}>{l}</div>)}
              {running && <div style={{ color: "#4aff8a", animation: "blink 1s infinite" }}>_</div>}
            </div>
            <style>{`
              @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
              @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(74, 184, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(74, 184, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(74, 184, 255, 0); } }
            `}</style>
          </div>
        )}

        {/* RESULT PHASE */}
        {phase === "result" && finalResult && (
          <ResultPanel result={finalResult} onReset={reset} parseMetadata={parseMetadata} />
        )}

        {/* GALLERY PHASE */}
        {phase === "gallery" && (
          selectedGalleryItem ? (
            <ResultPanel 
              result={selectedGalleryItem} 
              onReset={() => setSelectedGalleryItem(null)} 
              parseMetadata={parseMetadata}
              isGalleryView={true}
            />
          ) : (
            <GalleryPanel 
              data={galleryData} 
              loading={loadingGallery} 
              onReset={reset} 
              onViewScenes={(item) => setSelectedGalleryItem(item)}
            />
          )
        )}
      </div>
    </div>
  );
}

function GalleryPanel({ data, loading, onReset, onViewScenes }) {
  return (
    <div style={{ animation: "fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 30 }}>
        <div style={{ fontSize: "2rem", color: "#fff", fontWeight: 600, fontFamily: "'Outfit', sans-serif" }}>
          Public Archive
        </div>
        <button onClick={onReset} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "#fff", padding: "10px 20px", borderRadius: 12, cursor: "pointer", fontSize: 14 }}>
          ← Back to Studio
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "100px 0", color: "rgba(255,255,255,0.5)" }}>
          Loading the vault...
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 24 }}>
          {data.map((item, idx) => (
            <div key={idx} style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 24, padding: 20, display: "flex", flexDirection: "column" }}>
              <div style={{ position: "relative", marginBottom: 16 }}>
                <img src={item.image_urls?.[0]} style={{ width: "100%", height: 180, objectFit: "cover", borderRadius: 16 }} />
                <div style={{ position: "absolute", top: 12, left: 12, background: "rgba(0,0,0,0.6)", padding: "4px 10px", borderRadius: 8, fontSize: 10, color: "#fff", backdropFilter: "blur(4px)", textTransform: "uppercase", letterSpacing: 1 }}>
                  {item.source === "reddit" ? "🤖 Automated" : "👤 Manual"}
                </div>
              </div>
              <div style={{ fontSize: 18, color: "#fff", fontWeight: 600, marginBottom: 8, fontFamily: "'Outfit', sans-serif" }}>
                {item.topic}
              </div>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", marginBottom: 16, lineHeight: 1.4, flex: 1 }}>
                {item.concept.slice(0, 100)}...
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                {item.video_url && (
                  <a href={item.video_url} target="_blank" rel="noopener noreferrer" style={{ flex: 1, textAlign: "center", background: "linear-gradient(135deg, #4ab8ff, #4aff8a)", color: "#000", padding: "10px", borderRadius: 12, textDecoration: "none", fontSize: 14, fontWeight: 600 }}>
                    Watch Video
                  </a>
                )}
                <button onClick={() => onViewScenes(item)} style={{ flex: 1, background: "rgba(255,255,255,0.1)", color: "#fff", border: "none", padding: "10px", borderRadius: 12, fontSize: 14, cursor: "pointer" }}>
                  View Scenes
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ResultPanel({ result, onReset, parseMetadata, isGalleryView }) {
  const [tab, setTab] = useState("images");
  const [showCinematic, setShowCinematic] = useState(false);
  const meta = parseMetadata(result.metadata);
  
  const visualPromptsList = (typeof result.visuals === 'string') 
    ? result.visuals.split('\n').filter(line => line.trim() && (line.trim().charAt(0) >= '0' && line.trim().charAt(0) <= '9' || line.trim().startsWith('-')))
    : [];

  const tabs = [
    { id: "images", label: "🖼️ Scenes" },
    { id: "metadata", label: "❋ YouTube Meta" },
    { id: "visuals", label: "◈ Prompts" },
    { id: "script", label: "✿ Script" },
  ];

  return (
    <div style={{ animation: "fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)" }}>
      {/* Header Summary Card */}
      <div style={{
        background: "rgba(255,255,255,0.05)", backdropFilter: "blur(24px)", WebkitBackdropFilter: "blur(24px)",
        border: "1px solid rgba(255,255,255,0.1)", borderRadius: 24, padding: "30px 40px", marginBottom: 24,
        boxShadow: "0 20px 40px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.1)",
      }}>
        <div style={{ fontSize: 12, color: "#4aff8a", letterSpacing: 3, textTransform: "uppercase", fontFamily: "'Inter', sans-serif", fontWeight: 600, marginBottom: 12 }}>
          ✦ Output Ready
        </div>
        <div style={{ fontFamily: "'Outfit', sans-serif", fontSize: "2.2rem", color: "#ffffff", fontWeight: 600, marginBottom: 12, lineHeight: 1.2 }}>
          {meta.title || result.topic}
        </div>
        {meta.thumbnail && (
          <div style={{
            display: "inline-block", background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 100, padding: "6px 16px", fontSize: 14, color: "rgba(255,255,255,0.9)", marginBottom: 16,
            fontFamily: "'Inter', sans-serif"
          }}>
            🖼 Thumbnail: {meta.thumbnail}
          </div>
        )}
        <div style={{ fontSize: 15, color: "rgba(255,255,255,0.6)", fontFamily: "'Inter', sans-serif", lineHeight: 1.6 }}>{result.concept}</div>
      </div>

      {/* Tabs and Toggles */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 8 }}>
          {tabs.map(t => (
            <button key={t.id} className="tab-btn" onClick={() => setTab(t.id)} style={{
              padding: "14px 20px", borderRadius: 16,
              background: tab === t.id ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.3)",
              border: "1px solid",
              borderColor: tab === t.id ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.05)",
              color: tab === t.id ? "#fff" : "rgba(255,255,255,0.5)",
              fontSize: 14, fontWeight: tab === t.id ? 600 : 400, cursor: "pointer", fontFamily: "'Inter', sans-serif",
              transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
            }}>{t.label}</button>
          ))}
        </div>
        
        {tab === "images" && (
          <button 
            onClick={() => setShowCinematic(!showCinematic)}
            style={{
              padding: "12px 20px", borderRadius: 16,
              background: showCinematic ? "linear-gradient(135deg, #bd93f9, #ff79c6)" : "rgba(189,147,249,0.1)",
              border: "1px solid",
              borderColor: showCinematic ? "#bd93f9" : "rgba(189,147,249,0.3)",
              color: showCinematic ? "#fff" : "#bd93f9",
              fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "'Inter', sans-serif",
              display: "flex", alignItems: "center", gap: 8, transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
            }}
          >
            {showCinematic ? <Eye size={16} /> : <Sparkles size={16} />}
            {showCinematic ? "Disable Preview" : "🎬 Cinematic Title Preview"}
          </button>
        )}
      </div>

      {/* Main Content Area */}
      <div style={{
        background: "rgba(0,0,0,0.5)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.1)", borderRadius: 24, padding: 30, minHeight: 450,
        marginBottom: 30, boxShadow: "inset 0 4px 20px rgba(0,0,0,0.4)",
      }}>
        {/* IMAGES TAB */}
        {tab === "images" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
            {showCinematic && result.image_urls?.[0] && (
              <div style={{ animation: "fadeInDown 0.5s cubic-bezier(0.16, 1, 0.3, 1)" }}>
                <div style={{ marginBottom: 16, color: "rgba(189,147,249,0.8)", fontSize: 11, textTransform: "uppercase", letterSpacing: 2, fontWeight: 600 }}>
                  🎥 Kinetic Typography Preview (Pretext API)
                </div>
                <GhibliTitleCard 
                  text={meta.title || result.topic} 
                  imageUrl={result.image_urls[0]} 
                  width={1280} 
                  height={720}
                />
              </div>
            )}
            
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 20 }}>
              {result.image_urls && result.image_urls.length > 0 ? (
                result.image_urls.map((url, i) => (
                  <div key={i} style={{ position: "relative", background: "rgba(255,255,255,0.05)", borderRadius: 16, padding: 12, border: "1px solid rgba(255,255,255,0.1)", display: "flex", flexDirection: "column" }}>
                    <img src={url} alt={`Scene ${i+1}`} style={{ width: "100%", borderRadius: 8, marginBottom: 12 }} />
                    <div style={{ marginTop: "auto" }}>
                      <a href={url} download={`scene_${i+1}.png`} target="_blank" rel="noopener noreferrer" style={{ display: "block", textAlign: "center", background: "rgba(74,255,138,0.2)", color: "#4aff8a", textDecoration: "none", padding: "8px", borderRadius: 8, fontFamily: "'Inter', sans-serif", fontSize: 13, fontWeight: 500, transition: "background 0.2s" }} onMouseEnter={e=>e.target.style.background="rgba(74,255,138,0.3)"} onMouseLeave={e=>e.target.style.background="rgba(74,255,138,0.2)"}>Download Image</a>
                      {visualPromptsList[i] && (
                        <>
                          <button onClick={() => {
                            const basePrompt = visualPromptsList[i].replace(/^[\d\.\-\s]+/, '');
                            const videoPrompt = `${basePrompt} -- subtle cinematic motion, slow panning, high quality animation.`;
                            navigator.clipboard.writeText(videoPrompt);
                            alert("Video Prompt Copied!\n\n" + videoPrompt);
                          }} style={{ display: "block", width: "100%", textAlign: "center", background: "rgba(255,255,255,0.1)", color: "#fff", border: "none", padding: "10px", borderRadius: 8, fontFamily: "'Inter', sans-serif", fontSize: 13, marginTop: 8, cursor: "pointer", transition: "all 0.2s" }} onMouseEnter={e=>e.target.style.background="rgba(255,255,255,0.15)"} onMouseLeave={e=>e.target.style.background="rgba(255,255,255,0.1)"}>Copy Video Prompt</button>
                        </>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ gridColumn: "1 / -1", padding: "80px 0", textAlign: "center", color: "rgba(255,255,255,0.5)", fontFamily: "'Inter', sans-serif" }}>Images not available.</div>
              )}
            </div>
          </div>
        )}

        {/* SCRIPT TAB */}
        {tab === "script" && (
          <pre style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.85)", fontSize: 15, lineHeight: 1.8, margin: 0, fontFamily: "'Inter', sans-serif" }}>
            {result.script || "◈ Creative script data not available for this archived generation."}
          </pre>
        )}

        {/* PROMPTS TAB */}
        {tab === "visuals" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div style={{ fontSize: 13, color: "rgba(74,255,138,0.8)", fontFamily: "'Inter', sans-serif", textTransform: "uppercase", letterSpacing: 1 }}>
                ◈ Visual Prompt Library
              </div>
              <button onClick={() => {
                navigator.clipboard.writeText(result.visuals);
                alert("Prompts copied to clipboard!");
              }} style={{ background: "rgba(74,255,138,0.2)", border: "1px solid rgba(74,255,138,0.5)", color: "#4aff8a", padding: "6px 16px", borderRadius: 100, cursor: "pointer", fontFamily: "'Inter', sans-serif", fontSize: 13, transition: "all 0.2s" }} onMouseEnter={e=>e.target.style.background="rgba(74,255,138,0.3)"} onMouseLeave={e=>e.target.style.background="rgba(74,255,138,0.2)"}>
                Copy All Prompts
              </button>
            </div>
            <pre style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.85)", fontSize: 15, lineHeight: 1.8, margin: 0, fontFamily: "'Inter', sans-serif" }}>
              {result.visuals || "◈ Visual prompt library not available for this archived generation."}
            </pre>
          </div>
        )}

        {/* METADATA TAB */}
        {tab === "metadata" && (
          <pre style={{ whiteSpace: "pre-wrap", color: "rgba(255,255,255,0.85)", fontSize: 14, lineHeight: 1.8, margin: 0, fontFamily: "'SF Mono', monospace", background: "rgba(0,0,0,0.2)", padding: 20, borderRadius: 16 }}>
            {typeof result.metadata === 'object' ? JSON.stringify(result.metadata, null, 2) : (result.metadata || "◈ Metadata not available.")}
          </pre>
        )}
      </div>

      {/* Action Footer */}
      <button className="run-btn" onClick={onReset} style={{
        width: "100%", padding: "20px", borderRadius: 20,
        border: "none", color: "#000", fontSize: 18, fontWeight: 700,
        cursor: "pointer", fontFamily: "'Outfit', sans-serif", letterSpacing: 1,
        transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
      }}>
        {isGalleryView ? "← Back to Archive" : "Create Another Masterpiece"}
      </button>
    </div>
  );
}
