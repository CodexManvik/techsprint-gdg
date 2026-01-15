import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, Upload, BrainCircuit, XCircle, Activity, Eye, Play, 
  AlertTriangle, ChevronRight, BarChart3, TrendingUp, Award,
  Clock, MessageSquare, Zap, Target, CheckCircle2, XOctagon
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  AreaChart, Area
} from 'recharts';
import { Cockpit } from './CockpitComponent';

// ============================================================================
// COMPONENT: DASHBOARD (Landing Page)
// ============================================================================
const Dashboard = ({ onStart }) => {
  const [resumeText, setResumeText] = useState(null);
  const [config, setConfig] = useState({
    persona: "Google_SRE",
    difficulty: "Mid-Level",
    topic: "System Design"
  });
  const [options, setOptions] = useState({ personas: {}, difficulties: {}, topics: {} });
  const [isLoading, setIsLoading] = useState(false);
  const [prevSessions, setPrevSessions] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch available options from backend
    fetch('http://localhost:8000/config/options')
      .then(r => r.json())
      .then(data => setOptions(data))
      .catch(err => console.error("Failed to load options", err));

    // Load previous sessions from localStorage
    const saved = JSON.parse(localStorage.getItem("interview_sessions") || "[]");
    setPrevSessions(saved.slice(0, 3)); // Show last 3
  }, []);

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/upload-resume', { 
        method: 'POST', 
        body: formData 
      });
      const data = await res.json();
      if (data.status === 'success') {
        setResumeText(data.text);
      } else {
        setError("Resume parsing failed");
      }
    } catch (err) { 
      setError("Upload failed"); 
    }
    setIsLoading(false);
  };

  const startSession = async (usePrevious = false, sessionId = null) => {
    if (!usePrevious && !resumeText) {
      setError("⚠️ Please upload your resume to begin");
      return;
    }

    setIsLoading(true);
    setError(null);

    if (usePrevious && sessionId) {
      // Resume previous session
      onStart(sessionId, "Welcome back. Let's continue where we left off.", config);
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/start_interview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...config, resume_text: resumeText })
      });
      const data = await res.json();
      
      // Save session to localStorage
      const sessions = JSON.parse(localStorage.getItem("interview_sessions") || "[]");
      sessions.unshift({
        id: data.session_id,
        ...config,
        timestamp: new Date().toISOString()
      });
      localStorage.setItem("interview_sessions", JSON.stringify(sessions.slice(0, 10)));
      
      onStart(data.session_id, data.opening_question, config);
    } catch (err) { 
      setError("Server connection failed"); 
    }
    setIsLoading(false);
  };

  // Group personas by company
  const groupedPersonas = Object.entries(options.personas || {}).reduce((acc, [key, val]) => {
    if (!acc[val.company]) acc[val.company] = [];
    acc[val.company].push({ key, ...val });
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-blue-900 text-white">
      {/* Header */}
      <div className="border-b border-white/10 backdrop-blur-xl bg-black/30">
        <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Interview Mirror</h1>
            <p className="text-gray-400 text-sm mt-1">AI-Powered Interview Preparation</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-gray-400 font-mono">SYSTEM ONLINE</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* Error Alert */}
            <AnimatePresence>
              {error && (
                <motion.div 
                  initial={{ opacity: 0, y: -10 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-red-500/10 border border-red-500/50 p-4 rounded-xl text-red-200 flex items-center gap-3"
                >
                  <AlertTriangle size={20} />
                  <span className="text-sm font-medium">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Resume Upload */}
            <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Upload size={20} className="text-blue-400" />
                Resume Upload
              </h3>
              <div className="relative group cursor-pointer">
                <input 
                  type="file" 
                  accept=".pdf" 
                  onChange={handleResumeUpload} 
                  className="absolute inset-0 opacity-0 z-10 cursor-pointer" 
                />
                <div className={`p-6 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all ${
                  resumeText 
                    ? 'border-emerald-500 bg-emerald-500/10' 
                    : 'border-white/20 hover:border-white/40 hover:bg-white/5'
                }`}>
                  {resumeText ? (
                    <>
                      <CheckCircle2 size={32} className="text-emerald-400 mb-2" />
                      <span className="text-emerald-400 font-medium">Resume Analyzed</span>
                      <span className="text-xs text-gray-400 mt-1">
                        {resumeText.length} characters extracted
                      </span>
                    </>
                  ) : (
                    <>
                      <Upload size={32} className="text-gray-400 mb-2" />
                      <span className="text-gray-300 font-medium">Drop PDF or Click to Upload</span>
                      <span className="text-xs text-gray-500 mt-1">Required to start interview</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Company/Persona Selection */}
            <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target size={20} className="text-purple-400" />
                Select Company & Interviewer
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(groupedPersonas).map(([company, personas]) => (
                  personas.map(persona => (
                    <button
                      key={persona.key}
                      onClick={() => setConfig({ ...config, persona: persona.key })}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        config.persona === persona.key
                          ? 'border-blue-500 bg-blue-500/20 shadow-lg shadow-blue-500/20'
                          : 'border-white/10 hover:border-white/30 bg-white/5'
                      }`}
                    >
                      <div className="text-xs text-gray-400 mb-1">{company}</div>
                      <div className="text-sm font-medium">{persona.name}</div>
                    </button>
                  ))
                ))}
              </div>
            </div>

            {/* Difficulty & Topic */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Difficulty */}
              <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 size={20} className="text-yellow-400" />
                  Difficulty Level
                </h3>
                <div className="space-y-2">
                  {Object.entries(options.difficulties || {}).map(([key, name]) => (
                    <button
                      key={key}
                      onClick={() => setConfig({ ...config, difficulty: key })}
                      className={`w-full p-3 rounded-lg border transition-all text-left ${
                        config.difficulty === key
                          ? 'border-yellow-500 bg-yellow-500/20'
                          : 'border-white/10 hover:border-white/30 bg-white/5'
                      }`}
                    >
                      <span className="text-sm font-medium">{name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Topic */}
              <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Zap size={20} className="text-emerald-400" />
                  Interview Topic
                </h3>
                <div className="space-y-2">
                  {Object.keys(options.topics || {}).map(topic => (
                    <button
                      key={topic}
                      onClick={() => setConfig({ ...config, topic })}
                      className={`w-full p-3 rounded-lg border transition-all text-left ${
                        config.topic === topic
                          ? 'border-emerald-500 bg-emerald-500/20'
                          : 'border-white/10 hover:border-white/30 bg-white/5'
                      }`}
                    >
                      <span className="text-sm font-medium">{topic}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Start Button */}
            <button
              onClick={() => startSession(false)}
              disabled={isLoading || !resumeText}
              className="w-full py-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-700 disabled:to-gray-600 disabled:cursor-not-allowed text-white font-bold text-lg rounded-2xl shadow-2xl shadow-blue-900/50 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-3"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Initializing...
                </>
              ) : (
                <>
                  <Play size={24} />
                  Start Interview
                  <ChevronRight size={24} />
                </>
              )}
            </button>
          </div>

          {/* Right: Previous Sessions */}
          <div className="space-y-6">
            <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Clock size={20} className="text-blue-400" />
                Recent Sessions
              </h3>
              {prevSessions.length === 0 ? (
                <p className="text-gray-400 text-sm">No previous sessions</p>
              ) : (
                <div className="space-y-3">
                  {prevSessions.map(session => (
                    <div
                      key={session.id}
                      className="p-4 bg-white/5 rounded-xl border border-white/10 hover:border-white/30 transition-all cursor-pointer"
                      onClick={() => startSession(true, session.id)}
                    >
                      <div className="text-sm font-medium mb-1">{session.topic}</div>
                      <div className="text-xs text-gray-400">
                        {options.personas[session.persona]?.name || session.persona}
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        {new Date(session.timestamp).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-xl p-6 rounded-2xl border border-white/20">
              <h3 className="text-lg font-semibold mb-4">System Features</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <Eye size={16} className="text-blue-400" />
                  <span>Real-time eye contact tracking</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity size={16} className="text-emerald-400" />
                  <span>Body language analysis</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageSquare size={16} className="text-purple-400" />
                  <span>Live speech transcription</span>
                </div>
                <div className="flex items-center gap-2">
                  <Award size={16} className="text-yellow-400" />
                  <span>AI-powered feedback report</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENT: RESULTS PAGE (After-Action Report)
// ============================================================================
const ResultsPage = ({ sessionId, onBackToDashboard }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/interview_report/${sessionId}`)
      .then(r => r.json())
      .then(data => {
        setReport(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load report", err);
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Analyzing Performance...</p>
        </div>
      </div>
    );
  }

  if (!report || !report.ai_report) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <XOctagon size={64} className="text-red-500 mx-auto mb-4" />
          <p className="text-white text-lg mb-4">Failed to generate report</p>
          <button
            onClick={onBackToDashboard}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { analytics, ai_report } = report;
  const { radar_chart, feedback, summary } = ai_report;

  // Prepare timeline data for stress graph
  const timelineData = analytics.history.timestamps.map((time, idx) => ({
    time: `${Math.floor(time / 60)}:${(time % 60).toString().padStart(2, '0')}`,
    stress: analytics.history.stress_flags[idx] * 100,
    eyeContact: (analytics.history.eye_contact_scores[idx] || 0) * 100,
    fidget: analytics.history.fidget_scores[idx] || 0
  }));

  // Prepare radar chart data
  const radarData = [
    { skill: 'Technical', value: radar_chart.technical_accuracy },
    { skill: 'Communication', value: radar_chart.communication_clarity },
    { skill: 'Confidence', value: radar_chart.confidence_level },
    { skill: 'Problem Solving', value: radar_chart.problem_solving },
    { skill: 'Cultural Fit', value: radar_chart.cultural_fit }
  ];

  // Calculate overall score
  const overallScore = Math.round(
    Object.values(radar_chart).reduce((a, b) => a + b, 0) / Object.values(radar_chart).length
  );

  // Verdict styling
  const getVerdictStyle = () => {
    switch (feedback.hiring_verdict) {
      case 'STRONG HIRE':
        return 'bg-emerald-500 text-white border-emerald-400';
      case 'HIRE':
        return 'bg-blue-500 text-white border-blue-400';
      case 'NO HIRE':
        return 'bg-red-500 text-white border-red-400';
      default:
        return 'bg-gray-500 text-white border-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-blue-900 text-white">
      {/* Header */}
      <div className="border-b border-white/10 backdrop-blur-xl bg-black/30">
        <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Interview Report</h1>
            <p className="text-gray-400 text-sm mt-1">Performance Analysis & Feedback</p>
          </div>
          <button
            onClick={onBackToDashboard}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl border border-white/20 transition-all"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-12 space-y-8">
        {/* Top Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Overall Score */}
          <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-xl p-8 rounded-3xl border border-white/20 text-center">
            <div className="text-6xl font-bold mb-2">{overallScore}</div>
            <div className="text-gray-300 text-sm">Overall Score</div>
            <div className="mt-4 w-full h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                style={{ width: `${overallScore}%` }}
              />
            </div>
          </div>

          {/* Duration */}
          <div className="bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/10 text-center">
            <Clock size={48} className="text-blue-400 mx-auto mb-3" />
            <div className="text-3xl font-bold mb-2">
              {Math.floor(analytics.duration / 60)}:{(analytics.duration % 60).toString().padStart(2, '0')}
            </div>
            <div className="text-gray-300 text-sm">Interview Duration</div>
          </div>

          {/* Verdict */}
          <div className={`backdrop-blur-xl p-8 rounded-3xl border-4 text-center ${getVerdictStyle()}`}>
            <Award size={48} className="mx-auto mb-3" />
            <div className="text-3xl font-bold mb-2">{feedback.hiring_verdict}</div>
            <div className="text-sm opacity-90">Final Verdict</div>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/10">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
            <MessageSquare size={28} className="text-blue-400" />
            Executive Summary
          </h2>
          <p className="text-gray-300 text-lg leading-relaxed">{summary}</p>
        </div>

        {/* Radar Chart & Timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Skills Radar */}
          <div className="bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <Target size={28} className="text-purple-400" />
              Skills Assessment
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#ffffff20" />
                <PolarAngleAxis dataKey="skill" stroke="#ffffff60" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#ffffff40" />
                <Radar
                  name="Performance"
                  dataKey="value"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-4 mt-6">
              {radarData.map(item => (
                <div key={item.skill} className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">{item.skill}</span>
                  <span className="text-lg font-bold">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline Analysis */}
          <div className="bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <TrendingUp size={28} className="text-emerald-400" />
              Performance Timeline
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={timelineData}>
                <defs>
                  <linearGradient id="colorEye" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#ffffff40" />
                <YAxis stroke="#ffffff40" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#000000cc',
                    border: '1px solid #ffffff20',
                    borderRadius: '8px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="eyeContact"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#colorEye)"
                  name="Eye Contact"
                />
                <Area
                  type="monotone"
                  dataKey="stress"
                  stroke="#ef4444"
                  fillOpacity={1}
                  fill="url(#colorStress)"
                  name="Stress Level"
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="flex items-center justify-center gap-6 mt-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-emerald-500 rounded-full" />
                <span className="text-gray-400">Eye Contact</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-gray-400">Stress Level</span>
              </div>
            </div>
          </div>
        </div>

        {/* Strengths & Improvements */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Strengths */}
          <div className="bg-gradient-to-br from-emerald-500/20 to-green-500/20 backdrop-blur-xl p-8 rounded-3xl border border-emerald-500/30">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <CheckCircle2 size={28} className="text-emerald-400" />
              Strengths
            </h2>
            <ul className="space-y-4">
              {feedback.strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <CheckCircle2 size={16} className="text-emerald-400" />
                  </div>
                  <span className="text-gray-200">{strength}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Areas for Improvement */}
          <div className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 backdrop-blur-xl p-8 rounded-3xl border border-yellow-500/30">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <TrendingUp size={28} className="text-yellow-400" />
              Areas for Improvement
            </h2>
            <ul className="space-y-4">
              {feedback.improvements.map((improvement, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <AlertTriangle size={16} className="text-yellow-400" />
                  </div>
                  <span className="text-gray-200">{improvement}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Action Button */}
        <div className="text-center pt-8">
          <button
            onClick={onBackToDashboard}
            className="px-12 py-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-lg rounded-2xl shadow-2xl shadow-blue-900/50 transition-all transform hover:scale-105"
          >
            Start New Interview
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// APP ROOT
// ============================================================================
function App() {
  const [view, setView] = useState('dashboard'); // 'dashboard', 'cockpit', 'results'
  const [sessionData, setSessionData] = useState({ id: null, intro: "", config: {} });

  const handleStartInterview = (id, intro, config) => {
    setSessionData({ id, intro, config });
    setView('cockpit');
  };

  const handleEndInterview = (sessionId) => {
    setSessionData({ ...sessionData, id: sessionId });
    setView('results');
  };

  const handleBackToDashboard = () => {
    setView('dashboard');
    setSessionData({ id: null, intro: "", config: {} });
  };

  return (
    <div className="font-sans antialiased selection:bg-blue-500 selection:text-white">
      <AnimatePresence mode='wait'>
        {view === 'dashboard' && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Dashboard onStart={handleStartInterview} />
          </motion.div>
        )}
        {view === 'cockpit' && (
          <motion.div
            key="cockpit"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Cockpit
              sessionId={sessionData.id}
              initialQuestion={sessionData.intro}
              config={sessionData.config}
              onEnd={handleEndInterview}
            />
          </motion.div>
        )}
        {view === 'results' && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <ResultsPage
              sessionId={sessionData.id}
              onBackToDashboard={handleBackToDashboard}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
