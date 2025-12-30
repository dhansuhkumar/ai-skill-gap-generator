import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

function Main() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [backendStatus, setBackendStatus] = useState('Checking...');
  const [extractedSkills, setExtractedSkills] = useState([]);
  const [aiProvider, setAiProvider] = useState('auto'); // 'auto', 'gemini', 'openai'

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/status`);
        if (response.ok) {
          setBackendStatus('Connected');
        } else {
          setBackendStatus('Offline');
        }
      } catch (error) {
        setBackendStatus('Offline');
      }
    };
    checkBackend();
  }, []);

  const handleResumeChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setResume(file);

    // Extract skills automatically when resume is uploaded
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/upload_resume`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setExtractedSkills(data.extracted_skills || []);
      }
    } catch (err) {
      console.error("Skill extraction failed", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobDescription) {
      setError('Please enter a target role or job description.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const analysisResponse = await fetch(`${API_BASE_URL}/api/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: jobDescription,
          skills: extractedSkills,
          provider: aiProvider === 'auto' ? null : aiProvider
        }),
      });

      if (!analysisResponse.ok) throw new Error('Analysis failed.');
      const analysisData = await analysisResponse.json();
      setAnalysisResult(analysisData);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      {/* Header Area */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
            AI Skill-Gap Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">Bridge your career gap with AI-powered insights.</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-semibold ${backendStatus === 'Connected' ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' : 'bg-rose-500/10 border-rose-500/50 text-rose-400'
          }`}>
          <span className={`w-2 h-2 rounded-full animate-pulse ${backendStatus === 'Connected' ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          Backend: {backendStatus}
        </div>
      </div>

      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Controls */}
        <div className="lg:col-span-4 space-y-6">
          <section className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span className="text-cyan-400">01</span> Analyze Skills
            </h2>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">Your Resume (PDF)</label>
                <div className="relative group">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleResumeChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  />
                  <div className="border-2 border-dashed border-slate-700 group-hover:border-cyan-500/50 rounded-xl p-4 text-center transition-all bg-slate-950/50">
                    <p className="text-sm text-slate-300">{resume ? resume.name : "Drop resume or click to upload"}</p>
                  </div>
                </div>
                {extractedSkills.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {extractedSkills.slice(0, 5).map((s, i) => (
                      <span key={i} className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700">{s}</span>
                    ))}
                    {extractedSkills.length > 5 && <span className="text-[10px] text-slate-500">+{extractedSkills.length - 5} more</span>}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">Target Role / Description</label>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="e.g. Senior Machine Learning Engineer..."
                  className="w-full h-32 bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-400 transition-all outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">AI Model Selection</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'auto', label: 'Auto (Best)' },
                    { id: 'gemini', label: 'Gemini' },
                    { id: 'openai', label: 'GPT-4o' }
                  ].map(option => (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => setAiProvider(option.id)}
                      className={`py-2 px-1 text-[10px] font-bold rounded-lg border transition-all ${aiProvider === option.id
                        ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400'
                        : 'bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700 hover:text-slate-400'
                        }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-500 hover:to-purple-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-cyan-900/20 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <span className="border-2 border-white/30 border-t-white rounded-full w-4 h-4 animate-spin"></span>
                    Analyzing...
                  </>
                ) : 'Run Analysis'}
              </button>
            </form>
            {error && <p className="mt-4 text-xs text-center text-rose-400 font-medium">{error}</p>}
          </section>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-8">
          {!analysisResult && !isLoading && (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-slate-800 rounded-2xl bg-slate-900/20">
              <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4 text-2xl">🔍</div>
              <h3 className="text-xl font-bold text-slate-300">No Analysis Yet</h3>
              <p className="text-slate-500 text-sm max-w-sm mt-2">Upload your resume and enter a target role to see your skill-gap visualization and project path.</p>
            </div>
          )}

          {isLoading && (
            <div className="space-y-6">
              <div className="h-40 bg-slate-900 animate-pulse rounded-2xl"></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="h-32 bg-slate-900 animate-pulse rounded-2xl"></div>
                <div className="h-32 bg-slate-900 animate-pulse rounded-2xl"></div>
              </div>
            </div>
          )}

          {analysisResult && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Skill Gap Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl">
                  <h3 className="text-sm font-bold text-slate-400 mb-4 uppercase tracking-widest">Skills to Acquire</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.missing_skills?.map((skill, i) => (
                      <span key={i} className="px-3 py-1 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-full text-xs font-semibold hover:bg-rose-500/20 transition-colors">
                        {skill}
                      </span>
                    )) || <span className="text-slate-500 text-xs italic">All required skills found!</span>}
                  </div>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col justify-center text-center">
                  <div className="text-3xl font-black text-cyan-400">
                    {analysisResult.missing_skills?.length || 0}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase font-bold mt-1 tracking-tighter">Gap Indicators</div>
                </div>
              </div>

              {/* Learning Path / Recommended Projects */}
              <section>
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <span className="text-purple-400">#</span> Personalized Learning Path
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysisResult.recommended_projects?.map((proj, i) => (
                    <div key={i} className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 p-5 rounded-2xl hover:border-cyan-500/30 transition-all group">
                      <div className="flex justify-between items-start mb-3">
                        <span className="text-xs font-bold text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded uppercase">{proj.skill}</span>
                      </div>
                      <p className="text-sm text-slate-300 leading-relaxed min-h-[4rem] group-hover:text-white transition-colors">
                        {proj.project}
                      </p>
                      {proj.learning_path_steps?.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-800">
                          <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Key Steps</p>
                          <ul className="text-xs space-y-2 text-slate-400">
                            {proj.learning_path_steps.slice(0, 3).map((step, si) => (
                              <li key={si} className="flex items-start gap-2">
                                <span className="text-cyan-500 mt-0.5 text-[8px]">●</span> {typeof step === 'string' ? step : step.title}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>

              {/* AI Ideas */}
              {analysisResult.ai_projects?.length > 0 && (
                <section className="bg-gradient-to-r from-purple-900/20 to-cyan-900/20 border border-purple-500/20 p-6 rounded-2xl">
                  <h3 className="text-sm font-bold text-purple-300 mb-4 uppercase tracking-widest flex items-center gap-2">
                    <span className="animate-pulse">✨</span> AI-Generated Project Concepts
                  </h3>
                  <ul className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 list-disc pl-5 text-sm text-slate-300">
                    {analysisResult.ai_projects.map((idea, i) => (
                      <li key={i} className="marker:text-purple-400">{idea}</li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Main;