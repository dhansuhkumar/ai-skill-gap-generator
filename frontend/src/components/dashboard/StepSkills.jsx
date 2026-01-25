import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Loader2, Github } from 'lucide-react';
import ResumeUpload from '../ResumeUpload';
import SkillInput from '../SkillInput';
import SkillRadar from './SkillRadar';
import axios from 'axios';

const StepSkills = ({ skills, setSkills, onConfirm, loading, skillsSaved, error, onGithubUsernameChange }) => {
    const [githubUsername, setGithubUsername] = useState('');
    const [githubLoading, setGithubLoading] = useState(false);
    const [githubError, setGithubError] = useState('');
    const [radarData, setRadarData] = useState(null);
    const [detectedLanguages, setDetectedLanguages] = useState([]);

    const handleGithubVerify = async () => {
        if (!githubUsername.trim()) {
            setGithubError('Please enter a GitHub username');
            return;
        }

        setGithubLoading(true);
        setGithubError('');

        try {
            const response = await axios.post('http://localhost:8080/api/analyze-github', {
                username: githubUsername.trim()
            });

            if (response.data.error) {
                setGithubError(response.data.error);
                setRadarData(null);
            } else {
                setRadarData(response.data.chart_data);
                // Extract language names for adding to skills
                const languages = Object.keys(response.data.skills || {});
                setDetectedLanguages(languages);

                // Notify parent component of GitHub username
                if (onGithubUsernameChange) {
                    onGithubUsernameChange(githubUsername.trim());
                }
            }
        } catch (err) {
            setGithubError(err.response?.data?.error || 'Failed to analyze GitHub profile');
            setRadarData(null);
        } finally {
            setGithubLoading(false);
        }
    };

    const handleAddDetectedSkills = () => {
        if (detectedLanguages.length > 0) {
            setSkills(prev => [...new Set([...prev, ...detectedLanguages])]);
        }
    };

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

            {/* GitHub Integration Section */}
            <div style={{
                marginTop: '2rem',
                padding: '1.5rem',
                background: 'rgba(102, 126, 234, 0.05)',
                border: '1px solid rgba(102, 126, 234, 0.2)',
                borderRadius: '12px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
                    <Github size={20} style={{ marginRight: '0.5rem', color: '#667eea' }} />
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Connect GitHub</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                    Analyze your repositories to auto-detect language proficiency
                </p>

                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
                    <input
                        type="text"
                        placeholder="Enter GitHub username"
                        value={githubUsername}
                        onChange={(e) => setGithubUsername(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleGithubVerify()}
                        disabled={githubLoading}
                        style={{
                            flex: 1,
                            padding: '0.75rem',
                            borderRadius: '8px',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'var(--color-text)',
                            fontSize: '0.95rem'
                        }}
                    />
                    <button
                        onClick={handleGithubVerify}
                        disabled={githubLoading}
                        className="btn btn-primary"
                        style={{ padding: '0.75rem 1.5rem', whiteSpace: 'nowrap' }}
                    >
                        {githubLoading ? <Loader2 className="animate-spin" size={18} /> : 'Verify'}
                    </button>
                </div>

                {githubError && (
                    <p style={{ color: 'var(--color-error)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                        {githubError}
                    </p>
                )}

                {radarData && (
                    <>
                        <SkillRadar data={radarData} />
                        {detectedLanguages.length > 0 && (
                            <button
                                onClick={handleAddDetectedSkills}
                                className="btn"
                                style={{
                                    marginTop: '1rem',
                                    width: '100%',
                                    background: 'rgba(102, 126, 234, 0.1)',
                                    border: '1px solid rgba(102, 126, 234, 0.3)'
                                }}
                            >
                                Add Detected Languages to Skills
                            </button>
                        )}
                    </>
                )}
            </div>

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

