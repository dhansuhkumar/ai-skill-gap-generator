import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Gift, Youtube, ExternalLink } from 'lucide-react';

const Timeline = ({ steps, youtubeVideos, onToggleStep }) => {
    return (
        <div style={{ position: 'relative', marginLeft: '1rem' }}>
            {/* Vertical line */}
            <div style={{
                position: 'absolute',
                left: '8px',
                top: '12px',
                bottom: '12px',
                width: '2px',
                background: 'linear-gradient(180deg, var(--color-primary) 0%, var(--color-border) 100%)'
            }} />

            {steps.map((step, idx) => {
                const isCompleted = step.completed;

                return (
                    <motion.div
                        key={idx}
                        style={{ position: 'relative', paddingLeft: '2.5rem', marginBottom: '1.5rem' }}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        {/* Node circle with clickable checkbox */}
                        <motion.button
                            onClick={(e) => {
                                e.stopPropagation();
                                onToggleStep && onToggleStep(idx, !isCompleted);
                            }}
                            style={{
                                position: 'absolute',
                                left: 0,
                                top: '4px',
                                width: '22px',
                                height: '22px',
                                borderRadius: '50%',
                                border: `2px solid ${isCompleted ? 'var(--color-success)' : 'var(--color-border)'}`,
                                background: 'var(--color-bg-app)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                padding: 0,
                                transition: 'all 0.2s'
                            }}
                            whileTap={{ scale: 0.9 }}
                            whileHover={{ scale: 1.1 }}
                        >
                            <motion.div
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: isCompleted ? 1 : 0, opacity: isCompleted ? 1 : 0 }}
                                transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                                style={{
                                    width: '12px',
                                    height: '12px',
                                    borderRadius: '50%',
                                    background: 'var(--color-success)'
                                }}
                            />
                            {!isCompleted && (
                                <div style={{
                                    width: '8px',
                                    height: '8px',
                                    borderRadius: '50%',
                                    background: 'var(--color-border)'
                                }} />
                            )}
                        </motion.button>

                        {/* Card Content */}
                        <div
                            className="glass-panel"
                            style={{
                                padding: '1.25rem',
                                transition: 'all 0.3s',
                                borderColor: isCompleted ? 'rgba(16,185,129,0.3)' : 'var(--color-border)'
                            }}
                        >
                            <div style={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: '0.75rem',
                                justifyContent: 'space-between',
                                alignItems: 'flex-start',
                                marginBottom: '0.75rem'
                            }}>
                                <div style={{ flex: 1, minWidth: '200px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            fontFamily: 'monospace',
                                            color: 'var(--color-text-muted)',
                                            background: 'rgba(139, 92, 246, 0.1)',
                                            padding: '0.2rem 0.5rem',
                                            borderRadius: '4px'
                                        }}>
                                            Days {step.day_from}-{step.day_to}
                                        </span>
                                        {step.project && (
                                            <span style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '4px',
                                                padding: '0.2rem 0.5rem',
                                                borderRadius: '4px',
                                                fontSize: '0.7rem',
                                                fontWeight: 500,
                                                background: 'rgba(16,185,129,0.1)',
                                                color: 'var(--color-success)',
                                                border: '1px solid rgba(16,185,129,0.2)'
                                            }}>
                                                <Gift size={10} /> Project
                                            </span>
                                        )}
                                        {/* Checkbox indicator */}
                                        <motion.span
                                            initial={{ scale: 0 }}
                                            animate={{ scale: isCompleted ? 1 : 0 }}
                                            transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                                            style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                width: '18px',
                                                height: '18px',
                                                borderRadius: '4px',
                                                background: 'var(--color-success)',
                                                color: 'white'
                                            }}
                                        >
                                            <CheckCircle2 size={12} />
                                        </motion.span>
                                    </div>
                                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
                                        {step.title}
                                    </h3>
                                </div>

                                {/* Mark Complete Button */}
                                <motion.button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onToggleStep && onToggleStep(idx, !isCompleted);
                                    }}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem',
                                        fontSize: '0.85rem',
                                        fontWeight: 500,
                                        padding: '0.5rem 1rem',
                                        borderRadius: '2rem',
                                        border: 'none',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        background: isCompleted
                                            ? 'linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(16,185,129,0.1) 100%)'
                                            : 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%)',
                                        color: isCompleted ? 'var(--color-success)' : 'var(--color-primary)',
                                        boxShadow: isCompleted
                                            ? '0 0 0 1px rgba(16,185,129,0.3)'
                                            : '0 0 0 1px rgba(139, 92, 246, 0.3)'
                                    }}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    {isCompleted ? <CheckCircle2 size={16} /> : <Circle size={16} />}
                                    {isCompleted ? 'Completed' : 'Mark Complete'}
                                </motion.button>
                            </div>

                            {/* Tasks List */}
                            {step.tasks && step.tasks.length > 0 && (
                                <ul style={{ margin: 0, padding: 0, listStyle: 'none', marginTop: '0.75rem' }}>
                                    {step.tasks.map((task, taskIdx) => (
                                        <li key={taskIdx} style={{
                                            display: 'flex',
                                            alignItems: 'flex-start',
                                            gap: '0.5rem',
                                            color: 'var(--color-text-muted)',
                                            fontSize: '0.9rem',
                                            marginBottom: '0.35rem'
                                        }}>
                                            <span style={{
                                                marginTop: '0.5rem',
                                                width: '5px',
                                                height: '5px',
                                                borderRadius: '50%',
                                                background: 'var(--color-primary)',
                                                opacity: 0.6,
                                                flexShrink: 0
                                            }} />
                                            <span>{task}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </motion.div>
                );
            })}

            {/* YouTube Videos Section */}
            {youtubeVideos && youtubeVideos.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                        marginTop: '1.5rem',
                        marginLeft: '2.5rem',
                        padding: '1.25rem',
                        background: 'rgba(255, 0, 0, 0.05)',
                        borderRadius: '12px',
                        border: '1px solid rgba(255, 0, 0, 0.1)'
                    }}
                >
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        marginBottom: '1rem',
                        color: '#ff4444'
                    }}>
                        <Youtube size={20} />
                        <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
                            Recommended Videos
                        </h4>
                    </div>
                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {youtubeVideos.map((video, idx) => (
                            <div key={idx}>
                                {video.embed_url ? (
                                    <div style={{
                                        position: 'relative',
                                        paddingBottom: '56.25%',
                                        height: 0,
                                        overflow: 'hidden',
                                        borderRadius: '12px',
                                        marginBottom: '0.5rem'
                                    }}>
                                        <iframe
                                            src={video.embed_url}
                                            title={video.title}
                                            style={{
                                                position: 'absolute',
                                                top: 0, left: 0,
                                                width: '100%', height: '100%',
                                                border: 'none',
                                                borderRadius: '12px'
                                            }}
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                            allowFullScreen
                                        />
                                    </div>
                                ) : (
                                    <a
                                        href={video.url || `https://youtube.com/watch?v=${video.video_id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.75rem',
                                            padding: '0.75rem',
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '8px',
                                            textDecoration: 'none',
                                            transition: 'all 0.2s',
                                            border: '1px solid transparent',
                                            marginBottom: '0.5rem'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                                            e.currentTarget.style.borderColor = 'rgba(255, 0, 0, 0.2)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                                            e.currentTarget.style.borderColor = 'transparent';
                                        }}
                                    >
                                        {video.thumbnail && (
                                            <img
                                                src={video.thumbnail}
                                                alt=""
                                                style={{
                                                    width: '80px',
                                                    height: '45px',
                                                    objectFit: 'cover',
                                                    borderRadius: '6px'
                                                }}
                                            />
                                        )}
                                        <div style={{ flex: 1 }}>
                                            <div style={{
                                                fontSize: '0.9rem',
                                                color: 'var(--color-text-main)',
                                                marginBottom: '0.25rem',
                                                fontWeight: 500
                                            }}>
                                                {video.title}
                                            </div>
                                            {video.channel && (
                                                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                                    {video.channel}
                                                </div>
                                            )}
                                        </div>
                                        <ExternalLink size={16} style={{ color: 'var(--color-text-muted)' }} />
                                    </a>
                                )}
                            </div>
                        ))}
                    </div>
                </motion.div>
            )}
        </div>
    );
};

export default Timeline;
