import React, { useState, useEffect } from 'react';
import { Briefcase, Code2, Globe, Youtube, Sparkles, Loader2, ArrowLeft, Rocket } from 'lucide-react';
import { motion } from 'framer-motion';

const projectTypes = [
    {
        id: 'portfolio',
        icon: Briefcase,
        label: 'Portfolio Project',
        desc: 'Build one impressive showcase app that demonstrates your skills to employers.',
        color: 'var(--color-primary)',
        glow: 'rgba(99,102,241,0.2)'
    },
    {
        id: 'practice',
        icon: Code2,
        label: 'Mini Practice Apps',
        desc: 'Focused exercises to master each individual concept before combining them.',
        color: 'var(--color-secondary)',
        glow: 'rgba(6,182,212,0.2)'
    },
    {
        id: 'real-world',
        icon: Globe,
        label: 'Real-world Clone',
        desc: 'Recreate a popular product like Netflix, Airbnb or Notion from scratch.',
        color: '#10B981',
        glow: 'rgba(16,185,129,0.2)'
    }
];

const StepProjectPreferences = ({ onGenerate, onBack, loading }) => {
    const [projectType, setProjectType] = useState('portfolio');
    const [includeYoutube, setIncludeYoutube] = useState(true);
    const [context, setContext] = useState('');
    const [messageIndex, setMessageIndex] = useState(0);

    const loadingMessages = [
        "Analyzing your skill gaps...",
        "Mapping learning resources...",
        "Structuring your timeline...",
        "Building project ideas...",
        "Finalizing your path..."
    ];

    useEffect(() => {
        let interval;
        if (loading) {
            interval = setInterval(() => {
                setMessageIndex(prev => (prev + 1) % loadingMessages.length);
            }, 2300);
        } else {
            setMessageIndex(0);
        }
        return () => clearInterval(interval);
    }, [loading]);

    const handleGenerate = () => {
        onGenerate({ project_type: projectType, include_youtube: includeYoutube, additional_context: context });
    };

    return (
        <motion.div
            key="step5"
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
                <span className="section-label"><Rocket size={11} /> Step 5 of 5</span>
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>Project focus</h2>
                <p style={{ fontSize: '0.9rem' }}>Choose how you'd like to apply your new skills through real projects.</p>
            </div>

            {/* Project type cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                {projectTypes.map(type => {
                    const isSelected = projectType === type.id;
                    const Icon = type.icon;
                    return (
                        <motion.div
                            key={type.id}
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.97 }}
                            onClick={() => setProjectType(type.id)}
                            style={{
                                padding: '1.5rem',
                                borderRadius: 'var(--radius-xl)',
                                background: isSelected
                                    ? `linear-gradient(135deg, ${type.glow}, rgba(255,255,255,0.02))`
                                    : 'rgba(255,255,255,0.03)',
                                border: isSelected ? `1px solid ${type.color}55` : '1px solid var(--color-border)',
                                cursor: 'pointer',
                                transition: 'all 0.22s',
                                boxShadow: isSelected ? `0 0 24px ${type.glow}` : 'none',
                            }}
                        >
                            <div style={{
                                width: '42px', height: '42px', borderRadius: '10px',
                                background: isSelected ? `${type.glow}` : 'rgba(255,255,255,0.06)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                marginBottom: '1rem', border: `1px solid ${isSelected ? type.color + '40' : 'transparent'}`
                            }}>
                                <Icon size={20} color={isSelected ? type.color : 'var(--color-text-dim)'} />
                            </div>
                            <h4 style={{ marginBottom: '0.5rem', color: isSelected ? 'var(--color-text)' : 'var(--color-text-muted)' }}>
                                {type.label}
                            </h4>
                            <p style={{ fontSize: '0.82rem', lineHeight: 1.5, margin: 0, color: 'var(--color-text-dim)' }}>
                                {type.desc}
                            </p>
                        </motion.div>
                    );
                })}
            </div>

            {/* YouTube toggle */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '1.125rem 1.25rem',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                marginBottom: '1.75rem',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
                    <div style={{
                        width: '38px', height: '38px', borderRadius: '10px',
                        background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Youtube size={18} color="#F87171" />
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text)' }}>Include Video Tutorials</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-dim)' }}>Find YouTube videos for each topic</div>
                    </div>
                </div>
                <label className="toggle-switch">
                    <input type="checkbox" checked={includeYoutube} onChange={e => setIncludeYoutube(e.target.checked)} />
                    <span className="slider" />
                </label>
            </div>

            {/* Context textarea */}
            <div style={{ marginBottom: '2.25rem' }}>
                <label style={{ marginBottom: '0.5rem', display: 'block' }}>Your interests or goals <span style={{ color: 'var(--color-text-dim)', fontWeight: 400 }}>(optional)</span></label>
                <textarea
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="e.g. I love music — maybe a music streaming app? I prefer backend-heavy projects."
                    style={{
                        width: '100%',
                        padding: '0.875rem 1.125rem',
                        borderRadius: 'var(--radius-lg)',
                        background: 'rgba(10,10,20,0.6)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text)',
                        minHeight: '90px',
                        resize: 'vertical',
                        fontFamily: 'var(--font-main)',
                        fontSize: '0.9rem',
                        outline: 'none',
                        transition: 'border-color 0.15s',
                        lineHeight: 1.6,
                    }}
                    onFocus={e => e.target.style.borderColor = 'var(--color-primary)'}
                    onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
                />
            </div>

            {/* Generate button */}
            <button
                onClick={handleGenerate}
                disabled={loading}
                className="btn btn-primary"
                style={{ width: '100%', padding: '1rem', fontSize: '1rem', justifyContent: 'center' }}
            >
                {loading ? (
                    <><Loader2 size={18} className="animate-spin" /> {loadingMessages[messageIndex]}</>
                ) : (
                    <><Sparkles size={18} /> Generate My Learning Path</>
                )}
            </button>
        </motion.div>
    );
};

export default StepProjectPreferences;
