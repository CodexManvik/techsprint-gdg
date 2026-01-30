import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSessionStore } from '../../stores/sessionStore';
import { cn } from '../../lib/utils'; // Assuming this exists

interface ChatInterfaceProps {
    onSendMessage: (text: string) => void;
    disabled?: boolean;
}

export const ChatInterface = ({ onSendMessage, disabled = false }: ChatInterfaceProps) => {
    const { messages } = useSessionStore();
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !disabled) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    return (
        <div className="flex flex-col h-[350px] w-full max-w-2xl bg-black/40 backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/10 bg-white/5 flex items-center gap-2">
                <MessageSquare size={16} className="text-primary" />
                <span className="text-sm font-medium text-white/80">Live Chat</span>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="flex items-center justify-center h-full text-white/30 text-sm italic">
                        Start the conversation via voice or text...
                    </div>
                )}

                <AnimatePresence initial={false}>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={cn(
                                "flex gap-3 max-w-[85%]",
                                msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
                            )}
                        >
                            <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                                msg.role === 'user' ? "bg-primary text-white" : "bg-accent-purple text-white"
                            )}>
                                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                            </div>

                            <div className={cn(
                                "p-3 rounded-2xl text-sm leading-relaxed shadow-sm",
                                msg.role === 'user'
                                    ? "bg-primary/20 text-white rounded-tr-none border border-primary/20"
                                    : "bg-white/10 text-neutral-200 rounded-tl-none border border-white/10"
                            )}>
                                {msg.content}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="p-3 border-t border-white/10 bg-black/20">
                <div className="relative flex items-center gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={disabled}
                        placeholder="Type your answer..."
                        className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-primary/50 focus:bg-white/10 transition-all"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || disabled}
                        className="p-2.5 bg-primary/20 hover:bg-primary/40 text-primary rounded-xl disabled:opacity-50 disabled:hover:bg-primary/20 transition-all"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </form>
        </div>
    );
};
