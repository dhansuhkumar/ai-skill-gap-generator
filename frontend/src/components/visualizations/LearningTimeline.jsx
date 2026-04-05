import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Flame, Zap, Award, Clock, BookOpen, Star } from 'lucide-react';
import EnhancedLearningCard from '../gamification/EnhancedLearningCard';

/**
 * LearningTimeline - Enhanced interactive timeline with gamification
 * 
 * Props:
 * - timelineData: Array of { skill, summary, milestones, total_steps, completed_steps, progress_percentage, youtube_videos }
 * - onToggleComplete: Callback when user marks step as complete (skill, stepIndex, completed)
 * - onCompleteSkill: Callback when a skill is fully completed
 * - gamification: { xp, level, streak, achievements, progressPercentage }
 */
const LearningTimeline = ({ 
    timelineData, 
    onToggleComplete, 
    onCompleteSkill,
    gamification 
}) => {
    if (!timelineData || timelineData.length === 0) {
        return (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                <p style={{ color: 'var(--color-text-muted)' }}>No learning timeline available</p>
            </div>
        );
    }

    const handleToggleComplete = (skill, stepIndex, completed) => {
        if (onToggleComplete) {
            onToggleComplete(skill, stepIndex, completed);
        }
    };

    const completedSkills = timelineData.filter(s => s.progress_percentage === 100).length;
    const totalSkills = timelineData.length;
    const totalTasks = timelineData.reduce((acc, s) => acc + s.total_steps, 0);
    const completedTasks = timelineData.reduce((acc, s) => acc + s.completed_steps, 0);

    return (
        <div>
            {/* Summary Header */}
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '1rem',
                marginBottom: '1.5rem'
            }}>
                <SummaryCard 
                    icon={<Trophy size={20} color="#fbbf24" />}
                    value={completedSkills}
                    label="Skills Mastered"
                    color="#fbbf24"
                />
                <SummaryCard 
                    icon={<Award size={20} color="#8b5cf6" />}
                    value={`${completedTasks}/${totalTasks}`}
                    label="Tasks Done"
                    color="#8b5cf6"
                />
                <SummaryCard 
                    icon={<Zap size={20} color="#f97316" />}
                    value={gamification?.xp || 0}
                    label="XP Earned"
                    color="#f97316"
                />
                <SummaryCard 
                    icon={<Flame size={20} color="#ef4444" />}
                    value={gamification?.streak || 0}
                    label="Day Streak"
                    color="#ef4444"
                />
            </div>

            {/* Learning Path Cards */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                style={{ display: 'grid', gap: '1.5rem' }}
            >
                {timelineData.map((skillData, idx) => (
                    <motion.div
                        key={skillData.skill}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        <EnhancedLearningCard
                            skillData={skillData}
                            onToggleComplete={handleToggleComplete}
                            onCompleteSkill={onCompleteSkill}
                        />
                    </motion.div>
                ))}
            </motion.div>
        </div>
    );
};

const SummaryCard = ({ icon, value, label, color }) => (
    <div className="glass-panel" style={{ 
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        gap: '0.5rem'
    }}>
        <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            {icon}
        </div>
        <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 800, 
            color: 'var(--color-text-main)',
            lineHeight: 1
        }}>
            {value}
        </div>
        <div style={{ 
            fontSize: '0.75rem', 
            color: 'var(--color-text-muted)'
        }}>
            {label}
        </div>
    </div>
);

export default LearningTimeline;
