import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Loader2, Target } from 'lucide-react';

const StepRole = ({ role, setRole, onConfirm, onBack, loading, error }) => {
    const suggestedRoles = [
        'Software Engineer', 'Data Scientist', 'ML Engineer',
        'DevOps Engineer', 'Frontend Developer', 'Full Stack Developer',
        'Backend Engineer', 'Cloud Architect', 'Product Manager', 'Cybersecurity Analyst'
    ];

    return (
        <motion.div
            key="step2"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel"
            style={{ maxWidth: '760px', margin: '0 auto', padding: '2.5rem 3rem' }}
        >
            {/* Step badge + back */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
                <button onClick={onBack} className="back-btn">
                    ← Back
                </button>
                <span className="section-label"><Target size={11} /> Step 2 of 5</span>
            </div>

            {/* Header */}
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>What's your target role?</h2>
                <p style={{ fontSize: '0.9rem' }}>We'll find the exact skills this role demands in the current job market.</p>
            </div>

            {/* Input */}
            <div style={{ position: 'relative', marginBottom: '1.75rem' }}>
                <input
                    type="text"
                    id="role-input"
                    className="input-field"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && role.trim() && onConfirm()}
                    placeholder="e.g. Machine Learning Engineer"
                    style={{ fontSize: '1.1rem', padding: '1rem 1.25rem' }}
                />
            </div>

            {/* Role chips */}
            <div style={{ marginBottom: '2.5rem' }}>
                <label style={{ marginBottom: '0.875rem', display: 'block' }}>Popular roles</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {suggestedRoles.map(r => (
                        <motion.button
                            key={r}
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.97 }}
                            onClick={() => setRole(r)}
                            style={{
                                padding: '0.5rem 1.125rem',
                                borderRadius: '999px',
                                fontSize: '0.85rem',
                                fontWeight: 500,
                                cursor: 'pointer',
                                border: role === r
                                    ? '1px solid rgba(99,102,241,0.6)'
                                    : '1px solid var(--color-border)',
                                background: role === r
                                    ? 'rgba(99,102,241,0.15)'
                                    : 'rgba(255,255,255,0.03)',
                                color: role === r ? 'var(--color-primary-light)' : 'var(--color-text-muted)',
                                transition: 'all 0.2s',
                                fontFamily: 'var(--font-main)',
                                boxShadow: role === r ? '0 0 12px rgba(99,102,241,0.2)' : 'none'
                            }}
                        >
                            {r}
                        </motion.button>
                    ))}
                </div>
            </div>

            {/* Action */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                    className="btn btn-primary"
                    onClick={onConfirm}
                    disabled={loading || !role.trim()}
                    style={{ padding: '0.75rem 2rem', minWidth: '160px' }}
                >
                    {loading ? <Loader2 size={18} className="animate-spin" /> : <>Analyze Role <ArrowRight size={16} /></>}
                </button>
            </div>

            {error && (
                <div className="alert alert-error" style={{ marginTop: '1rem' }}>{error}</div>
            )}
        </motion.div>
    );
};

export default StepRole;
