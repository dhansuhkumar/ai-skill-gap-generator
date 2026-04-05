import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    CheckCircle2, Circle, ChevronDown, ChevronUp, Play, 
    Clock, Star, Trophy, Zap, BookOpen, ExternalLink, Lock
} from 'lucide-react';
import { getSkillDescription, estimateTaskTime, getRandomMotivation } from '../../hooks/useGamification';

const EnhancedLearningCard = ({ skillData, onToggleComplete, onCompleteSkill, isLast }) => {
    const [expanded, setExpanded] = useState(false);
    const [showMotivation, setShowMotivation] = useState(false);
    const [justCompleted, setJustCompleted] = useState(false);
    
    const isSkillComplete = skillData.progress_percentage === 100;
    const totalTime = skillData.milestones?.reduce((acc, step) => {
        const tasks = step.tasks?.length || 1;
        return acc + (tasks * 30);
    }, 0) || 0;

    useEffect(() => {
        if (isSkillComplete && !justCompleted) {
            setJustCompleted(true);
            setShowMotivation(true);
            onCompleteSkill?.();
            setTimeout(() => setShowMotivation(false), 5000);
        }
    }, [isSkillComplete]);

    const handleToggleComplete = (stepIdx, completed) => {
        onToggleComplete?.(skillData.skill, stepIdx, completed);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel"
            style={{ 
                overflow: 'hidden',
                borderColor: isSkillComplete ? 'rgba(16,185,129,0.3)' : 'var(--color-border)',
            }}
        >
            {/* Skill Header */}
            <div 
                className="skill-header"
                onClick={() => setExpanded(!expanded)}
                style={{
                    padding: '1.5rem',
                    cursor: 'pointer',
                    background: isSkillComplete 
                        ? 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(16,185,129,0.02) 100%)'
                        : 'transparent',
                    transition: 'all 0.3s ease',
                }}
            >
                <div className="skill-header-content">
                    {/* Skill Icon/Avatar */}
                    <div style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '16px',
                        background: isSkillComplete 
                            ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                            : 'linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(6,182,212,0.1) 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.5rem',
                        marginRight: '1rem',
                        boxShadow: isSkillComplete 
                            ? '0 4px 20px rgba(16,185,129,0.3)'
                            : '0 4px 20px rgba(99,102,241,0.2)',
                    }}>
                        {isSkillComplete ? <Trophy size={24} color="white" /> : <Star size={24} color="#818cf8" />}
                    </div>

                    <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                            <h3 style={{ 
                                fontSize: '1.35rem', 
                                fontWeight: 700,
                                color: isSkillComplete ? 'var(--color-success)' : 'var(--color-text-main)',
                                margin: 0
                            }}>
                                {skillData.skill}
                            </h3>
                            {isSkillComplete && (
                                <motion.span
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    style={{
                                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                        color: 'white',
                                        padding: '0.2rem 0.6rem',
                                        borderRadius: '999px',
                                        fontSize: '0.7rem',
                                        fontWeight: 600,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.25rem'
                                    }}
                                >
                                    <CheckCircle2 size={12} /> Mastered
                                </motion.span>
                            )}
                        </div>
                        
                        <p style={{ 
                            fontSize: '0.9rem', 
                            color: 'var(--color-text-muted)',
                            margin: '0 0 0.75rem 0',
                            lineHeight: 1.5
                        }}>
                            {getSkillDescription(skillData.skill)}
                        </p>

                        {/* Quick Stats */}
                        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                            <div style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '0.35rem',
                                fontSize: '0.8rem',
                                color: 'var(--color-text-muted)'
                            }}>
                                <Clock size={14} />
                                ~{Math.round(totalTime / 60)}h {totalTime % 60}m
                            </div>
                            <div style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '0.35rem',
                                fontSize: '0.8rem',
                                color: 'var(--color-text-muted)'
                            }}>
                                <BookOpen size={14} />
                                {skillData.total_steps} modules
                            </div>
                            <div style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '0.35rem',
                                fontSize: '0.8rem',
                                color: 'var(--color-text-muted)'
                            }}>
                                <Zap size={14} />
                                +{skillData.total_steps * 10} XP
                            </div>
                        </div>
                    </div>
                </div>

                {/* Progress Section */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
                    <div style={{ flex: 1 }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '0.85rem',
                            marginBottom: '0.5rem'
                        }}>
                            <span style={{ color: 'var(--color-text-muted)' }}>
                                {skillData.completed_steps} of {skillData.total_steps} completed
                            </span>
                            <span style={{ 
                                color: isSkillComplete ? 'var(--color-success)' : 'var(--color-primary)',
                                fontWeight: 600
                            }}>
                                {skillData.progress_percentage}%
                            </span>
                        </div>
                        <div style={{
                            height: '8px',
                            background: 'rgba(255,255,255,0.1)',
                            borderRadius: '4px',
                            overflow: 'hidden'
                        }}>
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${skillData.progress_percentage}%` }}
                                transition={{ duration: 0.5, ease: 'easeOut' }}
                                style={{
                                    height: '100%',
                                    background: isSkillComplete
                                        ? 'linear-gradient(90deg, #10b981 0%, #34d399 100%)'
                                        : 'linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%)',
                                    borderRadius: '4px'
                                }}
                            />
                        </div>
                    </div>
                    <motion.div
                        animate={{ rotate: expanded ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        {expanded ? <ChevronUp size={24} color="var(--color-text-muted)" /> : <ChevronDown size={24} color="var(--color-text-muted)" />}
                    </motion.div>
                </div>
            </div>

            {/* Expanded Content */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        style={{ overflow: 'hidden' }}
                    >
                        <div style={{ padding: '0 1.5rem 1.5rem 1.5rem' }}>
                            {/* Milestones */}
                            <div style={{ 
                                display: 'grid', 
                                gap: '1rem',
                                marginTop: '1rem'
                            }}>
                                {skillData.milestones?.map((step, idx) => (
                                    <MilestoneCard 
                                        key={idx}
                                        step={step}
                                        stepIndex={idx}
                                        onToggle={(completed) => handleToggleComplete(idx, completed)}
                                    />
                                ))}
                            </div>

                            {/* YouTube Videos */}
                            {skillData.youtube_videos?.length > 0 && (
                                <div style={{ marginTop: '1.5rem' }}>
                                    <h4 style={{ 
                                        fontSize: '0.9rem', 
                                        color: 'var(--color-text-muted)',
                                        marginBottom: '0.75rem',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem'
                                    }}>
                                        <Play size={14} color="#ef4444" />
                                        Recommended Videos
                                    </h4>
                                    <div style={{ display: 'grid', gap: '0.75rem' }}>
                                        {skillData.youtube_videos.slice(0, 3).map((video, idx) => (
                                            <VideoCard key={idx} video={video} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Completion Celebration */}
            <AnimatePresence>
                {showMotivation && isSkillComplete && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        style={{
                            padding: '1.5rem',
                            background: 'linear-gradient(135deg, rgba(16,185,129,0.15) 0%, rgba(16,185,129,0.05) 100%)',
                            borderTop: '1px solid rgba(16,185,129,0.2)',
                            textAlign: 'center'
                        }}
                    >
                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎉</div>
                        <p style={{ 
                            color: 'var(--color-success)', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            margin: 0
                        }}>
                            {getRandomMotivation()}
                        </p>
                        <p style={{ 
                            color: 'var(--color-text-muted)',
                            fontSize: '0.85rem',
                            marginTop: '0.5rem'
                        }}>
                            +{skillData.total_steps * 10 + 50} XP earned!
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

const MilestoneCard = ({ step, stepIndex, onToggle }) => {
    const isCompleted = step.completed;
    const estimatedTime = (step.tasks?.length || 3) * 30;

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: stepIndex * 0.05 }}
            style={{
                display: 'flex',
                gap: '1rem',
                padding: '1rem',
                background: isCompleted 
                    ? 'rgba(16,185,129,0.05)' 
                    : 'rgba(255,255,255,0.02)',
                borderRadius: '12px',
                border: `1px solid ${isCompleted ? 'rgba(16,185,129,0.2)' : 'var(--color-border)'}`,
                transition: 'all 0.2s ease'
            }}
        >
            {/* Checkbox */}
            <motion.button
                onClick={() => onToggle(!isCompleted)}
                style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '8px',
                    border: `2px solid ${isCompleted ? 'var(--color-success)' : 'var(--color-border)'}`,
                    background: isCompleted ? 'var(--color-success)' : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    flexShrink: 0,
                    transition: 'all 0.2s ease'
                }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
            >
                {isCompleted && <CheckCircle2 size={18} color="white" />}
                {!isCompleted && <Circle size={18} color="var(--color-border)" />}
            </motion.button>

            <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{
                        fontSize: '0.7rem',
                        fontFamily: 'monospace',
                        color: 'var(--color-text-muted)',
                        background: 'rgba(139, 92, 246, 0.1)',
                        padding: '0.15rem 0.4rem',
                        borderRadius: '4px'
                    }}>
                        Days {step.day_from}-{step.day_to}
                    </span>
                    <span style={{
                        fontSize: '0.7rem',
                        color: 'var(--color-text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                    }}>
                        <Clock size={10} /> ~{estimatedTime}min
                    </span>
                </div>
                
                <h4 style={{ 
                    fontSize: '1rem', 
                    fontWeight: 600,
                    color: isCompleted ? 'var(--color-success)' : 'var(--color-text-main)',
                    margin: '0 0 0.5rem 0',
                    textDecoration: isCompleted ? 'line-through' : 'none'
                }}>
                    {step.title}
                </h4>

                {/* Tasks */}
                <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                    {step.tasks?.slice(0, 3).map((task, taskIdx) => (
                        <li key={taskIdx} style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '0.5rem',
                            fontSize: '0.85rem',
                            color: isCompleted ? 'var(--color-success)' : 'var(--color-text-muted)',
                            marginBottom: '0.25rem'
                        }}>
                            <span style={{
                                width: '6px',
                                height: '6px',
                                borderRadius: '50%',
                                background: isCompleted ? 'var(--color-success)' : 'var(--color-primary)',
                                marginTop: '0.5rem',
                                flexShrink: 0,
                                opacity: isCompleted ? 1 : 0.6
                            }} />
                            <span>{task}</span>
                        </li>
                    ))}
                    {step.tasks?.length > 3 && (
                        <li style={{
                            fontSize: '0.8rem',
                            color: 'var(--color-text-muted)',
                            fontStyle: 'italic'
                        }}>
                            +{step.tasks.length - 3} more tasks...
                        </li>
                    )}
                </ul>

                {/* Project Badge */}
                {step.project && (
                    <div style={{
                        marginTop: '0.75rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        padding: '0.25rem 0.6rem',
                        background: 'rgba(16,185,129,0.1)',
                        border: '1px solid rgba(16,185,129,0.2)',
                        borderRadius: '999px',
                        fontSize: '0.75rem',
                        color: 'var(--color-success)',
                        fontWeight: 500
                    }}>
                        <Star size={12} /> Includes Project
                    </div>
                )}
            </div>
        </motion.div>
    );
};

const VideoCard = ({ video }) => {
    const videoId = video.url?.split('v=')[1]?.split('&')[0] || video.video_id;
    const thumbnail = video.thumbnail || (videoId ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg` : null);

    return (
        <a
            href={video.url || `https://youtube.com/watch?v=${videoId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem',
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--color-border)',
                borderRadius: '10px',
                textDecoration: 'none',
                transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                e.currentTarget.style.borderColor = 'rgba(255,0,0,0.3)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                e.currentTarget.style.borderColor = 'var(--color-border)';
            }}
        >
            {thumbnail && (
                <img 
                    src={thumbnail} 
                    alt={video.title}
                    style={{
                        width: '80px',
                        height: '45px',
                        objectFit: 'cover',
                        borderRadius: '6px'
                    }}
                />
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    color: 'var(--color-text-main)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                }}>
                    {video.title}
                </div>
                {video.channel && (
                    <div style={{
                        fontSize: '0.75rem',
                        color: 'var(--color-text-muted)'
                    }}>
                        {video.channel}
                    </div>
                )}
            </div>
            <ExternalLink size={14} color="var(--color-text-muted)" />
        </a>
    );
};

export default EnhancedLearningCard;
