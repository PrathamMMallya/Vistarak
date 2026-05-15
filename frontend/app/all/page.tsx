"use client";

import { useEffect, useRef, useState, useCallback } from "react";

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface Module {
  name: string;
  desc: string;
  color: string;
  bg: string;
  type: ModuleType;
}

type ModuleType = "whisper" | "sortformer" | "comfyui" | "gemma4" | "tts" | "qwen";

// ─────────────────────────────────────────────────────────────────────────────
// MODULE METADATA
// ─────────────────────────────────────────────────────────────────────────────

const MODS: Module[] = [
  { name: "Whisper ASR",      desc: "Audio Waveform → Mel Spectrogram → Encoder → Decoder → Text",              color: "#4488ff", bg: "#00081a", type: "whisper"    },
  { name: "Sortformer",       desc: "Transcribed Text + Timestamps → Diarization → Speaker Labels",             color: "#44ffaa", bg: "#001a0d", type: "sortformer" },
  { name: "ComfyUI",          desc: "Checkpoint → CLIP Encode → KSampler → VAE Decode → Image",                 color: "#ff8844", bg: "#1a0800", type: "comfyui"    },
  { name: "Gemma 4",          desc: "Text / Image / Audio / Video → Modality Encoders → Decoder → Tokens",      color: "#aa44ff", bg: "#0d0016", type: "gemma4"     },
  { name: "Chatterbox TTS",   desc: "Text → XML-RoBERTa Sentiment → TTS Transformer → Vocoder → .wav",          color: "#ffdd44", bg: "#1a1400", type: "tts"        },
  { name: "Qwen OCR",         desc: "Document Image → Vision Encoder → Visual Tokens → LM → JSON",             color: "#ff44aa", bg: "#1a0010", type: "qwen"       },
];

// ─────────────────────────────────────────────────────────────────────────────
// DRAWING UTILITIES
// ─────────────────────────────────────────────────────────────────────────────

function glow(ctx: CanvasRenderingContext2D, c: string, r = 20) {
  ctx.shadowColor = c;
  ctx.shadowBlur = r;
}
function noGlow(ctx: CanvasRenderingContext2D) {
  ctx.shadowBlur = 0;
}

function drawCircle(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, r: number,
  color: string, alpha = 1, glowR = 18
) {
  ctx.save();
  ctx.globalAlpha = alpha;
  glow(ctx, color, glowR);
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = color + "22";
  ctx.fill();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.stroke();
  noGlow(ctx);
  ctx.restore();
}

function drawEdge(
  ctx: CanvasRenderingContext2D,
  x1: number, y1: number, x2: number, y2: number,
  color: string, progress = 1, alpha = 0.25, dashed = false
) {
  if (progress <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  if (dashed) ctx.setLineDash([4, 6]);
  const ex = x1 + (x2 - x1) * progress;
  const ey = y1 + (y2 - y1) * progress;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(ex, ey);
  ctx.stroke();
  ctx.setLineDash([]);
  if (progress >= 0.98) {
    const angle = Math.atan2(y2 - y1, x2 - x1);
    ctx.globalAlpha = alpha * 1.6;
    glow(ctx, color, 6);
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - 10 * Math.cos(angle - 0.4), ey - 10 * Math.sin(angle - 0.4));
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - 10 * Math.cos(angle + 0.4), ey - 10 * Math.sin(angle + 0.4));
    ctx.stroke();
    noGlow(ctx);
  }
  ctx.restore();
}

