import React, { useState } from 'react';
import { Briefcase, Youtube, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

const StepProjectPreferences = ({ onGenerate, onBack, loading }) => {
    const [projectType, setProjectType] = useState('portfolio');
    const [includeYoutube, setIncludeYoutube] = useState(true);
    const [context, setContext] = useState('');

    const handleGenerate = () => {
        onGenerate({
            project_type: projectType,
            include_youtube: includeYoutube,
            additional_context: context
        });
    };

    // Toggle switch styles
    const toggleSwitchStyle = {
        position: 'relative',
        display: 'inline-block',
        width: '50px',
        height: '26px'
    };

    const inputStyle = {
        opacity: 0,
        width: 0,
        height: 0
    };

    const sliderStyle = (isChecked) => ({
        position: 'absolute',
        cursor: 'pointer',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: isChecked ? 'var(--color-primary)' : 'rgba(255,255,255,0.2)',
        transition: '.4s',
        borderRadius: '34px'
    });

    const sliderBeforeStyle = (isChecked) => ({
        position: 'absolute',
        content: '""',
        height: '18px',
        width: '18px',
        left: isChecked ? '28px' : '4px',
        bottom: '4px',
        backgroundColor: 'white',
        transition: '.4s',
        borderRadius: '50%'
    });

    return (
        <div className="glass-panel slide-up" style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>
                    Final step: Project Focus
                </h2>
                <p style={{ color: 'var(--color-text-muted)' }}>
                    How would you like to apply your new skills?
                </p>
            </div>

            {/* Project Type Selection */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                {[
                    { id: 'portfolio', label: 'Portfolio Project', desc: 'Build a significant project to show employers.' },
                    { id: 'practice', label: 'Mini Practice Apps', desc: 'Small, isolated exercises to learn concepts.' },
                    { id: 'real-world', label: 'Real-world Clone', desc: 'Recreate a popular app (e.g., Netflix, Airbnb).' }
                ].map(type => (
                    <motion.div
                        key={type.id}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setProjectType(type.id)}
                        style={{
                            padding: '1.5rem',
                            borderRadius: '1rem',
                            background: projectType === type.id ? 'var(--color-primary)' : 'rgba(255,255,255,0.05)',
                            cursor: 'pointer',
                            textAlign: 'left',
                            border: projectType === type.id ? 'none' : '1px solid rgba(255,255,255,0.1)',
                            transition: 'all 0.3s'
                        }}
                    >
                        <Briefcase size={24} style={{ marginBottom: '1rem', opacity: 0.9 }} />
                        <h4 style={{ marginBottom: '0.5rem' }}>{type.label}</h4>
                        <p style={{ fontSize: '0.85rem', opacity: 0.8, lineHeight: 1.4 }}>{type.desc}</p>
                    </motion.div>
                ))}
            </div>

            {/* Toggles */}
            <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{
                            width: '40px', height: '40px', borderRadius: '50%',
                            background: 'rgba(255,0,0,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center'
                        }}>
                            <Youtube size={20} color="#ff0000" />
                        </div>
                        <div>
                            <h4 style={{ marginBottom: '0', fontSize: '1rem' }}>Include Video Tutorials</h4>
                            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>
                                Find relevant YouTube videos for each topic.
                            </p>
                        </div>
                    </div>

                    {/* Custom Toggle Switch - No styled-jsx */}
                    <div
                        style={toggleSwitchStyle}
                        onClick={() => setIncludeYoutube(!includeYoutube)}
                    >
                        <div style={sliderStyle(includeYoutube)}>
                            <div style={sliderBeforeStyle(includeYoutube)} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Optional Context */}
            <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                    Any specific interests or goals? (Optional)
                </label>
                <textarea
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="e.g. I love music, so maybe a music app? Or I prefer backend heavy tasks."
                    style={{
                        width: '100%',
                        padding: '1rem',
                        borderRadius: '0.75rem',
                        background: 'rgba(0,0,0,0.2)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: 'white',
                        minHeight: '80px',
                        resize: 'vertical'
                    }}
                />
            </div>

            <div style={{ textAlign: 'center' }}>
                <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="btn btn-primary btn-lg"
                    style={{ width: '100%', maxWidth: '400px', display: 'inline-flex', justifyContent: 'center', gap: '0.75rem', padding: '1rem' }}
                >
                    {loading ? (
                        <>Generating your plan...</>
                    ) : (
                        <>
                            <Sparkles size={20} /> Generate My Learning Path
                        </>
                    )}
                </button>
                <div style={{ marginTop: '1rem' }}>
                    <button onClick={onBack} className="btn-link" style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                        Back to settings
                    </button>
                </div>
            </div>
        </div>
    );
};

export default StepProjectPreferences;
