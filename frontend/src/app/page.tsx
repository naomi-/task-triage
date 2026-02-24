"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

export default function InboxPage() {
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchApi("/api/inbox/", {
        method: "POST",
        body: JSON.stringify({ brain_dump: content }),
      });

      router.push(`/triage/${response.session_id}`);
    } catch (err: any) {
      console.error("Submission failed:", err);
      setError(err.message || "Failed to process brain dump. Are you logged in?");
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-12 py-12">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
          What&apos;s on your mind?
        </h1>
        <p className="text-lg text-muted-foreground max-w-xl mx-auto">
          Just dump everything out. Our AI will help you organize tasks, projects, and areas with peace of mind.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 relative group">
        <div className="relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="I need to fix the dishwasher, call the bank about the mortgage, and maybe plan a trip to Spain next July..."
            className={cn(
              "w-full min-h-[300px] p-8 text-xl bg-white border-2 rounded-2xl shadow-sm transition-all focus:outline-none focus:ring-4 focus:ring-primary/10 resize-none leading-relaxed",
              isLoading ? "opacity-50 blur-[2px]" : "border-border hover:border-accent group-hover:shadow-md"
            )}
            disabled={isLoading}
          />
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                <p className="text-primary font-medium bg-white/80 px-4 py-1 rounded-full backdrop-blur-sm">
                  Sorting out the cozy details...
                </p>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-xl">
            {error}
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || !content.trim()}
            className={cn(
              "flex items-center gap-2 px-8 py-4 text-lg font-semibold rounded-full transition-all shadow-lg active:scale-95",
              content.trim() && !isLoading
                ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-primary/20 hover:-translate-y-0.5"
                : "bg-muted text-muted-foreground cursor-not-allowed shadow-none"
            )}
          >
            {isLoading ? "Processing..." : "Sort it out"}
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </form>

      <div className="flex justify-center gap-12 pt-8 text-muted-foreground/60">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          <span className="text-xs uppercase tracking-widest font-semibold">AI Powered</span>
        </div>
      </div>
    </div>
  );
}
