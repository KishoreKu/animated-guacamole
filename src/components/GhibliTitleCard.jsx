import React, { useEffect, useRef } from 'react';
import { 
  prepareWithSegments, 
  layoutNextLine
} from '@chenglou/pretext';

export default function GhibliTitleCard({ 
  text, 
  imageUrl,
  width = 800, 
  height = 450, 
  fontSize = 42,
  lineHeight = 60,
  opacity = 1
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = imageUrl;
    
    img.onload = () => {
      // 1. Draw Background Image
      ctx.globalAlpha = opacity;
      ctx.drawImage(img, 0, 0, width, height);
      
      // 2. Overlay a very subtle vignette for text legibility
      const gradient = ctx.createRadialGradient(width/2, height/2, 0, width/2, height/2, width/1.2);
      gradient.addColorStop(0, "rgba(0,0,0,0)");
      gradient.addColorStop(1, "rgba(0,0,0,0.6)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);

      // 3. Prepare Typography (Studio Ghibli style)
      // We use 'Outfit' or 'Inter', fallback to sans-serif
      const fontStr = `600 ${fontSize}px 'Outfit', 'Inter', sans-serif`;
      ctx.font = fontStr;
      
      // 4. PRETEXT: Layout the text
      const prepared = prepareWithSegments(text, fontStr);
      let y = height / 2 - 50; // Pivot point
      let cursor = { segmentIndex: 0, graphemeIndex: 0 };
      const maxWidth = width * 0.8;

      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Studio Ghibli cinematic drop shadow (soft & deep)
      ctx.shadowColor = "rgba(0,0,0,0.8)";
      ctx.shadowBlur = 15;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 4;
      ctx.fillStyle = "#ffffff";

      // Loop through Pretext lines
      while (cursor !== null) {
        const line = layoutNextLine(prepared, cursor, maxWidth);
        if (!line) break;
        
        // Add theatrical letter spacing (extra cinematic)
        ctx.fillText(line.text.toUpperCase(), width / 2, y);
        
        cursor = line.end;
        y += lineHeight;
        if (y > height - 40) break;
      }
    };
  }, [text, imageUrl, width, height, fontSize, lineHeight, opacity]);

  return (
    <div style={{ position: "relative", borderRadius: 24, overflow: "hidden", boxShadow: "0 20px 50px rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)" }}>
      <canvas 
        ref={canvasRef} 
        width={width} 
        height={height} 
        style={{ width: "100%", height: "auto", display: "block" }}
      />
      <div style={{ position: "absolute", bottom: 20, right: 20, fontSize: 10, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 2 }}>
        ✦ Cinematic Preview Mode (Pretext)
      </div>
    </div>
  );
}
