import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface SliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  min?: number;
  max?: number;
  step?: number;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  ({ className, label, min = 0, max = 100, step = 1, ...props }, ref) => (
    <div className="w-full">
      {label && <label className="block text-sm font-medium text-slate-dark mb-2">{label}</label>}
      <input
        ref={ref}
        type="range"
        min={min}
        max={max}
        step={step}
        className={cn(
          'w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb',
          className
        )}
        {...props}
      />
    </div>
  )
);

Slider.displayName = 'Slider';
