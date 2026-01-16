import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface DetailedMetricsProps {
  posture?: any;
  stress?: any;
  integrity?: any;
  behavioral?: any;
}

export const DetailedMetrics = ({ posture, stress, integrity, behavioral }: DetailedMetricsProps) => {
  if (!posture && !stress && !integrity && !behavioral) {
    return null;
  }

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getAssessmentColor = (assessment: string) => {
    switch (assessment) {
      case 'low': case 'clean': case 'good': return 'text-green-600';
      case 'moderate': case 'suspicious': return 'text-yellow-600';
      case 'high': case 'highly_suspicious': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Posture Details */}
      {posture && (
        <Card>
          <CardHeader>
            <CardTitle>Posture Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Overall Quality:</span>
                <span className={`font-semibold capitalize ${getQualityColor(posture.posture_quality)}`}>
                  {posture.posture_quality}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Avg Slouch Score:</span>
                <span className="font-semibold">{(posture.avg_slouch_score * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Shoulder Stability:</span>
                <span className="font-semibold">{(posture.avg_shoulder_stability * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Arms Crossed:</span>
                <span className="font-semibold">{posture.arms_crossed_percentage.toFixed(1)}% of time</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Shoulder Angle:</span>
                <span className="font-semibold">{posture.avg_shoulder_angle.toFixed(1)}°</span>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Analyzed {posture.frames_analyzed} frames
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stress Details */}
      {stress && (
        <Card>
          <CardHeader>
            <CardTitle>Stress Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Overall Assessment:</span>
                <span className={`font-semibold capitalize ${getAssessmentColor(stress.stress_assessment)}`}>
                  {stress.stress_assessment}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Avg Blink Rate:</span>
                <span className="font-semibold">{stress.avg_blink_rate.toFixed(1)} blinks/min</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Blinks:</span>
                <span className="font-semibold">{stress.total_blinks}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Lip Pursing Events:</span>
                <span className="font-semibold">{stress.lip_pursing_count}</span>
              </div>
              {stress.max_lip_purse_duration > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Max Lip Purse:</span>
                  <span className="font-semibold">{stress.max_lip_purse_duration.toFixed(1)}s</span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Cognitive Load:</span>
                <span className={`font-semibold ${stress.high_cognitive_load_detected ? 'text-red-600' : 'text-green-600'}`}>
                  {stress.high_cognitive_load_detected ? 'High' : 'Normal'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrity Details */}
      {integrity && (
        <Card>
          <CardHeader>
            <CardTitle>Integrity Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Assessment:</span>
                <span className={`font-semibold capitalize ${getAssessmentColor(integrity.integrity_assessment)}`}>
                  {integrity.integrity_assessment}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Integrity Score:</span>
                <span className="font-semibold">{(integrity.avg_integrity_score * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Suspicious Events:</span>
                <span className="font-semibold">{integrity.suspicious_event_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Gaze Dispersion:</span>
                <span className="font-semibold">{(integrity.gaze_dispersion * 100).toFixed(1)}%</span>
              </div>
              {integrity.recommendations && integrity.recommendations.length > 0 && (
                <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-xs font-semibold text-yellow-800 mb-2">Recommendations:</p>
                  <ul className="text-xs text-yellow-700 space-y-1">
                    {integrity.recommendations.map((rec: string, idx: number) => (
                      <li key={idx}>• {rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Behavioral Details */}
      {behavioral && (
        <Card>
          <CardHeader>
            <CardTitle>Behavioral Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Engagement Score:</span>
                <span className="font-semibold">{behavioral.engagement_score}/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Nodding (Agreement):</span>
                <span className="font-semibold">{behavioral.nodding_count} times</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Head Shaking:</span>
                <span className="font-semibold">{behavioral.shaking_count} times</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Smile Count:</span>
                <span className="font-semibold">{behavioral.smile_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">High Load Frames:</span>
                <span className="font-semibold">{behavioral.high_cognitive_load_frames}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
