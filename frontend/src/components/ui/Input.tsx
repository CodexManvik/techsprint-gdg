import { forwardRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';

interface InputProps {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'glass' | 'glow';
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onKeyPress?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  className?: string;
  disabled?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, variant = 'default', type = 'text', ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    const handleFocus = () => {
      setIsFocused(true);
      props.onFocus?.();
    };

    const handleBlur = () => {
      setIsFocused(false);
      props.onBlur?.();
    };

    const variants = {
      default: `
        bg-surface border border-border
        focus:border-primary focus:ring-2 focus:ring-primary/20
      `,
      glass: `
        glass border-border-light
        focus:border-primary/50 focus:ring-2 focus:ring-primary/20
      `,
      glow: `
        bg-surface border border-primary/30
        focus:border-primary focus:ring-2 focus:ring-primary/30 focus:shadow-[0_0_20px_rgba(58,12,163,0.3)]
      `,
    };

    return (
      <div className="w-full space-y-2">
        {label && (
          <label className="block text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-muted">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            type={type}
            onFocus={handleFocus}
            onBlur={handleBlur}
            className={cn(
              'w-full px-4 py-3 rounded-xl text-foreground placeholder:text-foreground-muted',
              'transition-all duration-300 outline-none',
              variants[variant],
              icon && 'pl-10',
              error && 'border-error focus:border-error focus:ring-error/20',
              className
            )}
            {...props}
          />

          {/* Focus indicator line */}
          <motion.div
            className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-primary to-accent-purple rounded-full"
            initial={{ width: 0, opacity: 0 }}
            animate={{
              width: isFocused ? '100%' : 0,
              opacity: isFocused ? 1 : 0,
            }}
            transition={{ duration: 0.3 }}
          />
        </div>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-sm text-error"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

Input.displayName = 'Input';

interface TextareaProps {
  label?: string;
  error?: string;
  variant?: 'default' | 'glass' | 'glow';
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  className?: string;
  disabled?: boolean;
  rows?: number;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, variant = 'default', ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    const handleFocus = () => {
      setIsFocused(true);
      props.onFocus?.();
    };

    const handleBlur = () => {
      setIsFocused(false);
      props.onBlur?.();
    };

    const variants = {
      default: `
        bg-surface border border-border
        focus:border-primary focus:ring-2 focus:ring-primary/20
      `,
      glass: `
        glass border-border-light
        focus:border-primary/50 focus:ring-2 focus:ring-primary/20
      `,
      glow: `
        bg-surface border border-primary/30
        focus:border-primary focus:ring-2 focus:ring-primary/30 focus:shadow-[0_0_20px_rgba(58,12,163,0.3)]
      `,
    };

    return (
      <div className="w-full space-y-2">
        {label && (
          <label className="block text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <div className="relative">
          <textarea
            ref={ref}
            onFocus={handleFocus}
            onBlur={handleBlur}
            className={cn(
              'w-full px-4 py-3 rounded-xl text-foreground placeholder:text-foreground-muted',
              'transition-all duration-300 outline-none resize-none min-h-[120px]',
              variants[variant],
              error && 'border-error focus:border-error focus:ring-error/20',
              className
            )}
            {...props}
          />

          {/* Focus indicator line */}
          <motion.div
            className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-primary to-accent-purple rounded-full"
            initial={{ width: 0, opacity: 0 }}
            animate={{
              width: isFocused ? '100%' : 0,
              opacity: isFocused ? 1 : 0,
            }}
            transition={{ duration: 0.3 }}
          />
        </div>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-sm text-error"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Input;
