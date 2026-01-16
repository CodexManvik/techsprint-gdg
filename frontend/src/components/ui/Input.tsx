import { type InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'w-full px-4 py-2 bg-white border border-gray-200 rounded-lg text-slate-dark placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:border-transparent transition-all',
        className
      )}
      {...props}
    />
  )
);

Input.displayName = 'Input';
