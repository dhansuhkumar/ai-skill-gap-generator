import { useState } from "react";
import { Search, Briefcase, Code, Brain, Database, Cloud, Palette } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface RoleSelectorProps {
  selectedRole: string;
  onRoleChange: (role: string) => void;
}

const popularRoles = [
  { id: "software-engineer", name: "Software Engineer", icon: Code, color: "from-cyan to-sky" },
  { id: "data-scientist", name: "Data Scientist", icon: Brain, color: "from-purple to-primary" },
  { id: "ml-engineer", name: "ML Engineer", icon: Database, color: "from-rose to-accent" },
  { id: "devops-engineer", name: "DevOps Engineer", icon: Cloud, color: "from-emerald to-cyan" },
  { id: "frontend-dev", name: "Frontend Developer", icon: Palette, color: "from-amber to-rose" },
  { id: "fullstack-dev", name: "Full Stack Developer", icon: Briefcase, color: "from-sky to-purple" },
];

export function RoleSelector({ selectedRole, onRoleChange }: RoleSelectorProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredRoles = popularRoles.filter((role) =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search for a role..."
          className="pl-12 h-12 rounded-xl border-2 border-border focus:border-primary transition-colors"
        />
      </div>

      {/* Role grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {filteredRoles.map((role) => (
          <button
            key={role.id}
            onClick={() => onRoleChange(role.name)}
            className={cn(
              "relative p-6 rounded-2xl transition-all duration-300 text-left group",
              selectedRole === role.name
                ? "bg-gradient-to-br " + role.color + " text-primary-foreground scale-[1.02] shadow-lg"
                : "glass hover:scale-[1.02]"
            )}
          >
            <role.icon
              className={cn(
                "w-8 h-8 mb-3",
                selectedRole === role.name ? "text-primary-foreground" : "text-primary"
              )}
            />
            <p
              className={cn(
                "font-semibold",
                selectedRole === role.name ? "text-primary-foreground" : "text-foreground"
              )}
            >
              {role.name}
            </p>
            
            {selectedRole === role.name && (
              <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary-foreground/20 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-primary-foreground" />
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Custom role input */}
      <div className="glass rounded-xl p-4">
        <p className="text-sm text-muted-foreground mb-2">Or enter a custom role:</p>
        <Input
          value={!popularRoles.find(r => r.name === selectedRole) ? selectedRole : ""}
          onChange={(e) => onRoleChange(e.target.value)}
          placeholder="e.g., AI Research Scientist"
          className="h-12 rounded-xl border-2 border-border focus:border-primary transition-colors"
        />
      </div>
    </div>
  );
}
