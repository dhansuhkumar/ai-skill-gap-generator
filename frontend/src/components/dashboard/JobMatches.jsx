import React from 'react';
import { motion } from 'framer-motion';
import { Briefcase, MapPin, Building2, ExternalLink } from 'lucide-react';
import CircularProgress from '../ui/CircularProgress';

const JobMatches = ({ jobs, userSkills }) => {
    if (!jobs || jobs.length === 0) {
        return (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                <Briefcase size={48} style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }} />
                <h3 style={{ color: 'var(--color-text-main)', marginBottom: '0.5rem' }}>No Job Matches Found</h3>
                <p style={{ color: 'var(--color-text-muted)' }}>Try selecting a different role or adding more skills.</p>
            </div>
        );
    }

    const getSuccessColor = (rate) => {
        if (rate >= 70) return 'var(--color-success)';
        if (rate >= 40) return 'var(--color-warning)';
        return 'var(--color-error)';
    };

    const getSuccessLabel = (rate) => {
        if (rate >= 70) return 'Strong Match';
        if (rate >= 40) return 'Partial Match';
        return 'Low Match';
    };

    return (
        <div style={{ display: 'grid', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <Briefcase size={24} style={{ color: 'var(--color-primary)' }} />
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text-main)' }}>
                    Job Matches ({jobs.length})
                </h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1rem' }}>
                {jobs.map((job, idx) => (
                    <motion.div
                        key={idx}
                        className="glass-panel"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        style={{
                            padding: '1.25rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '1rem',
                            borderLeft: `3px solid ${getSuccessColor(job.success_rate)}`
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div style={{ flex: 1 }}>
                                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
                                    {job.job_title || 'Unknown Role'}
                                </h4>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                                    {job.company && (
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                            <Building2 size={14} /> {job.company}
                                        </span>
                                    )}
                                    {job.location && (
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                            <MapPin size={14} /> {job.location}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <CircularProgress
                                percentage={job.success_rate}
                                size={56}
                                strokeWidth={4}
                                color={getSuccessColor(job.success_rate)}
                            />
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                padding: '0.2rem 0.6rem',
                                borderRadius: '999px',
                                background: `${getSuccessColor(job.success_rate)}20`,
                                color: getSuccessColor(job.success_rate)
                            }}>
                                {getSuccessLabel(job.success_rate)}
                            </span>
                            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                {job.matched_skills_count}/{job.total_required} skills matched
                            </span>
                        </div>

                        {job.required_skills && job.required_skills.length > 0 && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                                {job.required_skills.slice(0, 6).map((skill, sIdx) => {
                                    const skillLower = skill.toLowerCase().strip ? skill.toLowerCase() : skill.toLowerCase();
                                    const userSkillsLower = userSkills ? userSkills.map(s => typeof s === 'string' ? s.toLowerCase() : (s.name || '').toLowerCase()) : [];
                                    const isMatched = userSkillsLower.some(us => us.includes(skillLower) || skillLower.includes(us));
                                    return (
                                        <span key={sIdx} style={{
                                            fontSize: '0.7rem',
                                            padding: '0.15rem 0.5rem',
                                            borderRadius: '4px',
                                            background: isMatched ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                                            color: isMatched ? 'var(--color-success)' : 'var(--color-text-muted)',
                                            border: `1px solid ${isMatched ? 'rgba(16,185,129,0.3)' : 'var(--color-border)'}`
                                        }}>
                                            {skill}
                                        </span>
                                    );
                                })}
                                {job.required_skills.length > 6 && (
                                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                                        +{job.required_skills.length - 6} more
                                    </span>
                                )}
                            </div>
                        )}

                        {job.job_link && (
                            <a
                                href={job.job_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '0.5rem',
                                    padding: '0.6rem 1.2rem',
                                    borderRadius: '8px',
                                    background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                                    color: 'white',
                                    textDecoration: 'none',
                                    fontWeight: 600,
                                    fontSize: '0.85rem',
                                    transition: 'all 0.2s',
                                    alignSelf: 'flex-start'
                                }}
                            >
                                Apply <ExternalLink size={14} />
                            </a>
                        )}
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default JobMatches;
