import { Plus, Search } from "lucide-react";

export function ProjectsPage() {
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

        <button className="mc-button mc-button-primary" type="button">
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
            disabled
          />
        </label>
      </div>

      <div className="mc-panel mc-project-empty">
        <div className="mc-empty-icon">
          <FolderPlaceholder />
        </div>

        <h2>Project foundation ready</h2>

        <p>
          The Projects module is registered and running. Persistent project
          storage is the next implementation milestone.
        </p>
      </div>
    </section>
  );
}

function FolderPlaceholder() {
  return (
    <svg
      aria-hidden="true"
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5v7A2.5 2.5 0 0 1 18.5 19h-13A2.5 2.5 0 0 1 3 16.5z" />
    </svg>
  );
}