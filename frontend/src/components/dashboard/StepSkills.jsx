import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Loader2 } from 'lucide-react';
import ResumeUpload from '../ResumeUpload';
import SkillInput from '../SkillInput';

const StepSkills = ({ skills, setSkills, onConfirm, loading, skillsSaved, error }) => {
    return (
        <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            className="glass-panel"
            style={{ maxWidth: '800px', margin: '0 auto', padding: '2.5rem' }}
        >
            <h2 style={{ marginBottom: '0.5rem' }}>What skills do you have?</h2>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem' }}>Add your technical skills or upload your resume</p>

            <div style={{ marginBottom: '2rem' }}>
                <SkillInput skills={skills} onSkillsChange={setSkills} />
            </div>

            <p style={{ textAlign: 'center', margin: '1rem 0', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>or upload resume</p>

            <ResumeUpload onSkillsExtracted={(newSkills) => setSkills(prev => [...new Set([...prev, ...newSkills])])} />

            <div style={{ marginTop: '2rem', textAlign: 'right' }}>
                <button
                    className="btn btn-primary"
                    onClick={onConfirm}
                    disabled={loading || skillsSaved}
                    style={{ padding: '0.75rem 2rem', opacity: skillsSaved ? 0.7 : 1 }}
                >
                    {loading ? <Loader2 className="animate-spin" /> : skillsSaved ? <>Saved <CheckCircle2 size={18} /></> : <>Next <ArrowRight size={18} /></>}
                </button>
            </div>
            {error && <p style={{ color: 'var(--color-error)', marginTop: '1rem' }}>{error}</p>}
            {skillsSaved && !error && <p style={{ color: 'var(--color-success)', marginTop: '1rem', fontSize: '0.9rem' }}>✓ Skills saved successfully</p>}
        </motion.div>
    );
};

export default StepSkills;
