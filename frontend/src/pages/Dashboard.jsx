import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { AnimatePresence } from 'framer-motion';
import { CheckCircle2, User, Target, BrainCircuit } from 'lucide-react';
import api from '../services/api';

// Sub-components
import StepSkills from '../components/dashboard/StepSkills';
import StepRole from '../components/dashboard/StepRole';
import StepConfig from '../components/dashboard/StepConfig';
import StepResults from '../components/dashboard/StepResults';

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
                    {step === 1 && (
                        <StepSkills
                            skills={skills}
                            setSkills={setSkills}
                            onConfirm={handleConfirmSkills}
                            loading={loading}
                            skillsSaved={skillsSaved}
                            error={error}
                        />
                    )}

                    {step === 2 && (
                        <StepRole
                            role={role}
                            setRole={setRole}
                            onConfirm={handleConfirmRole}
                            onBack={() => setStep(1)}
                            loading={loading}
                            error={error}
                        />
                    )}

                    {step === 3 && (
                        <StepConfig
                            missingSkills={missingSkills}
                            onComplete={handleAnalysisComplete}
                            onBack={() => setStep(2)}
                            error={error}
                        />
                    )}

                    {step === 4 && results && (
                        <StepResults
                            results={results}
                            onReset={() => setStep(3)}
                        />
                    )}
                </AnimatePresence>
            </div>
        </>
    );
};

export default Dashboard;
