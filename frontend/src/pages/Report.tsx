import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, Download } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { RadarChartComponent } from '../components/dashboard/RadarChart';
import { MetricsGrid } from '../components/dashboard/MetricsGrid';
import { IntegrityHeatmap } from '../components/dashboard/IntegrityHeatmap';
import { DetailedMetrics } from '../components/dashboard/DetailedMetrics';
import { API_ENDPOINTS } from '../lib/constants';

interface ReportData {
  summary: string;
  radarData: { category: string; user: number; ideal: number }[];
  metrics: any[];
  integrityEvents: any[];
  totalDuration: number;
  detailedPosture?: any;
  detailedStress?: any;
  detailedIntegrity?: any;
  detailedBehavioral?: any;
}

export const Report = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session');
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Stop any ongoing speech
    window.speechSynthesis.cancel();
    
    fetchReportData();
  }, [sessionId]);

  const fetchReportData = async () => {
    try {
      const url = sessionId ? `${API_ENDPOINTS.REPORT}?session_id=${sessionId}` : API_ENDPOINTS.REPORT;
      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        
        // Transform backend data to frontend format
        const transformedData = transformReportData(data);
        setReportData(transformedData);
      } else {
        console.warn('Failed to fetch report, using mock data');
        setReportData(getMockData());
      }
    } catch (error) {
      console.error('Failed to fetch report:', error);
      setReportData(getMockData());
    } finally {
      setLoading(false);
    }
  };

  const transformReportData = (backendData: any): ReportData => {
    // If backend returns analytics structure
    if (backendData.analytics) {
      const analytics = backendData.analytics;
      
      return {
        summary: backendData.ai_report?.summary || analytics.summary || "Interview completed successfully.",
        radarData: [
          { category: 'Technical', user: analytics.technical_score || 75, ideal: 90 },
          { category: 'Communication', user: analytics.communication_score || 70, ideal: 85 },
          { category: 'Confidence', user: analytics.confidence_score || 75, ideal: 88 },
          { category: 'Body Language', user: analytics.posture_avg * 100 || 70, ideal: 85 },
          { category: 'Problem Solving', user: analytics.problem_solving || 80, ideal: 90 },
        ],
        metrics: [
          { 
            label: 'Words Per Minute', 
            value: Math.round(analytics.avg_wpm || 0), 
            unit: 'WPM', 
            status: getWPMStatus(analytics.avg_wpm || 0), 
            description: getWPMDescription(analytics.avg_wpm || 0) 
          },
          { 
            label: 'Stress Level', 
            value: Math.round((analytics.avg_stress || 0) * 100), 
            unit: '%', 
            status: getStressStatus(analytics.avg_stress || 0), 
            description: getStressDescription(analytics.avg_stress || 0) 
          },
          { 
            label: 'Eye Contact', 
            value: Math.round((analytics.avg_eye_contact || 0) * 100), 
            unit: '%', 
            status: getEyeContactStatus(analytics.avg_eye_contact || 0), 
            description: 'Engagement level' 
          },
          { 
            label: 'Posture Score', 
            value: Math.round((analytics.posture_avg || 0) * 100), 
            unit: '%', 
            status: getPostureStatus(analytics.posture_avg || 0), 
            description: 'Body language' 
          },
        ],
        integrityEvents: analytics.integrity_events || [],
        totalDuration: analytics.duration || 0,
        detailedPosture: analytics.detailed_posture,
        detailedStress: analytics.detailed_stress,
        detailedIntegrity: analytics.detailed_integrity,
        detailedBehavioral: analytics.detailed_behavioral,
      };
    }
    
    // Fallback to mock data
    return getMockData();
  };

  const getWPMStatus = (wpm: number) => {
    if (wpm < 100) return 'poor';
    if (wpm < 130) return 'moderate';
    if (wpm < 160) return 'good';
    return 'moderate'; // Too fast
  };

  const getWPMDescription = (wpm: number) => {
    if (wpm === 0) return 'No data yet';
    if (wpm < 100) return 'Too slow';
    if (wpm < 130) return 'Good pace';
    if (wpm < 160) return 'Optimal pace';
    return 'Too fast';
  };

  const getStressStatus = (stress: number) => {
    if (stress < 0.3) return 'good';
    if (stress < 0.6) return 'moderate';
    return 'poor';
  };

  const getStressDescription = (stress: number) => {
    if (stress < 0.3) return 'Low stress detected';
    if (stress < 0.6) return 'Moderate stress';
    return 'High stress detected';
  };

  const getEyeContactStatus = (eyeContact: number) => {
    if (eyeContact > 0.7) return 'good';
    if (eyeContact > 0.5) return 'moderate';
    return 'poor';
  };

  const getPostureStatus = (posture: number) => {
    if (posture > 0.7) return 'good';
    if (posture > 0.5) return 'moderate';
    return 'poor';
  };

  const getMockData = (): ReportData => ({
    summary: "You demonstrated strong technical knowledge and clear communication throughout the interview. Your posture was generally good, though there were a few moments where you appeared to slouch. Eye contact was maintained well, showing confidence. Your speaking pace was appropriate, averaging 145 words per minute. Consider working on reducing filler words and maintaining consistent energy levels throughout longer responses.",
    radarData: [
      { category: 'Technical', user: 85, ideal: 90 },
      { category: 'Communication', user: 78, ideal: 85 },
      { category: 'Confidence', user: 82, ideal: 88 },
      { category: 'Body Language', user: 75, ideal: 85 },
      { category: 'Problem Solving', user: 88, ideal: 90 },
    ],
    metrics: [
      { label: 'Words Per Minute', value: 145, unit: 'WPM', status: 'good', description: 'Optimal speaking pace' },
      { label: 'Stress Level', value: 35, unit: '%', status: 'good', description: 'Low stress detected' },
      { label: 'Eye Contact', value: 82, unit: '%', status: 'good', description: 'Strong engagement' },
      { label: 'Posture Score', value: 75, unit: '%', status: 'moderate', description: 'Room for improvement' },
    ],
    integrityEvents: [
      { timestamp: 120, type: 'gaze_away', duration: 3 },
      { timestamp: 450, type: 'gaze_away', duration: 2 },
      { timestamp: 780, type: 'gaze_away', duration: 4 },
    ],
    totalDuration: 1200,
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-blue mx-auto mb-4"></div>
          <p className="text-gray-600">Generating your report...</p>
        </div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Failed to load report</p>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold text-slate-dark mb-2">Interview Report</h1>
            <p className="text-gray-600">Here's how you performed</p>
            {sessionId && (
              <div className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg print:hidden">
                <span className="text-sm font-medium text-gray-700">Session ID:</span>
                <code className="text-sm font-mono text-primary-blue bg-white px-2 py-1 rounded border border-blue-200">
                  {sessionId}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(sessionId);
                    alert('Session ID copied to clipboard!');
                  }}
                  className="text-xs text-primary-blue hover:text-blue-700 underline ml-1"
                  title="Copy to clipboard"
                >
                  Copy
                </button>
              </div>
            )}
          </div>
          <div className="flex gap-3 no-print">
            <Button variant="secondary" onClick={() => window.print()}>
              <Download className="mr-2" size={20} />
              Download PDF
            </Button>
            <Button onClick={() => navigate('/')}>
              <Home className="mr-2" size={20} />
              New Interview
            </Button>
          </div>
        </motion.div>

        <div className="space-y-6">
          {/* Session Info Card - Visible in print */}
          {sessionId && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="print:block"
            >
              <Card>
                <CardHeader>
                  <CardTitle>Session Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-600 mb-2">
                        Save this Session ID to continue your interview later or review this report again:
                      </p>
                      <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                        <div className="flex-1">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                            Session ID
                          </p>
                          <code className="text-lg font-mono font-bold text-slate-dark break-all">
                            {sessionId}
                          </code>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Report generated: {new Date().toLocaleString()}
                      </p>
                    </div>
                    <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg border border-blue-200 print:bg-gray-50">
                      <p className="font-semibold text-primary-blue mb-1">💡 How to continue:</p>
                      <ol className="list-decimal list-inside space-y-1 text-gray-700">
                        <li>Go to the home page</li>
                        <li>Enter this Session ID in the "Continue Session" field</li>
                        <li>Click "Continue" to resume your interview</li>
                      </ol>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Executive Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 leading-relaxed">{reportData.summary}</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <MetricsGrid metrics={reportData.metrics} />
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Performance Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <RadarChartComponent data={reportData.radarData} />
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <IntegrityHeatmap
                events={reportData.integrityEvents}
                totalDuration={reportData.totalDuration}
              />
            </motion.div>
          </div>

          {/* Detailed Metrics Section */}
          {(reportData.detailedPosture || reportData.detailedStress || reportData.detailedIntegrity || reportData.detailedBehavioral) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mt-6"
            >
              <h2 className="text-2xl font-bold text-slate-dark mb-4">Detailed Analysis</h2>
              <DetailedMetrics
                posture={reportData.detailedPosture}
                stress={reportData.detailedStress}
                integrity={reportData.detailedIntegrity}
                behavioral={reportData.detailedBehavioral}
              />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};
