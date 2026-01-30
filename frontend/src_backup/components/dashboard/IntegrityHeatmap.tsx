import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Eye, EyeOff } from 'lucide-react';

interface IntegrityEvent {
  timestamp: number;
  type: 'gaze_away' | 'multiple_faces' | 'no_face';
  duration: number;
}

interface IntegrityHeatmapProps {
  events: IntegrityEvent[];
  totalDuration: number;
}

export const IntegrityHeatmap = ({ events }: IntegrityHeatmapProps) => {
  const gazeAwayCount = events.filter(e => e.type === 'gaze_away').length;
  const multipleFacesCount = events.filter(e => e.type === 'multiple_faces').length;
  const noFaceCount = events.filter(e => e.type === 'no_face').length;

  const totalEvents = events.length;
  const integrityScore = Math.max(0, 100 - (totalEvents * 2));

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-accent-amber';
    return 'text-accent-red';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Integrity Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="text-center">
            <div className={`text-5xl font-bold ${getScoreColor(integrityScore)}`}>
              {integrityScore}%
            </div>
            <p className="text-gray-600 mt-2">Overall Integrity Score</p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <EyeOff className="text-gray-600" size={20} />
                <span className="text-sm font-medium text-slate-dark">Looked Away</span>
              </div>
              <span className="text-lg font-semibold text-slate-dark">{gazeAwayCount}x</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Eye className="text-gray-600" size={20} />
                <span className="text-sm font-medium text-slate-dark">Multiple Faces</span>
              </div>
              <span className="text-lg font-semibold text-slate-dark">{multipleFacesCount}x</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Eye className="text-gray-600" size={20} />
                <span className="text-sm font-medium text-slate-dark">Face Not Visible</span>
              </div>
              <span className="text-lg font-semibold text-slate-dark">{noFaceCount}x</span>
            </div>
          </div>

          {totalEvents > 10 && (
            <div className="mt-4 p-3 bg-amber-50 border border-accent-amber rounded-lg">
              <p className="text-sm text-gray-700">
                Multiple integrity flags detected. Consider maintaining better eye contact and ensuring you're alone during the interview.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
