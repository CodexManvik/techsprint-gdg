"use client";
import React from "react";
import { cn } from "../../lib/utils";

interface GridBackgroundProps {
    children?: React.ReactNode;
    className?: string;
    containerClassName?: string;
}

export const GridBackground = ({
    children,
    className,
    containerClassName,
}: GridBackgroundProps) => {
    return (
        <div
            className={cn(
                "h-full w-full bg-background relative flex items-center justify-center",
                containerClassName
            )}
        >
            {/* Grid pattern */}
            <div
                className={cn(
                    "absolute inset-0",
                    "[background-image:linear-gradient(to_right,rgba(58,12,163,0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgba(58,12,163,0.1)_1px,transparent_1px)] dark:[background-image:linear-gradient(to_right,rgba(58,12,163,0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgba(58,12,163,0.1)_1px,transparent_1px)]",
                    "[background-size:40px_40px]",
                    className
                )}
            />
            {/* Radial gradient overlay */}
            <div className="absolute inset-0 bg-background [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />
            {/* Content */}
            <div className="relative z-10">{children}</div>
        </div>
    );
};

export const DotBackground = ({
    children,
    className,
    containerClassName,
}: GridBackgroundProps) => {
    return (
        <div
            className={cn(
                "h-full w-full bg-background relative flex items-center justify-center",
                containerClassName
            )}
        >
            {/* Dot pattern */}
            <div
                className={cn(
                    "absolute inset-0",
                    "[background-image:radial-gradient(rgba(58,12,163,0.2)_1px,transparent_1px)] dark:[background-image:radial-gradient(rgba(58,12,163,0.3)_1px,transparent_1px)]",
                    "[background-size:20px_20px]",
                    className
                )}
            />
            {/* Radial gradient overlay */}
            <div className="absolute inset-0 bg-background [mask-image:radial-gradient(ellipse_at_center,transparent_30%,black)]" />
            {/* Content */}
            <div className="relative z-10">{children}</div>
        </div>
    );
};
