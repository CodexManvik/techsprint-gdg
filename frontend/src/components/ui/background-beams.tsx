"use client";
import React from "react";
import { cn } from "../../lib/utils";

export const BackgroundBeams = React.memo(
    ({ className }: { className?: string }) => {
        const beams = [
            { left: "10%", delay: 0, duration: 8 },
            { left: "20%", delay: 1, duration: 10 },
            { left: "35%", delay: 2, duration: 7 },
            { left: "55%", delay: 0.5, duration: 9 },
            { left: "70%", delay: 1.5, duration: 11 },
            { left: "85%", delay: 2.5, duration: 8 },
            { left: "95%", delay: 3, duration: 10 },
        ];

        return (
            <div
                className={cn(
                    "absolute inset-0 overflow-hidden pointer-events-none",
                    className
                )}
            >
                <svg
                    className="absolute inset-0 w-full h-full"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <defs>
                        <linearGradient id="beamGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="rgba(58, 12, 163, 0)" />
                            <stop offset="50%" stopColor="rgba(124, 58, 237, 0.5)" />
                            <stop offset="100%" stopColor="rgba(58, 12, 163, 0)" />
                        </linearGradient>
                        <filter id="glow">
                            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>
                    {beams.map((beam, index) => (
                        <rect
                            key={index}
                            x={beam.left}
                            y="-100%"
                            width="2"
                            height="100%"
                            fill="url(#beamGradient)"
                            filter="url(#glow)"
                            style={{
                                animation: `beam ${beam.duration}s ${beam.delay}s ease-in-out infinite`,
                            }}
                        />
                    ))}
                </svg>
            </div>
        );
    }
);

BackgroundBeams.displayName = "BackgroundBeams";
