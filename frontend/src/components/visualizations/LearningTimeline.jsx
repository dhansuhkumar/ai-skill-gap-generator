import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Clock, ChevronRight, Gift } from 'lucide-react';
import Timeline from '../ui/Timeline';

/**
 * LearningTimeline - Interactive timeline showing learning path milestones
 * 
 * Props:
 * - timelineData: Array of { skill, summary, milestones, total_steps, completed_steps, progress_percentage }
 * - onToggleComplete: Callback when user marks step as complete (skill, stepIndex, completed)
 */
const LearningTimeline = ({ timelineData, onToggleComplete }) => {
    const [expandedSkill, setExpandedSkill] = useState(null);

    if (!timelineData || timelineData.length === 0) {
        return (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                <p style={{ color: 'var(--color-text-muted)' }}>No learning timeline available</p>
            </div>
        );
    }

    const handleToggleComplete = (skill, stepIndex, currentCompleted) => {
        if (onToggleComplete) {
            onToggleComplete(skill, stepIndex, !currentCompleted);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ display: 'grid', gap: '1.5rem' }}
        >
            {timelineData.map((skillData, idx) => {
                const isExpanded = expandedSkill === skillData.skill;

                return (
                    <div
                        key={skillData.skill}
                        className="glass-panel"
                        style={{ padding: '1.5rem', overflow: 'hidden' }}
                    >
                        {/* Skill Header */}
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                cursor: 'pointer',
                                marginBottom: isExpanded ? '1.5rem' : 0
                            }}
                            onClick={() => setExpandedSkill(isExpanded ? null : skillData.skill)}
                        >
                            <div style={{ flex: 1 }}>
                                <h4 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--color-primary)' }}>
                                    {skillData.skill}
                                </h4>
                                <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                                    {skillData.summary}
                                </p>

                                {/* Progress Bar */}
                                <div style={{ marginBottom: '0.5rem' }}>
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        fontSize: '0.85rem',
                                        marginBottom: '0.5rem'
                                    }}>
                                        <span style={{ color: 'var(--color-text-muted)' }}>
                                            {skillData.completed_steps} of {skillData.total_steps} steps completed
                                        </span>
                                        <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
                                            {skillData.progress_percentage}%
                                        </span>
                                    </div>
                                    <div style={{
                                        width: '100%',
                                        height: '8px',
                                        background: 'rgba(255,255,255,0.1)',
                                        borderRadius: '4px',
                                        overflow: 'hidden'
                                    }}>
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${skillData.progress_percentage}%` }}
                                            transition={{ duration: 0.5, delay: idx * 0.1 }}
                                            style={{
                                                height: '100%',
                                                background: 'linear-gradient(90deg, #667eea 0%, #f093fb 100%)',
                                                borderRadius: '4px'
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <motion.div
                                animate={{ rotate: isExpanded ? 90 : 0 }}
                                transition={{ duration: 0.2 }}
                                style={{ marginLeft: '1rem' }}
                            >
                                <ChevronRight size={24} color="var(--color-text-muted)" />
                            </motion.div>
                        </div>

                        {/* Milestones (Expandable) */}
                        <AnimatePresence>
                            {isExpanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.3 }}
                                    style={{ overflow: 'hidden' }}
                                >
                                    <div style={{ paddingTop: '1rem' }}>
                                        <Timeline
                                            steps={skillData.milestones}
                                            youtubeVideos={skillData.youtube_videos}
                                            onToggleStep={(stepIdx, completed) => handleToggleComplete(skillData.skill, stepIdx, completed)}
                                        />
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                );
            })}
        </motion.div>
    );
};

export default LearningTimeline;
