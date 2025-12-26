import React, { useState } from 'react';

function Main() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleResumeChange = (e) => {
    setResume(e.target.files[0]);
  };

  const handleJobDescriptionChange = (e) => {
    setJobDescription(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!resume || !jobDescription) {
      setError('Please upload a resume and enter a job description.');
      return;
    }

    setIsLoading(true);
    setError('');
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append('file', resume);

    try {
      // Step 1: Upload resume and get skills
      const resumeResponse = await fetch('http://127.0.0.1:8080/api/upload_resume', {
        method: 'POST',
        body: formData,
      });

      if (!resumeResponse.ok) {
        throw new Error('Failed to analyze resume.');
      }

      const resumeData = await resumeResponse.json();
      const skills = resumeData.extracted_skills;

      // Step 2: Get skill gap analysis
      const analysisResponse = await fetch('http://127.0.0.1:8080/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role: jobDescription,
          skills: skills,
        }),
      });

      if (!analysisResponse.ok) {
        throw new Error('Failed to get skill gap analysis.');
      }

      const analysisData = await analysisResponse.json();
      setAnalysisResult(analysisData);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="resume">Upload Resume:</label>
          <input
            type="file"
            id="resume"
            accept=".pdf"
            onChange={handleResumeChange}
          />
        </div>
        <div>
          <label htmlFor="jobDescription">Job Description:</label>
          <textarea
            id="jobDescription"
            value={jobDescription}
            onChange={handleJobDescriptionChange}
          />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {analysisResult && (
        <div>
          <h2>Analysis Result</h2>
          {analysisResult.missing_skills && (
            <div>
              <h3>Missing Skills</h3>
              <ul>
                {analysisResult.missing_skills.map((skill, index) => (
                  <li key={index}>{skill}</li>
                ))}
              </ul>
            </div>
          )}
          {analysisResult.recommended_projects && (
            <div>
              <h3>Recommended Projects</h3>
              <ul>
                {analysisResult.recommended_projects.map((project, index) => (
                  <li key={index}>{project.title}: {project.description}</li>
                ))}
              </ul>
            </div>
          )}
           {analysisResult.starter_projects && (
            <div>
              <h3>Starter Projects</h3>
              <ul>
                {analysisResult.starter_projects.map((project, index) => (
                  <li key={index}><a href={`http://127.0.0.1:8080/api/starter/${project.split('/').pop().replace('.zip', '')}`} download>{project.split('/').pop()}</a></li>
                ))}
              </ul>
            </div>
          )}
          {analysisResult.ai_projects && (
            <div>
                <h3>AI Generated Project Ideas</h3>
                <ul>
                {analysisResult.ai_projects.map((project, index) => (
                    <li key={index}>{project}</li>
                ))}
                </ul>
            </div>
            )}
        </div>
      )}
    </main>
  );
}

export default Main;