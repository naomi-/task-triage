"use client";

import { useEffect, useState, useMemo } from "react";
import { CheckCircle2, Circle, Clock, LayoutGrid, AlertCircle, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

const STATUSES = ["ALL", "INBOX", "NEXT", "IN_PROGRESS", "WAITING", "SOMEDAY", "DONE"];

export default function TasksPage() {
    const [tasks, setTasks] = useState<any[]>([]);
    const [projects, setProjects] = useState<any[]>([]);
    const [areas, setAreas] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const [activeTab, setActiveTab] = useState("ALL");
    const [filterProject, setFilterProject] = useState("");
    const [filterArea, setFilterArea] = useState("");
    const [filterEffort, setFilterEffort] = useState("");

    useEffect(() => {
        async function loadData() {
            try {
                const data = await fetchApi("/api/tasks/");
                setTasks(data.tasks);
                setProjects(data.projects || []);
                setAreas(data.areas || []);
            } catch (err) {
                console.error("Failed to load tasks:", err);
            } finally {
                setIsLoading(false);
            }
        }
        loadData();
    }, []);

    const filteredTasks = useMemo(() => {
        return tasks.filter(task => {
            if (activeTab !== "ALL" && task.status !== activeTab) return false;
            if (filterProject && task.project_id !== filterProject) return false;
            if (filterArea && task.area_id !== filterArea) return false;
            if (filterEffort && task.effort !== filterEffort) return false;
            return true;
        });
    }, [tasks, activeTab, filterProject, filterArea, filterEffort]);

    const handleStatusChange = async (taskId: string, newStatus: string) => {
        // Optimistic update
        const originalTasks = [...tasks];
        setTasks(tasks.map(t => t.id === taskId ? { ...t, status: newStatus } : t));

        try {
            await fetchApi(`/api/tasks/${taskId}/status/`, {
                method: "PATCH",
                body: JSON.stringify({ status: newStatus })
            });
        } catch (err) {
            console.error("Failed to update status:", err);
            setTasks(originalTasks); // Revert on failure
            alert("Failed to update task status.");
        }
    };

    if (isLoading) {
        return <div className="animate-pulse py-12 text-center text-muted-foreground">Opening your task collection...</div>;
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 pb-24">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight mb-2">Your Tasks</h1>
                    <p className="text-muted-foreground text-lg">Manage your organized actions and get things done.</p>
                </div>
                <button className="flex items-center gap-2 bg-secondary text-secondary-foreground px-6 py-3 rounded-full font-semibold hover:bg-secondary/80 transition-all shrink-0">
                    <Plus className="w-5 h-5" />
                    Quick Add
                </button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-white p-4 rounded-2xl border border-border/60 shadow-sm">
                <select
                    className="bg-transparent border-none focus:ring-0 text-foreground cursor-pointer"
                    value={filterProject}
                    onChange={(e) => setFilterProject(e.target.value)}
                >
                    <option value="">All Projects</option>
                    {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>

                <select
                    className="bg-transparent border-none focus:ring-0 text-foreground cursor-pointer border-l-0 sm:border-l border-border/60"
                    value={filterArea}
                    onChange={(e) => setFilterArea(e.target.value)}
                >
                    <option value="">All Areas</option>
                    {areas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>

                <select
                    className="bg-transparent border-none focus:ring-0 text-foreground cursor-pointer border-l-0 sm:border-l border-border/60"
                    value={filterEffort}
                    onChange={(e) => setFilterEffort(e.target.value)}
                >
                    <option value="">Any Effort</option>
                    {["XS", "S", "M", "L", "XL"].map(e => <option key={e} value={e}>{e}</option>)}
                </select>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-border/60 pb-4 overflow-x-auto no-scrollbar scroll-smooth">
                {STATUSES.map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={cn(
                            "px-5 py-2.5 rounded-full text-sm font-bold transition-all whitespace-nowrap tracking-wide",
                            activeTab === tab
                                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20 scale-100"
                                : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground scale-95"
                        )}
                    >
                        {tab.replace("_", " ")}
                    </button>
                ))}
            </div>

            {/* Task Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredTasks.map((task) => (
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
                                {STATUSES.filter(s => s !== "ALL").map(s => (
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

                        <h3 className="font-bold text-lg mb-2 leading-tight group-hover:text-primary transition-colors pr-4">{task.title}</h3>

                        {(task.description || task.next_action) && (
                            <div className="space-y-3 mt-4">
                                {task.next_action && (
                                    <div className="bg-accent/5 border border-accent/10 rounded-lg p-3 text-sm flex gap-2 items-start">
                                        <AlertCircle className="w-4 h-4 text-accent mt-0.5 shrink-0" />
                                        <p className="text-accent-dark font-medium leading-relaxed">{task.next_action}</p>
                                    </div>
                                )}
                                {task.description && (
                                    <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed h-10">
                                        {task.description}
                                    </p>
                                )}
                            </div>
                        )}

                        <div className="mt-6 pt-5 border-t border-border/60 flex items-center justify-between text-xs font-semibold text-muted-foreground">
                            <span className="flex items-center gap-1.5">
                                <Clock className="w-3.5 h-3.5" />
                                {task.effort || "XS"} Effort
                            </span>

                            {(task.project_name || task.area_name) && (
                                <span className="opacity-70 truncate max-w-[120px] text-right" title={task.project_name || task.area_name}>
                                    {task.project_name || task.area_name}
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {filteredTasks.length === 0 && (
                <div className="py-24 text-center space-y-4 bg-white border border-border/60 rounded-3xl shadow-sm">
                    <LayoutGrid className="w-12 h-12 mx-auto text-muted-foreground/30" />
                    <p className="text-muted-foreground font-medium text-lg">No tasks found for these filters.</p>
                </div>
            )}
        </div>
    );
}
