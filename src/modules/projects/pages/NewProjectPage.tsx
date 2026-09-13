import { useState } from "react";
import {
  ArrowLeft,
  Github,
  PencilLine
} from "lucide-react";
import {
  Link,
  useNavigate
} from "react-router-dom";

import { GitHubImportForm } from "../components/GitHubImportForm";
import { ProjectForm } from "../components/ProjectForm";
import { useCreateProject } from "../hooks";

type CreateMode = "manual" | "github";

export function NewProjectPage() {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  const [mode, setMode] =
    useState<CreateMode>("github");

  const create = async (
    input: Parameters<
      typeof createProject.mutateAsync
    >[0]
  ) => {
    const project =
      await createProject.mutateAsync(input);

    navigate(`/projects/${project.id}`);
  };

  return (
    <section className="mc-page mc-page-form">
      <Link
        className="mc-back-link"
        to="/projects"
      >
        <ArrowLeft size={14} />
        Projects
      </Link>

      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">
            Projects
          </p>

          <h1>New project</h1>

          <p className="mc-page-description">
            Create a project manually or import a
            repository directly from GitHub.
          </p>
        </div>
      </header>

      <div
        className="mc-create-mode"
        role="tablist"
        aria-label="Project creation method"
      >
        <button
          className={
            mode === "manual"
              ? "is-active"
              : ""
          }
          type="button"
          role="tab"
          aria-selected={mode === "manual"}
          onClick={() => setMode("manual")}
        >
          <PencilLine size={14} />

          <span>
            <strong>Create manually</strong>
            <small>
              Enter project state yourself
            </small>
          </span>
        </button>

        <button
          className={
            mode === "github"
              ? "is-active"
              : ""
          }
          type="button"
          role="tab"
          aria-selected={mode === "github"}
          onClick={() => setMode("github")}
        >
          <Github size={14} />

          <span>
            <strong>Import from GitHub</strong>
            <small>
              Load repository metadata
            </small>
          </span>
        </button>
      </div>

      {mode === "manual" ? (
        <ProjectForm
          submitLabel="Create project"
          busy={createProject.isPending}
          onCancel={() =>
            navigate("/projects")
          }
          onSubmit={create}
        />
      ) : (
        <GitHubImportForm
          busy={createProject.isPending}
          onCancel={() =>
            navigate("/projects")
          }
          onSubmit={create}
        />
      )}
    </section>
  );
}
