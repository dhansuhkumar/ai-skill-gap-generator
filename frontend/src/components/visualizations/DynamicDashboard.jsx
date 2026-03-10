import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Github, Loader2 } from 'lucide-react';
import SkillComparisonChart from './SkillComparisonChart';
import LearningTimeline from './LearningTimeline';
import axios from 'axios';

/**
 * DynamicDashboard - Unified visualization dashboard combining all data sources
 *
 * Props:
 * - results: Learning path data from backend
 * - userSkills: User's current skills
 * - roleAnalysis: Role gap analysis data
 * - githubUsername: GitHub username (optional) — now actually triggers API call
 */
const DynamicDashboard = ({ results, userSkills, roleAnalysis, githubUsername }) => {
    const [activeTab, setActiveTab] = useState('overview');
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // GitHub-specific state — fetched independently so it doesn't block the main view
    const [githubData, setGithubData] = useState(null);
    const [githubLoading, setGithubLoading] = useState(false);
    const [githubError, setGithubError] = useState('');

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

    useEffect(() => {
        fetchDashboardData();
    }, [results, userSkills, roleAnalysis]);

    // Fire GitHub analysis whenever a username is (or becomes) available
    useEffect(() => {
        if (githubUsername && githubUsername.trim()) {
            fetchGithubData(githubUsername.trim());
        }
    }, [githubUsername]);

    const fetchGithubData = async (username) => {
        setGithubLoading(true);
        setGithubError('');
        try {
            const token = localStorage.getItem('jwtToken');
            const response = await axios.post(
                `${API_URL}/api/analyze-github`,
                { github_username: username },
                { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
            );
            if (response.data && response.data.status === 'ok') {
                // Normalise language data into a sorted list for display
                const rawLangs = response.data.languages || {};
                const languages = Object.entries(rawLangs)
                    .map(([name, info]) => ({
                        name,
                        score: typeof info === 'object' ? (info.score ?? 0) : info,
                        repos: typeof info === 'object' ? (info.repos ?? 0) : 0,
                        has_tests: typeof info === 'object' ? (info.has_tests ?? false) : false,
                    }))
                    .sort((a, b) => b.score - a.score)
                    .slice(0, 10);
                setGithubData({
                    available: true,
                    username: response.data.username || username,
                    total_repos: response.data.total_repos || 0,
                    language_count: response.data.language_count || languages.length,
                    diversity_bonus: response.data.diversity_bonus || 0,
                    languages,
                });
            } else {
                setGithubError(response.data?.error || 'GitHub analysis returned no data');
            }
        } catch (err) {
            const msg = err.response?.data?.error || err.message || 'Failed to analyse GitHub profile';
            setGithubError(msg);
            console.error('GitHub analysis failed:', msg);
        } finally {
            setGithubLoading(false);
        }
    };



    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            setError('');

            const token = localStorage.getItem('jwtToken');

            const response = await axios.post(
                `${API_URL}/api/get_dashboard_data`,
                {
                    role_analysis: roleAnalysis || {},
                    learning_path: results?.learning_path || {}
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (response.data && response.data.dashboard_data) {
                setDashboardData(response.data.dashboard_data);
            }
            setLoading(false);
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err);
            setError('Failed to load visualization data');
            setLoading(false);

            // Create fallback data from results
            createFallbackData();
        }
    };

    const createFallbackData = () => {
        // Create basic visualization data from results if API fails
        const learningPaths = results?.learning_path?.skills || {};
        const projects = results?.learning_path?.projects || [];
        const videos = results?.learning_path?.videos || [];

        // Calculate current proficiency from userSkills
        const getUserProficiency = (skillName) => {
            if (!userSkills || userSkills.length === 0) return 0;

            for (const skill of userSkills) {
                const name = typeof skill === 'string' ? skill : skill.name;
                if (name?.toLowerCase() === skillName.toLowerCase()) {
                    // If skill is in user's list, they have some proficiency
                    return typeof skill === 'object' ? (skill.confidence || 80) : 80;
                }
            }
            return 0; // Skill not in user's list
        };

        // Build skill comparison with actual proficiency data
        const skillItems = Object.keys(learningPaths).map(skill => {
            const currentProf = getUserProficiency(skill);
            const requiredProf = 80;
            return {
                name: skill,
                current_proficiency: currentProf,
                required_proficiency: requiredProf,
                gap: Math.max(0, requiredProf - currentProf),
                source: currentProf > 0 ? 'user' : 'missing'
            };
        });

        // Calculate averages
        const totalCurrent = skillItems.reduce((sum, s) => sum + s.current_proficiency, 0);
        const totalRequired = skillItems.reduce((sum, s) => sum + s.required_proficiency, 0);
        const numSkills = skillItems.length || 1;

        // Count videos from skill paths
        let totalVideos = videos.length;
        Object.values(learningPaths).forEach(path => {
            totalVideos += (path.youtube_videos || []).length;
        });

        const fallbackData = {
            skill_comparison: {
                skills: skillItems,
                average_current: Math.round(totalCurrent / numSkills),
                average_required: Math.round(totalRequired / numSkills),
                overall_gap: Math.round((totalRequired - totalCurrent) / numSkills)
            },
            learning_timeline: Object.keys(learningPaths).map(skill => ({
                skill: skill,
                summary: learningPaths[skill].summary || '',
                milestones: (learningPaths[skill].steps || []).map(step => ({
                    ...step,
                    completed: false
                })),
                youtube_videos: learningPaths[skill].youtube_videos || [],
                total_steps: (learningPaths[skill].steps || []).length,
                completed_steps: 0,
                progress_percentage: 0
            })),
            github_insights: {
                available: !!githubUsername,
                username: githubUsername,
                total_repos: 0,
                languages: []
            },
            summary: {
                total_skills: Object.keys(learningPaths).length,
                projects: projects.length,
                videos: totalVideos,
                github_available: !!githubUsername
            }
        };

        setDashboardData(fallbackData);
    };

    const handleToggleProgress = async (skill, stepIndex, completed) => {
        try {
            const token = localStorage.getItem('jwtToken');

            await axios.post(
                `${API_URL}/api/save_learning_progress`,
                {
                    skill_name: skill,
                    step_index: stepIndex,
                    completed: completed
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            // Update local state
            setDashboardData(prev => {
                const newTimeline = prev.learning_timeline.map(item => {
                    if (item.skill === skill) {
                        const newMilestones = item.milestones.map((m, idx) =>
                            idx === stepIndex ? { ...m, completed } : m
                        );
                        const completedCount = newMilestones.filter(m => m.completed).length;
                        return {
                            ...item,
                            milestones: newMilestones,
                            completed_steps: completedCount,
                            progress_percentage: Math.round((completedCount / newMilestones.length) * 100)
                        };
                    }
                    return item;
                });

                return { ...prev, learning_timeline: newTimeline };
            });
        } catch (err) {
            console.error('Failed to save progress:', err);
        }
    };

    const tabs = [
        { id: 'overview', label: 'Overview', icon: BarChart3 },
        { id: 'timeline', label: 'Learning Path', icon: TrendingUp },
        { id: 'github', label: 'GitHub Insights', icon: Github },
    ];

    if (loading) {
        return (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                <div className="loader" style={{ margin: '0 auto' }}></div>
                <p style={{ color: 'var(--color-text-muted)', marginTop: '1rem' }}>
                    Loading dashboard data...
                </p>
            </div>
        );
    }

    if (error && !dashboardData) {
        return (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                <p style={{ color: 'var(--color-error)' }}>{error}</p>
            </div>
        );
    }

    return (
        <div>
            {/* Summary Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                        Skills to Learn
                    </h4>
                    <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                        {dashboardData?.summary?.total_skills || 0}
                    </div>
                </div>
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                        Portfolio Projects
                    </h4>
                    <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--color-secondary)' }}>
                        {dashboardData?.summary?.projects || 0}
                    </div>
                </div>
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                        Video Resources
                    </h4>
                    <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#ef4444' }}>
                        {dashboardData?.summary?.videos || 0}
                    </div>
                </div>
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                        GitHub Status
                    </h4>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: dashboardData?.github_insights?.available ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
                        {dashboardData?.github_insights?.available ? '✓ Connected' : 'Not Connected'}
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div style={{
                display: 'flex',
                gap: '1rem',
                marginBottom: '2rem',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: '0'
            }}>
                {tabs.map(tab => {
                    const Icon = tab.icon;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                background: 'none',
                                border: 'none',
                                padding: '1rem 1.5rem',
                                color: activeTab === tab.id ? 'var(--color-primary)' : 'var(--color-text-muted)',
                                cursor: 'pointer',
                                borderBottom: activeTab === tab.id ? '2px solid var(--color-primary)' : '2px solid transparent',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                fontSize: '1rem',
                                fontWeight: activeTab === tab.id ? 600 : 400,
                                transition: 'all 0.2s'
                            }}
                        >
                            <Icon size={20} />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Tab Content */}
            <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
            >
                {activeTab === 'overview' && dashboardData?.skill_comparison && (
                    <SkillComparisonChart
                        skillData={dashboardData.skill_comparison.skills}
                        averageCurrent={dashboardData.skill_comparison.average_current}
                        averageRequired={dashboardData.skill_comparison.average_required}
                    />
                )}

                {activeTab === 'timeline' && dashboardData?.learning_timeline && (
                    <LearningTimeline
                        timelineData={dashboardData.learning_timeline}
                        onToggleComplete={handleToggleProgress}
                    />
                )}

                {activeTab === 'github' && (
                    <div className="glass-panel" style={{ padding: '2rem' }}>
                        {/* Loading state */}
                        {githubLoading && (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <Loader2 size={40} style={{ margin: '0 auto 1rem', animation: 'spin 1s linear infinite', display: 'block' }} color="var(--color-primary)" />
                                <p style={{ color: 'var(--color-text-muted)' }}>
                                    Analysing GitHub profile for <strong>{githubUsername}</strong>...
                                </p>
                            </div>
                        )}

                        {/* Error state */}
                        {!githubLoading && githubError && (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <Github size={48} color="var(--color-error)" style={{ margin: '0 auto 1rem', display: 'block' }} />
                                <h3 style={{ marginBottom: '0.5rem', color: 'var(--color-error)' }}>Analysis Failed</h3>
                                <p style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }}>{githubError}</p>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => fetchGithubData(githubUsername)}
                                >
                                    Retry
                                </button>
                            </div>
                        )}

                        {/* Data available */}
                        {!githubLoading && !githubError && githubData?.available && (
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                                    <Github size={28} color="var(--color-primary)" />
                                    <div>
                                        <h3 style={{ margin: 0 }}>@{githubData.username}</h3>
                                        <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                                            {githubData.total_repos} repositories · {githubData.language_count} languages · +{githubData.diversity_bonus}% diversity bonus
                                        </span>
                                    </div>
                                </div>

                                <h4 style={{ marginBottom: '0.75rem', color: 'var(--color-text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                    Language Proficiency
                                </h4>
                                <div style={{ display: 'grid', gap: '0.6rem' }}>
                                    {githubData.languages.map((lang, idx) => (
                                        <div key={idx} style={{
                                            display: 'grid',
                                            gridTemplateColumns: '120px 1fr 60px',
                                            alignItems: 'center',
                                            gap: '1rem',
                                            padding: '0.75rem 1rem',
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '8px',
                                            border: '1px solid var(--color-border)'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span style={{ fontWeight: 600 }}>{lang.name}</span>
                                                {lang.has_tests && (
                                                    <span title="Has test files" style={{ fontSize: '0.7rem', background: 'rgba(34,197,94,0.2)', color: '#4ade80', padding: '1px 6px', borderRadius: '999px' }}>
                                                        tests
                                                    </span>
                                                )}
                                            </div>
                                            <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '999px', height: '8px', overflow: 'hidden' }}>
                                                <div style={{
                                                    width: `${lang.score}%`,
                                                    height: '100%',
                                                    background: 'linear-gradient(90deg, var(--color-primary), var(--color-secondary))',
                                                    borderRadius: '999px',
                                                    transition: 'width 0.6s ease'
                                                }} />
                                            </div>
                                            <span style={{ fontWeight: 'bold', color: 'var(--color-primary)', textAlign: 'right' }}>
                                                {lang.score}%
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* No username provided */}
                        {!githubLoading && !githubError && !githubData?.available && (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <Github size={48} color="var(--color-text-muted)" style={{ margin: '0 auto 1rem', display: 'block' }} />
                                <h3 style={{ marginBottom: '1rem' }}>No GitHub Data Available</h3>
                                <p style={{ color: 'var(--color-text-muted)' }}>
                                    Enter your GitHub username in <strong>Step 1</strong> to see detailed repository and language insights here.
                                </p>
                            </div>
                        )}
                    </div>
                )}

            </motion.div>
        </div>
    );
};

export default DynamicDashboard;
