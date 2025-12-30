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
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                Current Skills
                <span style={{ fontSize: '0.8rem', background: 'var(--color-border)', padding: '2px 8px', borderRadius: '12px', color: 'var(--color-text-muted)' }}>{skills.length}</span>
            </h3>

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                <input
                    type="text"
                    className="input-field"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a skill (e.g., Python, React)..."
                    style={{ flex: 1 }}
                />
                <button
                    onClick={handleAddSkill}
                    className="btn btn-primary"
                    style={{ padding: '0.75rem' }}
                    disabled={!inputValue.trim()}
                >
                    <Plus size={20} />
                </button>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', minHeight: '60px' }}>
                <AnimatePresence>
                    {skills.map((skill, index) => (
                        <motion.div
                            key={skill}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid var(--color-border)',
                                padding: '0.4rem 0.8rem',
                                borderRadius: '2rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                fontSize: '0.9rem'
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
                                    color: 'var(--color-text-muted)'
                                }}
                            >
                                <X size={14} />
                            </button>
                        </motion.div>
                    ))}
                    {skills.length === 0 && (
                        <div style={{ width: '100%', textAlign: 'center', color: 'var(--color-text-muted)', padding: '1rem', fontStyle: 'italic' }}>
                            No skills added yet. Type above or upload your resume.
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default SkillInput;
