"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Check, X, ChevronRight, Edit3, Save, Trash2, LayoutGrid, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

interface Suggestion {
    id: string;
    suggestion_type: string;
    title?: string;
    name?: string;
    status?: string;
    priority?: string;
    urgency?: string;
    effort?: string;
    description?: string;
    outcome?: string;
    [key: string]: any;
}

export default function TriageReviewPage() {
    const { session_id } = useParams();
    const router = useRouter();
    const [session, setSession] = useState<any>(null);
    const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isApplying, setIsApplying] = useState(false);
    const [decisions, setDecisions] = useState<Record<string, { action: "accept" | "reject"; edited_data?: any }>>({});

    useEffect(() => {
        async function loadData() {
            try {
                const data = await fetchApi(`/api/triage/${session_id}/`);
                setSession(data.session);
                setSuggestions(data.suggestions);

                // Default all to accept
                const initialDecisions: any = {};
                data.suggestions.forEach((s: Suggestion) => {
                    initialDecisions[s.id] = { action: "accept", edited_data: { ...s } };
                });
                setDecisions(initialDecisions);
            } catch (err) {
                console.error("Failed to load triage session:", err);
            } finally {
                setIsLoading(false);
            }
        }
        loadData();
    }, [session_id]);

    const handleToggleAction = (id: string) => {
        setDecisions(prev => ({
            ...prev,
            [id]: {
                ...prev[id],
                action: prev[id].action === "accept" ? "reject" : "accept"
            }
        }));
    };

    const handleEdit = (id: string, field: string, value: string) => {
        setDecisions(prev => ({
            ...prev,
            [id]: {
                ...prev[id],
                edited_data: {
                    ...prev[id].edited_data,
                    [field]: value
                }
            }
        }));
    };

    const handleApply = async () => {
        setIsApplying(true);
        try {
            const payload = Object.entries(decisions).map(([id, dec]) => ({
                id,
                action: dec.action,
                edited_data: dec.edited_data
            }));

            await fetchApi("/api/triage/apply/", {
                method: "POST",
                body: JSON.stringify({ session_id, decisions: payload }),
            });

            router.push("/tasks");
        } catch (err) {
            console.error("Apply failed:", err);
            setIsApplying(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 space-y-6">
                <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                <p className="text-muted-foreground animate-pulse text-lg">Gathering your thoughts...</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-32">
            <div className="flex items-end justify-between border-b pb-6">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">Review Suggestions</h1>
                    <p className="text-muted-foreground italic">&quot;{session?.input_text}&quot;</p>
                </div>
                <div className="text-right text-xs text-muted-foreground font-mono">
                    SESSION ID: {session_id?.slice(0, 8)}...
                </div>
            </div>

            <div className="space-y-6">
                {suggestions.map((s) => {
                    const decision = decisions[s.id];
                    const isAccepted = decision?.action === "accept";

                    return (
                        <div
                            key={s.id}
                            className={cn(
                                "group relative overflow-hidden bg-white border-2 rounded-2xl transition-all",
                                isAccepted
                                    ? "border-border hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
                                    : "border-destructive/20 opacity-40 grayscale-[0.5] scale-[0.98]"
                            )}
                        >
                            <div className="p-6 sm:p-8 flex items-start gap-6">
                                <div className="hidden sm:flex flex-col items-center gap-2">
                                    <div className={cn(
                                        "w-12 h-12 rounded-full flex items-center justify-center transition-colors",
                                        isAccepted ? "bg-primary/10 text-primary" : "bg-destructive/10 text-destructive"
                                    )}>
                                        {s.suggestion_type === "task" ? <CheckCircle2 className="w-6 h-6" /> : <LayoutGrid className="w-6 h-6" />}
                                    </div>
                                    <span className="text-[10px] font-bold uppercase tracking-tighter text-muted-foreground/50">
                                        {s.suggestion_type}
                                    </span>
                                </div>

                                <div className="flex-1 space-y-4">
                                    <div className="space-y-2">
                                        <input
                                            value={decision?.edited_data?.[s.suggestion_type === "task" ? "title" : "name"] || ""}
                                            onChange={(e) => handleEdit(s.id, s.suggestion_type === "task" ? "title" : "name", e.target.value)}
                                            className="w-full text-xl font-bold bg-transparent border-b border-transparent hover:border-muted-foreground/20 focus:border-primary focus:outline-none transition-colors py-1"
                                            placeholder="Enter title..."
                                        />
                                        <textarea
                                            value={decision?.edited_data?.description || decision?.edited_data?.outcome || ""}
                                            onChange={(e) => handleEdit(s.id, s.suggestion_type === "task" ? "description" : "outcome", e.target.value)}
                                            className="w-full text-muted-foreground bg-transparent border-none focus:ring-0 resize-none leading-relaxed h-12 hover:h-auto focus:h-auto transition-all"
                                            placeholder="No description..."
                                        />
                                    </div>

                                    {s.suggestion_type === "task" && (
                                        <div className="flex flex-wrap gap-4 text-sm pt-2">
                                            <div className="flex flex-col gap-1">
                                                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Status</span>
                                                <select
                                                    value={decision?.edited_data?.status || "INBOX"}
                                                    onChange={(e) => handleEdit(s.id, "status", e.target.value)}
                                                    className="bg-muted px-2 py-1 rounded-md text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary"
                                                >
                                                    <option value="INBOX">Inbox</option>
                                                    <option value="NEXT">Next</option>
                                                    <option value="WAITING">Waiting</option>
                                                    <option value="LATER">Later</option>
                                                </select>
                                            </div>
                                            {/* Simplified: more selectors can be added here */}
                                        </div>
                                    )}
                                </div>

                                <div className="flex flex-col gap-2">
                                    <button
                                        onClick={() => handleToggleAction(s.id)}
                                        className={cn(
                                            "w-10 h-10 rounded-full flex items-center justify-center transition-all border",
                                            isAccepted
                                                ? "bg-white border-border text-muted-foreground hover:bg-destructive/10 hover:border-destructive hover:text-destructive"
                                                : "bg-primary text-primary-foreground border-primary hover:bg-primary/90"
                                        )}
                                        title={isAccepted ? "Reject suggestion" : "Accept suggestion"}
                                    >
                                        {isAccepted ? <Trash2 className="w-5 h-5" /> : <Check className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>

                            {!isAccepted && (
                                <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center">
                                    <span className="bg-white/80 border border-destructive/20 text-destructive text-xs font-bold uppercase tracking-widest px-4 py-2 rounded-full shadow-sm">
                                        Rejected
                                    </span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="fixed bottom-0 inset-x-0 bg-white/80 backdrop-blur-xl border-t z-50 py-6">
                <div className="max-w-4xl mx-auto px-4 flex items-center justify-between">
                    <div className="text-sm">
                        <span className="font-bold text-primary">
                            {Object.values(decisions).filter(d => d.action === "accept").length}
                        </span>
                        <span className="text-muted-foreground"> suggestions ready to be applied.</span>
                    </div>
                    <button
                        onClick={handleApply}
                        disabled={isApplying || Object.values(decisions).filter(d => d.action === "accept").length === 0}
                        className="flex items-center gap-2 bg-primary text-primary-foreground px-10 py-4 rounded-full font-bold shadow-xl shadow-primary/20 hover:bg-primary/90 hover:-translate-y-1 active:scale-95 transition-all disabled:opacity-50 disabled:translate-y-0 disabled:shadow-none"
                    >
                        {isApplying ? "Applying..." : "Apply Decisions"}
                        <Save className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
