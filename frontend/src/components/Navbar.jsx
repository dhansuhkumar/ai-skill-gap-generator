import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { authService } from '../services/auth';
import { LayoutDashboard, User, MessageSquare, LogOut, BrainCircuit } from 'lucide-react';

const Navbar = () => {
    const location = useLocation();
    const username = authService.getCurrentUser() || '';

    const handleLogout = () => {
        authService.logout();
    };

    const NavLink = ({ to, icon: Icon, children }) => {
        const isActive = location.pathname === to;
        return (
            <Link to={to} className={`nav-link${isActive ? ' active' : ''}`}>
                <Icon size={16} />
                {children}
            </Link>
        );
    };

    const initial = username ? username[0].toUpperCase() : '?';

    return (
        <nav className="navbar">
            <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>

                {/* Logo */}
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

                {/* Right side */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <NavLink to="/" icon={LayoutDashboard}>Dashboard</NavLink>
                    <NavLink to="/chat" icon={MessageSquare}>AI Chat</NavLink>
                    <NavLink to="/profile" icon={User}>Profile</NavLink>

                    {/* Divider */}
                    <div style={{ width: '1px', height: '20px', background: 'var(--color-border)', margin: '0 0.625rem' }} />

                    {/* User area */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div className="user-avatar">{initial}</div>
                            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {username}
                            </span>
                        </div>

                        <button
                            onClick={handleLogout}
                            title="Sign out"
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
            </div>
        </nav>
    );
};

export default Navbar;
