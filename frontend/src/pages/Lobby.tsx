import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useSessionStore } from '../stores/sessionStore';
import { Mic, Camera, MonitorPlay, ChevronRight, Loader2, Code2, Cpu, TrendingUp } from 'lucide-react';

const PERSONAS = [
  {
    id: 'FAANG_Architect',
    name: 'Alex - System Architect',
    company: 'Google',
    focus: 'System Design',
    color: 'from-blue-500 to-cyan-400',
    description: "Expert in distributed systems and scalability.",
    icon: Code2
  },
  {
    id: 'Startup_Founder',
    name: 'Startup Founder',
    company: 'Startup',
    focus: 'Product & Speed',
    color: 'from-orange-500 to-red-500',
    description: "Focused on MVP, rapid iteration, and business value.",
    icon: TrendingUp
  },
  {
    id: 'HFT_Quant',
    name: 'David - Quant Dev',
    company: 'Jane Street',
    focus: 'Optimization & C++',
    color: 'from-green-500 to-emerald-600',
    description: "Obsessed with low-latency and algorithmic efficiency.",
    icon: Cpu
  },
  {
    id: 'Custom',
    name: 'Custom Persona',
    company: 'Your Choice',
    focus: 'Tailored Experience',
    color: 'from-purple-500 to-pink-500',
    description: "Create your own interviewer with specific instructions.",
    icon: Code2
  }
];

