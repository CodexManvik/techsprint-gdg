"use client";
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';
import { cn } from '../../lib/utils';

interface ThemeToggleProps {
    className?: string;
}

export const ThemeToggle = ({ className }: ThemeToggleProps) => {
    const { theme, toggleTheme } = useTheme();

    return (
        <motion.button
            onClick={toggleTheme}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={cn(
                'relative w-14 h-7 rounded-full p-1 transition-colors duration-300',
                theme === 'dark'
                    ? 'bg-primary/20 border border-primary/30'
                    : 'bg-yellow-100 border border-yellow-300',
                className
            )}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
            {/* Background glow */}
            <motion.div
                className={cn(
                    'absolute inset-0 rounded-full opacity-50 blur-md',
                    theme === 'dark' ? 'bg-primary/30' : 'bg-yellow-300/50'
                )}
                animate={{
                    opacity: [0.3, 0.5, 0.3],
                }}
                transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                }}
            />

            {/* Toggle knob */}
            <motion.div
                className={cn(
                    'relative w-5 h-5 rounded-full flex items-center justify-center',
                    theme === 'dark' ? 'bg-primary' : 'bg-yellow-400'
                )}
                animate={{
                    x: theme === 'dark' ? 0 : 28,
                }}
                transition={{
                    type: 'spring',
                    stiffness: 500,
                    damping: 30,
                }}
            >
                <motion.div
                    initial={false}
                    animate={{ rotate: theme === 'dark' ? 0 : 360 }}
                    transition={{ duration: 0.5 }}
                >
                    {theme === 'dark' ? (
                        <Moon className="w-3 h-3 text-white" />
                    ) : (
                        <Sun className="w-3 h-3 text-yellow-900" />
                    )}
                </motion.div>
            </motion.div>

            {/* Stars decoration for dark mode */}
            {theme === 'dark' && (
                <>
                    <motion.div
                        className="absolute top-1.5 right-3 w-0.5 h-0.5 bg-white rounded-full"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                    />
                    <motion.div
                        className="absolute top-3 right-1.5 w-0.5 h-0.5 bg-white rounded-full"
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                    />
                </>
            )}
        </motion.button>
    );
};

export default ThemeToggle;
