import { cn } from "@/lib/utils";

const bubbles = [
  { skill: "Python", color: "from-cyan to-sky", size: "w-20 h-20", position: "top-20 left-[10%]", delay: "0s" },
  { skill: "React", color: "from-purple to-primary", size: "w-16 h-16", position: "top-40 right-[15%]", delay: "1s" },
  { skill: "AI/ML", color: "from-rose to-accent", size: "w-24 h-24", position: "top-60 left-[5%]", delay: "2s" },
  { skill: "Data", color: "from-emerald to-cyan", size: "w-14 h-14", position: "bottom-40 right-[10%]", delay: "1.5s" },
  { skill: "Cloud", color: "from-amber to-rose", size: "w-18 h-18", position: "bottom-60 left-[20%]", delay: "0.5s" },
  { skill: "DevOps", color: "from-sky to-purple", size: "w-12 h-12", position: "top-32 left-[30%]", delay: "2.5s" },
];

export function FloatingBubbles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {bubbles.map((bubble, i) => (
        <div
          key={i}
          className={cn(
            "absolute rounded-full bg-gradient-to-br opacity-20 blur-sm",
            bubble.color,
            bubble.size,
            bubble.position,
            "animate-float-slow"
          )}
          style={{ animationDelay: bubble.delay }}
        />
      ))}
      {/* Mesh gradient background */}
      <div className="absolute inset-0 mesh-background opacity-50" />
    </div>
  );
}
