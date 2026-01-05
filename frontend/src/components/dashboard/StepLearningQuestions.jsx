import React, { useState } from 'react';
import { Clock, Calendar, Zap, ArrowRight, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';

const OptionCard = ({ label, description, isSelected, onClick, icon: Icon }) => (
    <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onClick}
        style={{
            padding: '1rem',
            borderRadius: '0.75rem',
            background: isSelected ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.05)',
            border: isSelected ? '1px solid var(--color-primary)' : '1px solid rgba(255,255,255,0.1)',
            cursor: 'pointer',
            transition: 'all 0.2s',
            flex: 1,
            minWidth: '200px'
        }}
    >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            {Icon && <Icon size={18} color={isSelected ? 'var(--color-primary)' : 'var(--color-text-muted)'} />}
            <h4 style={{ margin: 0, fontWeight: 600 }}>{label}</h4>
        </div>
        {description && <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{description}</p>}
    </motion.div>
);

const StepLearningQuestions = ({ onNext, onBack }) => {
    const [preferences, setPreferences] = useState({
        time_commitment: '1 hour',
        learning_pace: 'Balanced',
        duration: '1 month'
    });

    const handleContinue = () => {
        onNext(preferences);
    };

    return (
        <div className="glass-panel slide-up" style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>
                    Let's tailor your plan
                </h2>
                <p style={{ color: 'var(--color-text-muted)' }}>
                    We'll customize the schedule to fit your life.
                </p>
            </div>

            {/* Question 1: Time Commitment */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Clock size={20} color="var(--color-primary)" />
                    How much time can you spend daily?
                </h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
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

            {/* Question 2: Learning Pace */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Zap size={20} color="var(--color-primary)" />
                    What's your preferred learning pace?
                </h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <OptionCard
                        label="Slow & Steady"
                        description="Deep dive explanation, less rush."
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
                        description="Fast-paced, heavy on execution."
                        isSelected={preferences.learning_pace === 'Intensive'}
                        onClick={() => setPreferences({ ...preferences, learning_pace: 'Intensive' })}
                    />
                </div>
            </div>

            {/* Question 3: Duration */}
            <div style={{ marginBottom: '3rem' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Calendar size={20} color="var(--color-primary)" />
                    How long do you want this plan to be?
                </h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
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

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button
                    onClick={onBack}
                    className="btn btn-secondary"
                    style={{ padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                    <ArrowLeft size={18} /> Back
                </button>
                <button
                    onClick={handleContinue}
                    className="btn btn-primary"
                    style={{ padding: '0.75rem 2rem' }}
                >
                    Continue <ArrowRight size={18} />
                </button>
            </div>
        </div>
    );
};

export default StepLearningQuestions;