function drawSignalDot(
  ctx: CanvasRenderingContext2D,
  x1: number, y1: number, x2: number, y2: number,
  color: string, p: number, size = 5
) {
  const x = x1 + (x2 - x1) * p;
  const y = y1 + (y2 - y1) * p;
  ctx.save();
  glow(ctx, color, 20);
  ctx.beginPath();
  ctx.arc(x, y, size, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.globalAlpha = 0.95;
  ctx.fill();
  noGlow(ctx);
  ctx.restore();
}

function label(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, text: string,
  color = "#667", size = 11, align: CanvasTextAlign = "center"
) {
  ctx.save();
  ctx.font = `${size}px 'JetBrains Mono',monospace`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = "middle";
  ctx.fillText(text, x, y);
  ctx.restore();
}

function label2(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, line1: string, line2: string,
  color: string, subcolor = "#445"
) {
  ctx.save();
  ctx.font = "bold 12px 'JetBrains Mono',monospace";
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(line1, x, y - 7);
  ctx.font = "10px 'JetBrains Mono',monospace";
  ctx.fillStyle = subcolor;
  ctx.fillText(line2, x, y + 7);
  ctx.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// MODULE RENDERERS
// ─────────────────────────────────────────────────────────────────────────────

function drawWhisper(ctx: CanvasRenderingContext2D, W: number, H: number, t: number) {
  const col = "#4488ff";
  const sections = [
    { x: W * 0.08, label: "Waveform",  sub: ".wav" },
    { x: W * 0.25, label: "Mel Spec",  sub: "80 bands" },
    { x: W * 0.42, label: "Encoder",   sub: "6 layers" },
    { x: W * 0.60, label: "Features",  sub: "512-dim" },
    { x: W * 0.75, label: "Decoder",   sub: "6 layers" },
    { x: W * 0.90, label: "Text Out",  sub: "tokens" },
  ];
  const midY = H * 0.5;
  const wW = W * 0.11, wH = H * 0.22;

  // Waveform
  const wX = sections[0].x;
  ctx.save();
  ctx.strokeStyle = col + "33"; ctx.lineWidth = 1;
  ctx.strokeRect(wX - wW / 2, midY - wH / 2 - 20, wW, wH);
  ctx.beginPath();
  ctx.strokeStyle = col; ctx.lineWidth = 1.5;
  glow(ctx, col, 12);
  for (let i = 0; i <= 60; i++) {
    const px = wX - wW / 2 + (i / 60) * wW;
    const a = Math.sin(i / 60 * Math.PI * 8 + t * 2.5);
    const b = Math.sin(i / 60 * Math.PI * 14 + t * 3.7) * 0.4;
    const c2 = Math.sin(i / 60 * Math.PI * 3 + t * 1.2) * 0.6;
    const amp = (a + b + c2) * wH * 0.18;
    i === 0 ? ctx.moveTo(px, midY - 20 + amp) : ctx.lineTo(px, midY - 20 + amp);
  }
  ctx.stroke(); noGlow(ctx); ctx.restore();

  // Mel spectrogram
  const mX = sections[1].x, mW = W * 0.10, mH = wH, bands = 20, bw = mW / bands;
  ctx.save();
  ctx.strokeStyle = col + "33"; ctx.lineWidth = 1;
  ctx.strokeRect(mX - mW / 2, midY - mH / 2 - 20, mW, mH);
  for (let i = 0; i < bands; i++) {
    const energy = 0.3 + 0.7 * Math.abs(Math.sin(i * 0.7 + t * 1.5 + Math.cos(i * 0.3) * 2));
    const barH = energy * mH * 0.92;
    const warm = Math.pow(energy, 1.2);
    ctx.fillStyle = `rgba(${Math.round(warm * 100)},${Math.round(warm * 50)},${Math.round(200 + warm * 55)},0.85)`;
    glow(ctx, `rgb(${Math.round(warm * 100)},50,200)`, 4);
    ctx.fillRect(mX - mW / 2 + i * bw + 1, midY + mH / 2 - 20 - barH, bw - 2, barH);
  }
  noGlow(ctx); ctx.restore();

  // Encoder layers
  const eX = sections[2].x, eY = midY - 20, layerCount = 6, nodeCount = 5;
  const layerGap = H * 0.045, nodeGap = H * 0.065;
  for (let l = 0; l < layerCount; l++) {
    const lx = eX + (l - (layerCount - 1) / 2) * layerGap;
    for (let n = 0; n < nodeCount; n++) {
      const ny = eY + (n - (nodeCount - 1) / 2) * nodeGap;
      const pulse = 0.5 + 0.5 * Math.sin(t * 2.5 + l * 1.1 + n * 0.7);
      drawCircle(ctx, lx, ny, 5, col, 0.7 + pulse * 0.3, 12);
      if (l < layerCount - 1) {
        const lx2 = eX + (l + 1 - (layerCount - 1) / 2) * layerGap;
        for (let n2 = 0; n2 < nodeCount; n2++) {
          if (Math.abs(n2 - n) <= 1) {
            const ny2 = eY + (n2 - (nodeCount - 1) / 2) * nodeGap;
            drawEdge(ctx, lx, ny, lx2, ny2, col, 1, 0.05);
          }
        }
      }
    }
  }

  // Feature vector
  const fX = sections[3].x, fY = midY - 20, fCount = 16;
  for (let i = 0; i < fCount; i++) {
    const fy = fY + (i - (fCount - 1) / 2) * nodeGap * 0.65;
    const pulse = 0.3 + 0.7 * Math.abs(Math.sin(t * 1.8 + i * 0.5));
    drawCircle(ctx, fX, fy, 4, col, pulse, 10);
  }

  // Decoder
  const dX = sections[4].x, dY = midY - 20, dcol = "#88aaff";
  for (let l = 0; l < layerCount; l++) {
    const lx = dX + (l - (layerCount - 1) / 2) * layerGap;
    for (let n = 0; n < nodeCount; n++) {
      const ny = dY + (n - (nodeCount - 1) / 2) * nodeGap;
      const pulse = 0.5 + 0.5 * Math.sin(t * 2 + l * 1.3 + n * 0.8 + Math.PI);
      drawCircle(ctx, lx, ny, 5, dcol, 0.7 + pulse * 0.3, 12);
      if (l < layerCount - 1) {
        const lx2 = dX + (l + 1 - (layerCount - 1) / 2) * layerGap;
        for (let n2 = 0; n2 < nodeCount; n2++) {
          if (Math.abs(n2 - n) <= 1) {
            const ny2 = dY + (n2 - (nodeCount - 1) / 2) * nodeGap;
            drawEdge(ctx, lx, ny, lx2, ny2, dcol, 1, 0.05);
          }
        }
      }
    }
  }

  // Tokens
  const tX = sections[5].x, tY = midY - 20;
  ["the", "quick", "brown", "fox"].forEach((tok, i) => {
    const ty = tY + (i - 1.5) * nodeGap * 1.1;
    const pulse = 0.5 + 0.5 * Math.sin(t * 2 + i * 1.2);
    ctx.save();
    glow(ctx, col, 10 * pulse);
    ctx.strokeStyle = col; ctx.globalAlpha = 0.5 + pulse * 0.5; ctx.lineWidth = 1;
    ctx.strokeRect(tX - 30, ty - 10, 60, 20);
    ctx.fillStyle = col + "11"; ctx.fillRect(tX - 30, ty - 10, 60, 20);
    noGlow(ctx);
    ctx.fillStyle = col; ctx.font = "10px monospace";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(tok, tX, ty);
    ctx.restore();
  });

  // Connecting arrows + signals
  const speeds = [0.4, 0.5, 0.35, 0.45, 0.38];
  sections.forEach((s, i) => {
    if (i < sections.length - 1) {
      const nx = sections[i + 1].x;
      const p = (t * speeds[i]) % 1;
      drawEdge(ctx, s.x + (i < 2 ? (i === 0 ? wW / 2 : mW / 2) : 0), midY - 20,
        nx - (i + 1 < 2 ? (i + 1 === 1 ? mW / 2 : 0) : 0), midY - 20, col, 1, 0.15);
      drawSignalDot(ctx, s.x, midY - 20, nx, midY - 20, col, p, 5);
    }
  });

  sections.forEach((s) => {
    label2(ctx, s.x, midY + wH * 0.5 + 10, s.label, s.sub, col, "#335588");
  });
  label(ctx, W / 2, H * 0.06, "WHISPER  AUTOMATIC SPEECH RECOGNITION", col + "88", 11);
}

function drawSortformer(ctx: CanvasRenderingContext2D, W: number, H: number, t: number) {
  const col = "#44ffaa";
  const midX = W / 2;
  const stages = [
    { label: "Transcribed Text", sub: "+ timestamps",      y: H * 0.12 },
    { label: "Sortformer",       sub: "speaker diarization", y: H * 0.30 },
    { label: "Speaker Segments", sub: "cluster assignments", y: H * 0.50 },
    { label: "Merge Pass",       sub: "timestamps ∪ speakers", y: H * 0.68 },
    { label: "Final Transcript", sub: "speaker-labeled",   y: H * 0.86 },
  ];
  const spkColors = ["#44ffaa", "#ffaa44", "#aa44ff"];

  stages.forEach((s, i) => {
    const bw = W * 0.30, bh = 38;
    const pulse = 0.5 + 0.5 * Math.sin(t * 2 + i * 0.8);
    ctx.save();
    glow(ctx, col, 10 * pulse);
    ctx.strokeStyle = col; ctx.globalAlpha = 0.3 + pulse * 0.2; ctx.lineWidth = 1;
    ctx.strokeRect(midX - bw / 2, s.y - bh / 2, bw, bh);
    ctx.fillStyle = col + "08"; ctx.fillRect(midX - bw / 2, s.y - bh / 2, bw, bh);
    noGlow(ctx); ctx.restore();
    label2(ctx, midX, s.y, s.label, s.sub, col, "#336655");

    if (i < stages.length - 1) {
      const p = (t * 0.45 + i * 0.2) % 1;
      drawEdge(ctx, midX, s.y + bh / 2, midX, stages[i + 1].y - bh / 2, col, 1, 0.25);
      drawSignalDot(ctx, midX, s.y + bh / 2, midX, stages[i + 1].y - bh / 2, col, p, 5);
    }
  });

  // Speaker timeline
  const tlY = H * 0.40, tlX = midX - W * 0.32, tlW = W * 0.65, tlH = 20;
  label(ctx, midX, tlY - 18, "speaker timeline", col + "66", 10);
  const segs = [[0, 0.18], [0.22, 0.35], [0.55, 0.72], [0.78, 0.92]];
  for (let spk = 0; spk < 3; spk++) {
    const sy = tlY + spk * (tlH + 6);
    ctx.save();
    ctx.globalAlpha = 0.6;
    segs.filter((_, j) => j % 3 === spk || (j + 1) % 3 === spk).forEach(([a, b]) => {
      ctx.fillStyle = spkColors[spk] + "44";
      ctx.strokeStyle = spkColors[spk]; ctx.lineWidth = 0.5;
      ctx.fillRect(tlX + a * tlW, sy, Math.max(0, (b - a) * tlW), tlH);
      ctx.strokeRect(tlX + a * tlW, sy, Math.max(0, (b - a) * tlW), tlH);
    });
    label(ctx, tlX - 22, sy + tlH / 2, `S${spk + 1}`, spkColors[spk] + "cc", 9, "right");
    ctx.restore();
  }
  label(ctx, W / 2, H * 0.04, "SORTFORMER  SPEAKER DIARIZATION", col + "88", 11);
}

function drawComfyUI(ctx: CanvasRenderingContext2D, W: number, H: number, t: number) {
  const col = "#ff8844";
  const midX = W / 2;
  const nodes = [
    { x: midX,           y: H * 0.10, label: "Checkpoint Loader", sub: "SDXL 1.0",       w: 180, col: col },
    { x: midX - W * 0.22, y: H * 0.26, label: "CLIP Encode +",    sub: "positive prompt", w: 160, col: "#ffaa44" },
    { x: midX + W * 0.22, y: H * 0.26, label: "CLIP Encode −",    sub: "negative prompt", w: 160, col: "#ff6644" },
    { x: midX,           y: H * 0.43, label: "Empty Latent",      sub: "noise tensor",    w: 150, col: col },
    { x: midX,           y: H * 0.57, label: "KSampler",          sub: "DDIM 20 steps",   w: 150, col: col },
    { x: midX,           y: H * 0.72, label: "VAE Decode",        sub: "latent → pixels", w: 150, col: col },
    { x: midX,           y: H * 0.87, label: "Save Image",        sub: "PNG output",      w: 150, col: col },
  ];
  [[0,1],[0,2],[1,4],[2,4],[3,4],[4,5],[5,6]].forEach(([a, b]) => {
    const na = nodes[a], nb = nodes[b];
    drawEdge(ctx, na.x, na.y + 20, nb.x, nb.y - 20, na.col, 1, 0.2);
    drawSignalDot(ctx, na.x, na.y + 20, nb.x, nb.y - 20, na.col, (t * 0.4 + a * 0.15) % 1, 4);
  });
  nodes.forEach((n, i) => {
    const bh = 36, pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.9));
    ctx.save();
    glow(ctx, n.col, 14 * pulse);
    ctx.strokeStyle = n.col; ctx.lineWidth = 1; ctx.globalAlpha = 0.25 + pulse * 0.15;
    ctx.fillStyle = n.col + "11";
    ctx.fillRect(n.x - n.w / 2, n.y - bh / 2, n.w, bh);
    ctx.strokeRect(n.x - n.w / 2, n.y - bh / 2, n.w, bh);
    noGlow(ctx); ctx.restore();
    label2(ctx, n.x, n.y, n.label, n.sub, n.col, "#553322");
  });

  // Latent noise grid
  const noiseX = midX + W * 0.28, noiseY = H * 0.43, noiseS = 80;
  for (let r = 0; r < 12; r++) {
    for (let c = 0; c < 12; c++) {
      const v = Math.abs(Math.sin(r * 1.3 + c * 1.7 + t * 1.2));
      ctx.save();
      ctx.globalAlpha = v * 0.6;
      ctx.fillStyle = `rgba(${Math.round(Math.pow(v, 0.7) * 255)},${Math.round(Math.pow(v, 0.7) * 100)},80,1)`;
      ctx.fillRect(noiseX - noiseS / 2 + c * (noiseS / 12), noiseY - noiseS / 2 + r * (noiseS / 12), noiseS / 12 - 1, noiseS / 12 - 1);
      ctx.restore();
    }
  }
  label(ctx, W / 2, H * 0.03, "COMFYUI  LATENT DIFFUSION PIPELINE", col + "88", 11);
}

