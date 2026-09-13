import { useMemo, useState } from "react";
import { FolderKanban, Plus, Search } from "lucide-react";
import { Link } from "react-router-dom";

import { ProjectForm } from "../components/ProjectForm";
import { useCreateProject, useProjects } from "../hooks";
import { formatProjectPriority, formatProjectStatus, type Project } from "../types";

function matchesSearch(project: Project, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;

  return [
    project.name,
    project.description,
    project.currentVersion,
    project.currentPhase,
    project.currentStep
  ].some((value) => value.toLowerCase().includes(needle));
}

export function ProjectsPage() {
  const projectsQuery = useProjects();
  const createProject = useCreateProject();
  const [query, setQuery] = useState("");
  const [creating, setCreating] = useState(false);

  const projects = useMemo(
    () => (projectsQuery.data ?? []).filter((project) => matchesSearch(project, query)),
    [projectsQuery.data, query]
  );

  return (
    <section className="mc-page">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Workspace</p>
          <h1>Projects</h1>
          <p className="mc-page-description">
            Track the current state and next action for every project.
          </p>
        </div>

        <button className="mc-button mc-button-primary" type="button" onClick={() => setCreating(true)}>
          <Plus size={15} />
          New project
        </button>
      </header>

      <div className="mc-toolbar">
        <label className="mc-search">
          <Search size={15} />
          <input
            aria-label="Search projects"
            placeholder="Search projects..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>

      {projectsQuery.isLoading ? (
        <div className="mc-panel mc-project-empty"><p>Loading projects...</p></div>
      ) : projectsQuery.isError ? (
        <div className="mc-panel mc-project-empty">
          <h2>Could not load projects</h2>
          <p>{String(projectsQuery.error)}</p>
        </div>
      ) : projects.length ? (
        <div className="mc-panel mc-project-table">
          {projects.map((project) => (
            <Link className="mc-project-row" key={project.id} to={`/projects/${project.id}`}>
              <div>
                <strong>{project.name}</strong>
                <small>{project.currentPhase || project.description || "No phase set"}</small>
              </div>
              <span>{formatProjectStatus(project.status)}</span>
              <span>{formatProjectPriority(project.priority)}</span>
              <span>{project.currentVersion || "—"}</span>
              <span>{project.currentStep || "No current step"}</span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="mc-panel mc-project-empty">
          <div className="mc-empty-icon"><FolderKanban size={28} /></div>
          <h2>{query ? "No matching projects" : "No projects yet"}</h2>
          <p>{query ? "Try a different search." : "Create your first project to begin tracking it."}</p>
        </div>
      )}

      {creating ? (
        <ProjectForm
          title="New project"
          submitLabel="Create project"
          busy={createProject.isPending}
          onCancel={() => setCreating(false)}
          onSubmit={async (input) => {
            await createProject.mutateAsync(input);
            setCreating(false);
          }}
        />
      ) : null}
    </section>
  );
}
