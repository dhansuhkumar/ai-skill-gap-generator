import React, { useState } from 'react';
import { Clock, Calendar, Zap, ArrowRight, ArrowLeft, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

const OptionCard = ({ label, description, isSelected, onClick, icon: Icon }) => (
    <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        onClick={onClick}
        style={{
            padding: '1rem 1.125rem',
            borderRadius: 'var(--radius-lg)',
            background: isSelected ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.03)',
            border: isSelected ? '1px solid rgba(99,102,241,0.5)' : '1px solid var(--color-border)',
            cursor: 'pointer',
            transition: 'all 0.18s',
            flex: 1,
            minWidth: '0',
            boxShadow: isSelected ? '0 0 14px rgba(99,102,241,0.12)' : 'none',
        }}
    >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: description ? '0.375rem' : 0 }}>
            {Icon && <Icon size={16} color={isSelected ? 'var(--color-primary-light)' : 'var(--color-text-dim)'} />}
            <h4 style={{ margin: 0, fontWeight: 600, fontSize: '0.9rem', color: isSelected ? 'var(--color-text)' : 'var(--color-text-muted)' }}>
                {label}
            </h4>
            {isSelected && (
                <div style={{ marginLeft: 'auto', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-primary)', flexShrink: 0 }} />
            )}
        </div>
        {description && (
            <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-dim)', lineHeight: 1.5 }}>{description}</p>
        )}
    </motion.div>
);

const SectionHeader = ({ icon: Icon, children }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.875rem' }}>
        <Icon size={16} color="var(--color-primary-light)" />
        <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>{children}</h4>
    </div>
);

const StepLearningQuestions = ({ onNext, onBack }) => {
    const [preferences, setPreferences] = useState({
        time_commitment: '1 hour',
        learning_pace: 'Balanced',
        duration: '1 month'
    });

    return (
        <motion.div
            key="step4"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel"
            style={{ maxWidth: '760px', margin: '0 auto', padding: '2.5rem 3rem' }}
        >
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
                <button onClick={onBack} className="back-btn">← Back</button>
                <span className="section-label"><Settings size={11} /> Step 4 of 5</span>
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>Tailor your learning plan</h2>
                <p style={{ fontSize: '0.9rem' }}>We'll customize the schedule to fit your life and pace.</p>
            </div>

            {/* Time commitment */}
            <div style={{ marginBottom: '2rem' }}>
                <SectionHeader icon={Clock}>Daily time commitment</SectionHeader>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    {['30 minutes', '1 hour', '2 hours', 'Flexible'].map(opt => (
                        <OptionCard
                            key={opt}
                            label={opt}
                            isSelected={preferences.time_commitment === opt}
                            onClick={() => setPreferences({ ...preferences, time_commitment: opt })}
                        />
                    ))}
                </div>
            </div>

            {/* Pace */}
            <div style={{ marginBottom: '2rem' }}>
                <SectionHeader icon={Zap}>Learning pace</SectionHeader>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <OptionCard
                        label="Slow & Steady"
                        description="Deep dive explanations, no rush."
                        isSelected={preferences.learning_pace === 'Slow & Steady'}
                        onClick={() => setPreferences({ ...preferences, learning_pace: 'Slow & Steady' })}
                    />
                    <OptionCard
                        label="Balanced"
                        description="Mix of theory and practice."
                        isSelected={preferences.learning_pace === 'Balanced'}
                        onClick={() => setPreferences({ ...preferences, learning_pace: 'Balanced' })}
                    />
                    <OptionCard
                        label="Intensive"
                        description="Fast-paced, heavy on building."
                        isSelected={preferences.learning_pace === 'Intensive'}
                        onClick={() => setPreferences({ ...preferences, learning_pace: 'Intensive' })}
                    />
                </div>
            </div>

            {/* Duration */}
            <div style={{ marginBottom: '2.5rem' }}>
                <SectionHeader icon={Calendar}>Plan duration</SectionHeader>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    {['2 weeks', '1 month', '2 months'].map(opt => (
                        <OptionCard
                            key={opt}
                            label={opt}
                            isSelected={preferences.duration === opt}
                            onClick={() => setPreferences({ ...preferences, duration: opt })}
                        />
                    ))}
                </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button onClick={onBack} className="btn btn-secondary">
                    <ArrowLeft size={16} /> Back
                </button>
                <button
                    onClick={() => onNext(preferences)}
                    className="btn btn-primary"
                    style={{ minWidth: '160px' }}
                >
                    Continue <ArrowRight size={16} />
                </button>
            </div>
        </motion.div>
    );
};

export default StepLearningQuestions;
