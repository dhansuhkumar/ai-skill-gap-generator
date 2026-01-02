import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, BookOpen, Gift, Download, ExternalLink, PlayCircle, Sparkles, Calendar, Clock, ArrowRight } from 'lucide-react';
import api from '../services/api';

const RecommendationsDisplay = ({ results }) => {
    if (!results) return null;

    // Handle new contract format: results.learning_path.skills
    const learningPathData = results.learning_path || results;
    const learningPaths = learningPathData.skills || learningPathData.learning_paths || {}; // Object: { "Skill": { summary, steps: [] } }
    const projects = learningPathData.projects || results.projects || [];
    const videos = learningPathData.videos || results.videos || [];
    const matchScore = results.matching_score || 0;
    const source = results.source || 'unknown';
    const selectedSkills = Object.keys(learningPaths);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="results-container"
        >
            {/* Score Banner */}
            <div
                className="glass-panel"
                style={{
                    padding: '2rem',
                    marginBottom: '2rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: `linear-gradient(90deg, rgba(139, 92, 246, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)`
                }}
            >
                <div>
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Sparkles color="var(--color-primary)" />
                        Your Personalized Learning Plan
                    </h2>
                    <p style={{ color: 'var(--color-text-muted)' }}>
                        Focusing on: <strong style={{ color: 'white' }}>{selectedSkills.join(', ')}</strong>
                    </p>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>{matchScore}%</div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Initial Match Score</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>Provider: {source}</div>
                </div>
            </div>

            {/* Learning Paths */}
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <BookOpen size={20} color="var(--color-secondary)" /> Learning Roadmap
            </h3>

            <div style={{ display: 'grid', gap: '2rem', marginBottom: '3rem' }}>
                {selectedSkills.map(skill => {
                    const path = learningPaths[skill];
                    return (
                        <motion.div
                            key={skill}
                            className="glass-panel"
                            style={{ padding: '0', overflow: 'hidden' }}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            <div style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--color-border)' }}>
                                <h4 style={{ fontSize: '1.25rem', color: 'var(--color-primary)' }}>{skill}</h4>
                            </div>
                            <div style={{ padding: '1.5rem' }}>
                                <div style={{ display: 'grid', gap: '1.5rem' }}>
                                    {path.steps && path.steps.map((step, idx) => (
                                        <div key={idx} style={{ display: 'flex', gap: '1rem' }}>
                                            <div style={{
                                                display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '60px',
                                                borderRight: '2px solid var(--color-border)', paddingRight: '1rem'
                                            }}>
                                                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Days</span>
                                                <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{step.day_from}-{step.day_to}</span>
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <h5 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>{step.title}</h5>
                                                <ul style={{ paddingLeft: '1.2rem', marginBottom: '0.75rem', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                                                    {step.tasks && step.tasks.map((t, ti) => (
                                                        <li key={ti}>{t}</li>
                                                    ))}
                                                </ul>
                                                {step.project && (
                                                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.5rem 1rem', borderRadius: '0.5rem', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                                                        <Gift size={14} color="var(--color-success)" />
                                                        <span style={{ color: 'var(--color-success)' }}>Micro-Project: {step.project}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Recommended Projects */}
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <RocketIcon /> Portfolio Projects
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
                {projects.map((proj, idx) => (
                    <div key={idx} className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
                        <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--color-secondary)' }}>{proj.title}</h4>
                        <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '1rem', flex: 1 }}>{proj.description}</p>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            {proj.skills && proj.skills.map(s => (
                                <span key={s} style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', padding: '0.2rem 0.6rem', borderRadius: '1rem' }}>{s}</span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Videos (Optional) */}
            {videos && videos.length > 0 && (
                <>
                    <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <PlayCircle size={20} color="#ef4444" /> Recommended Tutorials
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
                        {videos.map((vid, idx) => (
                            <a
                                key={idx}
                                href={vid.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="glass-panel"
                                style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', textDecoration: 'none', color: 'inherit', transition: 'transform 0.2s' }}
                            >
                                <PlayCircle size={24} color="#ef4444" />
                                <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{vid.title}</span>
                                <ExternalLink size={14} style={{ marginLeft: 'auto', opacity: 0.5 }} />
                            </a>
                        ))}
                    </div>
                </>
            )}

        </motion.div>
    );
};

const RocketIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path>
        <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path>
        <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"></path>
        <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"></path>
    </svg>
);

export default RecommendationsDisplay;
