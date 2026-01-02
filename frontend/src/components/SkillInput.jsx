import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SkillInput = ({ skills, onSkillsChange }) => {
    const [inputValue, setInputValue] = useState('');

    const handleAddSkill = (e) => {
        e.preventDefault();
        const trimmed = inputValue.trim();
        if (trimmed && !skills.includes(trimmed)) {
            onSkillsChange([...skills, trimmed]);
            setInputValue('');
        }
    };

    const removeSkill = (skillToRemove) => {
        onSkillsChange(skills.filter(skill => skill !== skillToRemove));
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleAddSkill(e);
        }
    };

    return (
        <div>
            {/* Input Row */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <input
                    type="text"
                    className="input-field"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a skill (e.g., Python, React)... or adding manual skills"
                    style={{ flex: 1 }}
                />
                <button
                    onClick={handleAddSkill}
                    className="btn btn-secondary"
                    style={{ padding: '0.75rem' }}
                    disabled={!inputValue.trim()}
                    type="button"
                >
                    <Plus size={20} />
                </button>
            </div>

            {/* Chips Container */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', minHeight: '40px' }}>
                <AnimatePresence>
                    {skills.map((skill, index) => (
                        <motion.div
                            key={skill}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            style={{
                                background: 'rgba(139, 92, 246, 0.15)',
                                border: '1px solid rgba(139, 92, 246, 0.3)',
                                padding: '0.4rem 0.8rem',
                                borderRadius: '2rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                fontSize: '0.9rem',
                                color: 'var(--color-primary)'
                            }}
                        >
                            {skill}
                            <button
                                onClick={() => removeSkill(skill)}
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    color: 'inherit',
                                    opacity: 0.7
                                }}
                            >
                                <X size={14} />
                            </button>
                        </motion.div>
                    ))}
                    {skills.length === 0 && (
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', fontStyle: 'italic', paddingLeft: '0.5rem' }}>
                            Added skills will appear here...
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default SkillInput;
