import { useState, KeyboardEvent } from "react";
import { X, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface SkillInputProps {
  skills: string[];
  onSkillsChange: (skills: string[]) => void;
}

const skillColors = [
  "from-cyan to-sky",
  "from-purple to-primary",
  "from-rose to-accent",
  "from-emerald to-cyan",
  "from-amber to-rose",
  "from-sky to-purple",
];

export function SkillInput({ skills, onSkillsChange }: SkillInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addSkill = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !skills.includes(trimmed)) {
      onSkillsChange([...skills, trimmed]);
      setInputValue("");
    }
  };

  const removeSkill = (skillToRemove: string) => {
    onSkillsChange(skills.filter((skill) => skill !== skillToRemove));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a skill and press Enter..."
          className="flex-1 h-12 rounded-xl border-2 border-border focus:border-primary transition-colors"
        />
        <button
          onClick={addSkill}
          className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center hover:opacity-90 transition-opacity"
        >
          <Plus className="w-5 h-5 text-primary-foreground" />
        </button>
      </div>

      <div className="flex flex-wrap gap-2 min-h-[48px]">
        {skills.map((skill, index) => (
          <div
            key={skill}
            className={cn(
              "group inline-flex items-center gap-2 px-4 py-2 rounded-full text-primary-foreground font-medium text-sm animate-scale-in bg-gradient-to-r",
              skillColors[index % skillColors.length]
            )}
          >
            {skill}
            <button
              onClick={() => removeSkill(skill)}
              className="w-5 h-5 rounded-full bg-primary-foreground/20 flex items-center justify-center hover:bg-primary-foreground/30 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
        {skills.length === 0 && (
          <p className="text-muted-foreground text-sm italic">
            Add your skills above or upload a resume
          </p>
        )}
      </div>
    </div>
  );
}
