import { forwardRef } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { cn } from '../../lib/utils';

interface ButtonProps extends Omit<HTMLMotionProps<"button">, 'size'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'gradient' | 'glow';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled,
    children,
    ...props
  }, ref) => {
    const baseStyles = `
      relative inline-flex items-center justify-center font-medium
      rounded-xl transition-all duration-300 focus:outline-none
      focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2
      focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50
    `;

    const variants = {
      primary: `
        bg-primary text-white
        hover:bg-primary-light hover:shadow-lg hover:shadow-primary/25
        active:scale-[0.98]
      `,
      secondary: `
        bg-surface-light text-foreground border border-border
        hover:bg-surface-elevated hover:border-border-light
        active:scale-[0.98]
      `,
      ghost: `
        bg-transparent text-foreground-muted
        hover:bg-surface hover:text-foreground
        active:scale-[0.98]
      `,
      outline: `
        bg-transparent text-primary border border-primary/50
        hover:bg-primary/10 hover:border-primary
        active:scale-[0.98]
      `,
      gradient: `
        bg-gradient-to-r from-primary via-accent-purple to-accent-pink
        text-white shadow-lg shadow-primary/25
        hover:shadow-xl hover:shadow-primary/30 hover:scale-[1.02]
        active:scale-[0.98]
      `,
      glow: `
        bg-primary text-white glow-lg
        hover:shadow-[0_0_50px_rgba(58,12,163,0.6)]
        active:scale-[0.98]
      `,
    };

    const sizes = {
      sm: 'text-sm px-3 py-1.5 gap-1.5',
      md: 'text-sm px-4 py-2.5 gap-2',
      lg: 'text-base px-6 py-3 gap-2.5',
    };

    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
        whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
          />
        )}
        {children}

        {/* Shimmer effect for gradient variant */}
        {variant === 'gradient' && (
          <span className="absolute inset-0 rounded-xl overflow-hidden">
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          </span>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

// Export a simple version for backward compatibility
export default Button;
