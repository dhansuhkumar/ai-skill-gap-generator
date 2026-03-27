import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/auth';
import { motion } from 'framer-motion';
import { Loader2, UserPlus, Sparkles, Mail, CheckCircle } from 'lucide-react';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [registered, setRegistered] = useState(false); // email confirmation pending
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError("Passwords don't match");
            return;
        }
        if (password.length < 6) {
            setError("Password must be at least 6 characters");
            return;
        }

        setLoading(true);
        try {
            const result = await authService.register(email, password);
            // If Supabase requires email confirmation, session will be null
            if (result?.session?.access_token) {
                // Auto-logged in (email confirmation disabled in Supabase)
                navigate('/');
            } else {
                // Email confirmation required — show success state
                setRegistered(true);
            }
        } catch (err) {
            setError(typeof err === 'string' ? err : 'Registration failed. Please try again.');
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
                <div className="glass-panel glass-panel-premium" style={{ padding: '2.75rem 2.5rem' }}>

                    {/* Header */}
                    <div style={{ textAlign: 'center', marginBottom: '2.25rem' }}>
                        <motion.div
                            style={{
                                display: 'inline-flex',
                                padding: '18px',
                                background: 'linear-gradient(135deg, rgba(6,182,212,0.2), rgba(99,102,241,0.1))',
                                borderRadius: '50%',
                                marginBottom: '1.5rem',
                                border: '1px solid rgba(6,182,212,0.3)',
                                boxShadow: '0 0 40px rgba(6,182,212,0.2)',
                            }}
                            animate={{ boxShadow: ['0 0 20px rgba(6,182,212,0.15)', '0 0 45px rgba(6,182,212,0.35)', '0 0 20px rgba(6,182,212,0.15)'] }}
                            transition={{ duration: 2.5, repeat: Infinity }}
                        >
                            <Sparkles size={38} color="#22D3EE" />
                        </motion.div>
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
                            Create account
                        </h2>
                        <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                            Start building your AI career roadmap
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

                    {/* Email confirmation success state */}
                    {registered ? (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            style={{
                                textAlign: 'center',
                                padding: '2rem 1rem',
                            }}
                        >
                            <CheckCircle size={48} color="#22D3EE" style={{ marginBottom: '1rem' }} />
                            <h3 style={{ color: '#fff', marginBottom: '0.75rem' }}>Check your email!</h3>
                            <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                                We sent a confirmation link to <strong style={{ color: '#22D3EE' }}>{email}</strong>.<br />
                                Click the link in the email to activate your account, then sign in.
                            </p>
                            <Link
                                to="/login"
                                className="btn btn-primary"
                                style={{ display: 'inline-flex', padding: '0.75rem 2rem', background: 'linear-gradient(135deg, var(--color-secondary), var(--color-secondary-dark))' }}
                            >
                                Go to Sign In →
                            </Link>
                        </motion.div>
                    ) : (
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
                        <div style={{ marginBottom: '1.125rem' }}>
                            <label htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                className="input-field"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Min. 6 characters"
                                required
                            />
                        </div>
                        <div style={{ marginBottom: '1.75rem' }}>
                            <label htmlFor="confirmPassword">Confirm password</label>
                            <input
                                id="confirmPassword"
                                type="password"
                                className="input-field"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <button
                                type="submit"
                                className="btn btn-primary"
                                style={{
                                    width: '100%',
                                    padding: '0.875rem',
                                    fontSize: '1rem',
                                    background: 'linear-gradient(135deg, var(--color-secondary), var(--color-secondary-dark))',
                                    boxShadow: '0 4px 16px rgba(6,182,212,0.4)'
                                }}
                                disabled={loading}
                            >
                                {loading
                                    ? <><Loader2 size={18} className="animate-spin" /> Creating account...</>
                                    : <><UserPlus size={18} /> Create Free Account</>
                                }
                            </button>
                        </form>
                    )}

                    <div style={{ marginTop: '1.875rem', textAlign: 'center' }}>
                        <div className="divider" />
                        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-dim)' }}>
                            Already have an account?{' '}
                            <Link to="/login" style={{ color: 'var(--color-primary-light)', fontWeight: 600, textDecoration: 'none' }}>
                                Sign in →
                            </Link>
                        </p>
                    </div>
                </div>
                <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--color-text-dim)' }}>
                    Powered by Gemini AI · Secure · Private
                </p>
            </motion.div>
        </div>
    );
};

export default Register;
