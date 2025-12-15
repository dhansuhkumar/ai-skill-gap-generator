import { useState } from "react";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StepIndicator } from "./StepIndicator";
import { SkillInput } from "./SkillInput";
import { ResumeUpload } from "./ResumeUpload";
import { RoleSelector } from "./RoleSelector";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import type { SkillGapAnalysisResponse } from "@/lib/types";

interface WizardFormProps {
  onComplete: (data: { skills: string[]; role: string; analysis: SkillGapAnalysisResponse }) => void;
  onBack: () => void;
}

const steps = ["Your Skills", "Target Role", "Analyze"];

export function WizardForm({ onComplete, onBack }: WizardFormProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [skills, setSkills] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState("");
  const [includeYoutube, setIncludeYoutube] = useState(true);
  const [rawProfile, setRawProfile] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleSkillsExtracted = (extractedSkills: string[]) => {
    setSkills((prev) => [...new Set([...prev, ...extractedSkills])]);
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleAnalyze();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    } else {
      onBack();
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const analysis = await api.getRecommendations({
        skills,
        role: selectedRole,
        include_youtube: includeYoutube,
        raw_profile: rawProfile || undefined,
      });
      onComplete({ skills, role: selectedRole, analysis });
    } catch (error) {
      toast({
        title: "Analysis failed",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const isNextDisabled = () => {
    if (currentStep === 0) return skills.length === 0;
    if (currentStep === 1) return !selectedRole;
    return false;
  };

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <StepIndicator steps={steps} currentStep={currentStep} />

      <div className="glass rounded-2xl p-6 md:p-8">
        {/* Step 1: Skills */}
        {currentStep === 0 && (
          <div className="space-y-8 animate-fade-in">
            <div>
              <h2 className="font-display text-2xl font-bold mb-2">
                What skills do you have?
              </h2>
              <p className="text-muted-foreground">
                Add your technical skills or upload your resume
              </p>
            </div>

            <SkillInput skills={skills} onSkillsChange={setSkills} />

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-card px-4 text-sm text-muted-foreground">
                  or upload resume
                </span>
              </div>
            </div>

            <ResumeUpload onSkillsExtracted={handleSkillsExtracted} />
          </div>
        )}

        {/* Step 2: Role Selection */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <h2 className="font-display text-2xl font-bold mb-2">
                What's your target role?
              </h2>
              <p className="text-muted-foreground">
                Select the role you want to pursue
              </p>
            </div>

            <RoleSelector
              selectedRole={selectedRole}
              onRoleChange={setSelectedRole}
            />
          </div>
        )}

        {/* Step 3: Additional Options & Analyze */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <h2 className="font-display text-2xl font-bold mb-2">
                Ready to analyze!
              </h2>
              <p className="text-muted-foreground">
                Configure additional options and start analysis
              </p>
            </div>

            {/* Summary */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 border border-border/50">
              <p className="text-sm text-muted-foreground mb-2">Summary</p>
              <p className="font-semibold">
                {skills.length} skills → {selectedRole}
              </p>
            </div>

            {/* Options */}
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-muted/50">
                <Label htmlFor="youtube" className="flex flex-col gap-1">
                  <span className="font-medium">Include YouTube Videos</span>
                  <span className="text-sm text-muted-foreground">
                    Get video tutorials with project recommendations
                  </span>
                </Label>
                <Switch
                  id="youtube"
                  checked={includeYoutube}
                  onCheckedChange={setIncludeYoutube}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rawProfile">
                  Additional context (optional)
                </Label>
                <Textarea
                  id="rawProfile"
                  value={rawProfile}
                  onChange={(e) => setRawProfile(e.target.value)}
                  placeholder="Add any additional context about your experience, goals, or preferences..."
                  className="min-h-[100px] rounded-xl resize-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-border">
          <Button
            variant="ghost"
            onClick={handlePrev}
            className="rounded-xl"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {currentStep === 0 ? "Home" : "Back"}
          </Button>

          <Button
            onClick={handleNext}
            disabled={isNextDisabled() || isAnalyzing}
            className="rounded-xl bg-gradient-to-r from-primary to-accent hover:opacity-90 px-8"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : currentStep === steps.length - 1 ? (
              "Analyze My Skills"
            ) : (
              <>
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
