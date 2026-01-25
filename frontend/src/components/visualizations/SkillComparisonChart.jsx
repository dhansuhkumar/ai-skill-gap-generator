import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { motion } from 'framer-motion';

/**
 * SkillComparisonChart - Interactive radar chart comparing current vs required proficiency
 * 
 * Props:
 * - skillData: Array of { name, current_proficiency, required_proficiency, gap, source }
 * - averageCurrent: Overall average current proficiency
 * - averageRequired: Overall average required proficiency
 */
const SkillComparisonChart = ({ skillData, averageCurrent, averageRequired }) => {
    if (!skillData || skillData.length === 0) {
        return (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                <p style={{ color: 'var(--color-text-muted)' }}>No skill data available for comparison</p>
            </div>
        );
    }

    // Transform data for Recharts
    const chartData = skillData.map(skill => ({
        skill: skill.name,
        Current: skill.current_proficiency,
        Required: skill.required_proficiency,
        gap: skill.gap,
        source: skill.source
    }));

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="glass-panel" style={{
                    padding: '1rem',
                    minWidth: '200px',
                    background: 'rgba(23, 25, 35, 0.95)',
                    border: '1px solid var(--color-border)'
                }}>
                    <h4 style={{ marginBottom: '0.5rem', color: 'var(--color-primary)' }}>{data.skill}</h4>
                    <div style={{ fontSize: '0.9rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <span style={{ color: '#667eea' }}>Current:</span>
                            <strong>{data.Current}%</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <span style={{ color: '#f093fb' }}>Required:</span>
                            <strong>{data.Required}%</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--color-border)' }}>
                            <span style={{ color: data.gap > 0 ? 'var(--color-error)' : 'var(--color-success)' }}>
                                Gap:
                            </span>
                            <strong style={{ color: data.gap > 0 ? 'var(--color-error)' : 'var(--color-success)' }}>
                                {data.gap > 0 ? `+${data.gap}%` : 'None'}
                            </strong>
                        </div>
                        {data.source && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                                Source: {data.source === 'github' ? 'GitHub Analysis' : 'Manual'}
                            </div>
                        )}
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel"
            style={{ padding: '2rem' }}
        >
            {/* Header */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Skill Proficiency Comparison</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    <div style={{
                        padding: '1rem',
                        background: 'rgba(102, 126, 234, 0.1)',
                        borderRadius: '8px',
                        border: '1px solid rgba(102, 126, 234, 0.3)'
                    }}>
                        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                            Avg. Current
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#667eea' }}>
                            {averageCurrent}%
                        </div>
                    </div>
                    <div style={{
                        padding: '1rem',
                        background: 'rgba(240, 147, 251, 0.1)',
                        borderRadius: '8px',
                        border: '1px solid rgba(240, 147, 251, 0.3)'
                    }}>
                        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                            Avg. Required
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f093fb' }}>
                            {averageRequired}%
                        </div>
                    </div>
                    <div style={{
                        padding: '1rem',
                        background: `rgba(${averageRequired - averageCurrent > 0 ? '239, 68, 68' : '16, 185, 129'}, 0.1)`,
                        borderRadius: '8px',
                        border: `1px solid rgba(${averageRequired - averageCurrent > 0 ? '239, 68, 68' : '16, 185, 129'}, 0.3)`
                    }}>
                        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                            Overall Gap
                        </div>
                        <div style={{
                            fontSize: '2rem',
                            fontWeight: 'bold',
                            color: averageRequired - averageCurrent > 0 ? 'var(--color-error)' : 'var(--color-success)'
                        }}>
                            {averageRequired - averageCurrent > 0 ? '+' : ''}{(averageRequired - averageCurrent).toFixed(1)}%
                        </div>
                    </div>
                </div>
            </div>

            {/* Radar Chart */}
            <div style={{ width: '100%', height: '500px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={chartData}>
                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                        <PolarAngleAxis
                            dataKey="skill"
                            tick={{ fill: 'var(--color-text)', fontSize: 12 }}
                            stroke="rgba(255,255,255,0.2)"
                        />
                        <PolarRadiusAxis
                            angle={90}
                            domain={[0, 100]}
                            tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
                            stroke="rgba(255,255,255,0.2)"
                        />
                        <Radar
                            name="Current Proficiency"
                            dataKey="Current"
                            stroke="#667eea"
                            fill="#667eea"
                            fillOpacity={0.3}
                            strokeWidth={2}
                        />
                        <Radar
                            name="Required Proficiency"
                            dataKey="Required"
                            stroke="#f093fb"
                            fill="#f093fb"
                            fillOpacity={0.3}
                            strokeWidth={2}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend
                            wrapperStyle={{ paddingTop: '20px' }}
                            iconType="circle"
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>

            {/* Legend Info */}
            <div style={{
                marginTop: '1.5rem',
                padding: '1rem',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '8px',
                fontSize: '0.85rem',
                color: 'var(--color-text-muted)'
            }}>
                <strong>How to read this chart:</strong> The blue area shows your current skill proficiency (from GitHub analysis or manual input).
                The pink area shows the required proficiency for your target role. Larger gaps indicate skills to prioritize in your learning path.
            </div>
        </motion.div>
    );
};

export default SkillComparisonChart;
