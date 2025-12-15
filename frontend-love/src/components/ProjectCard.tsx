import { useState } from "react";
import { ChevronDown, Play, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecommendedProject } from "@/lib/types";

interface ProjectCardProps {
  project: RecommendedProject;
  index: number;
}

const cardColors = [
  "from-cyan/20 to-sky/10 border-cyan/30",
  "from-purple/20 to-primary/10 border-purple/30",
  "from-rose/20 to-accent/10 border-rose/30",
  "from-emerald/20 to-cyan/10 border-emerald/30",
  "from-amber/20 to-rose/10 border-amber/30",
];

export function ProjectCard({ project, index }: ProjectCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const firstVideo = project.videos?.[0];

  return (
    <div
      className={cn(
        "rounded-2xl p-6 border transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br animate-fade-in-up",
        cardColors[index % cardColors.length]
      )}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Skill badge */}
      <span className="inline-block px-3 py-1 rounded-full bg-background/50 text-sm font-medium mb-3">
        {project.skill}
      </span>

      {/* Title */}
      <h4 className="font-display font-semibold text-lg mb-4">{project.title}</h4>

      {/* Learning steps */}
      {project.learning_path_steps && project.learning_path_steps.length > 0 && (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-primary mb-3 hover:underline"
          >
            <span>{isExpanded ? "Hide" : "Show"} Learning Path</span>
            <ChevronDown
              className={cn(
                "w-4 h-4 transition-transform duration-300",
                isExpanded && "rotate-180"
              )}
            />
          </button>

          <div
            className={cn(
              "overflow-hidden transition-all duration-300",
              isExpanded ? "max-h-96" : "max-h-0"
            )}
          >
            <ol className="space-y-3 mb-4">
              {project.learning_path_steps.map((step, stepIndex) => (
                <li key={stepIndex} className="flex gap-3 text-sm">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary font-semibold flex items-center justify-center text-xs">
                    {stepIndex + 1}
                  </span>
                  <span className="text-muted-foreground">{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </>
      )}

      {/* Video link */}
      {firstVideo && (
        <a
          href={firstVideo.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 p-3 rounded-xl bg-background/50 hover:bg-background/80 transition-colors group"
        >
          {firstVideo.thumbnail ? (
            <img
              src={firstVideo.thumbnail}
              alt={firstVideo.title}
              className="w-10 h-10 rounded-lg object-cover"
            />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-rose flex items-center justify-center">
              <Play className="w-4 h-4 text-primary-foreground" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{firstVideo.title}</p>
            <p className="text-xs text-muted-foreground">YouTube Tutorial</p>
          </div>
          <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
        </a>
      )}
    </div>
  );
}
