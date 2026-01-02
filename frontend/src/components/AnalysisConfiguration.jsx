import React, { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, Loader2, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ProviderSelector from './ProviderSelector';

const AnalysisConfiguration = ({ missingSkills, onComplete }) => {
    const [step, setStep] = useState(1);
    const [input, setInput] = useState('');
    const [config, setConfig] = useState({
        selected_skills: [],
        project_type: 'portfolio',
        days: 30,
        daily_hours: 1.5,
        additional_context: '',
        include_youtube: true,
        provider: 'auto'
    });

    const inputRef = useRef(null);

    useEffect(() => {
        if (inputRef.current) inputRef.current.focus();
    }, [step]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim() && step !== 3) return; // Allow empty for step 3 (context)

        const val = input.trim();

        if (step === 1) {
            // Step 1: Missing Skills Selection
            // Parse comma-separated list
            const skills = val.split(',').map(s => s.trim()).filter(s => s);
            if (skills.length === 0) {
                return; // Don't proceed if no skills
            }
            setConfig(prev => ({ ...prev, selected_skills: skills }));
            setStep(2);
            setInput('');
        } else if (step === 2) {
            // Step 2: Project Preferences
            // Parse: project_type, days, daily_hours from text
            // Examples: "portfolio, 30 days, 1.5 hours/day" or "capstone 60 days 2 hours"
            const daysMatch = val.match(/(\d+)\s*days?/i);
            const hoursMatch = val.match(/(\d+(?:\.\d+)?)\s*hours?/i);
            const typeMatch = val.match(/(portfolio|capstone|practice)/i);

            setConfig(prev => ({
                ...prev,
                days: daysMatch ? parseInt(daysMatch[1]) : 30,
                daily_hours: hoursMatch ? parseFloat(hoursMatch[1]) : 1.5,
                project_type: typeMatch ? typeMatch[1].toLowerCase() : 'portfolio'
            }));
            setStep(3);
            setInput('');
        } else if (step === 3) {
            // Step 3: Additional Context (optional)
            setConfig(prev => ({ ...prev, additional_context: val }));
            onComplete(config);
        }
    };

    const getPlaceholder = () => {
        if (step === 1) {
            const examples = missingSkills.slice(0, 3).join(', ');
            return `Type skills to learn (e.g., ${examples || 'React, SQL'}) and press Enter`;
        }
        if (step === 2) return "Project type and timeline (e.g., portfolio, 30 days, 1.5 hours/day)";
        if (step === 3) return "Additional context (or press Enter to skip)...";
        return "";
    };

    const getAgentMessage = () => {
        if (step === 1) {
            if (missingSkills.length > 0) {
                return `Based on your role, you are missing: ${missingSkills.join(', ')}. Which ones do you want to learn now?`;
            }
            return "Which skills would you like to learn?";
        }
        if (step === 2) return "Great! What's your preferred project type and time availability?";
        if (step === 3) return "Almost done. Any additional context about your experience, goals, or preferences? (Optional)";
        return "";
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>
            {/* Summary Section */}
            <div style={{ 
                background: 'rgba(139, 92, 246, 0.1)', 
                padding: '1rem', 
                borderRadius: '0.5rem', 
                marginBottom: '2rem' 
            }}>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>Summary</h3>
                <p style={{ fontSize: '0.85rem' }}>
                    {config.selected_skills.length > 0 
                        ? `${config.selected_skills.length} skills → ${config.project_type} project`
                        : 'Configure your learning path'}
                </p>
            </div>

            {/* AI Provider Selection */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ marginBottom: '0.75rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>AI Provider</h3>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
                    <ProviderSelector 
                        selected={config.provider} 
                        onSelect={(provider) => setConfig(prev => ({ ...prev, provider }))} 
                    />
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Last working: {config.provider}</p>
            </div>

            {/* Include YouTube Videos Toggle */}
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h3 style={{ marginBottom: '0.25rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>Include YouTube Videos</h3>
                    <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Get video tutorials with project recommendations</p>
                </div>
                <button
                    onClick={() => setConfig(prev => ({ ...prev, include_youtube: !prev.include_youtube }))}
                    style={{
                        width: '48px',
                        height: '24px',
                        borderRadius: '12px',
                        background: config.include_youtube ? 'var(--color-primary)' : 'rgba(255,255,255,0.2)',
                        border: 'none',
                        cursor: 'pointer',
                        position: 'relative',
                        transition: 'all 0.2s'
                    }}
                >
                    <div style={{
                        position: 'absolute',
                        top: '2px',
                        left: config.include_youtube ? '26px' : '2px',
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: 'white',
                        transition: 'left 0.2s'
                    }} />
                </button>
            </div>

            {/* Agent Message */}
            <div style={{ marginBottom: '1.5rem', maxHeight: '200px', overflowY: 'auto' }}>
                <motion.div 
                    initial={{ opacity: 0, y: 10 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    style={{ display: 'flex', gap: '1rem' }}
                >
                    <div style={{ 
                        width: '32px', 
                        height: '32px', 
                        background: 'var(--color-primary)', 
                        borderRadius: '50%', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        flexShrink: 0
                    }}>
                        <Sparkles size={16} color="white" />
                    </div>
                    <div style={{ 
                        background: 'rgba(255,255,255,0.05)', 
                        padding: '1rem', 
                        borderRadius: '0 1rem 1rem 1rem', 
                        fontSize: '0.95rem', 
                        lineHeight: '1.5',
                        flex: 1
                    }}>
                        {getAgentMessage()}
                    </div>
                </motion.div>
            </div>

            {/* Input Area - Single Prompt Box */}
            {step <= 3 && (
                <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={getPlaceholder()}
                        className="input-field"
                        style={{ paddingRight: '3rem', width: '100%' }}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() && step !== 3}
                        style={{
                            position: 'absolute',
                            right: '0.5rem',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            background: 'var(--color-primary)',
                            border: 'none',
                            borderRadius: '50%',
                            width: '36px',
                            height: '36px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            opacity: (!input.trim() && step !== 3) ? 0.5 : 1
                        }}
                    >
                        <ArrowRight size={18} color="white" />
                    </button>
                </form>
            )}

            {/* Additional Context Textarea (Step 3) */}
            {step === 3 && (
                <div style={{ marginTop: '1rem' }}>
                    <h3 style={{ marginBottom: '0.75rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                        Additional context (optional)
                    </h3>
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Add any additional context about your experience, goals, or preferences..."
                        className="input-field"
                        style={{ 
                            width: '100%', 
                            minHeight: '100px', 
                            resize: 'vertical',
                            padding: '1rem'
                        }}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                                handleSubmit(e);
                            }
                        }}
                    />
                    <button
                        onClick={(e) => {
                            e.preventDefault();
                            const finalConfig = { ...config, additional_context: input };
                            onComplete(finalConfig);
                        }}
                        className="btn btn-primary"
                        style={{ marginTop: '1rem', width: '100%' }}
                    >
                        Start Analysis
                    </button>
                </div>
            )}
        </div>
    );
};

export default AnalysisConfiguration;
