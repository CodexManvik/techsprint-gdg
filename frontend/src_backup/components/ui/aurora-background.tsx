"use client";
import { cn } from "../../lib/utils";
import { motion } from "framer-motion";
import React from "react";

interface AuroraBackgroundProps extends React.HTMLProps<HTMLDivElement> {
    children: React.ReactNode;
    showRadialGradient?: boolean;
}

export const AuroraBackground = ({
    className,
    children,
    showRadialGradient = true,
    ...props
}: AuroraBackgroundProps) => {
    return (
        <div
            className={cn(
                "relative flex flex-col min-h-screen items-center justify-center bg-background text-foreground transition-bg",
                className
            )}
            {...props}
        >
            <div className="absolute inset-0 overflow-hidden fixed">
                <div
                    className={cn(
                        `
            [--aurora:repeating-linear-gradient(100deg,#3a0ca3_10%,#7c3aed_15%,#050505_20%,#3a0ca3_25%,#050505_30%)]
            [background-image:var(--aurora)]
            [background-size:300%_200%]
            [background-position:50%_50%]
            absolute inset-0
            opacity-40
            blur-[100px]
            will-change-transform
            `,
                        showRadialGradient &&
                        `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,transparent_70%)]`
                    )}
                    style={{
                        animation: "aurora 25s ease infinite",
                    }}
                />
                <div
                    className={cn(
                        `
            [--aurora:repeating-linear-gradient(100deg,#7c3aed_10%,#3a0ca3_15%,#050505_20%,#ec4899_25%,#3a0ca3_30%)]
            [background-image:var(--aurora)]
            [background-size:200%_100%]
            absolute inset-0
            opacity-20
            blur-[80px]
            will-change-transform
            `,
                        showRadialGradient &&
                        `[mask-image:radial-gradient(ellipse_at_0%_100%,black_10%,transparent_70%)]`
                    )}
                    style={{
                        animation: "aurora 30s ease infinite reverse",
                    }}
                />
            </div>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="relative z-10"
            >
                {children}
            </motion.div>
        </div>
    );
};
