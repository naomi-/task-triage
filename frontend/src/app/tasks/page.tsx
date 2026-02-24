"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Circle, Clock, LayoutGrid, Search, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

export default function TasksPage() {
    const [tasks, setTasks] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function loadTasks() {
            try {
                const data = await fetchApi("/api/tasks/");
                setTasks(data.tasks);
            } catch (err) {
                console.error("Failed to load tasks:", err);
            } finally {
                setIsLoading(false);
            }
        }
        loadTasks();
    }, []);

    if (isLoading) {
        return <div className="animate-pulse py-12 text-center text-muted-foreground">Opening your task collection...</div>;
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="flex items-center justify-between">
                <h1 className="text-4xl font-extrabold tracking-tight">Your Tasks</h1>
                <button className="flex items-center gap-2 bg-secondary text-secondary-foreground px-6 py-3 rounded-full font-semibold hover:bg-secondary/80 transition-all">
                    <Plus className="w-5 h-5" />
                    Quick Add
                </button>
            </div>

            <div className="flex gap-4 border-b pb-4 overflow-x-auto no-scrollbar">
                {["ALL", "INBOX", "NEXT", "WAITING", "LATER", "DONE"].map((tab) => (
                    <button
                        key={tab}
                        className={cn(
                            "px-4 py-2 rounded-full text-sm font-bold transition-all whitespace-nowrap",
                            tab === "ALL" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-muted/80"
                        )}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {tasks.map((task) => (
                    <div key={task.id} className="group bg-white border border-border/60 p-6 rounded-2xl hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 transition-all">
                        <div className="flex items-start justify-between mb-4">
                            <div className={cn(
                                "w-10 h-10 rounded-xl flex items-center justify-center",
                                task.status === "NEXT" ? "bg-accent/10 text-accent" : "bg-muted text-muted-foreground"
                            )}>
                                {task.status === "DONE" ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5" />}
                            </div>
                            <div className="flex gap-1">
                                {[...Array(3)].map((_, i) => (
                                    <div key={i} className={cn("w-1.5 h-1.5 rounded-full", i < (task.priority === "HIGH" ? 3 : task.priority === "MEDIUM" ? 2 : 1) ? "bg-accent" : "bg-muted")} />
                                ))}
                            </div>
                        </div>

                        <h3 className="font-bold text-lg mb-2 group-hover:text-primary transition-colors">{task.title}</h3>
                        <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed h-10">
                            {task.description || "No description provided."}
                        </p>

                        <div className="mt-6 pt-6 border-t flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                            <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {task.effort || "Unknown"} Effort
                            </span>
                            <span className="bg-muted px-2 py-0.5 rounded italic">
                                {task.status}
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            {tasks.length === 0 && (
                <div className="py-24 text-center space-y-4 bg-muted/20 border-2 border-dashed rounded-3xl">
                    <LayoutGrid className="w-12 h-12 mx-auto text-muted-foreground/40" />
                    <p className="text-muted-foreground font-medium">No tasks found. Try running a brain dump!</p>
                </div>
            )}
        </div>
    );
}
