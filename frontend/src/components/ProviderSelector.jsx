import React from 'react';
import { Bot, Sparkles, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

const providers = [
    { id: 'auto', name: 'Auto', icon: Bot, desc: 'Smartest available model' },
    { id: 'gemini', name: 'Gemini', icon: Sparkles, desc: 'Google DeepMind' },
    { id: 'openai', name: 'OpenAI', icon: Cpu, desc: 'GPT-4 Models' },
];

const ProviderSelector = ({ selected, onSelect }) => {
    return (
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>AI Model Selection</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.75rem' }}>
                {providers.map((p) => {
                    const isSelected = selected === p.id;
                    const Icon = p.icon;

                    return (
                        <motion.button
                            key={p.id}
                            onClick={() => onSelect(p.id)}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                flexDirection: 'column',
                                gap: '0.5rem',
                                padding: '1rem',
                                borderRadius: 'var(--radius-md)',
                                border: isSelected ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
                                background: isSelected ? 'rgba(139, 92, 246, 0.1)' : 'rgba(255, 255, 255, 0.02)',
                                cursor: 'pointer',
                                color: isSelected ? 'white' : 'var(--color-text-muted)',
                                transition: 'all 0.2s'
                            }}
                        >
                            <Icon size={24} color={isSelected ? '#8b5cf6' : 'currentColor'} />
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.name}</div>
                                <div style={{ fontSize: '0.7rem', opacity: 0.7 }}>{p.desc}</div>
                            </div>
                        </motion.button>
                    );
                })}
            </div>
        </div>
    );
};

export default ProviderSelector;
