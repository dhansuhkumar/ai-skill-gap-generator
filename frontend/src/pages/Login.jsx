import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/auth';
import { motion } from 'framer-motion';
import { Loader2, LogIn, Sparkles, Rocket } from 'lucide-react';


const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await authService.login(email, password);
            navigate('/');
        } catch (err) {
            setError(typeof err === 'string' ? err : 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>

            <div className="container" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 1 }}>
                <motion.div
                    initial={{ opacity: 0, y: 30, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    className="glass-panel glass-panel-glow"
                    style={{
                        width: '100%',
                        maxWidth: '420px',
                        padding: '2.5rem',
                        background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%)',
                        border: '1px solid rgba(139, 92, 246, 0.2)',
                    }}
                >
                    {/* Logo and Title */}
                    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                        <motion.div
                            style={{
                                display: 'inline-flex',
                                padding: '16px',
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(6, 182, 212, 0.1))',
                                borderRadius: '50%',
                                marginBottom: '1.25rem',
                                border: '1px solid rgba(139, 92, 246, 0.3)',
                                boxShadow: '0 0 30px rgba(139, 92, 246, 0.3)',
                            }}
                            animate={{
                                boxShadow: [
                                    '0 0 20px rgba(139, 92, 246, 0.3)',
                                    '0 0 40px rgba(139, 92, 246, 0.5)',
                                    '0 0 20px rgba(139, 92, 246, 0.3)',
                                ]
                            }}
                            transition={{ duration: 2, repeat: Infinity }}
                        >
                            <Rocket size={36} color="#8b5cf6" />
                        </motion.div>
                        <h1 style={{
                            fontSize: '2.25rem',
                            marginBottom: '0.5rem',
                            background: 'linear-gradient(135deg, #fff, #94a3b8)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}>
                            Welcome Back
                        </h1>
                        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.95rem' }}>
                            Sign in to continue your <span style={{ color: 'var(--color-primary)' }}>AI</span> journey
                        </p>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="error-message"
                            style={{
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                color: '#fca5a5',
                                padding: '0.875rem 1rem',
                                borderRadius: '0.75rem',
                                marginBottom: '1.5rem',
                                fontSize: '0.875rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                            }}
                        >
                            <span style={{ fontSize: '1.1rem' }}>⚠️</span>
                            {error}
                        </motion.div>
                    )}

                    {/* Login Form */}
                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: '1.25rem' }}>
                            <label htmlFor="email" style={{ color: 'var(--color-text-muted)', marginBottom: '0.5rem', display: 'block' }}>
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                className="input-field"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                                style={{
                                    background: 'rgba(15, 23, 42, 0.6)',
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '1.75rem' }}>
                            <label htmlFor="password" style={{ color: 'var(--color-text-muted)', marginBottom: '0.5rem', display: 'block' }}>
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                className="input-field"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                required
                                style={{
                                    background: 'rgba(15, 23, 42, 0.6)',
                                }}
                            />
                        </div>

                        <motion.button
                            type="submit"
                            className="btn btn-primary"
                            style={{
                                width: '100%',
                                padding: '1rem',
                                fontSize: '1rem',
                                fontWeight: 600,
                            }}
                            disabled={loading}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            {loading ? (
                                <Loader2 className="animate-spin" size={20} />
                            ) : (
                                <>
                                    <LogIn size={20} />
                                    Sign In
                                </>
                            )}
                        </motion.button>
                    </form>

                    {/* Register Link */}
                    <div style={{
                        marginTop: '1.75rem',
                        textAlign: 'center',
                        fontSize: '0.9rem',
                        color: 'var(--color-text-muted)',
                        paddingTop: '1.5rem',
                        borderTop: '1px solid var(--color-border)',
                    }}>
                        Don't have an account?{' '}
                        <Link
                            to="/register"
                            style={{
                                color: 'var(--color-primary)',
                                textDecoration: 'none',
                                fontWeight: 600,
                                transition: 'all 0.2s',
                            }}
                        >
                            Create Account
                        </Link>
                    </div>
                </motion.div>
            </div>
        </>
    );
};

export default Login;
