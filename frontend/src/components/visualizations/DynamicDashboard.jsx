import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Github, Loader2 } from 'lucide-react';
import SkillComparisonChart from './SkillComparisonChart';
import LearningTimeline from './LearningTimeline';
import CircularProgress from '../ui/CircularProgress';
import { XPProgressBar, AchievementsPanel, LevelUpNotification, AchievementNotification } from '../gamification/GamificationPanel';
import { useGamification } from '../../hooks/useGamification';
import axios from 'axios';

/**
 * DynamicDashboard - Enhanced visualization dashboard with gamification
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

    // GitHub-specific state
    const [githubData, setGithubData] = useState(null);
    const [githubLoading, setGithubLoading] = useState(false);
    const [githubError, setGithubError] = useState('');

    // Path-based progress tracking state
    const [overallProgress, setOverallProgress] = useState({ completed: 0, total: 0, percentage: 0 });

    // Gamification
    const gamification = useGamification(overallProgress);

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

    // Compute overall progress from dashboard data
    useEffect(() => {
        if (dashboardData?.learning_timeline) {
            let total = 0;
            let completed = 0;
            dashboardData.learning_timeline.forEach(skill => {
                total += skill.total_steps || 0;
                completed += skill.completed_steps || 0;
            });
            setOverallProgress({
                completed,
                total,
                percentage: total > 0 ? Math.round((completed / total) * 100) : 0
            });
            // Check achievements
            gamification.checkAchievements(completed, total);
        }
    }, [dashboardData]);

    // Determine path_id from results
    const getPathId = () => {
        // Use target role + selected skills as a stable path identifier
        const role = results?.learning_path?.target_role || results?.target_role || 'default';
        const skills = results?.learning_path?.skills || {};
        const skillsKey = Object.keys(skills).sort().join('-');
        return `path-${role}-${skillsKey}`.replace(/\s+/g, '-').toLowerCase();
    };

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
                    learning_path: results?.learning_path || {},
                    user_skills: userSkills || []
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
        // Determine week_number and day_number from the step data
        const skillData = dashboardData?.learning_timeline?.find(s => s.skill === skill);
        const stepData = skillData?.milestones?.[stepIndex];
        const weekNumber = stepData?.day_from || 1;
        const dayNumber = stepData?.day_to || stepIndex + 1;
        const pathId = getPathId();

        // Update UI immediately (optimistic update)
        setDashboardData(prev => {
            if (!prev) return prev;
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

            // Recalculate overall progress
            let total = 0;
            let comp = 0;
            newTimeline.forEach(s => {
                total += s.total_steps || 0;
                comp += s.completed_steps || 0;
            });

            return {
                ...prev,
                learning_timeline: newTimeline,
                _overallProgress: {
                    completed: comp,
                    total,
                    percentage: total > 0 ? Math.round((comp / total) * 100) : 0
                }
            };
        });

        // Update overall progress state
        setOverallProgress(prev => {
            const delta = completed ? 1 : -1;
            const newCompleted = Math.max(0, prev.completed + delta);
            return {
                ...prev,
                completed: newCompleted,
                percentage: prev.total > 0 ? Math.round((newCompleted / prev.total) * 100) : 0
            };
        });

        // Update gamification if task completed
        if (completed) {
            gamification.completeTask();
        }

        // Call API in background
        try {
            const token = localStorage.getItem('jwtToken');
            await axios.post(
                `${API_URL}/api/update_task_progress`,
                {
                    path_id: pathId,
                    week_number: weekNumber,
                    day_number: dayNumber,
                    task_index: stepIndex,
                    completed: completed
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );
        } catch (err) {
            console.error('Failed to save progress:', err);
        }
    };

    const handleCompleteSkill = useCallback(() => {
        gamification.completeSkill();
    }, [gamification]);

    const githubConnected = githubData?.available || dashboardData?.github_insights?.available;

    const tabs = [
        { id: 'overview', label: 'Overview', icon: BarChart3 },
        { id: 'timeline', label: 'Learning Path', icon: TrendingUp },
        ...(githubConnected ? [{ id: 'github', label: 'GitHub Insights', icon: Github }] : []),
    ];

    if (loading) {
        return (
            <div className="glass-panel" style={{ padding: '4rem', textAlign: 'center' }}>
                <div className="loader" style={{ margin: '0 auto 1.25rem', width: '44px', height: '44px' }} />
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.95rem' }}>Building your dashboard...</p>
            </div>
        );
    }

    if (error && !dashboardData) {
        return (
            <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
                <p style={{ color: 'var(--color-error)', fontSize: '0.95rem' }}>{error}</p>
            </div>
        );
    }

    // Calculate week info for progress bar
    const getWeekInfo = () => {
        if (!dashboardData?.learning_timeline?.length) return null;
        let totalSteps = 0;
        let completedSteps = 0;
        let currentWeek = 1;
        let totalWeeks = 1;

        dashboardData.learning_timeline.forEach(skill => {
            totalSteps += skill.total_steps || 0;
            completedSteps += skill.completed_steps || 0;
        });

        // Estimate weeks from steps (roughly 5 steps per week)
        totalWeeks = Math.max(1, Math.ceil(totalSteps / 5));
        currentWeek = Math.max(1, Math.min(totalWeeks, Math.ceil((completedSteps / Math.max(1, totalSteps)) * totalWeeks)));

        return { currentWeek, totalWeeks, completedSteps, totalSteps };
    };

    const weekInfo = getWeekInfo();
    const weekPercentage = weekInfo ? Math.round((weekInfo.completedSteps / weekInfo.totalSteps) * 100) : 0;

    return (
        <div>
            {/* Sticky Progress Bar at top of results page */}
            {weekInfo && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                        position: 'sticky',
                        top: 0,
                        zIndex: 100,
                        background: 'rgba(15, 15, 35, 0.95)',
                        backdropFilter: 'blur(12px)',
                        borderBottom: '1px solid var(--color-border)',
                        padding: '0.875rem 1.25rem',
                        marginBottom: '1.5rem',
                        borderRadius: 'var(--radius-lg)'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: '1200px', margin: '0 auto' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <CircularProgress percentage={weekPercentage} size={48} strokeWidth={4} showLabel={false} />
                            <div>
                                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
                                    Week {weekInfo.currentWeek} of {weekInfo.totalWeeks} — {weekPercentage}% Complete
                                </div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                    {weekInfo.completedSteps} of {weekInfo.totalSteps} tasks completed
                                </div>
                            </div>
                        </div>
                        {/* Week progress bar */}
                        <div style={{ flex: 1, maxWidth: '300px', marginLeft: '2rem' }}>
                            <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${weekPercentage}%` }}
                                    transition={{ duration: 0.5 }}
                                    style={{
                                        height: '100%',
                                        background: 'linear-gradient(90deg, var(--color-primary), var(--color-secondary))',
                                        borderRadius: '3px'
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Summary Stats with Circular Progress Ring */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                {/* Circular Progress Ring Widget */}
                <div className="stat-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
                    <CircularProgress percentage={weekPercentage} size={80} strokeWidth={6} />
                    <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
                        Overall Progress
                    </div>
                </div>
                {[
                    { label: 'Skills to Learn', value: dashboardData?.summary?.total_skills || 0, suffix: '' },
                    { label: 'Portfolio Projects', value: dashboardData?.summary?.projects || 0, suffix: '' },
                    { label: 'Video Resources', value: dashboardData?.summary?.videos || 0, suffix: '' },
                    { label: 'Match Score', value: results?.matching_score ?? '—', suffix: results?.matching_score != null ? '%' : '' },
                ].map(stat => (
                    <div className="stat-card" key={stat.label}>
                        <div className="stat-value">{stat.value}{stat.suffix}</div>
                        <div className="stat-label">{stat.label}</div>
                    </div>
                ))}
            </div>

            {/* Gamification Section */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                <XPProgressBar 
                    xp={gamification.xp}
                    xpInCurrentLevel={gamification.xpInCurrentLevel}
                    xpToNextLevel={gamification.xpToNextLevel}
                    level={gamification.level}
                    streak={gamification.streak}
                />
                <AchievementsPanel 
                    achievements={gamification.achievements}
                    unlockedAchievements={gamification.unlockedAchievements}
                    progressPercentage={weekPercentage}
                />
            </div>

            {/* GitHub connected badge */}
            {githubConnected && (
                <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.4rem 0.875rem', marginBottom: '1.5rem',
                    background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                    borderRadius: '999px', fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-success)'
                }}>
                    <Github size={13} /> @{githubData?.username || githubUsername} · Connected
                </div>
            )}

            {/* Tab Navigation */}
            <div style={{
                display: 'flex',
                gap: '0.375rem',
                marginBottom: '2rem',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                padding: '0.375rem',
                width: 'fit-content'
            }}>
                {tabs.map(tab => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                background: isActive
                                    ? 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.1))'
                                    : 'transparent',
                                border: isActive ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
                                padding: '0.5rem 1.125rem',
                                color: isActive ? 'var(--color-primary-light)' : 'var(--color-text-muted)',
                                cursor: 'pointer',
                                borderRadius: 'var(--radius-md)',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.45rem',
                                fontSize: '0.875rem',
                                fontWeight: isActive ? 600 : 500,
                                transition: 'all 0.2s',
                                fontFamily: 'var(--font-main)'
                            }}
                        >
                            <Icon size={16} />
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
                        onCompleteSkill={handleCompleteSkill}
                        gamification={gamification}
                    />
                )}

                {activeTab === 'github' && (
                    <div className="glass-panel" style={{ padding: '2.25rem' }}>
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

            {/* Level Up Notification */}
            <LevelUpNotification level={gamification.level} show={gamification.showLevelUp} />
            
            {/* Achievement Notification */}
            <AchievementNotification achievement={gamification.newAchievement} show={!!gamification.newAchievement} />
        </div>
    );
};

export default DynamicDashboard;
