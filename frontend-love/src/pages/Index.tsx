import { useState } from "react";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { FloatingBubbles } from "@/components/FloatingBubbles";
import { WizardForm } from "@/components/WizardForm";
import { SkillGapResults } from "@/components/SkillGapResults";
import type { SkillGapAnalysisResponse } from "@/lib/types";

type AppState = "hero" | "wizard" | "results";

interface AnalysisData {
  skills: string[];
  role: string;
  analysis: SkillGapAnalysisResponse;
}

const Index = () => {
  const [appState, setAppState] = useState<AppState>("hero");
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);

  const handleGetStarted = () => {
    setAppState("wizard");
  };

  const handleWizardComplete = (data: AnalysisData) => {
    setAnalysisData(data);
    setAppState("results");
  };

  const handleReset = () => {
    setAnalysisData(null);
    setAppState("hero");
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <FloatingBubbles />
      <Header />
      
      <main className="relative z-10 pt-16">
        {appState === "hero" && (
          <HeroSection onGetStarted={handleGetStarted} />
        )}

        {appState === "wizard" && (
          <div className="container mx-auto px-4 py-12">
            <WizardForm
              onComplete={handleWizardComplete}
              onBack={() => setAppState("hero")}
            />
          </div>
        )}

        {appState === "results" && analysisData && (
          <div className="container mx-auto px-4 py-12">
            <SkillGapResults
              skills={analysisData.skills}
              role={analysisData.role}
              analysis={analysisData.analysis}
              onReset={handleReset}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;
