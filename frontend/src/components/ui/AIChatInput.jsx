import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send, Paperclip, Bot } from 'lucide-react';

const AIChatInput = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState('');

    const toggleDrawer = () => setIsOpen(!isOpen);

    const handleSubmit = (e) => {
        e.preventDefault();
        // Handle message sending here
        console.log('Sending message:', message);
        setMessage('');
    };

    return (
        <>
            {/* Toggle Button */}
            <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={toggleDrawer}
                className="fixed bottom-8 right-8 z-50 p-4 rounded-full bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary-glow)] hover:scale-110 transition-transform"
            >
                {isOpen ? <X size={24} /> : <MessageSquare size={24} />}
            </motion.button>

            {/* Backdrop */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={toggleDrawer}
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
                    />
                )}
            </AnimatePresence>

            {/* Drawer */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ x: '100%', opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: '100%', opacity: 0 }}
                        transition={{ type: 'spring', damping: 20, stiffness: 100 }}
                        className="fixed right-0 top-0 h-full w-full max-w-md bg-[var(--color-bg-surface)]/95 backdrop-blur-xl border-l border-[var(--color-border)] shadow-2xl z-50 flex flex-col"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-[var(--color-border)] flex justify-between items-center bg-[var(--color-bg-surface-glass)]">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-[var(--color-primary)]/20 flex items-center justify-center">
                                    <Bot size={24} className="text-[var(--color-primary)]" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-[var(--color-text-main)]">AI Companion</h2>
                                    <p className="text-xs text-[var(--color-text-muted)]">Ask for help or context</p>
                                </div>
                            </div>
                            <button onClick={toggleDrawer} className="text-[var(--color-text-muted)] hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Chat Area (Placeholder) */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-4">
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-[var(--color-primary)]/20 flex items-center justify-center flex-shrink-0">
                                    <Bot size={16} className="text-[var(--color-primary)]" />
                                </div>
                                <div className="bg-[var(--color-bg-surface-glass)] border border-[var(--color-border)] p-4 rounded-2xl rounded-tl-none text-sm text-[var(--color-text-muted)]">
                                    Hi! I can help you with your learning path. Do you have any questions about the current module?
                                </div>
                            </div>
                        </div>

                        {/* Input Area */}
                        <div className="p-6 border-t border-[var(--color-border)] bg-[var(--color-bg-surface)]">
                            <form onSubmit={handleSubmit} className="relative">
                                <div className="absolute -top-10 left-0">
                                    <button type="button" className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors px-3 py-1.5 rounded-full bg-[var(--color-border)]/50 border border-[var(--color-border)] backdrop-blur-md">
                                        <Paperclip size={12} />
                                        Attach Context
                                    </button>
                                </div>
                                <div className="relative group">
                                    <textarea
                                        value={message}
                                        onChange={(e) => setMessage(e.target.value)}
                                        placeholder="Type your message..."
                                        className="w-full bg-[var(--color-bg-app)] text-[var(--color-text-main)] rounded-2xl pl-4 pr-12 py-4 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 border border-[var(--color-border)] resize-none min-h-[56px] max-h-32 transition-all scrolbar-hide"
                                        rows="1"
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                handleSubmit(e);
                                            }
                                        }}
                                    />
                                    <button
                                        type="submit"
                                        disabled={!message.trim()}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-[var(--color-primary)] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--color-primary-dark)] transition-colors"
                                    >
                                        <Send size={16} />
                                    </button>
                                </div>
                            </form>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};

export default AIChatInput;