function drawGemma4(ctx: CanvasRenderingContext2D, W: number, H: number, t: number) {
  const col = "#aa44ff";
  const midX = W / 2;
  const inputs = [
    { label: "Text",  y: H * 0.20, col: "#6688ff" },
    { label: "Image", y: H * 0.35, col: "#44aaff" },
    { label: "Audio", y: H * 0.50, col: "#44ffee" },
    { label: "Video", y: H * 0.65, col: "#88ff44" },
  ];
  const encX = midX - W * 0.24, uniX = midX - W * 0.04;
  const transX = midX + W * 0.14, lmX = midX + W * 0.30, outX = midX + W * 0.42;
  const layerGap = H * 0.045, nodeGap = H * 0.065, layerCount = 6, nodeCount = 5;
  const tokenY = H * 0.42, transW = 80, transGap = 36, transLayers = 7;

  inputs.forEach((inp, i) => {
    drawCircle(ctx, W * 0.10, inp.y, 18, inp.col, 0.8, 20);
    label(ctx, W * 0.10, inp.y, inp.label, inp.col, 11);
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.7));
    ctx.save();
    glow(ctx, inp.col, 10 * pulse);
    ctx.strokeStyle = inp.col; ctx.globalAlpha = 0.35 * pulse; ctx.lineWidth = 1;
    ctx.strokeRect(encX - 40, inp.y - 14, 80, 28);
    ctx.fillStyle = inp.col + "10"; ctx.fillRect(encX - 40, inp.y - 14, 80, 28);
    noGlow(ctx); ctx.restore();
    label2(ctx, encX, inp.y, `${inp.label} Enc`, "tower", inp.col, "#334");
    drawEdge(ctx, W * 0.10 + 18, inp.y, encX - 40, inp.y, inp.col, 1, 0.25);
    drawSignalDot(ctx, W * 0.10 + 18, inp.y, encX - 40, inp.y, inp.col, (t * 0.5 + i * 0.2) % 1, 4);
  });

  const tokenCount = 8, tokenGap = 22;
  for (let i = 0; i < tokenCount; i++) {
    const tx = uniX + (i - (tokenCount - 1) / 2) * tokenGap;
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.5));
    drawCircle(ctx, tx, tokenY, 7, col, pulse, 12);
    if (i < 4) {
      drawEdge(ctx, encX + 40, inputs[i].y, tx, tokenY, inputs[i].col, 1, 0.08);
    }
  }
  label(ctx, uniX, tokenY + 28, "Unified Token Seq", col + "88", 10);

  for (let l = 0; l < transLayers; l++) {
    const ly = tokenY + (l - (transLayers - 1) / 2) * transGap;
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + l * 0.6 + 0.5));
    ctx.save();
    glow(ctx, col, 8 * pulse);
    ctx.strokeStyle = col; ctx.globalAlpha = 0.15 + pulse * 0.2; ctx.lineWidth = 1;
    ctx.fillStyle = col + "09";
    ctx.fillRect(transX - transW / 2, ly - transGap / 2 + 4, transW, transGap - 8);
    ctx.strokeRect(transX - transW / 2, ly - transGap / 2 + 4, transW, transGap - 8);
    noGlow(ctx);
    ctx.fillStyle = col + (pulse > 0.7 ? "cc" : "44");
    ctx.font = "9px monospace"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(`layer ${l + 1}`, transX, ly);
    ctx.restore();
    if (l === Math.floor(transLayers / 2)) {
      for (let i = 0; i < tokenCount; i++) {
        const tx = uniX + (i - (tokenCount - 1) / 2) * tokenGap;
        drawEdge(ctx, tx, tokenY, transX - transW / 2, ly, col, 1, 0.04);
      }
    }
  }

  const lmPulse = 0.6 + 0.4 * Math.sin(t * 2.5);
  drawCircle(ctx, lmX, tokenY, 22, col, lmPulse, 20);
  label2(ctx, lmX, tokenY, "LM Head", "linear proj", col, "#553377");
  drawEdge(ctx, transX + transW / 2, tokenY, lmX - 22, tokenY, col, 1, 0.3);
  drawSignalDot(ctx, transX + transW / 2, tokenY, lmX - 22, tokenY, col, (t * 0.55) % 1, 5);

  ["next", "token", "pred"].forEach((tok, i) => {
    const oy = tokenY + (i - 1) * 36;
    const oc = ["#ff66cc", "#ff44aa", "#cc2288"][i];
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i));
    ctx.save();
    glow(ctx, oc, 10 * pulse);
    ctx.strokeStyle = oc; ctx.globalAlpha = 0.3 + pulse * 0.3; ctx.lineWidth = 1;
    ctx.strokeRect(outX - 28, oy - 13, 56, 26); ctx.fillStyle = oc + "0c"; ctx.fillRect(outX - 28, oy - 13, 56, 26);
    noGlow(ctx);
    ctx.fillStyle = oc; ctx.font = "bold 11px monospace"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(tok, outX, oy);
    ctx.restore();
    drawEdge(ctx, lmX + 22, tokenY, outX - 28, oy, oc, 1, 0.12);
  });
  label(ctx, W / 2, H * 0.05, "GEMMA 4  MULTIMODAL DECODER-ONLY TRANSFORMER", col + "88", 11);
}