export const Lobby = () => {
  // const { user } = useAuth(); // Unused
  const navigate = useNavigate();
  const { setSessionId, setSelectedPersona, setResumeText } = useSessionStore();

  const [selectedPersonaId, setSelectedPersonaId] = useState(PERSONAS[0].id);
  const [difficulty, setDifficulty] = useState('Intermediate');
  const [isStarting, setIsStarting] = useState(false);
  const [permissions, setPermissions] = useState({ mic: false, cam: false });

  // Custom Persona State
  const [customName, setCustomName] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');

  // Resume State
  const [resumeFile, setLocalResumeFile] = useState<File | null>(null);
  const [isUploadingResume, setIsUploadingResume] = useState(false);

  // Check permissions on mount
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ audio: true, video: true })
      .then(() => setPermissions({ mic: true, cam: true }))
      .catch(() => setPermissions({ mic: false, cam: false }));
  }, []);

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLocalResumeFile(file);
    setIsUploadingResume(true);

    // Upload to get text
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/api/upload-resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.text) {
        setResumeText(res.data.text);
      }
    } catch (err) {
      console.error("Resume upload failed", err);
    } finally {
      setIsUploadingResume(false);
    }
  };

  const handleStart = async () => {
    setIsStarting(true);
    try {
      const persona = PERSONAS.find(p => p.id === selectedPersonaId);
      if (!persona) return;

      let payload: any = {
        persona: selectedPersonaId,
        difficulty: difficulty,
        topic: persona.focus || "General"
      };

      // Handle Custom Persona
      if (selectedPersonaId === 'Custom') {
        payload.custom_instructions = customInstructions;
        // Override persona-like fields for display (backend uses prompt)
        payload.topic = "Custom Topic";
      }

      // Included resume via sessionStore? 
      // Actually we need to pass it in payload if we want backend to save it in session context immediately
      const currentResumeText = useSessionStore.getState().resumeText;
      if (currentResumeText) {
        payload.resume_text = currentResumeText;
      }

      const res = await api.post('/api/start-interview', payload);

      if (res.data.session_id) {
        setSessionId(res.data.session_id);

        // Update store with custom details if needed
        if (selectedPersonaId === 'Custom') {
          setSelectedPersona({
            ...persona,
            name: customName || 'Custom Interviewer',
            description: 'Custom configured persona'
          });
        } else {
          setSelectedPersona(persona);
        }

        navigate(`/interview/${res.data.session_id}`);
      }
    } catch (err) {
      console.error("Failed to start interview", err);
      // Ideally show toast error here
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-6 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-purple-900/30 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-900/30 rounded-full blur-[120px]" />

      <div className="relative z-10 w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-12 items-center">

        {/* Left Column: Config */}
        <div>
          <h1 className="text-4xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-white to-neutral-400">
            Interview Setup
          </h1>
          <p className="text-neutral-400 mb-8">
            Configure your session. Our AI will adapt to your chosen difficulty and role.
          </p>

          <div className="space-y-6">
            {/* Persona Selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-3">Select Interviewer</label>
              <div className="space-y-3">
                {PERSONAS.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => setSelectedPersonaId(p.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedPersonaId === p.id
                      ? 'bg-neutral-800 border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.2)]'
                      : 'bg-neutral-900/50 border-neutral-800 hover:border-neutral-700'
                      }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${p.color}`} />
                        <div>
                          <div className="font-medium text-white">{p.name}</div>
                          <div className="text-xs text-neutral-400">{p.company} • {p.focus}</div>
                        </div>
                      </div>
                      {selectedPersonaId === p.id && <div className="text-purple-400">●</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Custom Persona Config */}
            {selectedPersonaId === 'Custom' && (
              <div className="bg-neutral-900/50 p-4 rounded-xl border border-purple-500/30 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div>
                  <label className="block text-xs font-medium text-neutral-400 mb-1">Interviewer Name</label>
                  <input
                    type="text"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    placeholder="e.g. Elon Musk, Senior Java Dev"
                    className="w-full bg-black/50 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 outline-none transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-400 mb-1">Instructions / System Prompt</label>
                  <textarea
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    placeholder="You are a strict interviewer focused on..."
                    rows={3}
                    className="w-full bg-black/50 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 outline-none resize-none transition-colors"
                  />
                </div>
              </div>
            )}

            {/* Difficulty */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-3">Difficulty Level</label>
              <div className="flex gap-2 bg-neutral-900/50 p-1 rounded-lg border border-neutral-800">
                {['Junior', 'Intermediate', 'Senior', 'Staff'].map((level) => (
                  <button
                    key={level}
                    onClick={() => setDifficulty(level)}
                    className={`flex-1 py-2 text-sm rounded-md transition-all ${difficulty === level
                      ? 'bg-neutral-800 text-white shadow-sm'
                      : 'text-neutral-400 hover:text-white'
                      }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>

            {/* Resume Upload */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-3">Upload Resume (Optional)</label>
              <div className="relative group">
                <input
                  type="file"
                  accept=".pdf,.txt,.doc,.docx"
                  onChange={handleResumeUpload}
                  className="hidden"
                  id="resume-upload"
                />
                <label
                  htmlFor="resume-upload"
                  className={`flex items-center justify-center gap-2 w-full p-3 rounded-xl border border-dashed transition-all cursor-pointer ${resumeFile
                      ? 'bg-green-500/10 border-green-500/50 text-green-400'
                      : 'bg-neutral-900/50 border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:bg-neutral-800'
                    }`}
                >
                  {isUploadingResume ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : resumeFile ? (
                    <>
                      <Code2 className="w-4 h-4" />
                      {resumeFile.name}
                    </>
                  ) : (
                    <>
                      <span className="text-xl">+</span>
                      <span className="text-sm">Upload PDF / Text</span>
                    </>
                  )}
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Preview & Launch */}
        <div className="flex flex-col items-center">
          {/* Camera Preview Mock */}
          <div className="w-full aspect-video bg-neutral-900 rounded-2xl border border-neutral-800 flex items-center justify-center mb-8 relative overflow-hidden group">
            {permissions.cam ? (
              <div className="absolute inset-0 flex items-center justify-center bg-neutral-800">
                {/* In a real app, Video element here. Mocking 'Active' state */}
                <div className="flex flex-col items-center gap-2">
                  <MonitorPlay className="w-10 h-10 text-purple-500 animate-pulse" />
                  <span className="text-sm text-neutral-400">Camera Active</span>
                </div>
              </div>
            ) : (
              <div className="text-center text-neutral-500">
                <Camera className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Camera access required</p>
              </div>
            )}

            {/* Tech Overlay */}
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20" />
            <div className="absolute bottom-4 left-4 flex gap-2">
              <div className={`px-2 py-1 rounded text-xs flex items-center gap-1 ${permissions.mic ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                <Mic className="w-3 h-3" /> {permissions.mic ? 'Mic On' : 'Check Mic'}
              </div>
            </div>
          </div>

          <button
            onClick={handleStart}
            disabled={isStarting || !permissions.mic}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 font-bold text-lg text-white shadow-[0_0_30px_rgba(124,58,237,0.4)] hover:shadow-[0_0_50px_rgba(124,58,237,0.6)] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStarting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                Start Interview <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
          {!permissions.mic && (
            <p className="text-xs text-red-400 mt-2">Microphone access is required to start.</p>
          )}
        </div>

      </div>
    </div>
  );
};
