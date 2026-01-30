import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  ({ className, label, showValue = true, formatValue, value, min = 0, max = 100, ...props }, ref) => {
    const percentage = ((Number(value) - Number(min)) / (Number(max) - Number(min))) * 100;
    const displayValue = formatValue ? formatValue(Number(value)) : value;

    return (
      <div className={cn('w-full space-y-3', className)}>
        {(label || showValue) && (
          <div className="flex justify-between items-center">
            {label && (
              <label className="text-sm font-medium text-foreground">
                {label}
              </label>
            )}
            {showValue && (
              <span className="text-sm font-semibold text-primary">
                {displayValue}
              </span>
            )}
          </div>
        )}
        <div className="relative">
          {/* Track background */}
          <div className="absolute top-1/2 -translate-y-1/2 w-full h-2 rounded-full bg-surface-elevated" />

          {/* Active track with gradient */}
          <motion.div
            className="absolute top-1/2 -translate-y-1/2 h-2 rounded-full bg-gradient-to-r from-primary to-accent-purple"
            style={{ width: `${percentage}%` }}
            initial={false}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.1 }}
          />

          {/* Glow effect on active track */}
          <motion.div
            className="absolute top-1/2 -translate-y-1/2 h-2 rounded-full bg-gradient-to-r from-primary to-accent-purple opacity-50 blur-sm"
            style={{ width: `${percentage}%` }}
          />

          {/* Input */}
          <input
            ref={ref}
            type="range"
            value={value}
            min={min}
            max={max}
            className="relative w-full h-2 appearance-none bg-transparent cursor-pointer z-10"
            {...props}
          />
        </div>
      </div>
    );
  }
);

Slider.displayName = 'Slider';

export default Slider;
