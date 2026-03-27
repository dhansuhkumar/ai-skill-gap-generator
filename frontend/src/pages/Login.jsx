import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/auth';
import { motion } from 'framer-motion';
import { Loader2, LogIn, BrainCircuit } from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [infoMsg, setInfoMsg] = useState(''); // non-error informational messages
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setInfoMsg('');
        setLoading(true);
        try {
            await authService.login(email, password);
            navigate('/');
        } catch (err) {
            const msg = typeof err === 'string' ? err : (err?.message || 'Login failed.');
            if (msg.toLowerCase().includes('email not confirmed')) {
                setInfoMsg('Your email is not confirmed yet. Please check your inbox and click the confirmation link, then try signing in again.');
            } else {
                setError(msg);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page-bg">
            <motion.div
                initial={{ opacity: 0, y: 32, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: '100%', maxWidth: '460px', position: 'relative', zIndex: 1 }}
            >
                {/* Card */}
                <div className="glass-panel glass-panel-premium" style={{ padding: '2.75rem 2.5rem' }}>

                    {/* Header */}
                    <div style={{ textAlign: 'center', marginBottom: '2.25rem' }}>
                        {/* Logo Icon */}
                        <motion.div
                            style={{
                                display: 'inline-flex',
                                padding: '18px',
                                background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.12))',
                                borderRadius: '50%',
                                marginBottom: '1.5rem',
                                border: '1px solid rgba(99,102,241,0.3)',
                                boxShadow: '0 0 40px rgba(99,102,241,0.25)',
                            }}
                            animate={{ boxShadow: ['0 0 20px rgba(99,102,241,0.2)', '0 0 45px rgba(99,102,241,0.4)', '0 0 20px rgba(99,102,241,0.2)'] }}
                            transition={{ duration: 2.5, repeat: Infinity }}
                        >
                            <BrainCircuit size={38} color="#818CF8" />
                        </motion.div>

                        {/* Tagline badge */}
                        <div style={{ marginBottom: '1rem' }}>
                            <span className="section-label">AI-Powered Career Intelligence</span>
                        </div>

                        <h2 style={{
                            fontSize: '2rem',
                            marginBottom: '0.5rem',
                            background: 'linear-gradient(135deg, #fff 40%, #94A3B8)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                        }}>
                            Welcome back
                        </h2>
                        <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                            Sign in to continue your journey
                        </p>
                    </div>

                    {/* Error */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -8 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="alert alert-error"
                            style={{ marginBottom: '1.25rem' }}
                        >
                            {error}
                        </motion.div>
                    )}

                    {/* Info message (e.g. email not confirmed) */}
                    {infoMsg && (
                        <motion.div
                            initial={{ opacity: 0, y: -8 }}
                            animate={{ opacity: 1, y: 0 }}
                            style={{
                                background: 'rgba(6,182,212,0.1)',
                                border: '1px solid rgba(6,182,212,0.3)',
                                borderRadius: '8px',
                                padding: '0.875rem 1rem',
                                marginBottom: '1.25rem',
                                color: '#22D3EE',
                                fontSize: '0.875rem',
                                lineHeight: 1.6
                            }}
                        >
                            📧 {infoMsg}
                        </motion.div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: '1.125rem' }}>
                            <label htmlFor="email">Email address</label>
                            <input
                                id="email"
                                type="email"
                                className="input-field"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div style={{ marginBottom: '1.625rem' }}>
                            <label htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                className="input-field"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            style={{ width: '100%', padding: '0.875rem', fontSize: '1rem' }}
                            disabled={loading}
                        >
                            {loading
                                ? <><Loader2 size={18} className="animate-spin" /> Signing in...</>
                                : <><LogIn size={18} /> Sign In</>
                            }
                        </button>
                    </form>

                    {/* Footer */}
                    <div style={{ marginTop: '1.875rem', textAlign: 'center' }}>
                        <div className="divider" />
                        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-dim)' }}>
                            Don't have an account?{' '}
                            <Link
                                to="/register"
                                style={{
                                    color: 'var(--color-primary-light)',
                                    fontWeight: 600,
                                    textDecoration: 'none',
                                    transition: 'color 0.15s'
                                }}
                            >
                                Create one free →
                            </Link>
                        </p>
                    </div>
                </div>

                {/* Bottom watermark */}
                <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--color-text-dim)' }}>
                    Powered by Gemini AI · Secure · Private
                </p>
            </motion.div>
        </div>
    );
};

export default Login;
