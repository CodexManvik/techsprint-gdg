import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../../lib/utils';

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
  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'good':
        return {
          bg: 'bg-success/20',
          text: 'text-success',
          glow: 'shadow-[0_0_15px_rgba(34,197,94,0.3)]',
          gradient: 'from-success/20 to-transparent',
        };
      case 'moderate':
        return {
          bg: 'bg-warning/20',
          text: 'text-warning',
          glow: 'shadow-[0_0_15px_rgba(245,158,11,0.3)]',
          gradient: 'from-warning/20 to-transparent',
        };
      case 'poor':
        return {
          bg: 'bg-error/20',
          text: 'text-error',
          glow: 'shadow-[0_0_15px_rgba(239,68,68,0.3)]',
          gradient: 'from-error/20 to-transparent',
        };
      default:
        return {
          bg: 'bg-surface-elevated',
          text: 'text-foreground-muted',
          glow: '',
          gradient: 'from-surface-elevated to-transparent',
        };
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good':
        return <TrendingUp className="w-5 h-5" />;
      case 'poor':
        return <TrendingDown className="w-5 h-5" />;
      default:
        return <Minus className="w-5 h-5" />;
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => {
        const styles = getStatusStyles(metric.status);

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -3, scale: 1.02 }}
            className={cn(
              'glass rounded-xl p-5 relative overflow-hidden',
              styles.glow
            )}
          >
            {/* Background gradient */}
            <div className={cn(
              'absolute inset-0 bg-gradient-to-br opacity-50',
              styles.gradient
            )} />

            <div className="relative z-10">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-foreground-muted">{metric.label}</span>
                <div className={cn('p-2 rounded-lg', styles.bg, styles.text)}>
                  {getStatusIcon(metric.status)}
                </div>
              </div>

              <div className="mb-2">
                <span className="text-3xl font-bold text-foreground">{metric.value}</span>
                <span className="text-lg text-foreground-muted ml-1">{metric.unit}</span>
              </div>

              <p className="text-sm text-foreground-muted">{metric.description}</p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
