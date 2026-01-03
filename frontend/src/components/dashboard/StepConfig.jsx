import React from 'react';
import { motion } from 'framer-motion';
import AnalysisConfiguration from '../AnalysisConfiguration';

const StepConfig = ({ missingSkills, onComplete, onBack, error }) => {
    return (
        <motion.div
            key="step3"
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
        >
            <div style={{ maxWidth: '800px', margin: '0 auto', marginBottom: '1rem' }}>
                <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>← Back</button>
            </div>
            <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Ready to analyze!</h2>
            <AnalysisConfiguration
                missingSkills={missingSkills || []}
                onComplete={onComplete}
            />
            {error && <p style={{ color: 'var(--color-error)', textAlign: 'center', marginTop: '1rem' }}>{error}</p>}
        </motion.div>
    );
};

export default StepConfig;
