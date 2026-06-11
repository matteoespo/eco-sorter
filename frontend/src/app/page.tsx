"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Head from "next/head";

type LLMResult = {
  item: string;
  category: string;
  action_required: string;
  fun_fact: string;
};

type Detection = {
  label: string;
  confidence: number;
  bbox: [number, number, number, number]; // normalized x1, y1, x2, y2
};

type FrameResponse = {
  detected: string | null;
  confidence: number;
  detections: Detection[];
  llm_result: LLMResult | null;
};

export default function EcoSorterDashboard() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bboxCanvasRef = useRef<HTMLCanvasElement>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState<"Disconnected" | "Connecting" | "Connected">("Disconnected");
  
  const [detectedItem, setDetectedItem] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [llmResult, setLlmResult] = useState<LLMResult | null>(null);

  // Draw bounding boxes on overlay canvas
  const drawBoundingBoxes = useCallback((dets: Detection[]) => {
    const canvas = bboxCanvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    // Match canvas to the video's rendered size
    const rect = video.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const colors = [
      "#10b981", // emerald
      "#3b82f6", // blue
      "#f59e0b", // amber
      "#ef4444", // red
      "#8b5cf6", // purple
      "#ec4899", // pink
      "#06b6d4", // cyan
    ];

    dets.forEach((det, i) => {
      const [nx1, ny1, nx2, ny2] = det.bbox;
      const x1 = nx1 * canvas.width;
      const y1 = ny1 * canvas.height;
      const x2 = nx2 * canvas.width;
      const y2 = ny2 * canvas.height;
      const w = x2 - x1;
      const h = y2 - y1;
      const color = colors[i % colors.length];

      // Draw box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 8;
      ctx.strokeRect(x1, y1, w, h);
      ctx.shadowBlur = 0;

      // Draw label background
      const label = `${det.label} ${Math.round(det.confidence * 100)}%`;
      ctx.font = "bold 13px Inter, sans-serif";
      const textMetrics = ctx.measureText(label);
      const labelH = 22;
      const labelW = textMetrics.width + 12;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x1, y1 - labelH, labelW, labelH, [6, 6, 0, 0]);
      ctx.fill();

      // Draw label text
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x1 + 6, y1 - 6);
    });
  }, []);

  // Initialize Camera
  useEffect(() => {
    async function setupCamera() {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
          });
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        } catch (err) {
          console.error("Error accessing camera: ", err);
        }
      }
    }
    setupCamera();
  }, []);

  // Initialize WebSocket
  useEffect(() => {
    let socket: WebSocket;
    const connectWs = () => {
      setStatus("Connecting");
      socket = new WebSocket("ws://localhost:8000/process-frame");
      
      socket.onopen = () => {
        setStatus("Connected");
        setWs(socket);
      };
      
      socket.onmessage = (event) => {
        try {
          const data: FrameResponse = JSON.parse(event.data);
          setDetectedItem(data.detected);
          setConfidence(data.confidence);
          setDetections(data.detections || []);
          drawBoundingBoxes(data.detections || []);
          if (data.llm_result) {
            setLlmResult(data.llm_result);
          }
        } catch (err) {
          console.error("Error parsing WS message:", err);
        }
      };
      
      socket.onclose = () => {
        setStatus("Disconnected");
        setWs(null);
        // Attempt reconnect after a delay
        setTimeout(connectWs, 3000);
      };
      
      socket.onerror = (err) => {
        console.error("WebSocket Error:", err);
      };
    };

    connectWs();
    return () => {
      if (socket) socket.close();
    };
  }, []);

  // Send frames
  useEffect(() => {
    if (!ws || status !== "Connected") return;

    const intervalId = setInterval(() => {
      if (videoRef.current && canvasRef.current && videoRef.current.readyState === 4) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          // Compress heavily for real-time performance
          const base64Img = canvas.toDataURL("image/jpeg", 0.5);
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(base64Img);
          }
        }
      }
    }, 200); // 5 FPS

    return () => clearInterval(intervalId);
  }, [ws, status]);

  const getCategoryColor = (category: string) => {
    if (!category) return "border-gray-500 text-gray-400";
    const lower = category.toLowerCase();
    if (lower.includes("recycling") || lower.includes("recycle")) return "border-emerald-500 text-emerald-400";
    if (lower.includes("trash") || lower.includes("landfill")) return "border-red-500 text-red-400";
    if (lower.includes("compost") || lower.includes("organic")) return "border-amber-500 text-amber-400";
    if (lower.includes("hazardous")) return "border-purple-500 text-purple-400";
    return "border-blue-500 text-blue-400";
  };

  const getCategoryBg = (category: string) => {
    if (!category) return "bg-gray-500/10";
    const lower = category.toLowerCase();
    if (lower.includes("recycling") || lower.includes("recycle")) return "bg-emerald-500/10";
    if (lower.includes("trash") || lower.includes("landfill")) return "bg-red-500/10";
    if (lower.includes("compost") || lower.includes("organic")) return "bg-amber-500/10";
    if (lower.includes("hazardous")) return "bg-purple-500/10";
    return "bg-blue-500/10";
  };

  return (
    <div className="min-h-screen text-slate-100 p-4 md:p-8 font-sans selection:bg-emerald-500/30">
      <Head>
        <title>Eco-Sorter | AI Waste Classification</title>
        <meta name="description" content="AI-powered waste sorting dashboard" />
      </Head>

      <header className="flex items-center justify-between mb-8 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center pulse-glow">
            <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400 tracking-tight">
              Eco-Sorter
            </h1>
            <p className="text-slate-400 text-sm">Intelligent Waste Classification</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50 backdrop-blur-md">
          <div className={`w-2.5 h-2.5 rounded-full ${status === 'Connected' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse' : status === 'Connecting' ? 'bg-amber-500' : 'bg-red-500'}`}></div>
          <span className="text-xs font-medium text-slate-300">{status}</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Camera Feed */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel rounded-2xl overflow-hidden relative group transition-all duration-300 hover:shadow-emerald-500/10">
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent z-10 pointer-events-none"></div>
            
            {/* Top Bar Overlay */}
            <div className="absolute top-4 left-4 right-4 z-20 flex justify-between items-start pointer-events-none">
              <div className="bg-slate-900/60 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span className="text-sm font-medium text-slate-200">Live Feed</span>
              </div>

              {detectedItem && (
                <div className="bg-slate-900/80 backdrop-blur-md px-4 py-2 rounded-xl border border-emerald-500/30 flex flex-col items-end animate-in fade-in duration-300">
                  <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Detecting</span>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400 font-mono font-bold">{Math.round(confidence * 100)}%</span>
                    <span className="text-lg font-bold text-white capitalize">{detectedItem}</span>
                  </div>
                </div>
              )}
            </div>

            <video 
              ref={videoRef} 
              autoPlay 
              playsInline 
              muted 
              className="w-full h-[50vh] md:h-[65vh] object-cover bg-slate-900 transform transition-transform duration-700 ease-out group-hover:scale-[1.02]"
            />
            {/* Bounding box overlay canvas */}
            <canvas 
              ref={bboxCanvasRef} 
              className="absolute inset-0 w-full h-full z-[15] pointer-events-none"
            />
            <canvas ref={canvasRef} className="hidden" />

            {/* Scanning Overlay Effect */}
            {!detectedItem && status === "Connected" && (
              <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center">
                <div className="w-full h-full relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.8)] animate-[scan_3s_ease-in-out_infinite]"></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Results Panel */}
        <div className="space-y-6">
          <div className="glass-panel rounded-2xl p-6 h-full flex flex-col relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
            
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 border-b border-white/5 pb-4">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              Analysis Results
            </h2>

            {!llmResult ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 min-h-[300px]">
                <div className="relative mb-6 animate-float">
                  <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-xl"></div>
                  <svg className="w-16 h-16 text-slate-600 relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                {detectedItem ? (
                  <div className="text-center space-y-2">
                    <div className="flex items-center gap-2 justify-center text-emerald-400">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <p className="font-medium">Analyzing {detectedItem}...</p>
                    </div>
                    <p className="text-sm opacity-70">Consulting AI model for sorting guidelines</p>
                  </div>
                ) : (
                  <div className="text-center">
                    <p className="font-medium text-slate-400">Waiting for object</p>
                    <p className="text-sm text-slate-500 mt-1">Place an item in front of the camera</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6 flex-1 animate-in fade-in duration-500">
                {/* Main Category Card */}
                <div className={`p-5 rounded-xl border-l-4 ${getCategoryColor(llmResult.category)} ${getCategoryBg(llmResult.category)} backdrop-blur-sm border-t border-r border-b border-white/5`}>
                  <p className="text-sm font-semibold uppercase tracking-wider mb-1 opacity-80">Category</p>
                  <p className="text-2xl font-bold tracking-tight">{llmResult.category}</p>
                </div>

                {/* Detected Item */}
                <div className="bg-slate-800/40 rounded-xl p-4 border border-white/5">
                  <p className="text-xs text-slate-400 uppercase font-semibold mb-1">Identified Item</p>
                  <p className="text-lg font-medium text-slate-200 capitalize">{llmResult.item}</p>
                </div>

                {/* Action Required */}
                <div className="bg-slate-800/40 rounded-xl p-4 border border-white/5 relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-blue-500/50 group-hover:bg-blue-400 transition-colors"></div>
                  <p className="text-xs text-slate-400 uppercase font-semibold mb-2">Action Required</p>
                  <p className="text-slate-300 leading-relaxed text-sm">{llmResult.action_required}</p>
                </div>

                {/* Fun Fact */}
                <div className="bg-slate-800/40 rounded-xl p-4 border border-white/5 relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-purple-500/50 group-hover:bg-purple-400 transition-colors"></div>
                  <p className="text-xs text-slate-400 uppercase font-semibold mb-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Did You Know?
                  </p>
                  <p className="text-slate-300 leading-relaxed text-sm italic">{llmResult.fun_fact}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}} />
    </div>
  );
}
