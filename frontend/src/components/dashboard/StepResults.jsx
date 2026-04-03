import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Briefcase } from 'lucide-react';
import DynamicDashboard from '../visualizations/DynamicDashboard';
import JobMatches from './JobMatches';
import api from '../../services/api';

const StepResults = ({ results, onReset, userSkills, roleAnalysis, githubUsername, jobMatches: parentJobMatches, targetRole, experienceLevel = 'neutral' }) => {
    const [jobMatches, setJobMatches] = useState(parentJobMatches || []);
    const [loadingJobs, setLoadingJobs] = useState(false);
    const [showJobs, setShowJobs] = useState(false);
    const [jobError, setJobError] = useState('');
    const fetchedRef = useRef(false);

    useEffect(() => {
        if (parentJobMatches && parentJobMatches.length > 0) {
            setJobMatches(parentJobMatches);
            setShowJobs(true);
        }
    }, [parentJobMatches]);

    useEffect(() => {
        if (fetchedRef.current) return;
        if (!targetRole || !results) return;

        fetchedRef.current = true;
        fetchJobMatches();
    }, [targetRole, results]);

    const fetchJobMatches = async () => {
        if (!targetRole) {
            setJobError('No target role available');
            return;
        }
        setLoadingJobs(true);
        setShowJobs(true);
        setJobError('');
        try {
            const skillNames = userSkills.map(s => typeof s === 'string' ? s : (s.name || s));
            console.log('Fetching job matches:', { skills: skillNames, role: targetRole, experienceLevel });
            const res = await api.getJobMatches(skillNames, targetRole, experienceLevel);
            console.log('Job matches response:', res.data);
            if (res.data && res.data.jobs) {
                setJobMatches(res.data.jobs);
            }
        } catch (err) {
            const errorMsg = err.response?.data?.error || err.message || 'Unknown error';
            console.error('Failed to fetch job matches:', errorMsg);
            setJobError(errorMsg);
        } finally {
            setLoadingJobs(false);
        }
    };

    return (
        <motion.div
            key="step4"
            initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }}
        >
            <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '1rem' }}>
                <button onClick={onReset} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>← Start Over</button>
            </div>

            <DynamicDashboard
                results={results}
                userSkills={userSkills}
                roleAnalysis={roleAnalysis}
                githubUsername={githubUsername}
            />

            <div style={{ maxWidth: '1200px', margin: '2rem auto 0' }}>
                {jobError && (
                    <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.1)', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.2)', color: 'var(--color-error)', marginBottom: '1rem' }}>
                        <p style={{ margin: 0 }}>Job matches unavailable: {jobError}</p>
                        <button onClick={fetchJobMatches} style={{ marginTop: '0.5rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: 'var(--color-error)', padding: '0.4rem 0.8rem', borderRadius: '6px', cursor: 'pointer' }}>
                            Retry
                        </button>
                    </div>
                )}
                {!showJobs && !jobError ? (
                    <button
                        onClick={fetchJobMatches}
                        disabled={loadingJobs}
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.75rem 1.5rem',
                            borderRadius: '12px',
                            background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                            color: 'white',
                            border: 'none',
                            cursor: loadingJobs ? 'wait' : 'pointer',
                            fontWeight: 600,
                            fontSize: '0.95rem',
                            transition: 'all 0.2s'
                        }}
                    >
                        <Briefcase size={18} />
                        {loadingJobs ? 'Finding Jobs...' : 'Find Matching Jobs'}
                    </button>
                ) : showJobs && jobMatches.length > 0 ? (
                    <JobMatches jobs={jobMatches} userSkills={userSkills} />
                ) : showJobs && jobMatches.length === 0 && !loadingJobs ? (
                    <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                        <Briefcase size={48} style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }} />
                        <h3 style={{ color: 'var(--color-text-main)', marginBottom: '0.5rem' }}>No Job Matches Found</h3>
                        <p style={{ color: 'var(--color-text-muted)' }}>Try selecting a different role or adding more skills.</p>
                    </div>
                ) : null}
            </div>
        </motion.div>
    );
};

export default StepResults;
