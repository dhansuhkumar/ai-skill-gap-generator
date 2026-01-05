import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, ArrowRight, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const StepMissingSkills = ({ missingSkills, onNext, onBack }) => {
    const [selected, setSelected] = useState([]);

    useEffect(() => {
        // Pre-select all by default to encourage learning
        if (missingSkills && missingSkills.length > 0) {
            setSelected(missingSkills);
        }
    }, [missingSkills]);

    const toggleSkill = (skill) => {
        if (selected.includes(skill)) {
            setSelected(selected.filter(s => s !== skill));
        } else {
            setSelected([...selected, skill]);
        }
    };

    const handleContinue = () => {
        if (selected.length === 0) return;
        onNext(selected);
    };

    return (
        <div className="glass-panel slide-up" style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>
                    What do you want to learn?
                </h2>
                <p style={{ color: 'var(--color-text-muted)' }}>
                    These skills are typically required for this role. Select the ones you want to focus on now.
                </p>
            </div>

            {missingSkills.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <div style={{ marginBottom: '1rem', color: 'var(--color-success)' }}>
                        <CheckCircle2 size={48} style={{ margin: '0 auto' }} />
                    </div>
                    <h3>You match this role perfectly!</h3>
                    <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
                        You already have the core skills we track for this role.
                    </p>
                    <button
                        onClick={() => onNext([])}
                        className="btn btn-primary"
                    >
                        Continue to Practice Projects <ArrowRight size={18} />
                    </button>
                </div>
            ) : (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                        gap: '1rem',
                        marginBottom: '2rem'
                    }}>
                        {missingSkills.map(skill => {
                            const isSelected = selected.includes(skill);
                            return (
                                <motion.div
                                    key={skill}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => toggleSkill(skill)}
                                    style={{
                                        padding: '1rem',
                                        borderRadius: '0.75rem',
                                        background: isSelected ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                                        border: isSelected ? '1px solid var(--color-primary)' : '1px solid rgba(255,255,255,0.1)',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.75rem',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {isSelected ? (
                                        <CheckCircle2 size={20} color="var(--color-primary)" />
                                    ) : (
                                        <Circle size={20} color="var(--color-text-muted)" />
                                    )}
                                    <span style={{ fontWeight: 500 }}>{skill}</span>
                                </motion.div>
                            );
                        })}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto' }}>
                        <button
                            onClick={onBack}
                            className="btn btn-secondary"
                        >
                            Back
                        </button>
                        <button
                            onClick={handleContinue}
                            className="btn btn-primary"
                            disabled={selected.length === 0}
                            style={{ opacity: selected.length === 0 ? 0.5 : 1 }}
                        >
                            Next Step <ArrowRight size={18} />
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default StepMissingSkills;
