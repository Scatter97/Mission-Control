import { invoke } from "@tauri-apps/api/core";
import {
  useEffect,
  useMemo,
  useState
} from "react";
import {
  Archive,
  ArrowRight,
  FolderKanban,
  Plus,
  Search
} from "lucide-react";
import {
  Link,
  useNavigate,
  useSearchParams
} from "react-router-dom";

import { ConfirmDialog } from "../../../shared/ui/ConfirmDialog";
import { StateBadge } from "../../../shared/ui/StateBadge";
import { AddNextStepDialog } from "../components/AddNextStepDialog";
import { ProjectActionsMenu } from "../components/ProjectActionsMenu";
import { ProjectForm } from "../components/ProjectForm";
import {
  useArchiveProject,
  useDeleteProject,
  useProjects,
  useRestoreProject,
  useUpdateProject
} from "../hooks";
import {
  formatProjectStatus,
  formatStepPriority,
  formatStepStatus,
  priorityTone,
  projectStatusTone,
  projectToInput,
  stepStatusTone,
  type Project
} from "../types";

type ConfirmState = {
  project: Project;
  action: "archive" | "restore" | "delete";
} | null;

type ContextMenuState = {
  project: Project;
  x: number;
  y: number;
} | null;

function matchesSearch(
  project: Project,
  query: string
): boolean {
  const needle =
    query.trim().toLowerCase();

  if (!needle) {
    return true;
  }

  return [
    project.name,
    project.description,
    project.currentVersion,
    project.currentPhase,
    project.currentStep,
    project.lastCompletedStep
  ].some((value) =>
    value.toLowerCase().includes(needle)
  );
}

