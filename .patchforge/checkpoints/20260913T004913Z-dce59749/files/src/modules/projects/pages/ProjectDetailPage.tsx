import { useState } from "react";
import { Archive, ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ProjectForm } from "../components/ProjectForm";
import {
  useArchiveProject,
  useDeleteProject,
  useProject,
  useUpdateProject
} from "../hooks";
import {
  formatProjectPriority,
  formatProjectStatus,
  projectToInput
} from "../types";

export function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const projectQuery = useProject(id);
  const updateProject = useUpdateProject();
  const archiveProject = useArchiveProject();
  const deleteProject = useDeleteProject();
  const [editing, setEditing] = useState(false);

  if (projectQuery.isLoading) {
    return <section className="mc-page"><div className="mc-panel mc-project-empty"><p>Loading project...</p></div></section>;
  }

  const project = projectQuery.data;

  if (!project) {
    return <section className="mc-page"><div className="mc-panel mc-project-empty"><h2>Project not found</h2></div></section>;
  }

  async function handleArchive() {
    if (!window.confirm(`Archive "${project.name}"?`)) return;
    await archiveProject.mutateAsync(project.id);
    navigate("/projects");
  }

  async function handleDelete() {
    if (!window.confirm(`Permanently delete "${project.name}"?`)) return;
    await deleteProject.mutateAsync(project.id);
    navigate("/projects");
  }

  return (
    <section className="mc-page">
      <Link className="mc-back-link" to="/projects">
        <ArrowLeft size={14} /> Projects
      </Link>

      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Project overview</p>
          <h1>{project.name}</h1>
          <p className="mc-page-description">{project.description || "No description yet."}</p>
        </div>

        <div className="mc-header-actions">
          <button className="mc-button" onClick={() => setEditing(true)}>
            <Pencil size={14} /> Edit
          </button>
          <button className="mc-button" onClick={handleArchive}>
            <Archive size={14} /> Archive
          </button>
          <button className="mc-button mc-button-danger" onClick={handleDelete}>
            <Trash2 size={14} /> Delete
          </button>
        </div>
      </header>

      <div className="mc-project-detail-grid">
        <div className="mc-project-detail-main">
          <section className="mc-panel mc-current-step-panel">
            <p className="mc-eyebrow">Current Step</p>
            <h2>{project.currentStep || "No current step set"}</h2>
            <p>{project.currentPhase || "No phase"} · {project.currentVersion || "No version"}</p>
          </section>

          <section className="mc-panel mc-detail-section">
            <h2>Next steps</h2>
            {project.nextSteps.length ? (
              <ol className="mc-detail-list">
                {project.nextSteps.map((step) => <li key={step}>{step}</li>)}
              </ol>
            ) : <p className="mc-muted">No next steps yet.</p>}
          </section>

          <section className="mc-panel mc-detail-section">
            <h2>Blockers</h2>
            {project.blockers.length ? (
              <ul className="mc-detail-list">
                {project.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}
              </ul>
            ) : <p className="mc-muted">No blockers.</p>}
          </section>
        </div>

        <aside className="mc-panel mc-project-inspector">
          <h2>Project details</h2>
          <p>Status: {formatProjectStatus(project.status)}</p>
          <p>Priority: {formatProjectPriority(project.priority)}</p>
          <p>Version: {project.currentVersion || "—"}</p>
          <p>Phase: {project.currentPhase || "—"}</p>
          <p>Last completed: {project.lastCompletedStep || "—"}</p>
          <p>Local path: {project.localPath || "—"}</p>
          <p>Repository: {project.repoUrl || "—"}</p>
        </aside>
      </div>

      {editing ? (
        <ProjectForm
          title={`Edit ${project.name}`}
          initialValue={projectToInput(project)}
          submitLabel="Save changes"
          busy={updateProject.isPending}
          onCancel={() => setEditing(false)}
          onSubmit={async (input) => {
            await updateProject.mutateAsync({ id: project.id, input });
            setEditing(false);
          }}
        />
      ) : null}
    </section>
  );
}
