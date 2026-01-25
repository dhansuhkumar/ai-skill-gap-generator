import React from 'react';
import { motion } from 'framer-motion';
import { Code2, BrainCircuit, BarChart3, Sparkles, Zap, Target } from 'lucide-react';

/**
 * FloatingIcons - Animated floating tech icons for Login/Register pages
 * 
 * Creates a futuristic atmosphere with floating, glowing icons
 */
const FloatingIcons = () => {
    const icons = [
        { Icon: Code2, x: '10%', y: '20%', delay: 0, size: 32, color: '#8b5cf6' },
        { Icon: BrainCircuit, x: '85%', y: '15%', delay: 0.5, size: 40, color: '#06b6d4' },
        { Icon: BarChart3, x: '75%', y: '70%', delay: 1, size: 36, color: '#ec4899' },
        { Icon: Sparkles, x: '15%', y: '75%', delay: 1.5, size: 28, color: '#f59e0b' },
        { Icon: Zap, x: '90%', y: '45%', delay: 2, size: 30, color: '#10b981' },
        { Icon: Target, x: '5%', y: '50%', delay: 2.5, size: 34, color: '#8b5cf6' },
    ];

    return (
        <div style={{
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 0,
            overflow: 'hidden',
        }}>
            {icons.map(({ Icon, x, y, delay, size, color }, index) => (
                <motion.div
                    key={index}
                    style={{
                        position: 'absolute',
                        left: x,
                        top: y,
                    }}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{
                        opacity: [0.3, 0.6, 0.3],
                        y: [0, -20, 0],
                        scale: [1, 1.1, 1],
                    }}
                    transition={{
                        duration: 4,
                        delay,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    }}
                >
                    <div style={{
                        padding: '1rem',
                        background: `${color}15`,
                        borderRadius: '50%',
                        border: `1px solid ${color}30`,
                        boxShadow: `0 0 30px ${color}20`,
                    }}>
                        <Icon size={size} color={color} style={{ opacity: 0.8 }} />
                    </div>
                </motion.div>
            ))}
        </div>
    );
};

export default FloatingIcons;
