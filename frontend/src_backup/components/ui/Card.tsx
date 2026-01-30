import { useState, useRef, forwardRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface CardProps {
  variant?: 'default' | 'glass' | 'spotlight' | 'gradient' | 'glow';
  hover?: boolean;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card = ({
  className,
  variant = 'default',
  hover = true,
  children,
  onClick,
}: CardProps) => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current || variant !== 'spotlight') return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  const variants = {
    default: 'bg-surface border border-border',
    glass: 'glass',
    spotlight: 'bg-surface border border-border relative overflow-hidden',
    gradient: 'bg-gradient-to-br from-surface-elevated to-surface border border-border-light',
    glow: 'bg-surface border-glow',
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onClick={onClick}
      whileHover={hover ? { scale: 1.01, y: -2 } : undefined}
      transition={{ duration: 0.2 }}
      className={cn(
        'rounded-xl p-6 transition-all duration-300',
        variants[variant],
        className
      )}
    >
      {/* Spotlight effect */}
      {variant === 'spotlight' && (
        <div
          className="pointer-events-none absolute -inset-px opacity-0 hover:opacity-100 transition-opacity duration-300"
          style={{
            background: `radial-gradient(400px circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(58, 12, 163, 0.15), transparent 50%)`,
          }}
        />
      )}
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
};


interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, children }, ref) => (
    <div
      ref={ref}
      className={cn('mb-4', className)}
    >
      {children}
    </div>
  )
);

CardHeader.displayName = 'CardHeader';

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, children }, ref) => (
    <h3
      ref={ref}
      className={cn('text-xl font-semibold text-foreground', className)}
    >
      {children}
    </h3>
  )
);

CardTitle.displayName = 'CardTitle';

interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, children }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-foreground-muted mt-1', className)}
    >
      {children}
    </p>
  )
);

CardDescription.displayName = 'CardDescription';

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, children }, ref) => (
    <div
      ref={ref}
      className={cn('', className)}
    >
      {children}
    </div>
  )
);

CardContent.displayName = 'CardContent';

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, children }, ref) => (
    <div
      ref={ref}
      className={cn('mt-4 pt-4 border-t border-border', className)}
    >
      {children}
    </div>
  )
);

CardFooter.displayName = 'CardFooter';
