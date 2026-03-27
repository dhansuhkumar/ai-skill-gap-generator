import React, { useState } from 'react';
import { CheckCircle2, Circle, ArrowRight, ArrowLeft, ListChecks, CheckCheck, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const StepMissingSkills = ({ missingSkills, matchData, onNext, onBack }) => {
    const [selected, setSelected] = useState([]);

    const toggleSkill = (skill) => {
        setSelected(prev => prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]);
    };

    const selectAll = () => setSelected([...missingSkills]);
    const clearAll = () => setSelected([]);

    const handleContinue = () => {
        if (selected.length === 0) return;
        onNext(selected);
    };

    const matchPct = matchData?.match_score ?? 0;
    const matchColor = matchPct >= 70 ? 'var(--color-success)' : matchPct >= 40 ? '#F59E0B' : '#EF4444';

    return (
        <motion.div
            key="step3"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel"
            style={{ maxWidth: '760px', margin: '0 auto', padding: '2.5rem 3rem' }}
        >
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
                <button onClick={onBack} className="back-btn">← Back</button>
                <span className="section-label"><ListChecks size={11} /> Step 3 of 5</span>
            </div>

            <div style={{ marginBottom: '1.75rem' }}>
                <h2 style={{ marginBottom: '0.5rem' }}>Skills to learn</h2>
                <p style={{ fontSize: '0.9rem' }}>Select the skills you want your learning path to cover.</p>
            </div>

            {/* Match score card */}
            {matchData && (
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: '0.875rem',
                    marginBottom: '2rem',
                }}>
                    {[
                        { value: `${matchPct}%`, label: 'Role Match', color: matchColor },
                        { value: matchData.user_skills_count, label: 'Skills You Have', color: 'var(--color-primary-light)' },
                        { value: matchData.required_skills_count, label: 'Skills Required', color: 'var(--color-text-muted)' },
                    ].map(stat => (
                        <div className="stat-card" key={stat.label}>
                            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: stat.color, lineHeight: 1 }}>{stat.value}</div>
                            <div className="stat-label" style={{ marginTop: '0.375rem' }}>{stat.label}</div>
                        </div>
                    ))}
                </div>
            )}

            {missingSkills.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                    <CheckCircle2 size={52} color="var(--color-success)" style={{ margin: '0 auto 1rem', display: 'block' }} />
                    <h3 style={{ marginBottom: '0.75rem' }}>You're a perfect match!</h3>
                    <p style={{ marginBottom: '2rem' }}>You already have the core skills required for this role.</p>
                    <button onClick={() => onNext([])} className="btn btn-primary">
                        Continue to Projects <ArrowRight size={16} />
                    </button>
                </div>
            ) : (
                <>
                    {/* Select / clear */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-dim)' }}>
                            {selected.length} of {missingSkills.length} selected
                        </p>
                        <div style={{ display: 'flex', gap: '0.875rem' }}>
                            <button onClick={selectAll} style={{ background: 'none', border: 'none', color: 'var(--color-primary-light)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                <CheckCheck size={13} /> Select all
                            </button>
                            <button onClick={clearAll} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                <X size={13} /> Clear
                            </button>
                        </div>
                    </div>

                    {/* Skills grid */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))',
                        gap: '0.75rem',
                        marginBottom: '2.5rem'
                    }}>
                        {missingSkills.map(skill => {
                            const isSelected = selected.includes(skill);
                            return (
                                <motion.div
                                    key={skill}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.97 }}
                                    onClick={() => toggleSkill(skill)}
                                    style={{
                                        padding: '0.875rem 1rem',
                                        borderRadius: 'var(--radius-lg)',
                                        background: isSelected ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.03)',
                                        border: isSelected ? '1px solid rgba(99,102,241,0.5)' : '1px solid var(--color-border)',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.75rem',
                                        transition: 'all 0.18s',
                                        boxShadow: isSelected ? '0 0 10px rgba(99,102,241,0.12)' : 'none'
                                    }}
                                >
                                    {isSelected
                                        ? <CheckCircle2 size={18} color="var(--color-primary-light)" />
                                        : <Circle size={18} color="var(--color-text-dim)" />
                                    }
                                    <span style={{ fontWeight: 500, fontSize: '0.9rem', color: isSelected ? 'var(--color-text)' : 'var(--color-text-muted)' }}>
                                        {skill}
                                    </span>
                                </motion.div>
                            );
                        })}
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <button onClick={onBack} className="btn btn-secondary">
                            <ArrowLeft size={16} /> Back
                        </button>
                        <button
                            onClick={handleContinue}
                            className="btn btn-primary"
                            disabled={selected.length === 0}
                            style={{ minWidth: '160px' }}
                        >
                            Next Step ({selected.length}) <ArrowRight size={16} />
                        </button>
                    </div>
                </>
            )}
        </motion.div>
    );
};

export default StepMissingSkills;
