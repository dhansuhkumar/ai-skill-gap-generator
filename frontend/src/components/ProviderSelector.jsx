import React from 'react';
import { Bot, Sparkles, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

const providers = [
    { id: 'auto', name: 'Auto', icon: Bot },
    { id: 'gemini', name: 'Gemini', icon: Sparkles },
    { id: 'openai', name: 'OpenAI', icon: Cpu },
    { id: 'local', name: 'Local', icon: Cpu },
];

const ProviderSelector = ({ selected, onSelect }) => {
    return (
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
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
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem',
                            padding: '1rem',
                            minWidth: '100px',
                            borderRadius: '0.5rem',
                            border: isSelected ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                            background: isSelected ? 'rgba(139, 92, 246, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                            cursor: 'pointer',
                            color: isSelected ? 'var(--color-primary)' : 'var(--color-text-muted)',
                            transition: 'all 0.2s',
                            position: 'relative'
                        }}
                    >
                        <Icon size={24} />
                        <span style={{ fontSize: '0.85rem', fontWeight: isSelected ? 600 : 400 }}>{p.name}</span>
                        {isSelected && (
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                style={{
                                    position: 'absolute',
                                    top: '0.5rem',
                                    right: '0.5rem',
                                    width: '20px',
                                    height: '20px',
                                    borderRadius: '50%',
                                    background: 'var(--color-primary)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontSize: '0.7rem'
                                }}
                            >
                                ✓
                            </motion.div>
                        )}
                    </motion.button>
                );
            })}
        </div>
    );
};

export default ProviderSelector;
