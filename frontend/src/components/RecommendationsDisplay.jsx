import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, BookOpen, Gift, Download, ExternalLink, PlayCircle, Sparkles } from 'lucide-react';
import api from '../services/api';

const RecommendationsDisplay = ({ results }) => {
    if (!results) return null;

    const { missing_skills, recommended_projects, starter_projects, ai_projects } = results;
    const hasMissing = missing_skills && missing_skills.length > 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="results-container"
        >
            {/* Status Banner */}
            <div
                className="glass-panel"
                style={{
                    padding: '1.5rem',
                    marginBottom: '1.5rem',
                    borderLeft: `4px solid ${hasMissing ? 'var(--color-warning)' : 'var(--color-success)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem'
                }}
            >
                {hasMissing ? (
                    <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '0.75rem', borderRadius: '50%' }}>
                        <AlertTriangle size={32} color="var(--color-warning)" />
                    </div>
                ) : (
                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.75rem', borderRadius: '50%' }}>
                        <CheckCircle size={32} color="var(--color-success)" />
                    </div>
                )}
                <div>
                    <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>
                        {hasMissing ? 'Skill Gaps Identified' : 'Perfect Match!'}
                    </h2>
                    <p>
                        {hasMissing
                            ? `We found ${missing_skills.length} skills to improve for this role.`
                            : 'You have all the required skills for this role!'}
                    </p>
                </div>
            </div>

            {/* Missing Skills & Projects Grid */}
            {hasMissing && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>

                    {/* Missing Skills List */}
                    <div className="glass-panel" style={{ padding: '1.5rem' }}>
                        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                            <BookOpen size={20} color="var(--color-primary)" />
                            Skills to Learn
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {missing_skills.map((skill, idx) => (
                                <div key={idx} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    padding: '0.75rem 1rem',
                                    borderRadius: '0.5rem',
                                    border: '1px solid var(--color-border)'
                                }}>
                                    <span style={{ fontWeight: 500 }}>{skill}</span>
                                    {starter_projects && starter_projects.find(p => p.includes(skill.replace(' ', '_'))) && (
                                        <a
                                            href={api.getStarterProjectUrl(skill)}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn btn-primary"
                                            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '0.25rem' }}
                                        >
                                            <Download size={14} /> Starter Code
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* AI Project Ideas */}
                    <div className="glass-panel" style={{ padding: '1.5rem' }}>
                        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                            <Gift size={20} color="var(--color-secondary)" />
                            Curated Projects
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {recommended_projects && recommended_projects.map((proj, idx) => (
                                <div key={idx} style={{
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    padding: '1rem',
                                    borderRadius: '0.5rem',
                                    border: '1px solid var(--color-border)'
                                }}>
                                    <h4 style={{ fontSize: '1rem', color: 'var(--color-secondary)', marginBottom: '0.5rem' }}>
                                        {proj.title}
                                    </h4>
                                    <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>{proj.description}</p>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                        <span>Skill: {proj.skill}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            )}

            {/* AI Generated Advanced Concepts */}
            {ai_projects && ai_projects.length > 0 && (
                <div className="glass-panel" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                        <Sparkles size={20} color="#8b5cf6" />
                        AI Recommended Projects
                    </h3>
                    <ul style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {ai_projects.map((idea, idx) => (
                            <li key={idx} style={{ color: 'var(--color-text-muted)' }}>
                                <span style={{ color: 'var(--color-text-main)' }}>{idea}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </motion.div>
    );
};

export default RecommendationsDisplay;
