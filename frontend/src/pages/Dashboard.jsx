import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import ResumeUpload from '../components/ResumeUpload';
import SkillInput from '../components/SkillInput';
import AnalysisConfiguration from '../components/AnalysisConfiguration';
import RecommendationsDisplay from '../components/RecommendationsDisplay';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight, CheckCircle2, Loader2, ChevronRight, User, Target, BrainCircuit } from 'lucide-react';
import api from '../services/api';

const Dashboard = () => {
    const [step, setStep] = useState(1);
    const [skills, setSkills] = useState([]);
    const [role, setRole] = useState('');
    const [missingSkills, setMissingSkills] = useState([]);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [profileId, setProfileId] = useState(null);
    const [skillsSaved, setSkillsSaved] = useState(false);

    // Step 1: Skills
    const handleConfirmSkills = async () => {
        if (skills.length === 0) {
            setError('Please add at least one skill.');
            return;
        }
        setError('');
        
        // Format skills as objects with name, confidence, source
        const formattedSkills = skills.map(skill => ({
            name: typeof skill === 'string' ? skill : skill.name || skill,
            confidence: typeof skill === 'object' ? (skill.confidence || 80) : 80,
            source: typeof skill === 'object' ? (skill.source || 'user') : 'user'
        }));

        // Optimistic UI: mark as saved immediately
        setSkillsSaved(true);
        setLoading(true);
        
        try {
            const response = await api.confirmSkills(formattedSkills);
            // Store profile_id if returned, or we'll resolve it later
            if (response.data && response.data.profile_id) {
                setProfileId(response.data.profile_id);
            }
            setLoading(false);
            setStep(2);
        } catch (err) {
            // Revert optimistic update on error
            setSkillsSaved(false);
            setLoading(false);
            setError(err.response?.data?.error || 'Failed to save skills. Please try again.');
        }
    };

    // Step 2: Role -> Analyze Gaps
    const handleConfirmRole = async () => {
        if (!role.trim()) {
            setError('Please enter a target role.');
            return;
        }
        setError('');
        setLoading(true);
        try {
            // Extract skill names for gap analysis
            const skillNames = skills.map(s => typeof s === 'string' ? s : (s.name || s));
            const res = await api.analyzeGaps(skillNames, role);
            if (res.data && res.data.missing_skills) {
                setMissingSkills(res.data.missing_skills);
                setStep(3);
            } else {
                setMissingSkills([]);
                setStep(3); // Proceed even if no gaps (maybe perfect match)
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Gap analysis failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Step 3: Analysis Config -> Generate Path
    const handleAnalysisComplete = async (config) => {
        setLoading(true);
        setError('');
        try {
            // Validate selected_skills
            if (!config.selected_skills || config.selected_skills.length === 0) {
                setError('Please select at least one skill to learn.');
                setLoading(false);
                return;
            }

            const params = {
                profile_id: profileId, // Will be resolved by backend if null
                target_role: role,
                selected_skills: config.selected_skills,
                days: config.days || 30,
                daily_hours: config.daily_hours || 1.5,
                project_type: config.project_type || 'portfolio',
                include_youtube: config.include_youtube !== undefined ? config.include_youtube : true,
                additional_context: config.additional_context || '',
                provider: config.provider || 'auto'
            };
            
            const res = await api.generateLearningPath(params);
            
            // Handle response - should match contract format
            if (res.data && res.data.status === 'ok') {
                setResults(res.data);
            } else if (res.data && res.data.learning_path) {
                // Already in correct format
                setResults(res.data);
            } else {
                // Legacy format - wrap it
                setResults({
                    status: 'ok',
                    learning_path: res.data,
                    matching_score: res.data.matching_score || 0,
                    source: res.data.source || 'unknown'
                });
            }
            setStep(4);
        } catch (err) {
            const status = err.response?.status;
            const errorMsg = err.response?.data?.error || 'Analysis generation failed. Please try again.';
            
            if (status === 401) {
                // Redirect to login handled by interceptor, but show message
                setError('Session expired. Please login again.');
            } else if (status === 429) {
                setError('AI provider busy — using heuristic fallback. Please try again.');
            } else if (status === 400) {
                setError(errorMsg || 'Invalid request. Please check your inputs.');
            } else {
                setError(errorMsg);
            }
            setStep(3); // Go back to config
        } finally {
            setLoading(false);
        }
    };

    const renderProgress = () => {
        const steps = [
            { id: 1, label: 'Your Skills', icon: User },
            { id: 2, label: 'Target Role', icon: Target },
            { id: 3, label: 'Analyze', icon: BrainCircuit }
        ];
        return (
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '3rem', gap: '1rem', flexWrap: 'wrap' }}>
                {steps.map((s, idx) => (
                    <div key={s.id} style={{ display: 'flex', alignItems: 'center' }}>
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            opacity: step >= s.id ? 1 : 0.5,
                            color: step >= s.id ? 'var(--color-primary)' : 'var(--color-text-muted)'
                        }}>
                            <div style={{
                                width: '32px', height: '32px', borderRadius: '50%',
                                background: step > s.id ? 'var(--color-success)' : (step === s.id ? 'var(--color-primary)' : 'rgba(255,255,255,0.1)'),
                                color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontWeight: 'bold'
                            }}>
                                {step > s.id ? <CheckCircle2 size={16} /> : s.id}
                            </div>
                            <span style={{ fontWeight: 500 }}>{s.label}</span>
                        </div>
                        {idx < steps.length - 1 && (
                            <div style={{ height: '2px', width: '50px', background: 'var(--color-border)', margin: '0 1rem' }} />
                        )}
                    </div>
                ))}
            </div>
        );
    };

    return (
        <>
            <Navbar />
            <div className="container" style={{ paddingTop: 'calc(var(--header-height) + 2rem)', paddingBottom: '5rem' }}>

                {renderProgress()}

                <AnimatePresence mode="wait">
                    {/* Step 1: Skills */}
                    {step === 1 && (
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
                                    onClick={handleConfirmSkills}
                                    disabled={loading || skillsSaved}
                                    style={{ padding: '0.75rem 2rem', opacity: skillsSaved ? 0.7 : 1 }}
                                >
                                    {loading ? <Loader2 className="animate-spin" /> : skillsSaved ? <>Saved <CheckCircle2 size={18} /></> : <>Next <ArrowRight size={18} /></>}
                                </button>
                            </div>
                            {error && <p style={{ color: 'var(--color-error)', marginTop: '1rem' }}>{error}</p>}
                            {skillsSaved && !error && <p style={{ color: 'var(--color-success)', marginTop: '1rem', fontSize: '0.9rem' }}>✓ Skills saved successfully</p>}
                        </motion.div>
                    )}

                    {/* Step 2: Role */}
                    {step === 2 && (
                        <motion.div
                            key="step2"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="glass-panel"
                            style={{ maxWidth: '800px', margin: '0 auto', padding: '2.5rem' }}
                        >
                            <button onClick={() => setStep(1)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', marginBottom: '1rem' }}>← Back</button>
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
                                    onClick={handleConfirmRole}
                                    disabled={loading || !role.trim()}
                                    style={{ padding: '0.75rem 2rem' }}
                                >
                                    {loading ? <Loader2 className="animate-spin" /> : <>Next <ArrowRight size={18} /></>}
                                </button>
                            </div>
                            {error && <p style={{ color: 'var(--color-error)', marginTop: '1rem' }}>{error}</p>}
                        </motion.div>
                    )}

                    {/* Step 3: Analysis Config (Prompt Box) */}
                    {step === 3 && (
                        <motion.div
                            key="step3"
                            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                        >
                            <div style={{ maxWidth: '800px', margin: '0 auto', marginBottom: '1rem' }}>
                                <button onClick={() => setStep(2)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>← Back</button>
                            </div>
                            <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Ready to analyze!</h2>
                            <AnalysisConfiguration
                                missingSkills={missingSkills || []}
                                onComplete={handleAnalysisComplete}
                            />
                            {error && <p style={{ color: 'var(--color-error)', textAlign: 'center', marginTop: '1rem' }}>{error}</p>}
                        </motion.div>
                    )}

                    {/* Step 4: Results */}
                    {step === 4 && results && (
                        <motion.div
                            key="step4"
                            initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }}
                        >
                            <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '1rem' }}>
                                <button onClick={() => setStep(3)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>← Start Over</button>
                            </div>
                            <RecommendationsDisplay results={results} />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </>
    );
};

export default Dashboard;
