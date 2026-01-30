import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Star, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ChatMessage {
    id: string;
    role: 'ai' | 'user';
    content: string;
    timestamp: string;
    rating?: number;
    feedback?: string;
    improved_answer?: string;
}

interface ChatLogProps {
    messages: ChatMessage[];
    onRateResponse?: (messageId: string, rating: number) => void;
}

export const ChatLog = ({ messages, onRateResponse }: ChatLogProps) => {
    const [expandedMessage, setExpandedMessage] = useState<string | null>(null);

    const toggleExpand = (id: string) => {
        setExpandedMessage(expandedMessage === id ? null : id);
    };

    const renderStars = (messageId: string, currentRating?: number) => {
        return (
            <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                    <motion.button
                        key={star}
                        whileHover={{ scale: 1.2 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={(e) => {
                            e.stopPropagation();
                            onRateResponse?.(messageId, star);
                        }}
                        className="focus:outline-none"
                    >
                        <Star
                            className={cn(
                                'w-4 h-4 transition-colors',
                                currentRating && star <= currentRating
                                    ? 'text-warning fill-warning'
                                    : 'text-foreground-muted hover:text-warning'
                            )}
                        />
                    </motion.button>
                ))}
            </div>
        );
    };

    return (
        <div className="space-y-4">
            <h3 className="text-xl font-bold text-foreground mb-4">Interview Transcript</h3>

            <div className="space-y-3">
                {messages.map((message, index) => (
                    <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={cn(
                            'glass rounded-xl p-4 cursor-pointer transition-all',
                            message.role === 'ai'
                                ? 'border-l-4 border-l-primary'
                                : 'border-l-4 border-l-success'
                        )}
                        onClick={() => toggleExpand(message.id)}
                    >
                        <div className="flex items-start gap-3">
                            {/* Avatar */}
                            <div className={cn(
                                'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                                message.role === 'ai'
                                    ? 'bg-primary/20 text-primary'
                                    : 'bg-success/20 text-success'
                            )}>
                                {message.role === 'ai' ? (
                                    <Bot className="w-5 h-5" />
                                ) : (
                                    <User className="w-5 h-5" />
                                )}
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm font-medium text-foreground">
                                        {message.role === 'ai' ? 'Interviewer' : 'You'}
                                    </span>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-foreground-muted">{message.timestamp}</span>
                                        {expandedMessage === message.id ? (
                                            <ChevronUp className="w-4 h-4 text-foreground-muted" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-foreground-muted" />
                                        )}
                                    </div>
                                </div>

                                {/* Preview or full content */}
                                <p className={cn(
                                    'text-foreground-muted text-sm transition-all',
                                    expandedMessage !== message.id && 'line-clamp-2'
                                )}>
                                    {message.content}
                                </p>

                                {/* Rating section for user responses */}
                                <AnimatePresence>
                                    {expandedMessage === message.id && message.role === 'user' && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="mt-4 pt-4 border-t border-border"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-foreground-muted">Rate this response:</span>
                                                {renderStars(message.id, message.rating)}
                                            </div>

                                            {message.feedback && (
                                                <div className="mt-3 p-3 rounded-lg bg-primary/10 border border-primary/30">
                                                    <p className="text-sm font-semibold text-primary mb-1">Feedback:</p>
                                                    <p className="text-sm text-foreground">{message.feedback}</p>
                                                </div>
                                            )}

                                            {message.improved_answer && (
                                                <div className="mt-3 p-3 rounded-lg bg-success/10 border border-success/30">
                                                    <p className="text-sm font-semibold text-success mb-1">Better Answer:</p>
                                                    <p className="text-sm text-foreground italic">"{message.improved_answer}"</p>
                                                </div>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};
