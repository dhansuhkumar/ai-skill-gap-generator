import React from 'react';
import { motion } from 'framer-motion';
import { Check, User, Target, BrainCircuit, ListChecks, Sparkles } from 'lucide-react';

/**
 * StepProgressIndicator - Animated step progress bar
 * 
 * Shows current step with glowing effects and smooth transitions
 */
const StepProgressIndicator = ({ currentStep, steps }) => {
    // Default steps if not provided
    const defaultSteps = [
        { id: 1, label: 'Skills', icon: User },
        { id: 2, label: 'Role', icon: Target },
        { id: 3, label: 'Gaps', icon: BrainCircuit },
        { id: 4, label: 'Prefs', icon: ListChecks },
        { id: 5, label: 'Results', icon: Sparkles },
    ];

    const stepsList = steps || defaultSteps;

    const getStepStatus = (stepId) => {
        if (stepId < currentStep) return 'completed';
        if (stepId === currentStep) return 'active';
        return 'pending';
    };

    const getLineStatus = (stepId) => {
        if (stepId < currentStep) return 'completed';
        if (stepId === currentStep) return 'active';
        return 'pending';
    };

    return (
        <>
        <div className="step-progress" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem 0',
            gap: 0,
            overflowX: 'auto',
        }}>
            {stepsList.map((step, index) => {
                const status = getStepStatus(step.id);
                const Icon = step.icon;
                const isLast = index === stepsList.length - 1;

                return (
                    <React.Fragment key={step.id}>
                        <div className="step-item" style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '0.5rem',
                        }}>
                            <motion.div
                                className={`step-circle ${status}`}
                                initial={false}
                                animate={{
                                    scale: status === 'active' ? 1 : 1,
                                    opacity: status === 'pending' ? 0.6 : 1,
                                }}
                                transition={{ duration: 0.3 }}
                                style={{
                                    width: 48,
                                    height: 48,
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontWeight: 600,
                                    fontSize: '1rem',
                                    position: 'relative',
                                    zIndex: 2,
                                    background: status === 'completed'
                                        ? 'linear-gradient(135deg, #10b981, #059669)'
                                        : status === 'active'
                                            ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
                                            : '#111827',
                                    color: 'white',
                                    border: status === 'pending' ? '2px solid rgba(148, 163, 184, 0.2)' : 'none',
                                    boxShadow: status === 'completed'
                                        ? '0 0 20px rgba(16, 185, 129, 0.4)'
                                        : status === 'active'
                                            ? '0 0 30px rgba(139, 92, 246, 0.6)'
                                            : 'none',
                                }}
                            >
                                {status === 'completed' ? (
                                    <Check size={22} />
                                ) : (
                                    <Icon size={20} style={{ opacity: status === 'pending' ? 0.5 : 1 }} />
                                )}

                                {/* Pulse ring for active step */}
                                {status === 'active' && (
                                    <motion.div
                                        style={{
                                            position: 'absolute',
                                            inset: -4,
                                            borderRadius: '50%',
                                            border: '2px solid rgba(139, 92, 246, 0.5)',
                                        }}
                                        animate={{
                                            scale: [1, 1.3, 1],
                                            opacity: [0.5, 0, 0.5],
                                        }}
                                        transition={{
                                            duration: 2,
                                            repeat: Infinity,
                                            ease: 'easeInOut',
                                        }}
                                    />
                                )}
                            </motion.div>
                            <span
                                className="step-label"
                                style={{
                                    fontSize: '0.7rem',
                                    color: status === 'active' ? 'white' : 'rgba(148, 163, 184, 0.8)',
                                    fontWeight: status === 'active' ? 600 : 500,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                }}
                            >
                                {step.label}
                            </span>
                        </div>

                        {/* Connecting line */}
                        {!isLast && (
                            <div
                                className={`step-line ${getLineStatus(step.id + 1)}`}
                                style={{
                                    width: 50,
                                    height: 2,
                                    margin: '0 0.25rem',
                                    marginBottom: '1.5rem',
                                    background: getLineStatus(step.id + 1) === 'completed'
                                        ? 'linear-gradient(90deg, #10b981, #10b981)'
                                        : getLineStatus(step.id + 1) === 'active'
                                            ? 'linear-gradient(90deg, #10b981, #8b5cf6)'
                                            : 'rgba(148, 163, 184, 0.2)',
                                    boxShadow: getLineStatus(step.id + 1) === 'completed'
                                        ? '0 0 10px rgba(16, 185, 129, 0.4)'
                                        : 'none',
                                    borderRadius: 1,
                                }}
                            />
                        )}
                    </React.Fragment>
                );
            })}
        </div>
        <style>{`
            @media (max-width: 480px) {
                .step-circle {
                    width: 36px !important;
                    height: 36px !important;
                }
                .step-label {
                    font-size: 0.6rem !important;
                }
            }
        `}</style>
        </>
    );
};

export default StepProgressIndicator;
