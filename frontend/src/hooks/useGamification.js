import { useState, useEffect, useCallback } from 'react';

const XP_PER_TASK = 10;
const XP_PER_SKILL = 50;
const XP_PER_LEVEL = 100;

const INITIAL_ACHIEVEMENTS = [
    { id: 'first_step', name: 'First Step', description: 'Complete your first task', icon: '🚀', xp: 25, unlocked: false },
    { id: 'on_fire', name: 'On Fire', description: 'Complete 5 tasks in a row', icon: '🔥', xp: 50, unlocked: false },
    { id: 'skill_starter', name: 'Skill Starter', description: 'Complete your first skill path', icon: '⭐', xp: 75, unlocked: false },
    { id: 'consistent', name: 'Consistent', description: '3 day learning streak', icon: '📈', xp: 30, unlocked: false },
    { id: 'dedicated', name: 'Dedicated', description: '7 day learning streak', icon: '💪', xp: 100, unlocked: false },
    { id: 'week_warrior', name: 'Week Warrior', description: 'Complete all tasks in a week', icon: '⚔️', xp: 150, unlocked: false },
    { id: 'skill_master', name: 'Skill Master', description: 'Complete 3 skill paths', icon: '👑', xp: 200, unlocked: false },
    { id: 'halfway', name: 'Halfway There', description: 'Reach 50% completion', icon: '🎯', xp: 100, unlocked: false },
];

export function useGamification(initialProgress = { completed: 0, total: 0 }) {
    const [xp, setXp] = useState(() => {
        const saved = localStorage.getItem('learning_xp');
        return saved ? parseInt(saved, 10) : 0;
    });
    
    const [level, setLevel] = useState(() => Math.floor(xp / XP_PER_LEVEL) + 1);
    
    const [achievements, setAchievements] = useState(() => {
        const saved = localStorage.getItem('learning_achievements');
        if (saved) {
            const savedIds = JSON.parse(saved);
            return INITIAL_ACHIEVEMENTS.map(a => ({
                ...a,
                unlocked: savedIds.includes(a.id)
            }));
        }
        return INITIAL_ACHIEVEMENTS;
    });
    
    const [streak, setStreak] = useState(() => {
        const saved = localStorage.getItem('learning_streak');
        return saved ? parseInt(saved, 10) : 0;
    });
    
    const [lastCompletionDate, setLastCompletionDate] = useState(() => {
        return localStorage.getItem('last_completion_date') || null;
    });
    
    const [consecutiveTasks, setConsecutiveTasks] = useState(0);
    const [skillsCompleted, setSkillsCompleted] = useState(() => {
        const saved = localStorage.getItem('skills_completed_count');
        return saved ? parseInt(saved, 10) : 0;
    });
    
    const [newAchievement, setNewAchievement] = useState(null);
    const [showLevelUp, setShowLevelUp] = useState(false);

    // Save to localStorage
    useEffect(() => {
        localStorage.setItem('learning_xp', xp.toString());
        setLevel(Math.floor(xp / XP_PER_LEVEL) + 1);
    }, [xp]);
    
    useEffect(() => {
        const unlockedIds = achievements.filter(a => a.unlocked).map(a => a.id);
        localStorage.setItem('learning_achievements', JSON.stringify(unlockedIds));
    }, [achievements]);
    
    useEffect(() => {
        localStorage.setItem('learning_streak', streak.toString());
    }, [streak]);
    
    useEffect(() => {
        localStorage.setItem('skills_completed_count', skillsCompleted.toString());
    }, [skillsCompleted]);

    // Calculate progress percentage
    const progressPercentage = initialProgress.total > 0 
        ? Math.round((initialProgress.completed / initialProgress.total) * 100) 
        : 0;
    
    const xpInCurrentLevel = xp % XP_PER_LEVEL;
    const xpToNextLevel = XP_PER_LEVEL;

    // Check achievements
    const checkAchievements = useCallback((completedCount, totalCount) => {
        setAchievements(prev => {
            const newAchievements = [...prev];
            let changed = false;
            
            // First Step
            if (completedCount >= 1 && !newAchievements[0].unlocked) {
                newAchievements[0].unlocked = true;
                changed = true;
            }
            
            // On Fire (5 consecutive)
            if (consecutiveTasks >= 5 && !newAchievements[1].unlocked) {
                newAchievements[1].unlocked = true;
                changed = true;
            }
            
            // Consistent (3 day streak)
            if (streak >= 3 && !newAchievements[3].unlocked) {
                newAchievements[3].unlocked = true;
                changed = true;
            }
            
            // Dedicated (7 day streak)
            if (streak >= 7 && !newAchievements[4].unlocked) {
                newAchievements[4].unlocked = true;
                changed = true;
            }
            
            // Halfway
            if (totalCount > 0 && (completedCount / totalCount) >= 0.5 && !newAchievements[7].unlocked) {
                newAchievements[7].unlocked = true;
                changed = true;
            }
            
            if (changed) {
                const justUnlocked = newAchievements.filter((a, i) => a.unlocked && !prev[i].unlocked);
                if (justUnlocked.length > 0) {
                    setNewAchievement(justUnlocked[0]);
                    setTimeout(() => setNewAchievement(null), 4000);
                }
            }
            
            return changed ? newAchievements : prev;
        });
    }, [consecutiveTasks, streak]);

    // Handle task completion
    const completeTask = useCallback(() => {
        const newXp = xp + XP_PER_TASK;
        setXp(newXp);
        setConsecutiveTasks(prev => prev + 1);
        
        // Update streak
        const today = new Date().toDateString();
        if (lastCompletionDate !== today) {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            if (lastCompletionDate === yesterday.toDateString()) {
                setStreak(prev => prev + 1);
            } else if (lastCompletionDate !== today) {
                setStreak(1);
            }
            setLastCompletionDate(today);
            localStorage.setItem('last_completion_date', today);
        }
        
        // Check for level up
        const newLevel = Math.floor(newXp / XP_PER_LEVEL) + 1;
        if (newLevel > level) {
            setShowLevelUp(true);
            setTimeout(() => setShowLevelUp(false), 3000);
        }
        
        return XP_PER_TASK;
    }, [xp, level, lastCompletionDate]);

    // Handle skill completion
    const completeSkill = useCallback(() => {
        const newXp = xp + XP_PER_SKILL;
        setXp(newXp);
        setSkillsCompleted(prev => prev + 1);
        
        setAchievements(prev => {
            const newAchievements = [...prev];
            
            // Skill Starter
            if (!newAchievements[2].unlocked) {
                newAchievements[2].unlocked = true;
                setNewAchievement(newAchievements[2]);
                setTimeout(() => setNewAchievement(null), 4000);
            }
            
            // Skill Master (3 skills)
            if (skillsCompleted + 1 >= 3 && !newAchievements[6].unlocked) {
                newAchievements[6].unlocked = true;
                setNewAchievement(newAchievements[6]);
                setTimeout(() => setNewAchievement(null), 4000);
            }
            
            return newAchievements;
        });
        
        return XP_PER_SKILL;
    }, [xp, skillsCompleted]);

    // Reset progress
    const resetProgress = useCallback(() => {
        setXp(0);
        setLevel(1);
        setStreak(0);
        setConsecutiveTasks(0);
        setSkillsCompleted(0);
        setLastCompletionDate(null);
        localStorage.removeItem('learning_xp');
        localStorage.removeItem('learning_streak');
        localStorage.removeItem('skills_completed_count');
        localStorage.removeItem('last_completion_date');
        localStorage.removeItem('learning_achievements');
        setAchievements(INITIAL_ACHIEVEMENTS);
    }, []);

    return {
        xp,
        level,
        xpInCurrentLevel,
        xpToNextLevel,
        achievements,
        unlockedAchievements: achievements.filter(a => a.unlocked),
        streak,
        consecutiveTasks,
        skillsCompleted,
        progressPercentage,
        newAchievement,
        showLevelUp,
        completeTask,
        completeSkill,
        checkAchievements,
        resetProgress,
    };
}

