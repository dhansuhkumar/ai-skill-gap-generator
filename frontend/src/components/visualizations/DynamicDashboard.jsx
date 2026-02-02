import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Github, Network } from 'lucide-react';
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
 * - githubUsername: GitHub username (optional)
 */
const DynamicDashboard = ({ results, userSkills, roleAnalysis, githubUsername }) => {
    const [activeTab, setActiveTab] = useState('overview');
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

    useEffect(() => {
        fetchDashboardData();
    }, [results, userSkills, roleAnalysis]);

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
                        {dashboardData?.github_insights?.available ? (
                            <div>
                                <h3 style={{ marginBottom: '1rem' }}>GitHub Profile: {dashboardData.github_insights.username}</h3>
                                <div style={{ display: 'grid', gap: '1rem' }}>
                                    <div>
                                        <strong>Total Repositories:</strong> {dashboardData.github_insights.total_repos}
                                    </div>
                                    <div>
                                        <strong>Languages Detected:</strong> {dashboardData.github_insights.language_count}
                                    </div>
                                    <div>
                                        <strong>Diversity Score:</strong> +{dashboardData.github_insights.diversity_score}%
                                    </div>

                                    <h4 style={{ marginTop: '1rem' }}>Top Languages:</h4>
                                    <div style={{ display: 'grid', gap: '0.5rem' }}>
                                        {dashboardData.github_insights.languages.map((lang, idx) => (
                                            <div key={idx} style={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                padding: '0.75rem',
                                                background: 'rgba(255,255,255,0.03)',
                                                borderRadius: '8px'
                                            }}>
                                                <span>{lang.name}</span>
                                                <span style={{ fontWeight: 'bold', color: 'var(--color-primary)' }}>
                                                    {lang.score}%
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <Github size={48} color="var(--color-text-muted)" style={{ margin: '0 auto 1rem' }} />
                                <h3 style={{ marginBottom: '1rem' }}>No GitHub Data Available</h3>
                                <p style={{ color: 'var(--color-text-muted)' }}>
                                    Connect your GitHub account in the skills step to see detailed repository insights.
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
