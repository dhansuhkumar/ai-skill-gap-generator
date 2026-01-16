import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { AnimatePresence } from 'framer-motion';
import { CheckCircle2, User, Target, BrainCircuit, ListChecks, Clock, Briefcase } from 'lucide-react';
import api from '../services/api';

// Sub-components
import StepSkills from '../components/dashboard/StepSkills';
import StepRole from '../components/dashboard/StepRole';
import StepMissingSkills from '../components/dashboard/StepMissingSkills';
import StepLearningQuestions from '../components/dashboard/StepLearningQuestions';
import StepProjectPreferences from '../components/dashboard/StepProjectPreferences';
import StepResults from '../components/dashboard/StepResults';

const Dashboard = () => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [profileId, setProfileId] = useState(null);
    const [skillsSaved, setSkillsSaved] = useState(false);

    // Data State
    const [skills, setSkills] = useState([]);
    const [role, setRole] = useState('');
    const [missingSkills, setMissingSkills] = useState([]);
    const [matchData, setMatchData] = useState(null); // Store match score data
    const [selectedToLearn, setSelectedToLearn] = useState([]);
    const [learningPrefs, setLearningPrefs] = useState({
        time_commitment: '1 hour',
        learning_pace: 'Balanced',
        duration: '1 month'
    });
    const [results, setResults] = useState(null);

    // Step 1: Skills
    const handleConfirmSkills = async () => {
        if (skills.length === 0) {
            setError('Please add at least one skill.');
            return;
        }
        setError('');
        setSkillsSaved(true);
        setLoading(true);

        const formattedSkills = skills.map(skill => ({
            name: typeof skill === 'string' ? skill : skill.name || skill,
            confidence: typeof skill === 'object' ? (skill.confidence || 80) : 80,
            source: typeof skill === 'object' ? (skill.source || 'user') : 'user'
        }));

        try {
            const response = await api.confirmSkills(formattedSkills);
            if (response.data && response.data.profile_id) {
                setProfileId(response.data.profile_id);
            }
            setLoading(false);
            setStep(2);
        } catch (err) {
            setSkillsSaved(false);
            setLoading(false);
            setError(err.response?.data?.error || 'Failed to save skills.');
        }
    };

    // Step 2: Role -> Compute Gaps (Deterministic)
    const handleConfirmRole = async () => {
        if (!role.trim()) {
            setError('Please enter a target role.');
            return;
        }
        setError('');
        setLoading(true);
        try {
            const skillNames = skills.map(s => typeof s === 'string' ? s : (s.name || s));
            const res = await api.analyzeRoleGaps(skillNames, role);

            if (res.data && res.data.missing_skills) {
                setMissingSkills(res.data.missing_skills);
                // Store match data for display
                setMatchData({
                    match_score: res.data.match_score || 0,
                    user_skills_count: res.data.user_skills_count || 0,
                    required_skills_count: res.data.required_skills_count || 0,
                    matched_jobs_count: res.data.matched_jobs_count || 0
                });
            } else {
                setMissingSkills([]);
                setMatchData(null);
            }
            setStep(3);
        } catch (err) {
            setError(err.response?.data?.error || 'Role analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    // Step 3: Select Missing Skills
    const handleSelectMissing = (selected) => {
        setSelectedToLearn(selected);
        setStep(4);
    };

    // Step 4: Learning Questions
    const handleLearningPrefs = (prefs) => {
        setLearningPrefs(prefs);
        setStep(5);
    };

    // Step 5: Project & Generate
    const handleGeneratePath = async (projectConfig) => {
        setLoading(true);
        setError('');

        try {
            // Combine all inputs
            const params = {
                profile_id: profileId,
                target_role: role,
                selected_skills: selectedToLearn,
                // Maps from learningPrefs
                time_commitment: learningPrefs.time_commitment,
                learning_pace: learningPrefs.learning_pace,
                duration: learningPrefs.duration,
                // Maps from projectConfig
                project_type: projectConfig.project_type || 'portfolio',
                include_youtube: projectConfig.include_youtube,
                additional_context: projectConfig.additional_context,
                provider: 'auto'
            };

            const res = await api.generateLearningPath(params);

            if (res.data && (res.data.status === 'ok' || res.data.learning_path)) {
                setResults(res.data);
                setStep(6);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (err) {
            const status = err.response?.status;
            if (status === 429) {
                setError('AI provider is busy. Please try again in a moment.');
            } else {
                setError(err.response?.data?.error || 'Failed to generate plan.');
            }
        } finally {
            setLoading(false);
        }
    };

    const renderProgress = () => {
        const steps = [
            { id: 1, label: 'Skills', icon: User },
            { id: 2, label: 'Role', icon: Target },
            { id: 3, label: 'Gaps', icon: ListChecks },
            { id: 4, label: 'Plan', icon: Clock }, // Grouping Questions/Project roughly
            { id: 6, label: 'Result', icon: BrainCircuit }
        ];

        // Map current step to progress index
        // Steps 4 & 5 map to "Plan" (id 4) visually for cleaner UI
        const activeId = step === 5 ? 4 : step;

        return (
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '3rem', gap: '1rem', flexWrap: 'wrap' }}>
                {steps.map((s, idx) => (
                    <div key={s.id} style={{ display: 'flex', alignItems: 'center' }}>
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            opacity: activeId >= s.id ? 1 : 0.5,
                            color: activeId >= s.id ? 'var(--color-primary)' : 'var(--color-text-muted)'
                        }}>
                            <div style={{
                                width: '32px', height: '32px', borderRadius: '50%',
                                background: activeId > s.id ? 'var(--color-success)' : (activeId === s.id ? 'var(--color-primary)' : 'rgba(255,255,255,0.1)'),
                                color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontWeight: 'bold'
                            }}>
                                {activeId > s.id || step === 6 ? <CheckCircle2 size={16} /> : (idx + 1)}
                            </div>
                            <span style={{ fontWeight: 500, display: window.innerWidth < 600 ? 'none' : 'block' }}>{s.label}</span>
                        </div>
                        {idx < steps.length - 1 && (
                            <div style={{ height: '2px', width: '30px', background: 'var(--color-border)', margin: '0 0.5rem' }} />
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

                {error && (
                    <div className="glass-panel" style={{
                        padding: '1rem', marginBottom: '2rem',
                        borderColor: 'var(--color-error)', color: 'var(--color-error)',
                        textAlign: 'center'
                    }}>
                        {error}
                    </div>
                )}

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
                        />
                    )}

                    {step === 3 && (
                        <StepMissingSkills
                            missingSkills={missingSkills}
                            matchData={matchData}
                            onNext={handleSelectMissing}
                            onBack={() => setStep(2)}
                        />
                    )}

                    {step === 4 && (
                        <StepLearningQuestions
                            onNext={handleLearningPrefs}
                            onBack={() => setStep(3)}
                        />
                    )}

                    {step === 5 && (
                        <StepProjectPreferences
                            onGenerate={handleGeneratePath}
                            onBack={() => setStep(4)}
                            loading={loading}
                        />
                    )}

                    {step === 6 && results && (
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
