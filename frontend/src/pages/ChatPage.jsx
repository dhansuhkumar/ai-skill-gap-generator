import React, { useState, useRef, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { motion } from 'framer-motion';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import api from '../services/api';

const ChatPage = () => {
    const [role, setRole] = useState('');
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [provider, setProvider] = useState('auto');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        if (!role.trim()) {
            // Prompt for role if missing
            setMessages(prev => [...prev, { role: 'system', content: 'Please enter a target role above to start the chat.' }]);
            return;
        }

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            // Send history + new message
            // Note: Backend might expect just the new message if it maintains state, 
            // but usually stateless APIs need history. 
            // The current backend `generate_role_chat_reply` takes `messages`.
            const currentHistory = [...messages, userMessage];
            const response = await api.roleChat(role, currentHistory, provider);

            setMessages(prev => [...prev, { role: 'assistant', content: response.data.reply }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'system', content: 'Error: Failed to get response from AI.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Navbar />
            <div className="container" style={{ paddingTop: 'calc(var(--header-height) + 2rem)', paddingBottom: '2rem', height: '100vh', display: 'flex', flexDirection: 'column' }}>

                <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <input
                        type="text"
                        className="input-field chat-role-input"
                        placeholder="Enter Role (e.g. Interviewer, Senior Dev)"
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        style={{ flex: 1, maxWidth: '300px' }}
                    />
                    <div style={{ flex: 1 }}>
                        {/* Compact Provider Selector or just a dropdown? reusing selector might be too big */}
                        <select
                            className="input-field chat-provider-select"
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                            style={{ maxWidth: '150px' }}
                        >
                            <option value="auto">Auto Model</option>
                            <option value="gemini">Gemini</option>
                            <option value="openai">OpenAI</option>
                        </select>
                    </div>
                </div>

                <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    {/* Chat Area */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {messages.length === 0 && (
                            <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginTop: '20%' }}>
                                <Bot size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                                <p>Start a conversation to simulate an interview or ask for advice.</p>
                            </div>
                        )}
                        {messages.map((msg, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                style={{
                                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    maxWidth: '80%',
                                    display: 'flex',
                                    gap: '0.75rem',
                                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
                                }}
                            >
                                <div style={{
                                    background: msg.role === 'user' ? 'var(--color-primary)' : 'rgba(255,255,255,0.1)',
                                    padding: '0.5rem',
                                    borderRadius: '50%',
                                    height: 'fit-content'
                                }}>
                                    {msg.role === 'user' ? <User size={16} color="white" /> : <Bot size={16} />}
                                </div>
                                <div style={{
                                    background: msg.role === 'user' ? 'var(--color-primary-dark)' : 'rgba(255,255,255,0.05)',
                                    padding: '1rem',
                                    borderRadius: '1rem',
                                    borderTopRightRadius: msg.role === 'user' ? '0' : '1rem',
                                    borderTopLeftRadius: msg.role === 'user' ? '1rem' : '0',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '0.95rem',
                                    lineHeight: '1.5'
                                }}>
                                    {msg.content}
                                </div>
                            </motion.div>
                        ))}
                        {loading && (
                            <div style={{ alignSelf: 'flex-start', marginLeft: '3rem' }}>
                                <Loader2 className="animate-spin" size={20} color="var(--color-text-muted)" />
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <form onSubmit={handleSend} className="chat-form" style={{ padding: '1.5rem', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '1rem' }}>
                        <input
                            type="text"
                            className="input-field"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type a message..."
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading || !input.trim()}
                            style={{ padding: '0 1.5rem' }}
                        >
                            <Send size={20} />
                        </button>
                    </form>
                </div>

            </div>
        <style>{`
            @media (max-width: 768px) {
                .chat-role-input { max-width: 100% !important; }
                .chat-provider-select { max-width: 100% !important; }
                .chat-form { flex-direction: column !important; }
                .chat-form .btn { width: 100% !important; justify-content: center !important; }
            }
        `}</style>
        </>
    );
};

export default ChatPage;
