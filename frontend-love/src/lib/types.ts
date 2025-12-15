export interface VideoResource {
  title: string;
  url: string;
  thumbnail?: string;
}

export interface RecommendedProject {
  id: number;
  title: string;
  skill: string;
  learning_path_steps: string[];
  videos: VideoResource[];
}

export interface SkillGapAnalysisResponse {
  required_skills_ai: string[];
  missing_skills: string[];
  recommended_projects: RecommendedProject[];
}

export interface ResumeUploadResponse {
  skills: string[];
}

export interface SkillGapAnalysisRequest {
  skills: string[];
  role: string;
  include_youtube: boolean;
  raw_profile?: string;
}
