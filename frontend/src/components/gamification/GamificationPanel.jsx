import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Zap, Trophy, Flame, Star, Lock, ChevronRight, 
    Award, Target, Clock, TrendingUp
} from 'lucide-react';

const XPProgressBar = ({ xp, xpInCurrentLevel, xpToNextLevel, level, streak }) => {
    const progressPercentage = Math.round((xpInCurrentLevel / xpToNextLevel) * 100);

    return (
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                {/* Level Badge */}
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 4px 20px rgba(139, 92, 246, 0.4)',
                        position: 'relative'
                    }}
                >
                    <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'white', lineHeight: 1 }}>LV</span>
                    <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', lineHeight: 1 }}>{level}</span>
                </motion.div>

                <div style={{ flex: 1 }}>
                    <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        marginBottom: '0.5rem'
                    }}>
                        <span style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>
                            Level {level}
                        </span>
                        <span style={{ 
                            fontSize: '0.85rem', 
                            color: 'var(--color-text-muted)',
                            fontFamily: 'monospace'
                        }}>
                            {xpInCurrentLevel} / {xpToNextLevel} XP
                        </span>
                    </div>
                    
                    {/* XP Bar */}
                    <div style={{
                        height: '10px',
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '5px',
                        overflow: 'hidden',
                        position: 'relative'
                    }}>
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercentage}%` }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                            style={{
                                height: '100%',
                                background: 'linear-gradient(90deg, #8b5cf6 0%, #a78bfa 100%)',
                                borderRadius: '5px',
                                position: 'relative'
                            }}
                        >
                            {/* Shine effect */}
                            <div style={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                right: 0,
                                height: '50%',
                                background: 'linear-gradient(180deg, rgba(255,255,255,0.3) 0%, transparent 100%)',
                                borderRadius: '5px 5px 0 0'
                            }} />
                        </motion.div>
                    </div>
                </div>
            </div>

            {/* Quick Stats */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <StatBadge 
                    icon={<Zap size={14} />} 
                    value={xp} 
                    label="Total XP" 
                    color="#fbbf24"
                />
                <StatBadge 
                    icon={<Flame size={14} />} 
                    value={streak} 
                    label="Day Streak" 
                    color="#f97316"
                />
            </div>
        </div>
    );
};

const StatBadge = ({ icon, value, label, color }) => (
    <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.5rem 0.75rem',
        background: `${color}15`,
        border: `1px solid ${color}30`,
        borderRadius: '8px',
        flex: 1,
        minWidth: '80px'
    }}>
        <span style={{ color }}>{icon}</span>
        <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-main)', lineHeight: 1 }}>
                {value}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                {label}
            </div>
        </div>
    </div>
);

const AchievementsPanel = ({ achievements, unlockedAchievements, progressPercentage }) => {
    const totalAchievements = achievements.length;
    const unlockedCount = unlockedAchievements.length;

    return (
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
            }}>
                <h3 style={{ 
                    fontSize: '1rem', 
                    fontWeight: 600, 
                    color: 'var(--color-text-main)',
                    margin: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                }}>
                    <Trophy size={18} color="#fbbf24" />
                    Achievements
                </h3>
                <span style={{ 
                    fontSize: '0.85rem', 
                    color: 'var(--color-text-muted)'
                }}>
                    {unlockedCount} / {totalAchievements}
                </span>
            </div>

            {/* Progress */}
            <div style={{
                height: '6px',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '3px',
                overflow: 'hidden',
                marginBottom: '1rem'
            }}>
                <div style={{
                    height: '100%',
                    width: `${(unlockedCount / totalAchievements) * 100}%`,
                    background: 'linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%)',
                    borderRadius: '3px'
                }} />
            </div>

            {/* Achievement Grid */}
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(70px, 1fr))',
                gap: '0.75rem'
            }}>
                {achievements.map((achievement) => (
                    <AchievementBadge key={achievement.id} achievement={achievement} />
                ))}
            </div>
        </div>
    );
};

const AchievementBadge = ({ achievement }) => {
    const isUnlocked = achievement.unlocked;

    return (
        <motion.div
            whileHover={{ scale: 1.05 }}
            style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '0.75rem 0.5rem',
                background: isUnlocked 
                    ? 'linear-gradient(135deg, rgba(251,191,36,0.15) 0%, rgba(251,191,36,0.05) 100%)'
                    : 'rgba(255,255,255,0.02)',
                border: `1px solid ${isUnlocked ? 'rgba(251,191,36,0.3)' : 'var(--color-border)'}`,
                borderRadius: '12px',
                cursor: 'pointer',
                position: 'relative',
                opacity: isUnlocked ? 1 : 0.5,
                transition: 'all 0.2s ease'
            }}
        >
            {/* Icon */}
            <div style={{
                fontSize: '1.75rem',
                marginBottom: '0.35rem',
                filter: isUnlocked ? 'none' : 'grayscale(100%)',
                opacity: isUnlocked ? 1 : 0.4
            }}>
                {isUnlocked ? achievement.icon : <Lock size={20} color="var(--color-text-muted)" />}
            </div>

            {/* Name */}
            <span style={{
                fontSize: '0.65rem',
                fontWeight: 600,
                color: isUnlocked ? 'var(--color-text-main)' : 'var(--color-text-muted)',
                textAlign: 'center',
                lineHeight: 1.2
            }}>
                {achievement.name}
            </span>

            {/* XP */}
            {isUnlocked && (
                <span style={{
                    fontSize: '0.6rem',
                    color: '#fbbf24',
                    marginTop: '0.25rem'
                }}>
                    +{achievement.xp} XP
                </span>
            )}

            {/* Tooltip on hover - would need a tooltip library in production */}
        </motion.div>
    );
};

// Level Up Notification
export const LevelUpNotification = ({ level, show }) => (
    <AnimatePresence>
        {show && (
            <motion.div
                initial={{ opacity: 0, scale: 0.5, y: 50 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.5, y: -50 }}
                style={{
                    position: 'fixed',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    zIndex: 9999,
                    background: 'linear-gradient(135deg, rgba(139,92,246,0.95) 0%, rgba(99,102,241,0.95) 100%)',
                    padding: '2rem 3rem',
                    borderRadius: '20px',
                    textAlign: 'center',
                    boxShadow: '0 20px 60px rgba(139,92,246,0.5)',
                    border: '2px solid rgba(255,255,255,0.2)'
                }}
            >
                <motion.div
                    animate={{ 
                        rotate: [0, 10, -10, 0],
                        scale: [1, 1.2, 1]
                    }}
                    transition={{ duration: 0.5, repeat: 2 }}
                    style={{ fontSize: '4rem', marginBottom: '1rem' }}
                >
                    🎉
                </motion.div>
                <h2 style={{ 
                    color: 'white', 
                    fontSize: '2rem', 
                    fontWeight: 800,
                    margin: '0 0 0.5rem 0',
                    textShadow: '0 2px 10px rgba(0,0,0,0.3)'
                }}>
                    LEVEL UP!
                </h2>
                <p style={{ 
                    color: 'rgba(255,255,255,0.9)', 
                    fontSize: '1.25rem',
                    margin: 0
                }}>
                    You reached <span style={{ fontWeight: 800 }}>Level {level}</span>!
                </p>
            </motion.div>
        )}
    </AnimatePresence>
);

// New Achievement Notification
export const AchievementNotification = ({ achievement, show }) => (
    <AnimatePresence>
        {show && achievement && (
            <motion.div
                initial={{ opacity: 0, x: 100, y: 0 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                exit={{ opacity: 0, x: 100 }}
                style={{
                    position: 'fixed',
                    top: '20px',
                    right: '20px',
                    zIndex: 9999,
                    background: 'linear-gradient(135deg, rgba(251,191,36,0.95) 0%, rgba(245,158,11,0.95) 100%)',
                    padding: '1rem 1.5rem',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    boxShadow: '0 10px 40px rgba(251,191,36,0.4)',
                    border: '2px solid rgba(255,255,255,0.3)'
                }}
            >
                <div style={{ fontSize: '2.5rem' }}>{achievement.icon}</div>
                <div>
                    <div style={{ 
                        color: 'white', 
                        fontWeight: 700,
                        fontSize: '0.9rem'
                    }}>
                        Achievement Unlocked!
                    </div>
                    <div style={{ 
                        color: 'rgba(255,255,255,0.9)', 
                        fontSize: '1.1rem',
                        fontWeight: 600
                    }}>
                        {achievement.name}
                    </div>
                </div>
            </motion.div>
        )}
    </AnimatePresence>
);

export { XPProgressBar, AchievementsPanel, AchievementBadge };
