import React from 'react';
import { Network, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        console.error("Dashboard caught an error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div style={{
                    minHeight: '400px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '2rem'
                }}>
                    <div className="glass-panel" style={{
                        maxWidth: '500px',
                        width: '100%',
                        padding: '3rem',
                        textAlign: 'center',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '1.5rem'
                    }}>
                        <div style={{
                            background: 'rgba(239, 68, 68, 0.1)',
                            padding: '1.5rem',
                            borderRadius: '50%',
                            color: '#ef4444'
                        }}>
                            <Network size={48} />
                        </div>

                        <div>
                            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'white' }}>
                                Oops, something went wrong
                            </h2>
                            <p style={{ color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
                                We encountered an unexpected error while rendering this step.
                                Don&apos;t worry, your progress is safe.
                            </p>
                            <p style={{
                                marginTop: '1rem',
                                padding: '1rem',
                                background: 'rgba(0,0,0,0.3)',
                                borderRadius: '8px',
                                fontFamily: 'monospace',
                                fontSize: '0.85rem',
                                color: '#ef4444',
                                wordBreak: 'break-all'
                            }}>
                                {this.state.error?.message || "Unknown rendering error"}
                            </p>
                        </div>

                        <button
                            className="btn btn-primary"
                            onClick={() => window.location.reload()}
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 2rem' }}
                        >
                            <RefreshCw size={18} />
                            Reload Dashboard
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
