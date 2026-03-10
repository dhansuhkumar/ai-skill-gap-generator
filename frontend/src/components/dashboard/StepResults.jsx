import React from 'react';
import { motion } from 'framer-motion';
import DynamicDashboard from '../visualizations/DynamicDashboard';

const StepResults = ({ results, onReset, userSkills, roleAnalysis, githubUsername }) => {
    return (
        <motion.div
            key="step4"
            initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }}
        >
            <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '1rem' }}>
                <button onClick={onReset} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>← Start Over</button>
            </div>

            <DynamicDashboard
                results={results}
                userSkills={userSkills}
                roleAnalysis={roleAnalysis}
                githubUsername={githubUsername}
            />
        </motion.div>
    );
};

export default StepResults;
