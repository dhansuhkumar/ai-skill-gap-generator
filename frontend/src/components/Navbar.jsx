import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { authService } from '../services/auth';
import { LayoutDashboard, User, MessageSquare, LogOut, BrainCircuit, Menu, X } from 'lucide-react';

const Navbar = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const location = useLocation();
    const sessionId = authService.getSessionId() || '';
    const shortId = sessionId ? sessionId.slice(0, 8) : '';

    const handleLogout = () => {
        authService.logout();
        setMobileMenuOpen(false);
    };

    const NavLink = ({ to, icon: Icon, children, onClick }) => {
        const isActive = location.pathname === to;
        return (
            <Link
                to={to}
                className={`nav-link${isActive ? ' active' : ''}`}
                onClick={onClick}
            >
                <Icon size={16} />
                {children}
            </Link>
        );
    };

    return (
        <nav className="navbar">
            <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>

                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none', flexShrink: 0 }}>
                    <div style={{
                        background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
                        padding: '7px',
                        borderRadius: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 0 16px rgba(99,102,241,0.4)'
                    }}>
                        <BrainCircuit size={20} color="white" />
                    </div>
                    <span style={{
                        fontSize: '1.1rem',
                        fontWeight: 800,
                        background: 'linear-gradient(135deg, #fff, #94A3B8)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        letterSpacing: '-0.03em'
                    }}>
                        SkillGap<span style={{ fontWeight: 400, opacity: 0.75 }}>AI</span>
                    </span>
                </Link>

                {/* Desktop Nav */}
                <div className="nav-desktop-links" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <NavLink to="/" icon={LayoutDashboard}>Dashboard</NavLink>
                    <NavLink to="/chat" icon={MessageSquare}>AI Chat</NavLink>
                    <NavLink to="/profile" icon={User}>Profile</NavLink>

                    <div style={{ width: '1px', height: '20px', background: 'var(--color-border)', margin: '0 0.625rem' }} />

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span className="nav-session-id" style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
                            Session: {shortId}
                        </span>

                        <button
                            onClick={handleLogout}
                            title="Reset session"
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                width: '32px',
                                height: '32px',
                                background: 'rgba(239,68,68,0.07)',
                                border: '1px solid rgba(239,68,68,0.15)',
                                borderRadius: '8px',
                                color: 'var(--color-text-dim)',
                                cursor: 'pointer',
                                transition: 'all 0.15s',
                                flexShrink: 0
                            }}
                            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.15)'; e.currentTarget.style.color = '#FCA5A5'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.3)'; }}
                            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.07)'; e.currentTarget.style.color = 'var(--color-text-dim)'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.15)'; }}
                        >
                            <LogOut size={15} />
                        </button>
                    </div>
                </div>

                {/* Mobile Hamburger */}
                <button
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    style={{
                        display: 'none',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '40px',
                        height: '40px',
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid var(--color-border)',
                        borderRadius: '10px',
                        color: 'var(--color-text)',
                        cursor: 'pointer',
                    }}
                    aria-label="Toggle menu"
                >
                    {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
                </button>
            </div>

            {/* Mobile Menu Drawer */}
            {mobileMenuOpen && (
                <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    background: 'rgba(10, 10, 20, 0.98)',
                    backdropFilter: 'blur(16px)',
                    borderBottom: '1px solid var(--color-border)',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.25rem',
                    zIndex: 200,
                }}>
                    <NavLink to="/" icon={LayoutDashboard} onClick={() => setMobileMenuOpen(false)}>Dashboard</NavLink>
                    <NavLink to="/chat" icon={MessageSquare} onClick={() => setMobileMenuOpen(false)}>AI Chat</NavLink>
                    <NavLink to="/profile" icon={User} onClick={() => setMobileMenuOpen(false)}>Profile</NavLink>
                    <div style={{ height: '1px', background: 'var(--color-border)', margin: '0.5rem 0' }} />
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontFamily: 'monospace', padding: '0 0.875rem' }}>
                        Session: {shortId}
                    </span>
                    <button
                        onClick={handleLogout}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.625rem',
                            padding: '0.75rem 0.875rem',
                            background: 'rgba(239,68,68,0.07)',
                            border: '1px solid rgba(239,68,68,0.15)',
                            borderRadius: 'var(--radius-lg)',
                            color: '#FCA5A5',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: 500,
                            fontFamily: 'var(--font-main)',
                        }}
                    >
                        <LogOut size={16} /> Reset Session
                    </button>
                </div>
            )}

            <style>{`
                @media (max-width: 768px) {
                    .nav-desktop-links {
                        display: none !important;
                    }
                    button[aria-label="Toggle menu"] {
                        display: flex !important;
                    }
                    .nav-session-id {
                        display: none;
                    }
                }
            `}</style>
        </nav>
    );
};

export default Navbar;
