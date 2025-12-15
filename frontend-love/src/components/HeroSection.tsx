import { ArrowRight, Zap, Target, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeroSectionProps {
  onGetStarted: () => void;
}

export function HeroSection({ onGetStarted }: HeroSectionProps) {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center pt-16">
      <div className="container mx-auto px-4 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8 animate-fade-in">
          <Zap className="w-4 h-4 text-amber" />
          <span className="text-sm font-medium text-muted-foreground">
            AI-Powered Career Analysis
          </span>
        </div>

        {/* Main heading */}
        <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold mb-6 animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
          Discover Your{" "}
          <span className="gradient-text">Skill Gap</span>
          <br />
          <span className="gradient-text-secondary">Bridge to Success</span>
        </h1>

        {/* Subheading */}
        <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
          Upload your resume, select your dream role, and get personalized
          project recommendations to close your skill gaps. Powered by AI.
        </p>

        {/* CTA Button */}
        <div className="animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
          <Button
            size="lg"
            onClick={onGetStarted}
            className="group relative px-8 py-6 text-lg font-semibold rounded-2xl bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-all duration-300 animate-pulse-glow"
          >
            Analyze My Skills
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>

        {/* Feature highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 max-w-4xl mx-auto">
          {[
            {
              icon: Target,
              title: "Smart Analysis",
              description: "AI identifies gaps in your skillset",
              color: "text-cyan",
            },
            {
              icon: TrendingUp,
              title: "Job Readiness",
              description: "See how close you are to your dream role",
              color: "text-purple",
            },
            {
              icon: Zap,
              title: "Project Roadmap",
              description: "Get personalized learning projects",
              color: "text-rose",
            },
          ].map((feature, i) => (
            <div
              key={feature.title}
              className="glass rounded-2xl p-6 hover:scale-105 transition-transform duration-300 animate-fade-in-up"
              style={{ animationDelay: `${0.4 + i * 0.1}s` }}
            >
              <feature.icon className={`w-10 h-10 ${feature.color} mb-4 mx-auto`} />
              <h3 className="font-display font-semibold text-lg mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
