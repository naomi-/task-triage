"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderGit2, ArrowRight } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function ProjectsPage() {
    const [projects, setProjects] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function loadProjects() {
            try {
                const data = await fetchApi("/api/projects/");
                setProjects(data.projects);
            } catch (err) {
                console.error("Failed to load projects:", err);
            } finally {
                setIsLoading(false);
            }
        }
        loadProjects();
    }, []);

    if (isLoading) {
        return <div className="animate-pulse py-12 text-center text-muted-foreground">Loading your projects...</div>;
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 pb-24">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight mb-2">Projects</h1>
                    <p className="text-muted-foreground text-lg">Tracks outcomes that require more than one step.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects.map((project) => (
                    <Link href={`/projects/${project.id}`} key={project.id}>
                        <div className="group bg-white border border-border/60 p-6 rounded-2xl hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5 transition-all h-full flex flex-col cursor-pointer">
                            <div className="flex items-start justify-between mb-4">
                                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-primary/10 text-primary">
                                    <FolderGit2 className="w-5 h-5" />
                                </div>
                                <span className="text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-muted text-muted-foreground">
                                    {project.status}
                                </span>
                            </div>

                            <h3 className="font-bold text-xl mb-2 leading-tight group-hover:text-primary transition-colors">{project.name}</h3>

                            {project.outcome && (
                                <p className="text-muted-foreground line-clamp-2 leading-relaxed flex-grow">
                                    {project.outcome}
                                </p>
                            )}

                            <div className="mt-6 pt-5 border-t border-border/60 flex items-center justify-between font-semibold text-muted-foreground group-hover:text-primary transition-colors">
                                <span className="text-sm">
                                    {project.task_count} Task{project.task_count !== 1 ? 's' : ''}
                                </span>
                                <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                            </div>
                        </div>
                    </Link>
                ))}
            </div>

            {projects.length === 0 && (
                <div className="py-24 text-center space-y-4 bg-white border border-border/60 rounded-3xl shadow-sm">
                    <FolderGit2 className="w-12 h-12 mx-auto text-muted-foreground/30" />
                    <p className="text-muted-foreground font-medium text-lg">No active projects yet.</p>
                </div>
            )}
        </div>
    );
}
