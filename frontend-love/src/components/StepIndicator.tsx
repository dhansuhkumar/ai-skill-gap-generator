import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-2 md:gap-4 mb-8">
      {steps.map((step, index) => (
        <div key={step} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all duration-500",
                index < currentStep
                  ? "bg-gradient-to-br from-emerald to-cyan text-primary-foreground"
                  : index === currentStep
                  ? "bg-gradient-to-br from-primary to-accent text-primary-foreground animate-pulse-glow"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {index < currentStep ? (
                <Check className="w-5 h-5" />
              ) : (
                index + 1
              )}
            </div>
            <span
              className={cn(
                "text-xs mt-2 font-medium hidden md:block",
                index <= currentStep ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {step}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={cn(
                "w-12 md:w-20 h-1 mx-2 rounded-full transition-all duration-500",
                index < currentStep
                  ? "bg-gradient-to-r from-emerald to-cyan"
                  : "bg-muted"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
