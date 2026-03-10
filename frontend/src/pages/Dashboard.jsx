import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, User, Target, BrainCircuit, ListChecks, Clock, Briefcase, Sparkles, RefreshCw } from 'lucide-react';
import api from '../services/api';

// Sub-components
import StepSkills from '../components/dashboard/StepSkills';
import StepRole from '../components/dashboard/StepRole';
import StepMissingSkills from '../components/dashboard/StepMissingSkills';
import StepLearningQuestions from '../components/dashboard/StepLearningQuestions';
import StepProjectPreferences from '../components/dashboard/StepProjectPreferences';
import StepResults from '../components/dashboard/StepResults';
import StepProgressIndicator from '../components/StepProgressIndicator';
import AIChatSidebar from '../components/ui/AIChatSidebar';
import ErrorBoundary from '../components/ErrorBoundary';

const Dashboard = () => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [profileId, setProfileId] = useState(null);
    const [skillsSaved, setSkillsSaved] = useState(false);
    const [hasSavedPath, setHasSavedPath] = useState(false);
    const [checkingExisting, setCheckingExisting] = useState(true);

    // Data State
    const [skills, setSkills] = useState([]);
    const [role, setRole] = useState('');
    const [missingSkills, setMissingSkills] = useState([]);
    const [matchData, setMatchData] = useState(null);
    const [selectedToLearn, setSelectedToLearn] = useState([]);
    const [githubUsername, setGithubUsername] = useState('');
    const [learningPrefs, setLearningPrefs] = useState({
        time_commitment: '1 hour',
        learning_pace: 'Balanced',
        duration: '1 month'
    });
    const [results, setResults] = useState(null);

    // Check for existing saved learning path on mount
    useEffect(() => {
        checkForSavedPath();
    }, []);

    const checkForSavedPath = async () => {
        try {
            const res = await api.getSavedLearningPath();
            if (res.data && res.data.has_saved_path) {
                setHasSavedPath(true);
                setRole(res.data.data.target_role || '');
                setSelectedToLearn(res.data.data.selected_skills || []);
                setResults({ learning_path: res.data.data.learning_path });
                setStep(6); // Go directly to results
            }
        } catch (err) {
            console.log('No saved path found');
        } finally {
            setCheckingExisting(false);
        }
    };

    const handleStartNew = () => {
        // Reset all state for new generation
        setStep(1);
        setSkills([]);
        setRole('');
        setMissingSkills([]);
        setMatchData(null);
        setSelectedToLearn([]);
        setGithubUsername('');
        setResults(null);
        setHasSavedPath(false);
    };

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

    // Step 2: Role -> Compute Gaps
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
            const params = {
                profile_id: profileId,
                target_role: role,
                selected_skills: selectedToLearn,
                time_commitment: learningPrefs.time_commitment,
                learning_pace: learningPrefs.learning_pace,
                duration: learningPrefs.duration,
                project_type: projectConfig.project_type || 'portfolio',
                include_youtube: projectConfig.include_youtube,
                additional_context: projectConfig.additional_context,
                provider: 'auto'
            };

            const res = await api.generateLearningPath(params);

            if (res.data && (res.data.status === 'ok' || res.data.learning_path)) {
                setResults(res.data);
                setStep(6);

                // Save learning path to persistence
                try {
                    await api.saveLearningPath({
                        target_role: role,
                        selected_skills: selectedToLearn,
                        learning_path: res.data
                    });
                } catch (saveErr) {
                    console.error('Failed to save learning path:', saveErr);
                }
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
        const displayStep = step === 5 ? 4 : (step === 6 ? 5 : step);

        const steps = [
            { id: 1, label: 'Skills', icon: User },
            { id: 2, label: 'Role', icon: Target },
            { id: 3, label: 'Gaps', icon: ListChecks },
            { id: 4, label: 'Plan', icon: Clock },
            { id: 5, label: 'Result', icon: Sparkles }
        ];

        return <StepProgressIndicator currentStep={displayStep} steps={steps} />;
    };

    // Context for AI sidebar
    const getAIContext = () => {
        const stepNames = ['', 'Adding Skills', 'Selecting Role', 'Choosing Skills to Learn', 'Setting Preferences', 'Configuring Projects', 'Viewing Learning Path'];
        return {
            currentStep: step,
            stepName: stepNames[step] || 'Dashboard',
            role: role,
            skills: skills.map(s => typeof s === 'string' ? s : s.name),
            selectedToLearn: selectedToLearn,
            hasResults: !!results
        };
    };

    if (checkingExisting) {
        return (
            <>
                <Navbar />
                <div className="container" style={{ paddingTop: 'calc(var(--header-height) + 4rem)', textAlign: 'center' }}>
                    <div className="loader" style={{ margin: '0 auto' }}></div>
                    <p style={{ color: 'var(--color-text-muted)', marginTop: '1rem' }}>
                        Loading your dashboard...
                    </p>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <div style={{
                display: 'flex',
                minHeight: '100vh',
                paddingTop: 'var(--header-height)'
            }}>
                {/* Main Content Area */}
                <div style={{
                    flex: 1,
                    padding: '2rem',
                    paddingBottom: '5rem',
                    marginRight: '400px' // Space for sidebar
                }}>
                    {/* New Generation Button if viewing saved path */}
                    {hasSavedPath && step === 6 && (
                        <div style={{ marginBottom: '1.5rem', textAlign: 'right' }}>
                            <button
                                onClick={handleStartNew}
                                className="btn btn-secondary"
                                style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}
                            >
                                <RefreshCw size={16} />
                                New Generation
                            </button>
                        </div>
                    )}

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

                    <ErrorBoundary>

                        <AnimatePresence mode="wait">
                            {step === 1 && (
                                <StepSkills
                                    skills={skills}
                                    setSkills={setSkills}
                                    onConfirm={handleConfirmSkills}
                                    loading={loading}
                                    skillsSaved={skillsSaved}
                                    error={error}
                                    githubUsername={githubUsername}
                                    setGithubUsername={setGithubUsername}
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
                                    onReset={handleStartNew}
                                    userSkills={skills}
                                    roleAnalysis={matchData}
                                    githubUsername={githubUsername}
                                />
                            )}
                        </AnimatePresence>
                    </ErrorBoundary>
                </div>

                {/* AI Chat Sidebar - Always visible on the right */}
                <AIChatSidebar
                    context={getAIContext()}
                    role={role}
                />
            </div>
        </>
    );
};

export default Dashboard;