function drawTTS(ctx: CanvasRenderingContext2D, W: number, H: number, t: number) {
  const col = "#ffdd44";
  const midX = W / 2;
  const stages = [
    { x: midX, y: H * 0.10, label: "Input Text",     sub: "raw sentences",      w: 160, col: col },
    { x: midX, y: H * 0.22, label: "XML-RoBERTa",    sub: "sentiment tags",     w: 160, col: "#ffaa44" },
    { x: midX, y: H * 0.34, label: "Text Normalize", sub: "numbers, abbrevs",   w: 160, col: col },
    { x: midX, y: H * 0.46, label: "Tokenizer",      sub: "phonemes / BPE",     w: 160, col: col },
    { x: midX, y: H * 0.57, label: "TTS Transformer",sub: "Llama-style arch",   w: 180, col: "#ffbb44" },
    { x: midX, y: H * 0.69, label: "Speech Tokens",  sub: "EnCodec codebooks",  w: 180, col: col },
    { x: midX, y: H * 0.81, label: "Vocoder",        sub: "HiFi-GAN",           w: 160, col: col },
    { x: midX, y: H * 0.92, label: "Waveform .wav",  sub: "24kHz audio",        w: 160, col: col },
  ];

  // Sentiment bars
  const sbX = midX + W * 0.28, sbY = H * 0.22;
  [
    { text: "😊 joy",     val: 0.65, col: "#44ff88" },
    { text: "😐 neutral", val: 0.20, col: "#aaaaaa" },
    { text: "😢 sadness", val: 0.10, col: "#4488ff" },
    { text: "😠 anger",   val: 0.05, col: "#ff4444" },
  ].forEach((s, i) => {
    const barW = W * 0.14 * s.val * (0.9 + 0.1 * Math.sin(t * 1.5 + i));
    ctx.save(); ctx.globalAlpha = 0.7;
    ctx.fillStyle = s.col + "55"; ctx.fillRect(sbX, sbY - 10 + i * 22, barW, 16);
    ctx.strokeStyle = s.col; ctx.lineWidth = 0.5; ctx.strokeRect(sbX, sbY - 10 + i * 22, barW, 16);
    ctx.fillStyle = s.col; ctx.font = "9px monospace"; ctx.textBaseline = "middle"; ctx.textAlign = "left";
    ctx.fillText(s.text, sbX + barW + 4, sbY + i * 22);
    ctx.restore();
  });

  // Output waveform
  const owX = midX + W * 0.28 + 30, owY = H * 0.92, owW = W * 0.20, owH = 30;
  ctx.save();
  ctx.beginPath(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; glow(ctx, col, 10);
  for (let i = 0; i <= 80; i++) {
    const px = owX + (i / 80) * owW - owW / 2;
    const env = Math.sin((i / 80) * Math.PI);
    const v = env * (Math.sin(i * 0.7 + t * 3) + 0.3 * Math.sin(i * 1.8 + t * 4.5)) * owH * 0.5;
    i === 0 ? ctx.moveTo(px, owY + v) : ctx.lineTo(px, owY + v);
  }
  ctx.stroke(); noGlow(ctx); ctx.restore();

  stages.forEach((s, i) => {
    const bh = 32, pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.7));
    ctx.save();
    glow(ctx, s.col, 10 * pulse); ctx.strokeStyle = s.col; ctx.lineWidth = 1; ctx.globalAlpha = 0.25 + pulse * 0.18;
    ctx.fillStyle = s.col + "0c"; ctx.fillRect(s.x - s.w / 2, s.y - bh / 2, s.w, bh);
    ctx.strokeRect(s.x - s.w / 2, s.y - bh / 2, s.w, bh); noGlow(ctx); ctx.restore();
    label2(ctx, s.x, s.y, s.label, s.sub, s.col, "#554422");
    if (i < stages.length - 1) {
      const ns = stages[i + 1];
      const p = (t * 0.38 + i * 0.12) % 1;
      drawEdge(ctx, s.x, s.y + bh / 2, ns.x, ns.y - bh / 2, s.col, 1, 0.25);
      drawSignalDot(ctx, s.x, s.y + bh / 2, ns.x, ns.y - bh / 2, s.col, p, 4);
    }
  });
  label(ctx, W / 2, H * 0.04, "CHATTERBOX TTS  EMOTION-AWARE SYNTHESIS", col + "88", 11);
}

