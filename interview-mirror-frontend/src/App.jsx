import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Upload, Video, BrainCircuit, XCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

// --- HELPER: SPEECH SYNTHESIS ---
const speakText = (text) => {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
};

// --- 1. THE LOBBY (Unchanged, but included for context) ---
const Lobby = ({ onStart }) => {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const companies = [
    { id: 'google', name: 'Google', focus: 'Algorithms', diff: 5, color: 'text-neon-cyan' },
    { id: 'dell', name: 'Dell', focus: 'Networks', diff: 3, color: 'text-blue-400' },
    { id: 'startup', name: 'Stealth Startup', focus: 'Culture Fit', diff: 4, color: 'text-neon-green' },
  ];

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
        // 1. Upload Resume
        const res = await fetch('http://localhost:8000/upload-resume', { method: 'POST', body: formData });
        const data = await res.json();
        
        // 2. Start Session
        const sessionRes = await fetch("http://localhost:8000/start_interview", { method: "POST" });
        const sessionData = await sessionRes.json();

        setResumeUploaded(true);
        setIsLoading(false);
        
        // Pass the session ID and the first AI question to the Cockpit
        onStart(sessionData.session_id, data.intro);
    } catch (err) {
        console.error(err);
        alert("Server Error. Is the Python backend running?");
        setIsLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-[#0a0a0a] to-black"
    >
      <h1 className="text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-neon-cyan to-purple-500 mb-8 tracking-tighter">
        INTERVIEW MIRROR
      </h1>
      
      <div className="grid grid-cols-3 gap-6 mb-12 w-full max-w-4xl">
        {companies.map((c) => (
          <motion.div 
            key={c.id}
            whileHover={{ scale: 1.05, borderColor: '#00f3ff' }}
            onClick={() => setSelectedCompany(c)}
            className={`p-6 rounded-xl border border-white/10 bg-white/5 backdrop-blur-md cursor-pointer transition-all ${selectedCompany?.id === c.id ? 'border-neon-cyan ring-2 ring-neon-cyan/20' : ''}`}
          >
            <h3 className={`text-2xl font-bold ${c.color}`}>{c.name}</h3>
            <p className="text-gray-400 mt-2 text-sm">Focus: {c.focus}</p>
            <div className="flex mt-4 text-yellow-500">{'⭐'.repeat(c.diff)}</div>
          </motion.div>
        ))}
      </div>

      <div className="w-full max-w-md p-8 border-2 border-dashed border-white/20 rounded-2xl bg-white/5 text-center hover:border-neon-cyan/50 transition-colors group cursor-pointer relative overflow-hidden">
        <input type="file" accept=".pdf" onChange={handleUpload} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
        {isLoading ? <p className="text-neon-cyan animate-pulse">ANALYZING BIOMETRICS...</p> : 
         resumeUploaded ? (
            <div className="text-neon-green flex flex-col items-center">
                <BrainCircuit size={48} />
                <span className="mt-2 font-mono">SYSTEM READY</span>
            </div>
        ) : (
            <div className="text-gray-400 group-hover:text-white transition-colors">
                <Upload className="mx-auto mb-4" size={32} />
                <p>Drop Resume Protocol (.PDF)</p>
            </div>
        )}
      </div>
    </motion.div>
  );
};

