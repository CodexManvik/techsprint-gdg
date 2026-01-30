"use client";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

interface MovingBorderProps {
    children: React.ReactNode;
    duration?: number;
    className?: string;
    containerClassName?: string;
    borderRadius?: string;
    as?: React.ElementType;
    borderClassName?: string;
}

export const MovingBorder = ({
    children,
    duration = 2000,
    className,
    containerClassName,
    borderRadius = "1rem",
    as: Component = "div",
    borderClassName,
    ...otherProps
}: MovingBorderProps & React.ComponentPropsWithoutRef<"div">) => {
    return (
        <Component
            className={cn(
                "relative p-[1px] overflow-hidden bg-transparent",
                containerClassName
            )}
            style={{
                borderRadius,
            }}
            {...otherProps}
        >
            <div
                className="absolute inset-0"
                style={{
                    borderRadius,
                }}
            >
                <div
                    className={cn(
                        "absolute inset-[-100%] bg-[conic-gradient(from_0deg,transparent_0_340deg,#3a0ca3_360deg)]",
                        borderClassName
                    )}
                    style={{
                        animation: `spin ${duration}ms linear infinite`,
                    }}
                />
            </div>
            <div
                className={cn(
                    "relative bg-background-secondary flex items-center justify-center w-full h-full",
                    className
                )}
                style={{
                    borderRadius: `calc(${borderRadius} - 1px)`,
                }}
            >
                {children}
            </div>
        </Component>
    );
};

interface GlowingBorderProps {
    children: React.ReactNode;
    className?: string;
    glowColor?: string;
}

export const GlowingBorder = ({
    children,
    className,
    glowColor = "rgba(58, 12, 163, 0.5)",
}: GlowingBorderProps) => {
    return (
        <div
            className={cn("relative rounded-xl p-[1px]", className)}
            style={{
                background: `linear-gradient(135deg, ${glowColor}, transparent, ${glowColor})`,
                boxShadow: `0 0 20px ${glowColor}`,
            }}
        >
            <div className="relative bg-background-secondary rounded-xl h-full w-full">
                {children}
            </div>
        </div>
    );
};

interface HoverBorderGradientProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    containerClassName?: string;
    className?: string;
    as?: React.ElementType;
}

export const HoverBorderGradient = ({
    children,
    containerClassName,
    className,
    as: Component = "button",
    ...props
}: HoverBorderGradientProps) => {
    return (
        <Component
            className={cn(
                "relative p-[2px] group inline-flex items-center justify-center rounded-full",
                containerClassName
            )}
            {...props}
        >
            <motion.div
                className="absolute inset-0 rounded-full bg-gradient-to-r from-primary via-accent-purple to-accent-pink opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                style={{ filter: "blur(8px)" }}
            />
            <div
                className={cn(
                    "relative bg-background-secondary px-6 py-2 rounded-full flex items-center gap-2 text-foreground font-medium transition-all duration-300 group-hover:bg-transparent",
                    className
                )}
            >
                {children}
            </div>
        </Component>
    );
};
