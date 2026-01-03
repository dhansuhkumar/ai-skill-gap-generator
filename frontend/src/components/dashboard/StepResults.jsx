import React from 'react';
import { motion } from 'framer-motion';
import RecommendationsDisplay from '../RecommendationsDisplay';

const StepResults = ({ results, onReset }) => {
    return (
        <motion.div
            key="step4"
            initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }}
        >
            <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '1rem' }}>
                <button onClick={onReset} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>← Start Over</button>
            </div>
            <RecommendationsDisplay results={results} />
        </motion.div>
    );
};

export default StepResults;