// --- 2. THE COCKPIT (Fixed: Audio & WebSocket Logic) ---
const Cockpit = ({ sessionId, initialQuestion, onEnd }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const [metrics, setMetrics] = useState({ eye: 0, fidget: 0, smile: false, gesture: 'neutral' });
  const [transcript, setTranscript] = useState(initialQuestion || "System Initializing...");
  const [aiState, setAiState] = useState('idle'); // idle, listening, processing, speaking
  const [isRecording, setIsRecording] = useState(false);

  // 1. INITIALIZE WEBSOCKET & CAMERA
  useEffect(() => {
    // Speak the intro immediately
    if (initialQuestion) speakText(initialQuestion);

    // Setup Socket
    const ws = new WebSocket(`ws://localhost:8000/ws/interview/${sessionId}`);
    socketRef.current = ws;

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'metrics_update') {
            setMetrics({
                eye: data.metrics.eye_contact_score || 0,
                fidget: data.metrics.fidget_score || 0,
                smile: data.metrics.is_smiling,
                gesture: data.metrics.head_gesture
            });
        }
        if (data.type === 'ai_response') {
            setAiState('speaking');
            setTranscript(data.reply);
            speakText(data.reply);
        }
        if (data.type === 'error') {
            setAiState('idle');
            setTranscript(data.message);
        }
    };

    // Setup Camera & Mic
    navigator.mediaDevices.getUserMedia({ video: true, audio: true }).then(stream => {
        if (videoRef.current) videoRef.current.srcObject = stream;
        
        // Setup Audio Recorder
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
        recorder.onstop = () => {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob); 
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1];
                if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                    setAiState('processing');
                    setTranscript("Analyzing audio...");
                    socketRef.current.send(JSON.stringify({
                        type: "conversation",
                        audio_data: base64Audio,
                        landmarks: [] // We let the tracking loop handle landmarks
                    }));
                }
            };
            audioChunksRef.current = [];
        };
    }).catch(err => console.error("Media Error:", err));

    return () => {
        if (ws) ws.close();
    };
  }, [sessionId, initialQuestion]);

  // 2. FACE MESH LOOP (Using the global variables from CDN)
  useEffect(() => {
    const faceMesh = new FaceMesh({locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`});
    faceMesh.setOptions({ maxNumFaces: 1, refineLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
    
    faceMesh.onResults((results) => {
        const ctx = canvasRef.current.getContext('2d');
        ctx.clearRect(0, 0, 640, 480);
        
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            const landmarks = results.multiFaceLandmarks[0];
            
            // Draw
            // Note: We use the global `drawConnectors` from the CDN script
            drawConnectors(ctx, landmarks, FACEMESH_TESSELATION, {color: '#C0C0C070', lineWidth: 1});
            
            // Send Data (Throttled)
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && !isRecording && Math.random() > 0.7) {
                 socketRef.current.send(JSON.stringify({ type: "tracking", landmarks: landmarks }));
            }
        }
    });

    if (videoRef.current) {
        const camera = new Camera(videoRef.current, {
            onFrame: async () => { await faceMesh.send({image: videoRef.current}); },
            width: 640,
            height: 480
        });
        camera.start();
    }
  }, []);

  // 3. TOGGLE RECORDING
  const toggleRecording = () => {
    if (!mediaRecorderRef.current) return;

    if (isRecording) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
        setAiState('processing');
        window.speechSynthesis.cancel(); // Stop AI if user interrupts
    } else {
        mediaRecorderRef.current.start();
        setIsRecording(true);
        setAiState('listening');
        setTranscript("Listening...");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative w-full h-screen bg-black overflow-hidden flex">
      {/* LEFT: Mirror */}
      <div className="relative w-3/4 h-full p-6">
        <div className="relative w-full h-full rounded-3xl overflow-hidden border border-white/10 bg-gray-900 shadow-2xl">
            <video ref={videoRef} autoPlay muted className={`w-full h-full object-cover transform -scale-x-100 border-4 ${isRecording ? 'border-neon-red' : 'border-transparent'} transition-all`} />
            <canvas ref={canvasRef} width="640" height="480" className="absolute inset-0 w-full h-full pointer-events-none transform -scale-x-100" />
            
            <div className="absolute bottom-10 left-0 right-0 text-center px-20">
                <span className="inline-block bg-black/60 backdrop-blur-md text-white px-6 py-3 rounded-full text-lg font-medium shadow-lg">
                    {transcript}
                </span>
            </div>
        </div>
      </div>

      {/* RIGHT: HUD */}
      <div className="w-1/4 h-full bg-[#0f0f0f] border-l border-white/10 p-6 flex flex-col justify-between">
        <div className="flex flex-col items-center mt-10">
            <div className={`w-32 h-32 rounded-full border-2 flex items-center justify-center transition-all ${aiState === 'speaking' ? 'border-neon-cyan shadow-[0_0_30px_#00f3ff]' : 'border-gray-700'}`}>
                {aiState === 'listening' ? <Mic size={48} className="text-neon-red animate-pulse" /> : 
                 aiState === 'processing' ? <BrainCircuit size={48} className="text-yellow-400 animate-spin" /> : 
                 <Video size={48} className="text-gray-500" />}
            </div>
            <h2 className="mt-4 font-mono text-neon-cyan tracking-widest text-sm">STATUS: {aiState.toUpperCase()}</h2>
        </div>

        <div className="space-y-8">
            <div>
                <div className="flex justify-between text-sm text-gray-400 mb-1"><span>Composure</span><span>{Math.max(0, 100 - metrics.fidget).toFixed(0)}%</span></div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden"><motion.div animate={{ width: `${Math.max(0, 100 - metrics.fidget)}%` }} className="h-full bg-neon-green" /></div>
            </div>
            <button 
                onClick={toggleRecording}
                className={`w-full py-6 rounded-xl font-bold text-xl tracking-widest transition-all ${isRecording ? 'bg-neon-red text-white shadow-[0_0_30px_rgba(255,0,85,0.4)]' : 'bg-gray-800 text-gray-300 hover:bg-neon-cyan hover:text-black'}`}
            >
                {isRecording ? "STOP RECORDING" : "HOLD TO SPEAK"}
            </button>
        </div>

        <button onClick={onEnd} className="w-full py-4 text-red-500 hover:text-white hover:bg-red-600 rounded-lg transition-colors">TERMINATE SESSION</button>
      </div>
    </motion.div>
  );
};

// --- 3. RESULTS (Placeholder) ---
const Results = ({ onRestart }) => (
    <div className="h-screen flex flex-col items-center justify-center text-white">
        <h1 className="text-4xl">Session Complete</h1>
        <button onClick={onRestart} className="mt-8 px-6 py-3 bg-neon-cyan text-black rounded font-bold">Restart</button>
    </div>
);

// --- MAIN APP ---
function App() {
  const [view, setView] = useState('lobby');
  const [sessionData, setSessionData] = useState({ id: null, intro: "" });

  return (
    <div className="text-white font-sans selection:bg-neon-cyan selection:text-black">
      <AnimatePresence mode='wait'>
        {view === 'lobby' && <Lobby key="lobby" onStart={(id, intro) => { setSessionData({ id, intro }); setView('cockpit'); }} />}
        {view === 'cockpit' && <Cockpit key="cockpit" sessionId={sessionData.id} initialQuestion={sessionData.intro} onEnd={() => setView('results')} />}
        {view === 'results' && <Results key="results" onRestart={() => setView('lobby')} />}
      </AnimatePresence>
    </div>
  );
}

export default App;