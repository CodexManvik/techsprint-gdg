"use client";
import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

interface SpotlightProps {
    className?: string;
    fill?: string;
}

export const Spotlight = ({ className, fill = "#3a0ca3" }: SpotlightProps) => {
    return (
        <svg
            className={cn(
                "animate-spotlight pointer-events-none absolute z-[1] h-[169%] w-[138%] lg:w-[84%] opacity-0",
                className
            )}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 3787 2842"
            fill="none"
        >
            <g filter="url(#filter)">
                <ellipse
                    cx="1924.71"
                    cy="273.501"
                    rx="1924.71"
                    ry="273.501"
                    transform="matrix(-0.822377 -0.568943 -0.568943 0.822377 3631.88 2291.09)"
                    fill={fill}
                    fillOpacity="0.21"
                />
            </g>
            <defs>
                <filter
                    id="filter"
                    x="0.860352"
                    y="0.838989"
                    width="3785.16"
                    height="2840.26"
                    filterUnits="userSpaceOnUse"
                    colorInterpolationFilters="sRGB"
                >
                    <feFlood floodOpacity="0" result="BackgroundImageFix" />
                    <feBlend
                        mode="normal"
                        in="SourceGraphic"
                        in2="BackgroundImageFix"
                        result="shape"
                    />
                    <feGaussianBlur
                        stdDeviation="151"
                        result="effect1_foregroundBlur_1065_8"
                    />
                </filter>
            </defs>
        </svg>
    );
};

interface CardSpotlightProps {
    children: React.ReactNode;
    className?: string;
    radius?: number;
    onClick?: () => void;
}

export const CardSpotlight = ({
    children,
    className,
    radius = 350,
    onClick,
}: CardSpotlightProps) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isHovered, setIsHovered] = useState(false);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        setPosition({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        });
    };

    return (
        <motion.div
            ref={containerRef}
            onClick={onClick}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={cn(
                "relative overflow-hidden rounded-xl border border-border bg-surface p-6",
                className
            )}
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
        >
            <motion.div
                className="pointer-events-none absolute -inset-px rounded-xl opacity-0 transition-opacity duration-300"
                style={{
                    background: `radial-gradient(${radius}px circle at ${position.x}px ${position.y}px, rgba(58, 12, 163, 0.25), transparent 60%)`,
                }}
                animate={{ opacity: isHovered ? 1 : 0 }}
            />
            <div className="relative z-10">{children}</div>
        </motion.div>
    );
};
