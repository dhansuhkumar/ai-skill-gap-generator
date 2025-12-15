import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface JobReadinessChartProps {
  percentage: number;
}

export function JobReadinessChart({ percentage }: JobReadinessChartProps) {
  const [animatedPercentage, setAnimatedPercentage] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedPercentage(percentage);
    }, 300);
    return () => clearTimeout(timer);
  }, [percentage]);

  const getStatusColor = () => {
    if (percentage >= 80) return "text-emerald";
    if (percentage >= 50) return "text-amber";
    return "text-rose";
  };

  const getStatusText = () => {
    if (percentage >= 80) return "Job Ready!";
    if (percentage >= 50) return "On Track";
    return "Getting Started";
  };

  const getGradient = () => {
    if (percentage >= 80) return "from-emerald to-cyan";
    if (percentage >= 50) return "from-amber to-rose";
    return "from-rose to-accent";
  };

  const circumference = 2 * Math.PI * 90;
  const strokeDashoffset = circumference - (animatedPercentage / 100) * circumference;

  return (
    <div className="flex flex-col md:flex-row items-center gap-8">
      {/* Circular progress */}
      <div className="relative w-48 h-48">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
          {/* Background circle */}
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            className="text-muted"
          />
          {/* Progress circle */}
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="url(#progressGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
          />
          {/* Gradient definition */}
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="hsl(var(--primary))" />
              <stop offset="100%" stopColor="hsl(var(--accent))" />
            </linearGradient>
          </defs>
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("font-display text-4xl font-bold", getStatusColor())}>
            {animatedPercentage}%
          </span>
          <span className="text-sm text-muted-foreground">Match</span>
        </div>
      </div>

      {/* Status and details */}
      <div className="flex-1 text-center md:text-left">
        <div
          className={cn(
            "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold mb-4 bg-gradient-to-r text-primary-foreground",
            getGradient()
          )}
        >
          {getStatusText()}
        </div>
        
        <p className="text-muted-foreground mb-4">
          Based on your skills and the target role requirements, you're{" "}
          <span className="font-semibold text-foreground">{percentage}%</span> ready
          for this position.
        </p>

        <div className="flex flex-wrap gap-2 justify-center md:justify-start">
          {percentage < 100 && (
            <span className="text-sm text-muted-foreground">
              Focus on the high-priority skills to close the gap faster.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
