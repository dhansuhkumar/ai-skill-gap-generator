import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Loader2, Github, Plus, Sparkles } from 'lucide-react';
import ResumeUpload from '../ResumeUpload';
import SkillInput from '../SkillInput';
import SkillRadar from './SkillRadar';
import axios from 'axios';

const StepSkills = ({ skills, setSkills, onConfirm, loading, skillsSaved, error, githubUsername, setGithubUsername, experienceLevel, setExperienceLevel }) => {
    const [githubLoading, setGithubLoading] = useState(false);
    const [githubError, setGithubError] = useState('');
    const [radarData, setRadarData] = useState(null);
    const [detectedLanguages, setDetectedLanguages] = useState([]);
    const [githubSuccess, setGithubSuccess] = useState(false);

    const handleGithubVerify = async () => {
        if (!githubUsername.trim()) {
            setGithubError('Please enter a GitHub username');
            return;
        }
        setGithubLoading(true);
        setGithubError('');
        setGithubSuccess(false);

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
            const response = await axios.post(`${API_URL}/api/analyze-github`, {
                github_username: githubUsername.trim()
            });

            if (response.data.error) {
                setGithubError(response.data.error);
                setRadarData(null);
            } else {
                setRadarData(response.data.chart_data);
                const languages = Object.keys(response.data.skills || {});
                setDetectedLanguages(languages);
                setGithubSuccess(true);
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
        <>
        <motion.div
            key="step1"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel step-panel"
            style={{ maxWidth: '760px', margin: '0 auto', padding: '2.5rem 3rem' }}
        >
            {/* Step header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginBottom: '1.75rem' }}>
                <span className="section-label"><Sparkles size={11} /> Step 1 of 5</span>
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>What skills do you have?</h2>
                <p style={{ fontSize: '0.9rem' }}>Add your technical skills manually, upload your resume, or connect GitHub to auto-detect them.</p>
            </div>

            {/* Skill input */}
            <div style={{ marginBottom: '1.5rem' }}>
                <SkillInput skills={skills} onSkillsChange={setSkills} />
            </div>

            {/* Or divider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
                <span style={{ fontSize: '0.78rem', color: 'var(--color-text-dim)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>or</span>
                <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
            </div>

            {/* Resume Upload */}
            <div style={{ marginBottom: '2rem' }}>
                <ResumeUpload 
                    onSkillsExtracted={(newSkills) => setSkills(prev => [...new Set([...prev, ...newSkills])])} 
                    onExperienceLevelExtracted={(expLevel) => setExperienceLevel(expLevel)}
                    onResumeDataExtracted={() => {}}
                />
            </div>

            {/* GitHub Integration */}
            <div style={{
                padding: '1.5rem',
                background: 'rgba(99,102,241,0.05)',
                border: '1px solid rgba(99,102,241,0.18)',
                borderRadius: 'var(--radius-xl)',
                marginBottom: '2rem'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.625rem' }}>
                    <div style={{
                        width: '34px', height: '34px', borderRadius: '9px',
                        background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Github size={17} color="var(--color-primary-light)" />
                    </div>
                    <div>
                        <h4 style={{ margin: 0, fontSize: '0.95rem' }}>Connect GitHub</h4>
                        <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-dim)' }}>
                            Auto-detect language proficiency from your repos
                        </p>
                    </div>
                </div>

                <div className="github-input-row" style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                    <input
                        type="text"
                        id="github-username-input"
                        placeholder="Enter your GitHub username"
                        value={githubUsername}
                        onChange={(e) => setGithubUsername(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleGithubVerify()}
                        disabled={githubLoading}
                        className="input-field"
                        style={{ flex: 1 }}
                    />
                    <button
                        onClick={handleGithubVerify}
                        disabled={githubLoading}
                        className="btn btn-outline github-verify-btn"
                        style={{ padding: '0.75rem 1.25rem', flexShrink: 0 }}
                    >
                        {githubLoading ? <Loader2 size={16} className="animate-spin" /> : 'Verify'}
                    </button>
                </div>

                {githubError && (
                    <div className="alert alert-error" style={{ marginTop: '0.75rem', padding: '0.625rem 0.875rem' }}>
                        {githubError}
                    </div>
                )}

                {githubSuccess && radarData && (
                    <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{ marginTop: '1rem' }}
                    >
                        <SkillRadar data={radarData} />
                        {detectedLanguages.length > 0 && (
                            <button
                                onClick={handleAddDetectedSkills}
                                className="btn btn-secondary"
                                style={{ marginTop: '0.875rem', width: '100%', justifyContent: 'center' }}
                            >
                                <Plus size={15} /> Add {detectedLanguages.length} detected languages to skills
                            </button>
                        )}
                    </motion.div>
                )}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    {skillsSaved && !error && (
                        <span style={{ fontSize: '0.85rem', color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                            <CheckCircle2 size={15} /> Skills saved
                        </span>
                    )}
                    {error && (
                        <span style={{ fontSize: '0.85rem', color: 'var(--color-error)' }}>{error}</span>
                    )}
                </div>
                <button
                    className="btn btn-primary"
                    onClick={onConfirm}
                    disabled={loading || skills.length === 0}
                    style={{ minWidth: '150px' }}
                >
                    {loading
                        ? <Loader2 size={16} className="animate-spin" />
                        : skillsSaved
                            ? <><CheckCircle2 size={16} /> Saved — Next</>
                            : <>Save & Continue <ArrowRight size={16} /></>
                    }
                </button>
            </div>
        </motion.div>
        <style>{`
            @media (max-width: 768px) {
                .step-panel {
                    padding: 1.5rem !important;
                }
                .github-input-row {
                    flex-direction: column !important;
                }
                .github-verify-btn {
                    width: 100% !important;
                    justify-content: center !important;
                }
            }
        `}</style>
        </>
    );
};

export default StepSkills;
