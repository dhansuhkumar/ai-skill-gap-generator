import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Clock, Gift } from 'lucide-react';

const Timeline = ({ steps, onToggleStep }) => {
    return (
        <div className="relative border-l border-gray-700 ml-4 space-y-8">
            {steps.map((step, idx) => {
                const isCompleted = step.completed;

                return (
                    <motion.div
                        key={idx}
                        className="relative pl-8"
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        {/* Node on the line */}
                        <div
                            className={`absolute -left-[9px] top-1 w-5 h-5 rounded-full border-2 flex items-center justify-center bg-[var(--color-bg-app)] ${isCompleted
                                    ? 'border-[var(--color-success)] text-[var(--color-success)]'
                                    : 'border-gray-600 text-gray-500'
                                }`}
                        >
                            {isCompleted ? <div className="w-2 h-2 bg-[var(--color-success)] rounded-full" /> : <div className="w-2 h-2 bg-gray-600 rounded-full" />}
                        </div>

                        {/* Card Content */}
                        <div
                            className={`glass-panel p-6 transition-all duration-300 ${isCompleted ? 'border-[var(--color-success)]/30' : 'border-[var(--color-border)]'}`}
                            onClick={() => onToggleStep && onToggleStep(idx, !isCompleted)}
                            style={{ cursor: onToggleStep ? 'pointer' : 'default' }}
                        >
                            <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center mb-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-mono text-[var(--color-text-muted)]">
                                            Days {step.day_from}-{step.day_to}
                                        </span>
                                        {step.project && (
                                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-[rgba(16,185,129,0.1)] text-[var(--color-success)] border border-[rgba(16,185,129,0.2)]">
                                                <Gift size={10} /> Project
                                            </span>
                                        )}
                                    </div>
                                    <h3 className="text-xl font-semibold text-[var(--color-text-main)]">
                                        {step.title}
                                    </h3>
                                </div>
                                <button
                                    className={`flex items-center gap-2 text-sm font-medium px-3 py-1 rounded-full transition-colors ${isCompleted
                                            ? 'bg-[rgba(16,185,129,0.1)] text-[var(--color-success)] hover:bg-[rgba(16,185,129,0.2)]'
                                            : 'bg-[var(--color-border)] text-[var(--color-text-muted)] hover:text-white'
                                        }`}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onToggleStep && onToggleStep(idx, !isCompleted);
                                    }}
                                >
                                    {isCompleted ? <CheckCircle2 size={16} /> : <Circle size={16} />}
                                    {isCompleted ? 'Completed' : 'Mark Complete'}
                                </button>
                            </div>

                            <ul className="space-y-2 mb-4">
                                {step.tasks && step.tasks.map((task, taskIdx) => (
                                    <li key={taskIdx} className="flex items-start gap-2 text-[var(--color-text-muted)] text-sm">
                                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] opacity-60 flex-shrink-0" />
                                        <span>{task}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </motion.div>
                );
            })}
        </div>
    );
};

export default Timeline;
