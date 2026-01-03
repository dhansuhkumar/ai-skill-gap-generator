import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Loader2 } from 'lucide-react';

const StepRole = ({ role, setRole, onConfirm, onBack, loading, error }) => {
    return (
        <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            className="glass-panel"
            style={{ maxWidth: '800px', margin: '0 auto', padding: '2.5rem' }}
        >
            <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', marginBottom: '1rem' }}>← Back</button>
            <h2 style={{ marginBottom: '0.5rem' }}>What's your target role?</h2>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem' }}>Select the role you want to pursue</p>

            <input
                type="text"
                className="input-field"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Full Stack Developer"
                style={{ fontSize: '1.2rem', padding: '1rem', width: '100%', marginBottom: '2rem' }}
            />

            {/* Role Chips */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
                {['Software Engineer', 'Data Scientist', 'ML Engineer', 'DevOps Engineer', 'Frontend Developer', 'Full Stack Developer'].map(r => (
                    <button
                        key={r}
                        onClick={() => setRole(r)}
                        style={{
                            background: role === r ? 'var(--color-primary)' : 'rgba(255,255,255,0.05)',
                            border: role === r ? 'none' : '1px solid var(--color-border)',
                            padding: '0.75rem 1.5rem',
                            borderRadius: '2rem',
                            color: 'white',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        {r}
                    </button>
                ))}
            </div>

            <div style={{ textAlign: 'right' }}>
                <button
                    className="btn btn-primary"
                    onClick={onConfirm}
                    disabled={loading || !role.trim()}
                    style={{ padding: '0.75rem 2rem' }}
                >
                    {loading ? <Loader2 className="animate-spin" /> : <>Next <ArrowRight size={18} /></>}
                </button>
            </div>
            {error && <p style={{ color: 'var(--color-error)', marginTop: '1rem' }}>{error}</p>}
        </motion.div>
    );
};

export default StepRole;