// Motivational messages
export const MOTIVATIONAL_MESSAGES = [
    "You're making great progress! Keep it up! 🚀",
    "Every expert was once a beginner. You're on your way! 💪",
    "Consistency is key. You're building great habits! 📈",
    "Skills compound just like interest. Keep learning! 📚",
    "The only way to do great work is to love what you do! ❤️",
    "Small steps every day lead to big results! 🌟",
    "You're investing in yourself. That's the best investment! 💎",
    "Learning today, earning tomorrow! 💰",
    "Your future self will thank you for starting today! 🙌",
    "Each task completed brings you closer to your goal! 🎯",
];

export function getRandomMotivation() {
    return MOTIVATIONAL_MESSAGES[Math.floor(Math.random() * MOTIVATIONAL_MESSAGES.length)];
}

// Skill descriptions
export const SKILL_DESCRIPTIONS = {
    'Python': 'One of the most versatile programming languages, used in web development, data science, AI, and automation.',
    'JavaScript': 'The language of the web. Essential for building interactive websites and web applications.',
    'React': 'A powerful library for building user interfaces. Used by Facebook, Instagram, and thousands of companies.',
    'Node.js': 'Run JavaScript on the server. Build fast, scalable network applications.',
    'SQL': 'The standard language for managing relational databases. Essential for any data-related role.',
    'Docker': 'Containerize your applications. Essential for modern deployment and DevOps practices.',
    'AWS': 'Amazon Web Services. The leading cloud platform with vast career opportunities.',
    'Git': 'Version control is essential for any developer. Track changes and collaborate effectively.',
    'TypeScript': 'JavaScript with types. Write safer, more maintainable code.',
    'REST API': 'Design and consume APIs. Connect different systems and services.',
    'Machine Learning': 'The future of technology. Teach computers to learn from data.',
    'Docker': 'Package your applications with their dependencies. Consistent environments everywhere.',
    'Kubernetes': 'Orchestrate containers at scale. Essential for modern cloud infrastructure.',
    'CI/CD': 'Automate your development pipeline. Ship code faster and with confidence.',
};

export function getSkillDescription(skill) {
    return SKILL_DESCRIPTIONS[skill] || `Master ${skill} to advance your career in tech.`;
}

// Time estimates (in minutes)
export const TIME_ESTIMATES = {
    beginner: 30,
    intermediate: 45,
    advanced: 60,
};

export function estimateTaskTime(task) {
    // Simple heuristic based on task content
    const taskLower = task.toLowerCase();
    if (taskLower.includes('build') || taskLower.includes('create') || taskLower.includes('project')) {
        return 90;
    }
    if (taskLower.includes('learn') || taskLower.includes('study')) {
        return 45;
    }
    if (taskLower.includes('practice') || taskLower.includes('exercise')) {
        return 30;
    }
    return 30; // Default
}
