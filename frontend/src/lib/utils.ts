import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to merge Tailwind CSS classes with proper precedence.
 * Combines clsx for conditional classes with tailwind-merge for deduplication.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Animation timing constants for consistent motion design
 */
export const ANIMATION = {
  duration: {
    fast: 0.15,
    normal: 0.3,
    slow: 0.5,
    slower: 0.8,
  },
  ease: {
    default: [0.4, 0, 0.2, 1],
    smooth: [0.25, 0.1, 0.25, 1],
    bounce: [0.68, -0.55, 0.265, 1.55],
  },
} as const;

/**
 * Color palette for the application
 */
export const COLORS = {
  primary: {
    purple: "#3a0ca3",
    black: "#050505",
  },
  gradient: {
    primary: "linear-gradient(135deg, #3a0ca3 0%, #050505 100%)",
    accent: "linear-gradient(135deg, #7209b7 0%, #3a0ca3 100%)",
    glow: "radial-gradient(ellipse at center, rgba(58, 12, 163, 0.4) 0%, transparent 70%)",
  },
} as const;
