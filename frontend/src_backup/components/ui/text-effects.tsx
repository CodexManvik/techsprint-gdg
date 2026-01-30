"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";

interface TypewriterEffectProps {
    words: {
        text: string;
        className?: string;
    }[];
    className?: string;
    cursorClassName?: string;
}

export const TypewriterEffect = ({
    words,
    className,
    cursorClassName,
}: TypewriterEffectProps) => {
    const [currentWordIndex, setCurrentWordIndex] = useState(0);
    const [currentText, setCurrentText] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
        const word = words[currentWordIndex].text;
        const timeout = setTimeout(
            () => {
                if (!isDeleting) {
                    if (currentText.length < word.length) {
                        setCurrentText(word.slice(0, currentText.length + 1));
                    } else {
                        setTimeout(() => setIsDeleting(true), 1500);
                    }
                } else {
                    if (currentText.length > 0) {
                        setCurrentText(word.slice(0, currentText.length - 1));
                    } else {
                        setIsDeleting(false);
                        setCurrentWordIndex((prev) => (prev + 1) % words.length);
                    }
                }
            },
            isDeleting ? 50 : 100
        );

        return () => clearTimeout(timeout);
    }, [currentText, isDeleting, currentWordIndex, words]);

    return (
        <div className={cn("inline-flex items-center", className)}>
            <span className={words[currentWordIndex].className}>{currentText}</span>
            <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                    duration: 0.5,
                    repeat: Infinity,
                    repeatType: "reverse",
                }}
                className={cn(
                    "inline-block w-[3px] h-[1em] bg-primary ml-1 rounded-full",
                    cursorClassName
                )}
            />
        </div>
    );
};

interface TypewriterEffectSmoothProps {
    words: {
        text: string;
        className?: string;
    }[];
    className?: string;
    cursorClassName?: string;
}

export const TypewriterEffectSmooth = ({
    words,
    className,
    cursorClassName,
}: TypewriterEffectSmoothProps) => {
    const wordsArray = words.map((word) => ({
        ...word,
        text: word.text.split(""),
    }));

    return (
        <div className={cn("flex items-center justify-center", className)}>
            <motion.div className="overflow-hidden">
                <motion.div
                    initial={{ width: "0%" }}
                    animate={{ width: "fit-content" }}
                    transition={{
                        duration: 2,
                        ease: "linear",
                        delay: 0.5,
                    }}
                    className="whitespace-nowrap"
                >
                    {wordsArray.map((word, idx) => (
                        <span key={idx} className="inline-block">
                            {word.text.map((char, charIdx) => (
                                <span
                                    key={charIdx}
                                    className={cn("text-foreground", word.className)}
                                >
                                    {char}
                                </span>
                            ))}
                            {idx < wordsArray.length - 1 && <span>&nbsp;</span>}
                        </span>
                    ))}
                </motion.div>
            </motion.div>
            <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                    duration: 0.8,
                    repeat: Infinity,
                    repeatType: "reverse",
                }}
                className={cn(
                    "inline-block rounded-sm w-[4px] h-8 bg-primary",
                    cursorClassName
                )}
            />
        </div>
    );
};

interface FlipWordsProps {
    words: string[];
    duration?: number;
    className?: string;
}

export const FlipWords = ({
    words,
    duration = 3000,
    className,
}: FlipWordsProps) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % words.length);
        }, duration);

        return () => clearInterval(interval);
    }, [words, duration]);

    return (
        <AnimatePresence mode="wait">
            <motion.span
                key={currentIndex}
                initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, y: -20, filter: "blur(8px)" }}
                transition={{ duration: 0.4 }}
                className={cn("inline-block text-gradient", className)}
            >
                {words[currentIndex]}
            </motion.span>
        </AnimatePresence>
    );
};

interface TextGenerateEffectProps {
    words: string;
    className?: string;
    filter?: boolean;
    duration?: number;
}

export const TextGenerateEffect = ({
    words,
    className,
    filter = true,
    duration = 0.5,
}: TextGenerateEffectProps) => {
    const wordsArray = words.split(" ");

    return (
        <motion.div className={cn("font-normal", className)}>
            {wordsArray.map((word, idx) => (
                <motion.span
                    key={word + idx}
                    initial={{
                        opacity: 0,
                        filter: filter ? "blur(10px)" : "none",
                    }}
                    animate={{
                        opacity: 1,
                        filter: filter ? "blur(0px)" : "none",
                    }}
                    transition={{
                        duration: duration,
                        delay: idx * 0.1,
                    }}
                    className="inline-block mr-1"
                >
                    {word}
                </motion.span>
            ))}
        </motion.div>
    );
};
