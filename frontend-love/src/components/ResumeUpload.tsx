import { useState, useCallback } from "react";
import { Upload, FileText, CheckCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

interface ResumeUploadProps {
  onSkillsExtracted: (skills: string[]) => void;
}

export function ResumeUpload({ onSkillsExtracted }: ResumeUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  }, []);

  const processFile = async (uploadedFile: File) => {
    setFile(uploadedFile);
    setIsUploading(true);
    
    try {
      const response = await api.uploadResume(uploadedFile);
      onSkillsExtracted(response.skills);
      setIsSuccess(true);
    } catch (error) {
      toast({
        title: "Failed to process resume",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
      setFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type === "application/pdf" || droppedFile.name.endsWith(".pdf"))) {
      processFile(droppedFile);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={cn(
        "relative border-2 border-dashed rounded-2xl p-8 transition-all duration-300 cursor-pointer",
        isDragging
          ? "border-primary bg-primary/5 scale-[1.02]"
          : isSuccess
          ? "border-emerald bg-emerald/5"
          : "border-border hover:border-primary/50 hover:bg-muted/50"
      )}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileSelect}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      <div className="flex flex-col items-center justify-center text-center">
        {isUploading ? (
          <>
            <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
            <p className="font-semibold text-foreground">Extracting skills...</p>
            <p className="text-sm text-muted-foreground mt-1">
              AI is analyzing your resume
            </p>
          </>
        ) : isSuccess ? (
          <>
            <CheckCircle className="w-12 h-12 text-emerald mb-4" />
            <p className="font-semibold text-foreground">Skills extracted!</p>
            <p className="text-sm text-muted-foreground mt-1">
              {file?.name}
            </p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-4">
              {file ? (
                <FileText className="w-8 h-8 text-primary" />
              ) : (
                <Upload className="w-8 h-8 text-primary" />
              )}
            </div>
            <p className="font-semibold text-foreground">
              Drop your resume here
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              or click to browse (PDF only)
            </p>
          </>
        )}
      </div>

      {/* Upload progress bar */}
      {isUploading && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-muted overflow-hidden rounded-b-2xl">
          <div className="h-full bg-gradient-to-r from-primary to-accent animate-progress" />
        </div>
      )}
    </div>
  );
}
