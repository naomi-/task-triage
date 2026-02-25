"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, Circle, Clock, AlertTriangle, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

export default function ProjectDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [projectData, setProjectData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadProject() {
            try {
                const data = await fetchApi(`/api/projects/${params.id}/`);
                setProjectData(data.project);
            } catch (err: any) {
                console.error("Failed to load project:", err);
                setError(err.message || "Failed to load project details");
            } finally {
                setIsLoading(false);
            }
        }
        if (params.id) loadProject();
    }, [params.id]);

    const handleStatusChange = async (taskId: string, newStatus: string) => {
        if (!projectData) return;

        // Optimistic update
        const originalTasks = [...projectData.tasks];
        setProjectData({
            ...projectData,
            tasks: projectData.tasks.map((t: any) => t.id === taskId ? { ...t, status: newStatus } : t)
        });

        try {
            await fetchApi(`/api/tasks/${taskId}/status/`, {
                method: "PATCH",
                body: JSON.stringify({ status: newStatus })
            });
        } catch (err) {
            console.error("Failed to update status:", err);
            setProjectData({ ...projectData, tasks: originalTasks });
            alert("Failed to update task status.");
        }
    };

    if (isLoading) {
        return <div className="animate-pulse py-12 text-center text-muted-foreground">Loading project details...</div>;
    }

    if (error || !projectData) {
        return (
            <div className="py-24 text-center space-y-4">
                <p className="text-destructive font-bold">{error || "Project not found"}</p>
                <button onClick={() => router.push("/projects")} className="text-primary hover:underline">
                    Back to Projects
                </button>
            </div>
        );
    }

    const tasks = projectData.tasks || [];
    const hasNextAction = tasks.some((t: any) => t.status === "NEXT");
    const STATUSES = ["INBOX", "NEXT", "IN_PROGRESS", "WAITING", "SOMEDAY", "DONE"];

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 pb-24">
            <button
                onClick={() => router.push("/projects")}
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors font-medium text-sm"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Projects
            </button>

            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-border/60">
                <div className="space-y-2">
                    <span className="text-sm font-bold uppercase tracking-widest text-primary">Project</span>
                    <h1 className="text-4xl font-extrabold tracking-tight">{projectData.name}</h1>
                    {projectData.outcome && (
                        <p className="text-lg text-muted-foreground mt-2 max-w-2xl">{projectData.outcome}</p>
                    )}
                </div>
                <div className="shrink-0 bg-white border border-border/60 px-6 py-4 rounded-xl shadow-sm text-center">
                    <div className="text-3xl font-black text-foreground">{tasks.length}</div>
                    <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mt-1">Total Tasks</div>
                </div>
            </div>

            {!hasNextAction && tasks.filter((t: any) => t.status !== "DONE").length > 0 && (
                <div className="bg-amber-50 border border-amber-200 p-6 rounded-2xl flex items-start gap-4">
                    <AlertTriangle className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
                    <div>
                        <h3 className="font-bold text-amber-900 text-lg">Stalled Project Warning</h3>
                        <p className="text-amber-800 leading-relaxed mt-1">
                            This project has no tasks marked as <strong>NEXT</strong>. To keep momentum, review the tasks below or add a new action step to move this project forward.
                        </p>
                    </div>
                </div>
            )}

            <div className="space-y-6">
                <h2 className="text-2xl font-bold tracking-tight">Tasks in this Project</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {tasks.map((task: any) => (
                        <div key={task.id} className={cn(
                            "group bg-white border border-border/60 p-6 rounded-2xl transition-all relative",
                            task.status === "DONE" ? "opacity-70 grayscale-[0.5]" : "hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5"
                        )}>
                            <div className="flex items-start justify-between mb-4">
                                <select
                                    value={task.status}
                                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                                    className={cn(
                                        "text-xs font-bold uppercase tracking-widest px-3 py-1.5 rounded-full outline-none cursor-pointer appearance-none transition-colors",
                                        task.status === "NEXT" ? "bg-accent/15 text-accent-dark border border-accent/20" :
                                            task.status === "DONE" ? "bg-green-100 text-green-700 border border-green-200" :
                                                "bg-muted text-muted-foreground border border-transparent"
                                    )}
                                >
                                    {STATUSES.map(s => (
                                        <option key={s} value={s}>{s.replace("_", " ")}</option>
                                    ))}
                                </select>

                                <div className="flex gap-1" title={`Priority: ${task.priority}`}>
                                    {[...Array(3)].map((_, i) => (
                                        <div key={i} className={cn("w-1.5 h-1.5 rounded-full",
                                            i < (task.priority >= 4 ? 3 : task.priority >= 3 ? 2 : 1) ? "bg-primary/80" : "bg-muted"
                                        )} />
                                    ))}
                                </div>
                            </div>

                            <h3 className="font-bold text-lg mb-2 leading-tight group-hover:text-primary transition-colors">{task.title}</h3>
                            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed h-10 mb-4">
                                {task.description || task.next_action || "No description."}
                            </p>

                            <div className="mt-6 pt-5 border-t border-border/60 flex items-center justify-between text-xs font-semibold text-muted-foreground">
                                <span className="flex items-center gap-1.5">
                                    <Clock className="w-3.5 h-3.5" />
                                    {task.effort || "XS"} Effort
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {tasks.length === 0 && (
                    <div className="py-12 border-2 border-dashed border-border/60 rounded-3xl text-center text-muted-foreground font-medium">
                        No tasks are linked to this project yet.
                    </div>
                )}
            </div>
        </div>
    );
}
