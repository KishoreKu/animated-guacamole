import React, { useState } from 'react';
import { supabase } from '../lib/supabaseClient';

export default function Auth({ onLogin }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      if (isSignUp) {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setMessage('✨ Welcome aboard! Please check your email to confirm your account.');
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        onLogin(data.user);
      }
    } catch (error) {
      setMessage(`🚨 ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "radial-gradient(circle at top right, #1a1a2e, #16213e)",
      padding: 20, fontFamily: "'Outfit', sans-serif"
    }}>
      <div style={{
        width: "100%", maxWidth: 450, background: "rgba(255,255,255,0.05)",
        backdropFilter: "blur(24px)", borderRadius: 32, padding: "40px 50px",
        border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 25px 50px rgba(0,0,0,0.3)"
      }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 13, color: "#4aff8a", letterSpacing: 4, textTransform: "uppercase", fontWeight: 700, marginBottom: 12 }}>
            ✦ Ghibli Studio
          </div>
          <h1 style={{ fontSize: "2.5rem", color: "#fff", margin: 0, fontWeight: 700 }}>
            {isSignUp ? "Create Account" : "Welcome Back"}
          </h1>
          <p style={{ color: "rgba(255,255,255,0.5)", marginTop: 10, fontSize: 15 }}>
            {isSignUp ? "Join the content factory today." : "Log in to orchestrate your stories."}
          </p>
        </div>

        <form onSubmit={handleAuth} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div>
            <label style={{ display: "block", color: "rgba(255,255,255,0.7)", fontSize: 13, marginBottom: 8, marginLeft: 5 }}>Email Address</label>
            <input type="email" placeholder="kiki@bakery.com" required
              value={email} onChange={e => setEmail(e.target.value)}
              style={{
                width: "100%", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 16, padding: "16px 20px", color: "#fff", outline: "none", fontSize: 16
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", color: "rgba(255,255,255,0.7)", fontSize: 13, marginBottom: 8, marginLeft: 5 }}>Password</label>
            <input type="password" placeholder="••••••••" required
              value={password} onChange={e => setPassword(e.target.value)}
              style={{
                width: "100%", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 16, padding: "16px 20px", color: "#fff", outline: "none", fontSize: 16
              }}
            />
          </div>

          <button type="submit" disabled={loading}
            style={{
              marginTop: 10, padding: 18, borderRadius: 16, border: "none",
              background: "linear-gradient(135deg, #4ab8ff, #4aff8a)",
              color: "#000", fontSize: 17, fontWeight: 700, cursor: "pointer",
              transition: "transform 0.2s", opacity: loading ? 0.7 : 1
            }}>
            {loading ? "Processing..." : (isSignUp ? "Sign Up" : "Log In")}
          </button>
        </form>

        {message && (
          <div style={{
            marginTop: 20, padding: 15, borderRadius: 12,
            background: message.includes('🚨') ? "rgba(255,74,138,0.1)" : "rgba(74,255,138,0.1)",
            color: message.includes('🚨') ? "#ff4a8a" : "#4aff8a", fontSize: 14, textAlign: "center"
          }}>
            {message}
          </div>
        )}

        <div style={{ textAlign: "center", marginTop: 30 }}>
          <button onClick={() => setIsSignUp(!isSignUp)}
            style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: 14 }}>
            {isSignUp ? "Already have an account? Log In" : "New creator? Create an account"}
          </button>
        </div>
      </div>
    </div>
  );
}
