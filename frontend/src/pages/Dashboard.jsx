import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import ResumeUpload from '../components/ResumeUpload';
import SkillInput from '../components/SkillInput';
import ProviderSelector from '../components/ProviderSelector';
import RecommendationsDisplay from '../components/RecommendationsDisplay';
import { motion } from 'framer-motion';
import { Search, Loader2 } from 'lucide-react';
import api from '../services/api';

const Dashboard = () => {
    const [role, setRole] = useState('Software Engineer');
    const [skills, setSkills] = useState([]);
    const [provider, setProvider] = useState('auto');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const handleAnalyze = async () => {
        if (!role.trim()) {
            setError('Please enter a target role.');
            return;
        }
        if (skills.length === 0) {
            setError('Please add at least one skill.');
            return;
        }

        setLoading(true);
        setError('');
        setResults(null);

        try {
            const response = await api.recommend(role, skills, provider, true);
            setResults(response.data);
            // Smooth scroll to results
            setTimeout(() => {
                document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        } catch (err) {
            setError('Analysis failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Navbar />
            <div className="container" style={{ paddingTop: 'calc(var(--header-height) + 2rem)', paddingBottom: '4rem' }}>

                <header style={{ marginBottom: '3rem', textAlign: 'center' }}>
                    <motion.h1
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{ marginBottom: '1rem', background: 'linear-gradient(to right, white, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
                    >
                        Bridge Your Skill Gap
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        style={{ fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto' }}
                    >
                        Identify missing skills, get AI-tailored project ideas, and accelerate your career growth with personalized learning paths.
                    </motion.p>
                </header>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>

                    {/* Left Column: Inputs */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        <div className="glass-panel" style={{ padding: '1.5rem' }}>
                            <label htmlFor="role" style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Target Role</label>
                            <input
                                id="role"
                                type="text"
                                className="input-field"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                placeholder="e.g. Full Stack Developer, Data Scientist"
                                style={{ fontSize: '1.1rem', padding: '1rem' }}
                            />
                        </div>

                        <ResumeUpload onSkillsExtracted={(newSkills) => setSkills(prev => [...new Set([...prev, ...newSkills])])} />

                        <ProviderSelector selected={provider} onSelect={setProvider} />
                    </div>

                    {/* Right Column: Skills & Action */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        <SkillInput skills={skills} onSkillsChange={setSkills} />

                        <button
                            onClick={handleAnalyze}
                            className="btn btn-primary"
                            style={{ padding: '1rem', fontSize: '1.1rem', justifyContent: 'center' }}
                            disabled={loading}
                        >
                            {loading ? <Loader2 className="animate-spin" /> : <Search />}
                            {loading ? 'Analyzing Profile...' : 'Analyze Skill Gap'}
                        </button>

                        {error && (
                            <div style={{ color: 'var(--color-error)', textAlign: 'center', background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '0.5rem' }}>
                                {error}
                            </div>
                        )}
                    </div>
                </div>

                {/* Results Section */}
                <div id="results-section">
                    {results && <RecommendationsDisplay results={results} />}
                </div>
            </div>
        </>
    );
};

export default Dashboard;
