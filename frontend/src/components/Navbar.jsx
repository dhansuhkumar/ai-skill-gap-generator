import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { authService } from '../services/auth';
import { LayoutDashboard, User, MessageSquare, LogOut, Code2 } from 'lucide-react';

const Navbar = () => {
    const location = useLocation();
    const username = authService.getCurrentUser();

    const handleLogout = () => {
        authService.logout();
    };

    const NavLink = ({ to, icon: Icon, children }) => {
        const isActive = location.pathname === to;
        return (
            <Link
                to={to}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.5rem',
                    color: isActive ? 'white' : 'var(--color-text-muted)',
                    background: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    textDecoration: 'none',
                    transition: 'all 0.2s',
                    fontWeight: 500
                }}
            >
                <Icon size={18} />
                {children}
            </Link>
        );
    };

    return (
        <nav style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: 'var(--header-height)',
            background: 'rgba(15, 23, 42, 0.8)',
            backdropFilter: 'blur(12px)',
            borderBottom: '1px solid var(--color-border)',
            zIndex: 50,
            display: 'flex',
            alignItems: 'center'
        }}>
            <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
                    <div style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))', padding: '6px', borderRadius: '8px' }}>
                        <Code2 size={24} color="white" />
                    </div>
                    <span style={{ fontSize: '1.25rem', fontWeight: 700, background: 'linear-gradient(to right, white, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        SkillGap<span style={{ fontWeight: 400 }}>AI</span>
                    </span>
                </Link>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <NavLink to="/" icon={LayoutDashboard}>Dashboard</NavLink>
                    <NavLink to="/chat" icon={MessageSquare}>AI Chat</NavLink>
                    <NavLink to="/profile" icon={User}>Profile</NavLink>

                    <div style={{ width: '1px', height: '24px', background: 'var(--color-border)', margin: '0 0.5rem' }} />

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                            Hi, <span style={{ color: 'white', fontWeight: 500 }}>{username}</span>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="btn btn-secondary"
                            style={{ padding: '0.5rem', border: 'none', background: 'transparent' }}
                            title="Logout"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
