import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, GraduationCap, Briefcase, Award, Languages, Github, Linkedin } from 'lucide-react';
import api from '../services/api';

const ResumeUpload = ({ onSkillsExtracted, onExperienceLevelExtracted, onResumeDataExtracted }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [resumeData, setResumeData] = useState(null);
    const fileInputRef = useRef(null);

    const handleFile = async (file) => {
        if (file.type !== 'application/pdf') {
            setError('Please upload a PDF file.');
            return;
        }

        setLoading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await api.uploadResume(formData);
            const parsed = response.data.parsed || {};
            
            const extractedSkills = parsed.skills || [];
            const experienceLevel = parsed.global_context || 'neutral';
            
            setResumeData(parsed);
            
            if (onSkillsExtracted) {
                onSkillsExtracted(extractedSkills);
            }
            if (onExperienceLevelExtracted) {
                onExperienceLevelExtracted(experienceLevel);
            }
            if (onResumeDataExtracted) {
                onResumeDataExtracted(parsed);
            }
            
            const filled = parsed.filled_boxes || 0;
            const total = parsed.total_boxes || 7;
            const pct = parsed.filled_percentage || 0;
            
            setSuccess(`${extractedSkills.length} skills extracted! ${pct}% resume data filled (${filled}/${total} sections)`);
        } catch (err) {
            setError('Failed to process resume. Please try again.');
            setResumeData(null);
        } finally {
            setLoading(false);
        }
    };

    const onDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const onDragLeave = () => {
        setIsDragging(false);
    };

    const onDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const DataBox = ({ icon: Icon, label, value, color }) => (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 0.75rem',
            background: value ? `${color}15` : 'rgba(255,255,255,0.03)',
            borderRadius: '8px',
            border: `1px solid ${value ? color : 'rgba(255,255,255,0.08)'}`,
            flex: '1 1 45%',
            minWidth: '140px',
        }}>
            <Icon size={16} color={value ? color : 'var(--color-text-dim)'} />
            <div style={{ overflow: 'hidden' }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {label}
                </div>
                <div style={{ 
                    fontSize: '0.8rem', 
                    color: value ? 'var(--color-text-main)' : 'var(--color-text-dim)',
                    fontWeight: value ? 500 : 400,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                }}>
                    {value || 'Not detected'}
                </div>
            </div>
        </div>
    );

    const InfoChip = ({ label, value }) => value ? (
        <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.25rem 0.6rem',
            background: 'rgba(99,102,241,0.1)',
            borderRadius: '20px',
            fontSize: '0.75rem',
            color: 'var(--color-text-main)',
            margin: '0.2rem',
        }}>
            <span style={{ fontWeight: 500 }}>{label}:</span>
            <span>{value}</span>
        </div>
    ) : null;

    return (
        <div>
            <div
                style={{
                    padding: '2rem',
                    textAlign: 'center',
                    borderStyle: 'dashed',
                    borderWidth: '2px',
                    borderColor: isDragging ? 'var(--color-primary)' : 'var(--color-border)',
                    background: isDragging ? 'rgba(139, 92, 246, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                    borderRadius: 'var(--radius-lg)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    marginBottom: resumeData ? '1rem' : '0'
                }}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    type="file"
                    style={{ display: 'none' }}
                    ref={fileInputRef}
                    accept=".pdf"
                    onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
                />

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', color: 'var(--color-text-muted)' }}>
                    {loading ? (
                        <>
                            <Loader2 className="animate-spin" size={48} color="var(--color-primary)" />
                            <p>Analyzing Resume with AI...</p>
                        </>
                    ) : success ? (
                        <>
                            <CheckCircle2 size={48} color="var(--color-success)" />
                            <p style={{ color: 'var(--color-text-main)' }}>{success}</p>
                        </>
                    ) : (
                        <>
                            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1rem', borderRadius: '50%' }}>
                                <Upload size={32} />
                            </div>
                            <div>
                                <p style={{ color: 'var(--color-text-main)', fontWeight: 500, marginBottom: '0.25rem' }}>
                                    Upload Resume (PDF)
                                </p>
                                <p style={{ fontSize: '0.875rem' }}>
                                    Drag & drop or click to auto-fill skills with AI
                                </p>
                            </div>
                        </>
                    )}

                    {error && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-error)', marginTop: '0.5rem' }}>
                            <AlertCircle size={16} />
                            <span style={{ fontSize: '0.9rem' }}>{error}</span>
                        </div>
                    )}
                </div>
            </div>

            {resumeData && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{
                        background: 'rgba(255,255,255,0.03)',
                        borderRadius: 'var(--radius-lg)',
                        padding: '1.25rem',
                        border: '1px solid rgba(255,255,255,0.08)',
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h4 style={{ margin: 0, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <FileText size={16} />
                            Extracted Resume Data
                        </h4>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.8rem',
                        }}>
                            <div style={{
                                width: '60px',
                                height: '6px',
                                background: 'rgba(255,255,255,0.1)',
                                borderRadius: '3px',
                                overflow: 'hidden',
                            }}>
                                <div style={{
                                    width: `${resumeData.filled_percentage || 0}%`,
                                    height: '100%',
                                    background: 'linear-gradient(90deg, var(--color-primary), var(--color-accent))',
                                    borderRadius: '3px',
                                    transition: 'width 0.3s ease',
                                }} />
                            </div>
                            <span style={{ color: 'var(--color-text-dim)' }}>
                                {resumeData.filled_boxes || 0}/{resumeData.total_boxes || 7}
                            </span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        <DataBox
                            icon={GraduationCap}
                            label="Education"
                            value={resumeData.education?.[0]?.degree || (resumeData.education?.length > 0 ? `${resumeData.education.length} entry` : null)}
                            color="#10b981"
                        />
                        <DataBox
                            icon={Briefcase}
                            label="Experience"
                            value={resumeData.experience?.[0] ? `${resumeData.experience.length} roles` : null}
                            color="#3b82f6"
                        />
                        <DataBox
                            icon={Award}
                            label="Certifications"
                            value={resumeData.certifications?.[0] || (resumeData.certifications?.length > 0 ? `${resumeData.certifications.length} certs` : null)}
                            color="#f59e0b"
                        />
                        <DataBox
                            icon={Languages}
                            label="Languages"
                            value={resumeData.languages?.[0] || (resumeData.languages?.length > 0 ? `${resumeData.languages.length} langs` : null)}
                            color="#8b5cf6"
                        />
                        <DataBox
                            icon={Github}
                            label="GitHub"
                            value={resumeData.github_url ? 'Found' : null}
                            color="#6b7280"
                        />
                        <DataBox
                            icon={Linkedin}
                            label="LinkedIn"
                            value={resumeData.linkedin_url ? 'Found' : null}
                            color="#0077b5"
                        />
                    </div>

                    {resumeData.education?.length > 0 && (
                        <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-dim)', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Education
                            </div>
                            {resumeData.education.slice(0, 2).map((edu, i) => (
                                <div key={i} style={{ fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                                    <span style={{ color: 'var(--color-text-main)' }}>{edu.degree}</span>
                                    {edu.institution && <span style={{ color: 'var(--color-text-dim)' }}> @ {edu.institution}</span>}
                                    {edu.graduation_year && <span style={{ color: 'var(--color-text-dim)' }}> ({edu.graduation_year})</span>}
                                </div>
                            ))}
                        </div>
                    )}

                    {resumeData.experience?.length > 0 && (
                        <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-dim)', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Experience
                            </div>
                            {resumeData.experience.slice(0, 2).map((exp, i) => (
                                <div key={i} style={{ fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                                    <span style={{ color: 'var(--color-text-main)' }}>{exp.title}</span>
                                    {exp.company && <span style={{ color: 'var(--color-text-dim)' }}> @ {exp.company}</span>}
                                    {exp.start_year && <span style={{ color: 'var(--color-text-dim)' }}> ({exp.start_year}{exp.end_year ? `-${exp.end_year}` : '-Present'})</span>}
                                </div>
                            ))}
                        </div>
                    )}

                    {(resumeData.certifications?.length > 0 || resumeData.languages?.length > 0) && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                            {resumeData.certifications?.slice(0, 3).map((cert, i) => (
                                <InfoChip key={`cert-${i}`} label="Cert" value={cert} />
                            ))}
                            {resumeData.languages?.slice(0, 3).map((lang, i) => (
                                <InfoChip key={`lang-${i}`} label="Lang" value={lang} />
                            ))}
                        </div>
                    )}
                </motion.div>
            )}
        </div>
    );
};

export default ResumeUpload;
