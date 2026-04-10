import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Send, User, Loader2, Sparkles, ChevronDown, ChevronUp, MessageCircle, X } from 'lucide-react';
import api from '../../services/api';

/**
 * AIChatSidebar - Fixed right sidebar AI assistant
 * Context-aware chat that adapts to user's current step
 */
const AIChatSidebar = ({ context, role }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const [mobileSheetOpen, setMobileSheetOpen] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        if (messages.length === 0) {
            const welcomeMessage = getContextualWelcome(context);
            setMessages([{ role: 'assistant', content: welcomeMessage }]);
        }
    }, []);

    useEffect(() => {
        if (messages.length > 0 && context.currentStep) {
            const contextHint = getContextHint(context);
            if (contextHint && messages[messages.length - 1]?.content !== contextHint) {
                setMessages(prev => [...prev, { role: 'system', content: contextHint }]);
            }
        }
    }, [context.currentStep]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const getContextualWelcome = (ctx) => {
        switch (ctx.currentStep) {
            case 1: return "Hi! I'm your AI learning assistant. I can help you identify skills or recommend skills based on your career goals. What would you like to know?";
            case 2: return "Great! Now let's find your target role. I can help you explore career paths or understand what skills are needed for specific positions.";
            case 3: return "Here are the skills you might want to learn. I can explain why each skill is important or suggest which ones to prioritize.";
            case 6: return `Your learning path is ready! I can help you understand any topic or suggest resources for ${role || 'your journey'}.`;
            default: return "Hi! I'm here to help with your learning journey. Ask me anything!";
        }
    };

    const getContextHint = (ctx) => {
        if (ctx.currentStep === 6 && ctx.hasResults) {
            return `You're now viewing your learning path for ${ctx.role || 'your target role'}. Ask me about any skill!`;
        }
        return null;
    };

    const getSuggestedQuestions = () => {
        switch (context.currentStep) {
            case 1: return ["What skills for a developer?", "How do I describe skill levels?", "Should I connect GitHub?"];
            case 2: return ["Frontend vs Full Stack?", "What roles are in demand?", "How specific should my role be?"];
            case 3: return ["Which skills to prioritize?", "How long to learn these?", "Can I skip any skills?"];
            case 6: return context.selectedToLearn?.slice(0, 2).map(s => `How do I start with ${s}?`) || ["How do I stay motivated?", "What to build first?"];
            default: return ["How does this work?", "What can you help with?"];
        }
    };

    const handleSubmit = async (e) => {
        e?.preventDefault();
        if (!input.trim() || loading) return;
        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setLoading(true);
        try {
            const systemContext = `
You are a helpful AI learning assistant. Step ${context.currentStep} (${context.stepName}) of skill gap analysis.
${context.role ? `Target role: ${context.role}` : ''}
${context.skills?.length ? `Current skills: ${context.skills.join(', ')}` : ''}
${context.selectedToLearn?.length ? `Wants to learn: ${context.selectedToLearn.join(', ')}` : ''}
Provide helpful, concise, encouraging responses. Focus on practical advice.
            `.trim();
            const messagesForAPI = [
                { role: 'system', content: systemContext },
                ...messages.filter(m => m.role !== 'system').map(m => ({ role: m.role, content: m.content })),
                { role: 'user', content: userMessage }
            ];
            const response = await api.roleChat(context.role || 'career advisor', messagesForAPI, 'auto');
            if (response.data && response.data.response) {
                setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
            } else { throw new Error('Invalid response'); }
        } catch (err) {
            console.error('Chat error:', err);
            setMessages(prev => [...prev, { role: 'assistant', content: "I'm having trouble connecting right now. Please try again." }]);
        } finally {
            setLoading(false);
        }
    };

    const handleQuickQuestion = (question) => {
        setInput(question);
        setTimeout(() => handleSubmit(), 100);
    };

    const chatHeader = (
        <div style={{
            padding: '1rem 1.25rem',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(139, 92, 246, 0.05)',
            cursor: 'pointer'
        }}
        onClick={() => setIsMinimized(!isMinimized)}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                    width: '36px', height: '36px', borderRadius: '10px',
                    background: 'linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    <Sparkles size={18} color="white" />
                </div>
                <div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.1rem' }}>AI Assistant</h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{context.stepName || 'Ready to help'}</span>
                </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <button
                    onClick={(e) => { e.stopPropagation(); setMobileSheetOpen(false); }}
                    className="chat-close-btn"
                    style={{
                        display: 'none',
                        alignItems: 'center', justifyContent: 'center',
                        width: '32px', height: '32px',
                        background: 'rgba(255,255,255,0.05)', border: '1px solid var(--color-border)',
                        borderRadius: '8px', color: 'var(--color-text-muted)', cursor: 'pointer'
                    }}
                >
                    <X size={16} />
                </button>
                {isMinimized ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>
        </div>
    );

    const chatBody = (
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {messages.map((msg, idx) => (
                <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                    {msg.role === 'assistant' && (
                        <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            <Bot size={14} color="white" />
                        </div>
                    )}
                    {msg.role === 'user' && (
                        <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'var(--color-bg-app)', border: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            <User size={14} />
                        </div>
                    )}
                    <div style={{
                        flex: 1, padding: msg.role === 'system' ? '0.5rem' : '0.75rem 1rem',
                        borderRadius: '12px',
                        background: msg.role === 'user' ? 'rgba(139, 92, 246, 0.15)' : msg.role === 'system' ? 'transparent' : 'rgba(255, 255, 255, 0.05)',
                        border: msg.role === 'system' ? 'none' : '1px solid var(--color-border)',
                        fontSize: msg.role === 'system' ? '0.8rem' : '0.9rem',
                        color: msg.role === 'system' ? 'var(--color-text-muted)' : 'var(--color-text-main)',
                        fontStyle: msg.role === 'system' ? 'italic' : 'normal', lineHeight: 1.5
                    }}>
                        {msg.content}
                    </div>
                </motion.div>
            ))}
            {loading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Loader2 size={14} color="white" className="animate-spin" />
                    </div>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Thinking...</span>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>
    );

    const suggestedQuestions = messages.length <= 2 && (
        <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--color-border)', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {getSuggestedQuestions().map((q, idx) => (
                <button key={idx} onClick={() => handleQuickQuestion(q)}
                    style={{ padding: '0.4rem 0.75rem', fontSize: '0.75rem', background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.3)', borderRadius: '1rem', color: 'var(--color-primary)', cursor: 'pointer', transition: 'all 0.2s' }}>
                    {q}
                </button>
            ))}
        </div>
    );

    const chatInput = (
        <form onSubmit={handleSubmit} style={{ padding: '1rem', borderTop: '1px solid var(--color-border)', background: 'var(--color-bg-app)' }}>
            <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '12px', border: '1px solid var(--color-border)', padding: '0.5rem' }}>
                <input type="text" id="chat-input" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask anything..." disabled={loading}
                    style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', fontSize: '0.9rem', color: 'var(--color-text-main)', padding: '0.5rem' }}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }} />
                <button type="submit" disabled={!input.trim() || loading}
                    style={{ width: '36px', height: '36px', borderRadius: '8px', background: input.trim() ? 'linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%)' : 'var(--color-border)', border: 'none', cursor: input.trim() ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s' }}>
                    <Send size={16} color={input.trim() ? 'white' : 'var(--color-text-muted)'} />
                </button>
            </div>
        </form>
    );

    const mobileFAB = (
        <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            onClick={() => setMobileSheetOpen(true)}
            className="ai-chat-fab"
            aria-label="Open AI Assistant"
            style={{
                display: 'none', /* overridden to flex by CSS on mobile */
                position: 'fixed',
                bottom: 'calc(1.5rem + env(safe-area-inset-bottom, 0px))',
                right: '1.5rem',
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--color-primary), #a855f7)',
                border: 'none',
                cursor: 'pointer',
                zIndex: 200,
                boxShadow: '0 4px 20px rgba(99,102,241,0.5)',
                alignItems: 'center',
                justifyContent: 'center',
            }}
        >
            <MessageCircle size={24} color="white" />
        </motion.button>
    );

    const mobileSheet = (
        <>
            <AnimatePresence>
                {mobileSheetOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setMobileSheetOpen(false)}
                            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 300 }}
                        />
                        <motion.div
                            initial={{ y: '100%' }}
                            animate={{ y: 0 }}
                            exit={{ y: '100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            style={{
                                position: 'fixed',
                                bottom: 0,
                                left: 0,
                                right: 0,
                                height: '78vh',
                                background: 'var(--color-bg-surface)',
                                borderTop: '1px solid var(--color-border)',
                                borderTopLeftRadius: '20px',
                                borderTopRightRadius: '20px',
                                display: 'flex',
                                flexDirection: 'column',
                                zIndex: 400,
                                overflow: 'hidden',
                                paddingBottom: 'env(safe-area-inset-bottom, 0px)',
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>
                                <div style={{ width: '40px', height: '4px', background: 'rgba(148,163,184,0.3)', borderRadius: '2px' }} />
                            </div>
                            {chatHeader}
                            <AnimatePresence>
                                {!isMinimized && (
                                    <motion.div
                                        initial={{ height: 0 }}
                                        animate={{ height: 'auto' }}
                                        exit={{ height: 0 }}
                                        style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
                                    >
                                        {chatBody}
                                        {suggestedQuestions}
                                        {chatInput}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );

    const desktopSidebar = (
        <motion.div
            initial={{ x: 400 }}
            animate={{ x: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="ai-chat-desktop-sidebar"
            style={{
                position: 'fixed',
                right: 0, top: 'var(--header-height)',
                width: '400px',
                height: 'calc(100vh - var(--header-height))',
                background: 'var(--color-bg-surface)',
                borderLeft: '1px solid var(--color-border)',
                display: 'flex', flexDirection: 'column',
                zIndex: 40
            }}
        >
            {chatHeader}
            <AnimatePresence>
                {!isMinimized && (
                    <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
                    >
                        {chatBody}
                        {suggestedQuestions}
                        {chatInput}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );

    return (
        <>
            {desktopSidebar}
            {mobileFAB}
            {mobileSheet}
            <style>{`
                @media (max-width: 768px) {
                    .chat-close-btn { display: flex !important; }
                }
            `}</style>
        </>
    );
};

export default AIChatSidebar;
