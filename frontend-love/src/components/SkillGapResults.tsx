import { useState } from "react";
import { Check, AlertTriangle, TrendingUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { JobReadinessChart } from "./JobReadinessChart";
import { ProjectCard } from "./ProjectCard";
import type { SkillGapAnalysisResponse } from "@/lib/types";

interface SkillGapResultsProps {
  skills: string[];
  role: string;
  analysis: SkillGapAnalysisResponse;
  onReset: () => void;
}

export function SkillGapResults({ skills, role, analysis, onReset }: SkillGapResultsProps) {
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  // Calculate matched skills (intersection of user skills and required skills)
  const matchedSkills = skills.filter((skill) =>
    analysis.required_skills_ai.some(
      (required) => required.toLowerCase() === skill.toLowerCase()
    )
  );

  // Calculate job readiness percentage
  const jobReadiness = analysis.required_skills_ai.length > 0
    ? Math.round((matchedSkills.length / analysis.required_skills_ai.length) * 100)
    : 0;

  // Assign priority based on position in missing skills array
  const missingSkillsWithPriority = analysis.missing_skills.map((skill, index) => ({
    name: skill,
    priority: index < 2 ? "high" : index < 4 ? "medium" : "low",
  }));

  const toggleSkillSelection = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "from-rose to-accent";
      case "medium":
        return "from-amber to-rose";
      default:
        return "from-sky to-cyan";
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center">
        <h2 className="font-display text-3xl md:text-4xl font-bold mb-2">
          Your <span className="gradient-text">Skill Gap Analysis</span>
        </h2>
        <p className="text-muted-foreground">
          For <span className="font-semibold text-foreground">{role}</span> role
        </p>
      </div>

      {/* Job Readiness */}
      <div className="glass rounded-2xl p-6 md:p-8">
        <h3 className="font-display font-semibold text-xl mb-6 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          Job Readiness Score
        </h3>
        <JobReadinessChart percentage={jobReadiness} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Matched Skills */}
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-semibold text-lg mb-4 flex items-center gap-2">
            <Check className="w-5 h-5 text-emerald" />
            Skills You Have ({matchedSkills.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {matchedSkills.length > 0 ? (
              matchedSkills.map((skill) => (
                <span
                  key={skill}
                  className="px-4 py-2 rounded-full bg-emerald/10 text-emerald font-medium text-sm border border-emerald/20"
                >
                  {skill}
                </span>
              ))
            ) : (
              <p className="text-muted-foreground text-sm">No matching skills found</p>
            )}
          </div>
        </div>

        {/* Missing Skills */}
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-semibold text-lg mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber" />
            Skills to Learn ({analysis.missing_skills.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {missingSkillsWithPriority.map((skill) => (
              <button
                key={skill.name}
                onClick={() => toggleSkillSelection(skill.name)}
                className={cn(
                  "px-4 py-2 rounded-full font-medium text-sm transition-all duration-300",
                  selectedSkills.includes(skill.name)
                    ? `bg-gradient-to-r ${getPriorityColor(skill.priority)} text-primary-foreground scale-105`
                    : "bg-muted hover:bg-muted/80 text-foreground"
                )}
              >
                {skill.name}
                {skill.priority === "high" && (
                  <span className="ml-1 text-xs opacity-70">★</span>
                )}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            Click skills to select for project generation
          </p>
        </div>
      </div>

      {/* Projects */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-display font-semibold text-xl flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber" />
            Recommended Projects ({analysis.recommended_projects.length})
          </h3>
          {selectedSkills.length > 0 && (
            <Button className="bg-gradient-to-r from-primary to-accent hover:opacity-90">
              Generate for Selected ({selectedSkills.length})
            </Button>
          )}
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          {analysis.recommended_projects.map((project, index) => (
            <ProjectCard key={project.id} project={project} index={index} />
          ))}
        </div>
      </div>

      {/* Reset Button */}
      <div className="text-center pt-4">
        <Button
          variant="outline"
          onClick={onReset}
          className="rounded-xl px-8"
        >
          Start New Analysis
        </Button>
      </div>
    </div>
  );
}
