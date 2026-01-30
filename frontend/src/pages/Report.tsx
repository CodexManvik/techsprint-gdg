import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api } from '../lib/api';
import { ArrowLeft, Download, Share2, Star } from 'lucide-react';

interface Metric {
  label: string;
  value: number;
  unit: string;
  status: string;
  description: string;
}

interface ReportData {
  summary: string;
  overallScore: number;
  metrics: Metric[];
  radarData: any[];
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

export const Report = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const reportRes = await api.get(`/interview_report/${sessionId}`);
        setData(reportRes.data);
      } catch (err) {
        console.error("Failed to load report", err);
      } finally {
        setLoading(false);
      }
    };

    if (sessionId) fetchReport();
  }, [sessionId]);

  if (loading) return <div className="text-white flex justify-center items-center h-screen">Analyzing Session...</div>;
  if (!data) return <div className="text-white flex justify-center items-center h-screen">Report not found.</div>;

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center text-neutral-400 hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
        </button>

        <header className="flex justify-between items-start mb-12">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600 mb-2">
              Interview Analysis
            </h1>
            <p className="text-neutral-400">Session ID: {sessionId}</p>
          </div>
          <div className="flex gap-2">
            <button className="p-2 rounded-full bg-neutral-800 hover:bg-neutral-700 transition-colors">
              <Download className="w-5 h-5" />
            </button>
            <button className="p-2 rounded-full bg-neutral-800 hover:bg-neutral-700 transition-colors">
              <Share2 className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Overall Score */}
        <section className="mb-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="col-span-1 p-6 rounded-2xl bg-gradient-to-br from-purple-900/30 to-blue-900/30 border border-purple-500/20 flex flex-col items-center justify-center text-center">
            <div className="text-6xl font-bold text-white mb-2">{data.overallScore}</div>
            <div className="text-sm text-purple-300 uppercase tracking-widest">Overall Score</div>
          </div>

          <div className="col-span-2 p-6 rounded-2xl bg-neutral-900/50 border border-neutral-800">
            <h3 className="text-lg font-semibold mb-4">Executive Summary</h3>
            <p className="text-neutral-300 leading-relaxed">{data.summary}</p>
          </div>
        </section>

        {/* Metrics Grid */}
        <section className="mb-12">
          <h3 className="text-xl font-semibold mb-6">Performance Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.metrics.map((metric, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-neutral-900/50 border border-neutral-800 hover:border-purple-500/30 transition-colors group">
                <div className="text-xs text-neutral-500 uppercase mb-2 group-hover:text-purple-400 transition-colors">{metric.label}</div>
                <div className="flex items-baseline gap-1">
                  <div className="text-2xl font-bold" style={{
                    color: metric.status === 'good' ? '#4ade80' : metric.status === 'moderate' ? '#facc15' : '#f87171'
                  }}>
                    {metric.value}
                  </div>
                  <div className="text-xs text-neutral-500">{metric.unit}</div>
                </div>
                <div className="text-[10px] text-neutral-600 mt-2 truncate">{metric.description}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Chat Analysis */}
        <section>
          <h3 className="text-xl font-semibold mb-6">Transcript & Feedback</h3>
          <div className="space-y-6">
            {data.chatLog.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className={`p-6 rounded-xl border ${msg.role === 'ai' ? 'bg-neutral-900/30 border-neutral-800' : 'bg-neutral-900/80 border-purple-500/20'}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className={`text-xs font-bold uppercase ${msg.role === 'ai' ? 'text-blue-400' : 'text-purple-400'}`}>
                    {msg.role}
                  </span>
                  {msg.rating && (
                    <div className="flex items-center gap-1 text-yellow-500">
                      <Star className="w-3 h-3 fill-current" />
                      <span className="text-sm font-bold">{msg.rating}/5</span>
                    </div>
                  )}
                </div>

                <p className="text-neutral-200 mb-4">{msg.content}</p>

                {(msg.feedback || msg.improved_answer) && (
                  <div className="mt-4 pt-4 border-t border-neutral-800 space-y-3">
                    {msg.feedback && (
                      <div className="text-sm">
                        <span className="text-blue-400 font-semibold">Feedback: </span>
                        <span className="text-neutral-400">{msg.feedback}</span>
                      </div>
                    )}
                    {msg.improved_answer && (
                      <div className="text-sm bg-green-900/10 p-3 rounded border border-green-500/20">
                        <span className="text-green-400 font-semibold block mb-1">Better Answer: </span>
                        <span className="text-neutral-300 italic">"{msg.improved_answer}"</span>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};
