import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../services/api';

const ResumeUpload = ({ onSkillsExtracted }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
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
            const extractedSkills = response.data.extracted_skills || [];

            onSkillsExtracted(extractedSkills);
            setSuccess(`Successfully extracted ${extractedSkills.length} skills!`);
        } catch (err) {
            setError('Failed to process resume. Please try again.');
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

    return (
        <div
            className="glass-panel"
            style={{
                padding: '2rem',
                textAlign: 'center',
                borderStyle: 'dashed',
                borderWidth: '2px',
                borderColor: isDragging ? 'var(--color-primary)' : 'var(--color-border)',
                background: isDragging ? 'rgba(139, 92, 246, 0.05)' : 'var(--color-bg-surface-glass)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                marginBottom: '1.5rem'
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
                        <p>Analyzing Resume...</p>
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
                                Drag & drop or click to auto-fill skills
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
    );
};

export default ResumeUpload;