function drawQwen(ctx: CanvasRenderingContext2D, W: number, H: number, t: number) {
  const col = "#ff44aa";
  const midX = W / 2, midY = H / 2;
  const docX = W * 0.12, docW = W * 0.14, docH = H * 0.30;
  const patchX = midX - W * 0.18, pSize = 14, pCols = 8, pRows = 6;
  const tokX = midX + W * 0.04, tCount = 12;
  const lmX = midX + W * 0.22, outX = midX + W * 0.40;

  // Document
  ctx.save();
  ctx.strokeStyle = col + "44"; ctx.lineWidth = 0.5;
  ctx.strokeRect(docX - docW / 2, midY - docH / 2, docW, docH);
  ctx.fillStyle = "#1a0010"; ctx.fillRect(docX - docW / 2, midY - docH / 2, docW, docH);
  for (let r = 0; r < 8; r++) {
    const lineW = (0.4 + 0.6 * (r % 3 === 0 ? 0.5 : r % 3 === 1 ? 0.9 : 0.7)) * docW * 0.8;
    ctx.fillStyle = col + (r % 2 === 0 ? "55" : "33");
    ctx.fillRect(docX - docW / 2 + 8, midY - docH / 2 + 14 + r * (docH - 14) / 8, lineW, 3);
  }
  ctx.restore();
  label(ctx, docX, midY + docH / 2 + 14, "Document", col + "88", 10);

  // Patch grid
  label(ctx, patchX, midY - pRows * pSize / 2 - 14, "ViT Patches", col + "66", 10);
  for (let r = 0; r < pRows; r++) {
    for (let c = 0; c < pCols; c++) {
      const v = Math.abs(Math.sin(c * 1.1 + r * 0.9 + t * 1.3));
      ctx.save(); ctx.globalAlpha = 0.2 + v * 0.7; glow(ctx, col, v * 10);
      ctx.fillStyle = col + Math.round(v * 200).toString(16).padStart(2, "0");
      ctx.fillRect(patchX + (c - (pCols - 1) / 2) * pSize, midY + (r - (pRows - 1) / 2) * pSize, pSize - 2, pSize - 2);
      noGlow(ctx); ctx.restore();
    }
  }

  // Visual tokens
  for (let i = 0; i < tCount; i++) {
    const ty = midY + (i - (tCount - 1) / 2) * H * 0.048;
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.4));
    drawCircle(ctx, tokX, ty, 6, col, pulse, 12);
  }

  // Qwen LM
  const lmPulse = 0.6 + 0.4 * Math.sin(t * 2.5);
  drawCircle(ctx, lmX, midY, 38, col, lmPulse, 28);
  label2(ctx, lmX, midY, "Qwen2-VL", "7B / 72B", col, "#663355");

  // Output
  ["Text", "Markdown", "JSON"].forEach((o, i) => {
    const oy = midY + (i - 1) * 36;
    const oc = ["#ff66cc", "#ff44aa", "#cc2288"][i];
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.8));
    ctx.save();
    glow(ctx, oc, 10 * pulse); ctx.strokeStyle = oc; ctx.globalAlpha = 0.3 + pulse * 0.3; ctx.lineWidth = 1;
    ctx.strokeRect(outX - 28, oy - 13, 56, 26); ctx.fillStyle = oc + "0c"; ctx.fillRect(outX - 28, oy - 13, 56, 26);
    noGlow(ctx); ctx.fillStyle = oc; ctx.font = "bold 11px monospace"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(o, outX, oy); ctx.restore();
    drawEdge(ctx, lmX + 38, midY, outX - 28, oy, oc, 1, 0.15);
    drawSignalDot(ctx, lmX + 38, midY, outX - 28, oy, oc, (t * 0.45 + i * 0.3) % 1, 4);
  });

  // Flow arrows
  drawEdge(ctx, docX + docW / 2, midY, patchX - pCols * pSize / 2, midY, col, 1, 0.2);
  drawSignalDot(ctx, docX + docW / 2, midY, patchX - pCols * pSize / 2, midY, col, (t * 0.5) % 1, 4);
  drawEdge(ctx, patchX + pCols * pSize / 2, midY, tokX - 6, midY, col, 1, 0.2);
  drawSignalDot(ctx, patchX + pCols * pSize / 2, midY, tokX - 6, midY, col, (t * 0.5 + 0.3) % 1, 4);
  drawEdge(ctx, tokX + 6, midY, lmX - 38, midY, col, 1, 0.2);
  drawSignalDot(ctx, tokX + 6, midY, lmX - 38, midY, col, (t * 0.5 + 0.6) % 1, 4);

  label(ctx, W / 2, H * 0.05, "QWEN2-VL  DOCUMENT VISION LANGUAGE MODEL", col + "88", 11);
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function AIPipelineViz() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tRef = useRef(0);
  const modRef = useRef(0);
  const animRef = useRef(0);
  const [currentMod, setCurrentMod] = useState(0);

  const setMod = useCallback((i: number) => {
    modRef.current = i;
    tRef.current = 0;
    setCurrentMod(i);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio, 2);
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const loop = () => {
      const W = canvas.offsetWidth;
      const H = canvas.offsetHeight;
      const mod = MODS[modRef.current];
      const t = tRef.current;

      // Background
      ctx.fillStyle = mod.bg;
      ctx.fillRect(0, 0, W, H);
      ctx.save();
      ctx.strokeStyle = "#ffffff07"; ctx.lineWidth = 0.5;
      for (let x = 0; x < W; x += 60) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y < H; y += 60) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
      ctx.restore();

      switch (mod.type) {
        case "whisper":    drawWhisper(ctx, W, H, t); break;
        case "sortformer": drawSortformer(ctx, W, H, t); break;
        case "comfyui":    drawComfyUI(ctx, W, H, t); break;
        case "gemma4":     drawGemma4(ctx, W, H, t); break;
        case "tts":        drawTTS(ctx, W, H, t); break;
        case "qwen":       drawQwen(ctx, W, H, t); break;
      }

      tRef.current += 0.016;
      animRef.current = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
    };
  }, []);

  const m = MODS[currentMod];

  return (
    <div style={{ width: "100vw", height: "100vh", background: "#0d0d0f", display: "flex", flexDirection: "column", fontFamily: "'JetBrains Mono',monospace", overflow: "hidden" }}>
      {/* NAV */}
      <nav style={{ height: 52, background: "#0d0d0f", borderBottom: "1px solid #1a1a2e", display: "flex", alignItems: "center", gap: 4, padding: "0 16px", flexShrink: 0, overflowX: "auto" }}>
        <div style={{ color: "#444", fontSize: 11, letterSpacing: 3, marginRight: 16, whiteSpace: "nowrap", flexShrink: 0 }}>
          ◈ <span style={{ color: "#6060ff" }}>AI</span>VIZ
        </div>
        {MODS.map((mod, i) => (
          <button
            key={mod.type}
            onClick={() => setMod(i)}
            style={{
              padding: "5px 13px", borderRadius: 6, border: "none", cursor: "pointer",
              background: currentMod === i ? "#1a1a2e" : "transparent",
              color: currentMod === i ? "#fff" : "#444",
              fontSize: 11, letterSpacing: 1, fontFamily: "inherit", whiteSpace: "nowrap",
              display: "flex", alignItems: "center", gap: 5, flexShrink: 0,
              transition: "all 0.2s",
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: mod.color, display: "inline-block" }} />
            {mod.name}
          </button>
        ))}
      </nav>

      {/* INFO */}
      <div style={{ padding: "7px 20px", borderBottom: "1px solid #111", display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
        <div style={{ color: m.color, fontSize: 12, letterSpacing: 2, fontWeight: "bold", textTransform: "uppercase" }}>{m.name}</div>
        <div style={{ color: "#222" }}>—</div>
        <div style={{ color: "#444", fontSize: 10, letterSpacing: 1 }}>{m.desc}</div>
      </div>

      {/* CANVAS */}
      <canvas ref={canvasRef} style={{ flex: 1, width: "100%", display: "block" }} />
    </div>
  );
}