import { ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { ProjectForm } from "../components/ProjectForm";
import { useCreateProject } from "../hooks";

export function NewProjectPage() {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  return (
    <section className="mc-page mc-page-form">
      <Link className="mc-back-link" to="/projects">
        <ArrowLeft size={14} /> Projects
      </Link>

      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Projects</p>
          <h1>New project</h1>
          <p className="mc-page-description">
            Capture the project state, the current step, and where the work lives.
          </p>
        </div>
      </header>

      <ProjectForm
        submitLabel="Create project"
        busy={createProject.isPending}
        onCancel={() => navigate("/projects")}
        onSubmit={async (input) => {
          const project = await createProject.mutateAsync(input);
          navigate(`/projects/${project.id}`);
        }}
      />
    </section>
  );
}
