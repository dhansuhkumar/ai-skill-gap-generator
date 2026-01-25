import React from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';
import { motion } from 'framer-motion';

const SkillRadar = ({ data, title = "GitHub Language Proficiency" }) => {
    if (!data || data.length === 0) {
        return null;
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="glass-panel"
            style={{
                padding: '2rem',
                marginTop: '2rem',
                background: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
            }}
        >
            <h3 style={{
                marginBottom: '1.5rem',
                textAlign: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.5rem',
                fontWeight: '600'
            }}>
                {title}
            </h3>

            <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={data}>
                    <PolarGrid
                        stroke="rgba(255, 255, 255, 0.2)"
                        strokeWidth={1}
                    />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: 'var(--color-text)', fontSize: 12 }}
                        stroke="rgba(255, 255, 255, 0.3)"
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
                        stroke="rgba(255, 255, 255, 0.2)"
                    />
                    <Radar
                        name="Proficiency"
                        dataKey="A"
                        stroke="#667eea"
                        fill="#667eea"
                        fillOpacity={0.6}
                        strokeWidth={2}
                    />
                    <Tooltip
                        contentStyle={{
                            background: 'rgba(0, 0, 0, 0.8)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '8px',
                            padding: '8px 12px',
                            color: '#fff'
                        }}
                        formatter={(value) => [`${value}/100`, 'Score']}
                    />
                </RadarChart>
            </ResponsiveContainer>

            <div style={{
                marginTop: '1rem',
                textAlign: 'center',
                fontSize: '0.85rem',
                color: 'var(--color-text-muted)'
            }}>
                Based on your GitHub repository analysis
            </div>
        </motion.div>
    );
};

export default SkillRadar;
