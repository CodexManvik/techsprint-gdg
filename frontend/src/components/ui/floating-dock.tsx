"use client";
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useRef, useState } from "react";
import { cn } from "../../lib/utils";

interface FloatingDockProps {
    items: {
        title: string;
        icon: React.ReactNode;
        onClick?: () => void;
        active?: boolean;
        danger?: boolean;
    }[];
    className?: string;
}

export const FloatingDock = ({ items, className }: FloatingDockProps) => {
    const mouseX = useMotionValue(Infinity);

    return (
        <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            onMouseMove={(e) => mouseX.set(e.pageX)}
            onMouseLeave={() => mouseX.set(Infinity)}
            className={cn(
                "fixed bottom-8 left-1/2 -translate-x-1/2 flex gap-3 px-4 py-3 rounded-2xl glass border-glow z-50",
                className
            )}
        >
            {items.map((item, index) => (
                <DockItem key={index} mouseX={mouseX} {...item} />
            ))}
        </motion.div>
    );
};

interface DockItemProps {
    title: string;
    icon: React.ReactNode;
    mouseX: any;
    onClick?: () => void;
    active?: boolean;
    danger?: boolean;
}

const DockItem = ({ title, icon, mouseX, onClick, active, danger }: DockItemProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [isHovered, setIsHovered] = useState(false);

    const distance = useTransform(mouseX, (val: number) => {
        const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 };
        return val - bounds.x - bounds.width / 2;
    });

    const widthSync = useTransform(distance, [-150, 0, 150], [48, 64, 48]);
    const heightSync = useTransform(distance, [-150, 0, 150], [48, 64, 48]);

    const width = useSpring(widthSync, {
        mass: 0.1,
        stiffness: 150,
        damping: 12,
    });

    const height = useSpring(heightSync, {
        mass: 0.1,
        stiffness: 150,
        damping: 12,
    });

    return (
        <motion.div
            ref={ref}
            style={{ width, height }}
            onClick={onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={cn(
                "relative flex items-center justify-center rounded-xl cursor-pointer transition-colors",
                danger
                    ? "bg-error/20 hover:bg-error/30 text-error"
                    : active
                        ? "bg-primary/30 text-primary"
                        : "bg-surface-light hover:bg-surface-elevated text-foreground-muted hover:text-foreground"
            )}
        >
            <div className="w-6 h-6 flex items-center justify-center">{icon}</div>
            <AnimatePresence>
                {isHovered && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.9 }}
                        transition={{ duration: 0.15 }}
                        className="absolute -top-12 px-3 py-1.5 rounded-lg glass text-sm font-medium whitespace-nowrap"
                    >
                        {title}
                        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 rotate-45 glass" />
                    </motion.div>
                )}
            </AnimatePresence>
            {active && (
                <motion.div
                    layoutId="active-indicator"
                    className="absolute -bottom-1 w-1.5 h-1.5 rounded-full bg-primary"
                />
            )}
        </motion.div>
    );
};