export function ProjectsPage() {
  const navigate = useNavigate();

  const [
    searchParams,
    setSearchParams
  ] = useSearchParams();

  const archived =
    searchParams.get("view") ===
    "archived";

  const projectsQuery =
    useProjects(archived);

  const updateProject =
    useUpdateProject();

  const archiveProject =
    useArchiveProject();

  const restoreProject =
    useRestoreProject();

  const deleteProject =
    useDeleteProject();

  const [query, setQuery] =
    useState("");

  const [
    selectedId,
    setSelectedId
  ] = useState<string | null>(null);

  const [
    contextMenu,
    setContextMenu
  ] = useState<ContextMenuState>(
    null
  );

  const [
    editingProject,
    setEditingProject
  ] = useState<Project | null>(null);

  const [
    stepProject,
    setStepProject
  ] = useState<Project | null>(null);

  const [
    confirmState,
    setConfirmState
  ] = useState<ConfirmState>(null);

  const projects = useMemo(
    () =>
      (projectsQuery.data ?? [])
        .filter((project) =>
          matchesSearch(
            project,
            query
          )
        ),
    [
      projectsQuery.data,
      query
    ]
  );

  useEffect(() => {
    if (!projects.length) {
      setSelectedId(null);
      return;
    }

    if (
      !projects.some(
        (project) =>
          project.id === selectedId
      )
    ) {
      setSelectedId(
        projects[0].id
      );
    }
  }, [
    projects,
    selectedId
  ]);

  const selectedProject =
    projects.find(
      (project) =>
        project.id === selectedId
    ) ?? null;

  const setArchivedView = (
    nextArchived: boolean
  ) => {
    const next =
      new URLSearchParams(
        searchParams
      );

    if (nextArchived) {
      next.set(
        "view",
        "archived"
      );
    } else {
      next.delete("view");
    }

    setSearchParams(next);
    setQuery("");
    setSelectedId(null);
  };

  async function openLocalFolder(
    project: Project
  ) {
    if (!project.localPath) {
      return;
    }

    await invoke(
      "open_local_folder",
      {
        path: project.localPath
      }
    );
  }

  async function openRepository(
    project: Project
  ) {
    if (!project.repoUrl) {
      return;
    }

    await invoke(
      "open_repository_url",
      {
        url: project.repoUrl
      }
    );
  }

  async function addStep(
    project: Project,
    step: string
  ) {
    await updateProject.mutateAsync({
      id: project.id,
      input: {
        ...projectToInput(project),
        nextSteps: [
          ...project.nextSteps,
          step
        ]
      }
    });

    setStepProject(null);
  }

  async function confirmAction() {
    if (!confirmState) {
      return;
    }

    const {
      project,
      action
    } = confirmState;

    if (action === "archive") {
      await archiveProject.mutateAsync(
        project.id
      );
    } else if (
      action === "restore"
    ) {
      await restoreProject.mutateAsync(
        project.id
      );
    } else {
      await deleteProject.mutateAsync(
        project.id
      );
    }

    setConfirmState(null);
  }

  const confirmConfig =
    confirmState?.action === "archive"
      ? {
          title: "Archive project?",
          description:
            `"${confirmState.project.name}" will move to Archived Projects.`,
          label: "Archive Project",
          destructive: false
        }
      : confirmState?.action ===
          "restore"
        ? {
            title: "Restore project?",
            description:
              `"${confirmState.project.name}" will return to active Projects.`,
            label: "Restore Project",
            destructive: false
          }
        : {
            title:
              "Delete project permanently?",
            description:
              confirmState
                ? `This will permanently delete "${confirmState.project.name}" from Mission Control.`
                : "",
            label: "Delete Project",
            destructive: true
          };

  const actionBusy =
    archiveProject.isPending ||
    restoreProject.isPending ||
    deleteProject.isPending;

  return (
    <section className="mc-page mc-page-projects">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">
            Workspace
          </p>

          <h1>Projects</h1>

          <p className="mc-page-description">
            Keep every project centered on its current
            step and the next decision.
          </p>
        </div>

        <Link
          className="mc-button mc-button-primary"
          to="/projects/new"
        >
          <Plus size={15} />
          New project
        </Link>
      </header>

      <div className="mc-project-toolbar">
        <div
          className="mc-segmented-control"
          aria-label="Project view"
        >
          <button
            type="button"
            className={
              !archived
                ? "is-active"
                : ""
            }
            onClick={() =>
              setArchivedView(false)
            }
          >
            Active
          </button>

          <button
            type="button"
            className={
              archived
                ? "is-active"
                : ""
            }
            onClick={() =>
              setArchivedView(true)
            }
          >
            <Archive size={13} />
            Archived
          </button>
        </div>

        <label className="mc-search">
          <Search size={15} />

          <input
            aria-label="Search projects"
            placeholder={
              archived
                ? "Search archived projects..."
                : "Search projects..."
            }
            value={query}
            onChange={(event) =>
              setQuery(
                event.target.value
              )
            }
          />
        </label>
      </div>

      {projectsQuery.isLoading ? (
        <div className="mc-panel mc-project-empty">
          <p>Loading projects...</p>
        </div>
      ) : projectsQuery.isError ? (
        <div className="mc-panel mc-project-empty">
          <h2>Could not load projects</h2>
          <p>
            {String(
              projectsQuery.error
            )}
          </p>
        </div>
      ) : projects.length ? (
        <div className="mc-projects-workspace">
          <div className="mc-panel mc-project-table-v2">
            <div
              className="mc-project-table-head"
              aria-hidden="true"
            >
              <span>Project</span>
              <span className="mc-col-status">
                Status
              </span>
              <span className="mc-col-step-status">
                Step
              </span>
              <span className="mc-col-priority">
                Priority
              </span>
              <span className="mc-col-version">
                Version
              </span>
              <span className="mc-col-current-step">
                Current step
              </span>
            </div>

            <div className="mc-project-table-body">
              {projects.map(
                (project) => (
                  <button
                    key={project.id}
                    type="button"
                    className={
                      `mc-project-row-v2${
                        selectedId ===
                        project.id
                          ? " is-selected"
                          : ""
                      }`
                    }
                    onClick={() =>
                      setSelectedId(
                        project.id
                      )
                    }
                    onDoubleClick={() =>
                      navigate(
                        `/projects/${project.id}`
                      )
                    }
                    onContextMenu={(
                      event
                    ) => {
                      event.preventDefault();

                      setSelectedId(
                        project.id
                      );

                      setContextMenu({
                        project,
                        x: event.clientX,
                        y: event.clientY
                      });
                    }}
                  >
                    <span className="mc-project-identity">
                      <strong>
                        {project.name}
                      </strong>

                      <small>
                        {project.currentPhase ||
                          project.description ||
                          "No phase set"}
                      </small>
                    </span>

                    <span className="mc-col-status">
                      <StateBadge
                        label={formatProjectStatus(
                          project.status
                        )}
                        tone={projectStatusTone(
                          project.status
                        )}
                      />
                    </span>

                    <span className="mc-col-step-status">
                      <StateBadge
                        label={formatStepStatus(
                          project.currentStepStatus
                        )}
                        tone={stepStatusTone(
                          project.currentStepStatus
                        )}
                      />
                    </span>

                    <span className="mc-col-priority">
                      <StateBadge
                        label={formatStepPriority(
                          project.currentStepPriority
                        )}
                        tone={priorityTone(
                          project.currentStepPriority
                        )}
                      />
                    </span>

                    <span className="mc-col-version mc-project-version">
                      {project.currentVersion ||
                        "—"}
                    </span>

                    <span className="mc-col-current-step mc-current-step-cell">
                      {project.currentStep ||
                        "No current step"}
                    </span>
                  </button>
                )
              )}
            </div>
          </div>

          {selectedProject ? (
            <aside className="mc-panel mc-project-preview">
              <div className="mc-project-preview-heading">
                <div>
                  <p className="mc-eyebrow">
                    {archived
                      ? "Archived project"
                      : "Selected project"}
                  </p>

                  <h2>
                    {selectedProject.name}
                  </h2>
                </div>

                <StateBadge
                  label={formatProjectStatus(
                    selectedProject.status
                  )}
                  tone={projectStatusTone(
                    selectedProject.status
                  )}
                />
              </div>

              <p className="mc-project-preview-description">
                {selectedProject.description ||
                  "No description yet."}
              </p>

              <div className="mc-preview-current-step">
                <span>Current step</span>

                <strong>
                  {selectedProject.currentStep ||
                    "No current step set"}
                </strong>

                <div className="mc-badge-row">
                  <StateBadge
                    label={formatStepStatus(
                      selectedProject.currentStepStatus
                    )}
                    tone={stepStatusTone(
                      selectedProject.currentStepStatus
                    )}
                  />

                  <StateBadge
                    label={formatStepPriority(
                      selectedProject.currentStepPriority
                    )}
                    tone={priorityTone(
                      selectedProject.currentStepPriority
                    )}
                  />
                </div>
              </div>

              <dl className="mc-inspector-list">
                <div>
                  <dt>Phase</dt>
                  <dd>
                    {selectedProject.currentPhase ||
                      "—"}
                  </dd>
                </div>

                <div>
                  <dt>Version</dt>
                  <dd>
                    {selectedProject.currentVersion ||
                      "—"}
                  </dd>
                </div>

                <div>
                  <dt>Next steps</dt>
                  <dd>
                    {
                      selectedProject
                        .nextSteps.length
                    }
                  </dd>
                </div>

                <div>
                  <dt>Blockers</dt>
                  <dd>
                    {
                      selectedProject
                        .blockers.length
                    }
                  </dd>
                </div>
              </dl>

              <Link
                className="mc-button mc-button-block"
                to={`/projects/${selectedProject.id}`}
              >
                Open project
                <ArrowRight size={14} />
              </Link>
            </aside>
          ) : null}
        </div>
      ) : (
        <div className="mc-panel mc-project-empty">
          <div className="mc-empty-icon">
            {archived ? (
              <Archive size={27} />
            ) : (
              <FolderKanban size={28} />
            )}
          </div>

          <h2>
            {query
              ? "No matching projects"
              : archived
                ? "No archived projects"
                : "No projects yet"}
          </h2>

          <p>
            {query
              ? "Try a different search."
              : archived
                ? "Projects you archive will stay accessible here."
                : "Create your first project to begin tracking it."}
          </p>

          {!query && !archived ? (
            <Link
              className="mc-button mc-button-primary mc-empty-action"
              to="/projects/new"
            >
              <Plus size={14} />
              New project
            </Link>
          ) : null}
        </div>
      )}

      {contextMenu ? (
        <ProjectActionsMenu
          project={contextMenu.project}
          includeOpen
          position={{
            x: contextMenu.x,
            y: contextMenu.y
          }}
          onClose={() =>
            setContextMenu(null)
          }
          onOpen={() =>
            navigate(
              `/projects/${contextMenu.project.id}`
            )
          }
          onAddStep={() =>
            setStepProject(
              contextMenu.project
            )
          }
          onEdit={() =>
            setEditingProject(
              contextMenu.project
            )
          }
          onOpenFolder={() =>
            void openLocalFolder(
              contextMenu.project
            )
          }
          onOpenRepository={() =>
            void openRepository(
              contextMenu.project
            )
          }
          onArchiveToggle={() =>
            setConfirmState({
              project:
                contextMenu.project,
              action:
                contextMenu.project
                  .archived
                  ? "restore"
                  : "archive"
            })
          }
          onDelete={() =>
            setConfirmState({
              project:
                contextMenu.project,
              action: "delete"
            })
          }
        />
      ) : null}

      {editingProject ? (
        <div className="mc-dialog-backdrop">
          <div
            className="mc-dialog mc-dialog-wide"
            role="dialog"
            aria-modal="true"
          >
            <div className="mc-dialog-header">
              <div>
                <p className="mc-eyebrow">
                  Project
                </p>

                <h2>
                  Edit {editingProject.name}
                </h2>
              </div>
            </div>

            <div className="mc-dialog-scroll">
              <ProjectForm
                initialValue={projectToInput(
                  editingProject
                )}
                submitLabel="Save changes"
                busy={updateProject.isPending}
                onCancel={() =>
                  setEditingProject(null)
                }
                onSubmit={async (
                  input
                ) => {
                  await updateProject.mutateAsync({
                    id:
                      editingProject.id,
                    input
                  });

                  setEditingProject(
                    null
                  );
                }}
              />
            </div>
          </div>
        </div>
      ) : null}

      <AddNextStepDialog
        open={stepProject !== null}
        projectName={
          stepProject?.name ?? ""
        }
        busy={updateProject.isPending}
        onCancel={() =>
          setStepProject(null)
        }
        onSubmit={async (step) => {
          if (stepProject) {
            await addStep(
              stepProject,
              step
            );
          }
        }}
      />

      <ConfirmDialog
        open={confirmState !== null}
        title={confirmConfig.title}
        description={
          confirmConfig.description
        }
        confirmLabel={
          confirmConfig.label
        }
        destructive={
          confirmConfig.destructive
        }
        busy={actionBusy}
        onCancel={() =>
          setConfirmState(null)
        }
        onConfirm={() =>
          void confirmAction()
        }
      />
    </section>
  );
}
