import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, RefreshCw, Printer, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ThemeToggle } from '../components/ui/ThemeToggle';
import { MetricsGrid } from '../components/dashboard/MetricsGrid';
import { RadarChartComponent } from '../components/dashboard/RadarChart';
import { ChatLog } from '../components/dashboard/ChatLog';
import { DotBackground } from '../components/ui/grid-background';
import { API_ENDPOINTS } from '../lib/constants';

interface ReportData {
  sessionId: string;
  summary: string;
  overallScore: number;
  metrics: {
    label: string;
    value: number;
    unit: string;
    status: 'good' | 'moderate' | 'poor';
    description: string;
  }[];
  radarData: {
    category: string;
    user: number;
    ideal: number;
  }[];
  chatLog: {
    id: string;
    role: 'ai' | 'user';
    content: string;
    timestamp: string;
    rating?: number;
    feedback?: string;
    improved_answer?: string;
  }[];
}

// Mock data for demonstration
const MOCK_DATA: ReportData = {
  sessionId: 'session_demo',
  summary: 'Great interview performance with strong technical knowledge. Focus on improving eye contact and reducing filler words.',
  overallScore: 78,
  metrics: [
    { label: 'Eye Contact', value: 72, unit: '%', status: 'moderate', description: 'Maintained eye contact most of the time' },
    { label: 'Posture', value: 85, unit: '%', status: 'good', description: 'Excellent upright posture throughout' },
    { label: 'Speech Clarity', value: 68, unit: '%', status: 'moderate', description: 'Some filler words detected' },
    { label: 'Confidence', value: 80, unit: '%', status: 'good', description: 'Spoke with good confidence' },
  ],
  radarData: [
    { category: 'Technical', user: 85, ideal: 90 },
    { category: 'Communication', user: 70, ideal: 85 },
    { category: 'Problem Solving', user: 78, ideal: 88 },
    { category: 'Body Language', user: 72, ideal: 80 },
    { category: 'Confidence', user: 80, ideal: 85 },
  ],
  chatLog: [
    { id: '1', role: 'ai', content: 'Tell me about yourself and your experience with distributed systems.', timestamp: '0:15' },
    { id: '2', role: 'user', content: 'I have 5 years of experience working with distributed systems, primarily focusing on microservices architecture and event-driven design patterns...', timestamp: '0:45', rating: 4, feedback: 'Good introduction but could be more concise' },
    { id: '3', role: 'ai', content: 'Can you describe a challenging technical problem you solved recently?', timestamp: '2:30' },
    { id: '4', role: 'user', content: 'Recently I worked on optimizing a database query that was causing performance issues in production. The query was taking 30 seconds to execute...', timestamp: '3:15', rating: 5, feedback: 'Excellent STAR method response with clear metrics' },
  ],
};

export const Report = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showChatLog, setShowChatLog] = useState(false);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await fetch(`${API_ENDPOINTS.REPORT}/${sessionId || ''}`);
        if (response.ok) {
          const data = await response.json();
          setReportData(data);
        } else {
          // Use mock data if API fails
          setReportData({ ...MOCK_DATA, sessionId: sessionId || 'demo' });
        }
      } catch (error) {
        // Use mock data if API fails
        setReportData({ ...MOCK_DATA, sessionId: sessionId || 'demo' });
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [sessionId]);

  const handleRateResponse = (messageId: string, rating: number) => {
    if (!reportData) return;
    setReportData({
      ...reportData,
      chatLog: reportData.chatLog.map((msg) =>
        msg.id === messageId ? { ...msg, rating } : msg
      ),
    });
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <DotBackground containerClassName="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-3 border-primary border-t-transparent rounded-full"
        />
      </DotBackground>
    );
  }

  if (!reportData) {
    return (
      <DotBackground containerClassName="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-4">Report not found</h2>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </div>
      </DotBackground>
    );
  }

  return (
    <DotBackground containerClassName="min-h-screen print:bg-white">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40 glass border-b border-border px-6 py-4 print:hidden">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-foreground-muted hover:text-foreground transition-colors"
          >
            <Home className="w-5 h-5" />
            <span className="font-medium">Home</span>
          </motion.button>
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={handlePrint}>
              <Printer className="w-4 h-4 mr-2" />
              Print
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto pt-24 pb-12 px-6">
        {/* Title Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-3">
            <span className="text-gradient">Interview Report</span>
          </h1>
          <p className="text-foreground-muted">
            Session ID: <span className="font-mono text-foreground">{reportData.sessionId}</span>
          </p>
        </motion.div>

        {/* Overall Score */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-8 mb-8 text-center"
        >
          <h2 className="text-lg font-medium text-foreground-muted mb-4">Overall Performance</h2>
          <div className="relative w-40 h-40 mx-auto mb-4">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="hsl(var(--surface-elevated))"
                strokeWidth="12"
              />
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="url(#scoreGradient)"
                strokeWidth="12"
                strokeDasharray={`${(reportData.overallScore / 100) * 440} 440`}
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3a0ca3" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-4xl font-bold text-foreground">{reportData.overallScore}</span>
            </div>
          </div>
          <p className="text-foreground-muted max-w-xl mx-auto">{reportData.summary}</p>
        </motion.div>

        {/* Metrics Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <h2 className="text-2xl font-bold text-foreground mb-4">Performance Breakdown</h2>
          <MetricsGrid metrics={reportData.metrics} />
        </motion.div>

        {/* Radar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass rounded-2xl p-8 mb-8"
        >
          <h2 className="text-2xl font-bold text-foreground mb-4">Skills Comparison</h2>
          <RadarChartComponent data={reportData.radarData} />
        </motion.div>

        {/* Chat Log Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-2xl p-8"
        >
          <button
            onClick={() => setShowChatLog(!showChatLog)}
            className="w-full flex items-center justify-between text-left"
          >
            <h2 className="text-2xl font-bold text-foreground">Interview Transcript</h2>
            {showChatLog ? (
              <ChevronUp className="w-6 h-6 text-foreground-muted" />
            ) : (
              <ChevronDown className="w-6 h-6 text-foreground-muted" />
            )}
          </button>

          {showChatLog && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-6"
            >
              <ChatLog messages={reportData.chatLog} onRateResponse={handleRateResponse} />
            </motion.div>
          )}
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex flex-wrap justify-center gap-4 mt-8 print:hidden"
        >
          <Button variant="gradient" onClick={() => navigate('/lobby')}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Practice Again
          </Button>
          <Button variant="secondary" onClick={() => navigate('/')}>
            <Home className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </motion.div>
      </div>
    </DotBackground>
  );
};
