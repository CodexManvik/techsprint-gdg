import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface Metric {
  label: string;
  value: number;
  unit: string;
  status: 'good' | 'moderate' | 'poor';
  description: string;
}

interface MetricsGridProps {
  metrics: Metric[];
}

export const MetricsGrid = ({ metrics }: MetricsGridProps) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'text-green-600 bg-green-50';
      case 'moderate':
        return 'text-accent-amber bg-amber-50';
      case 'poor':
        return 'text-accent-red bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good':
        return <TrendingUp size={20} />;
      case 'poor':
        return <TrendingDown size={20} />;
      default:
        return <Minus size={20} />;
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <Card key={index}>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">{metric.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between mb-2">
              <div className="text-3xl font-bold text-slate-dark">
                {metric.value}
                <span className="text-lg text-gray-500 ml-1">{metric.unit}</span>
              </div>
              <div className={`p-2 rounded-lg ${getStatusColor(metric.status)}`}>
                {getStatusIcon(metric.status)}
              </div>
            </div>
            <p className="text-sm text-gray-600">{metric.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
