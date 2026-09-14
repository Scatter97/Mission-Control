import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState, type DragEvent } from "react";
import {
  Archive,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FolderOpen,
  GripVertical,
  MoreHorizontal,
  Pencil,
  Plus,
  RotateCcw,
  Trash2
} from "lucide-react";
import {
  Link,
  useNavigate,
  useParams
} from "react-router-dom";

import { ConfirmDialog } from "../../../shared/ui/ConfirmDialog";
import { StateBadge } from "../../../shared/ui/StateBadge";
import { AddNextStepDialog } from "../components/AddNextStepDialog";
import { ProjectActionsMenu } from "../components/ProjectActionsMenu";
import { ProjectForm } from "../components/ProjectForm";
import {
  useArchiveProject,
  useDeleteProject,
  useProject,
  useProjectStepHistory,
  useRestoreProject,
  useUpdateProject,
  useUpdateProjectNextSteps
} from "../hooks";
import {
  formatProjectStatus,
  formatStepPriority,
  formatStepStatus,
  priorityTone,
  projectStatusTone,
  projectToInput,
  stepStatusTone
} from "../types";

type ActiveDetailTab =
  | "Overview"
  | "Activity";

type ConfirmAction =
  | "archive"
  | "restore"
  | "delete"
  | null;

const detailTabs = [
  "Overview",
  "Tasks",
  "Bugs",
  "Milestones",
  "Schedule",
  "Notes",
  "Patch Forge",
  "Git",
  "Activity",
  "Integrations"
];

function formatUpdated(
  timestamp: number
): string {
  if (!timestamp) {
    return "—";
  }

  return new Date(
    timestamp * 1000
  ).toLocaleString();
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const projectQuery =
    useProject(id);

  const [activeTab, setActiveTab] =
    useState<ActiveDetailTab>("Overview");

  const historyQuery =
    useProjectStepHistory(
      id,
      activeTab === "Activity"
    );

  useEffect(() => {
    if (!id) {
      return;
    }

    let active = true;

    async function consumeTransition() {
      try {
        const changed = await invoke<boolean>(
          "projects_consume_step_transition",
          { id }
        );

        if (changed && active) {
          await Promise.all([
            projectQuery.refetch(),
            historyQuery.refetch()
          ]);
        }
      } catch (error) {
        console.error(
          "Could not consume Mission Control step transition:",
          error
        );
      }
    }

    void consumeTransition();

    const interval = window.setInterval(
      () => void consumeTransition(),
      1500
    );

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [
    id,
    projectQuery.refetch,
    historyQuery.refetch
  ]);

  const updateProject =
    useUpdateProject();

  const updateNextSteps =
    useUpdateProjectNextSteps();

  const archiveProject =
    useArchiveProject();

  const restoreProject =
    useRestoreProject();

  const deleteProject =
    useDeleteProject();

  const [editing, setEditing] =
    useState(false);

  const [
    actionMenuOpen,
    setActionMenuOpen
  ] = useState(false);

  const [
    addingStep,
    setAddingStep
  ] = useState(false);

  const [
    confirmAction,
    setConfirmAction
  ] = useState<ConfirmAction>(
    null
  );

  const [
    editingNextSteps,
    setEditingNextSteps
  ] = useState(false);

  const [
    draftNextSteps,
    setDraftNextSteps
  ] = useState<string[]>([]);

  const [
    draggedStepIndex,
    setDraggedStepIndex
  ] = useState<number | null>(null);

  if (projectQuery.isLoading) {
    return (
      <section className="mc-page">
        <div className="mc-panel mc-project-empty">
          <p>Loading project...</p>
        </div>
      </section>
    );
  }

  const project =
    projectQuery.data!;

  if (!project) {
    return (
      <section className="mc-page">
        <div className="mc-panel mc-project-empty">
          <h2>Project not found</h2>
        </div>
      </section>
    );
  }

  const confirmConfig =
    confirmAction === "archive"
      ? {
          title: "Archive project?",
          description:
            `"${project.name}" will move to Archived Projects. You can restore it later.`,
          label: "Archive Project",
          destructive: false
        }
      : confirmAction === "restore"
        ? {
            title: "Restore project?",
            description:
              `"${project.name}" will return to the active Projects workspace.`,
            label: "Restore Project",
            destructive: false
          }
        : {
            title:
              "Delete project permanently?",
            description:
              `This will permanently delete "${project.name}" from Mission Control. This action cannot be undone.`,
            label: "Delete Project",
            destructive: true
          };

  const confirmBusy =
    archiveProject.isPending ||
    restoreProject.isPending ||
    deleteProject.isPending;

  async function handleConfirm() {
    if (!confirmAction) {
      return;
    }

    if (
      confirmAction === "archive"
    ) {
      await archiveProject.mutateAsync(
        project.id
      );

      navigate(
        "/projects?view=archived"
      );
    } else if (
      confirmAction === "restore"
    ) {
      await restoreProject.mutateAsync(
        project.id
      );

      navigate("/projects");
    } else {
      await deleteProject.mutateAsync(
        project.id
      );

      navigate(
        project.archived
          ? "/projects?view=archived"
          : "/projects"
      );
    }

    setConfirmAction(null);
  }

  async function openLocalFolder() {
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

  async function openRepository() {
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

  async function addNextStep(
    step: string
  ) {
    await updateNextSteps.mutateAsync({
      id: project.id,
      nextSteps: [
        ...project.nextSteps,
        step
      ]
    });

    setAddingStep(false);
  }

  function beginNextStepsEdit() {
    setDraftNextSteps([...project.nextSteps]);
    setEditingNextSteps(true);
  }

  function cancelNextStepsEdit() {
    setDraftNextSteps([]);
    setDraggedStepIndex(null);
    setEditingNextSteps(false);
  }

  function addDraftNextStep() {
    setDraftNextSteps(
      (steps) => [...steps, ""]
    );
  }

  function updateDraftNextStep(
    index: number,
    value: string
  ) {
    setDraftNextSteps(
      (steps) =>
        steps.map(
          (step, stepIndex) =>
            stepIndex === index
              ? value
              : step
        )
    );
  }

  function removeDraftNextStep(
    index: number
  ) {
    setDraftNextSteps(
      (steps) =>
        steps.filter(
          (_, stepIndex) =>
            stepIndex !== index
        )
    );
  }

  function handleStepDragStart(
    event: DragEvent<HTMLButtonElement>,
    index: number
  ) {
    setDraggedStepIndex(index);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData(
      "text/plain",
      String(index)
    );
  }

  function handleStepDrop(
    event: DragEvent<HTMLDivElement>,
    targetIndex: number
  ) {
    event.preventDefault();

    const sourceIndex =
      draggedStepIndex ??
      Number(
        event.dataTransfer.getData(
          "text/plain"
        )
      );

    if (
      !Number.isInteger(sourceIndex) ||
      sourceIndex < 0 ||
      sourceIndex >= draftNextSteps.length ||
      sourceIndex === targetIndex
    ) {
      setDraggedStepIndex(null);
      return;
    }

    setDraftNextSteps(
      (steps) => {
        const reordered = [...steps];
        const [moved] =
          reordered.splice(sourceIndex, 1);

        reordered.splice(
          targetIndex,
          0,
          moved
        );

        return reordered;
      }
    );

    setDraggedStepIndex(null);
  }

  async function saveNextSteps() {
    const cleaned =
      draftNextSteps.map(
        (step) => step.trim()
      );

    if (
      cleaned.some(
        (step) => !step
      )
    ) {
      return;
    }

    await updateNextSteps.mutateAsync({
      id: project.id,
      nextSteps: cleaned
    });

    setEditingNextSteps(false);
    setDraftNextSteps([]);
    setDraggedStepIndex(null);
  }

  const nextStepsValid =
    draftNextSteps.every(
      (step) => step.trim().length > 0
    );

  return (
    <section className="mc-page mc-project-detail-page">
      <Link
        className="mc-back-link"
        to={
          project.archived
            ? "/projects?view=archived"
            : "/projects"
        }
      >
        <ArrowLeft size={14} />

        {project.archived
          ? "Archived Projects"
          : "Projects"}
      </Link>

      <header className="mc-project-detail-header">
        <div className="mc-project-title-block">
          <div className="mc-title-row">
            <h1>{project.name}</h1>

            <StateBadge
              label={
                project.archived
                  ? "Archived"
                  : formatProjectStatus(
                      project.status
                    )
              }
              tone={
                project.archived
                  ? "neutral"
                  : projectStatusTone(
                      project.status
                    )
              }
            />
          </div>

          <p>
            {project.description ||
              "No description yet."}
          </p>

          <div className="mc-project-meta-row">
            <span>
              {project.currentPhase ||
                "No phase"}
            </span>

            <span className="mc-meta-separator">
              •
            </span>

            <span>
              {project.currentVersion ||
                "No version"}
            </span>

            <span className="mc-meta-separator">
              •
            </span>

            <span>
              Updated{" "}
              {formatUpdated(
                project.updatedAt
              )}
            </span>
          </div>
        </div>

        <div className="mc-header-actions">
          {!project.archived ? (
            <button
              className="mc-button"
              type="button"
              onClick={() =>
                setEditing(true)
              }
            >
              <Pencil size={14} />
              Edit
            </button>
          ) : null}

          {project.archived ? (
            <button
              className="mc-button"
              type="button"
              onClick={() =>
                setConfirmAction(
                  "restore"
                )
              }
            >
              <RotateCcw size={14} />
              Restore
            </button>
          ) : (
            <button
              className="mc-button"
              type="button"
              onClick={() =>
                setConfirmAction(
                  "archive"
                )
              }
            >
              <Archive size={14} />
              Archive
            </button>
          )}

          <button
            className="mc-icon-button mc-delete-button"
            type="button"
            aria-label="Delete project"
            title="Delete project"
            onClick={() =>
              setConfirmAction("delete")
            }
          >
            <Trash2 size={15} />
          </button>
        </div>
      </header>

      <div
        className="mc-detail-tabs"
        role="tablist"
        aria-label="Project sections"
      >
        {detailTabs.map((tab) => {
          const enabled =
            tab === "Overview" ||
            tab === "Activity";

          return (
            <button
              key={tab}
              type="button"
              className={
                tab === activeTab
                  ? "is-active"
                  : ""
              }
              disabled={!enabled}
              title={
                enabled
                  ? undefined
                  : "Planned for a future Mission Control update"
              }
              onClick={() => {
                if (enabled) {
                  setActiveTab(
                    tab as ActiveDetailTab
                  );
                }
              }}
            >
              {tab}
            </button>
          );
        })}
      </div>

      {activeTab === "Overview" ? (
      <div className="mc-project-detail-grid-v2">
        <div className="mc-project-detail-main-v2">
          <section className="mc-panel mc-current-step-card">
            <div className="mc-section-topline">
              <div>
                <p className="mc-eyebrow">
                  Current Step
                </p>

                <h2>
                  {project.currentStep ||
                    "No current step set"}
                </h2>
              </div>

              <div className="mc-badge-row">
                <StateBadge
                  label={formatStepStatus(
                    project.currentStepStatus
                  )}
                  tone={stepStatusTone(
                    project.currentStepStatus
                  )}
                />

                <StateBadge
                  label={formatStepPriority(
                    project.currentStepPriority
                  )}
                  tone={priorityTone(
                    project.currentStepPriority
                  )}
                />
              </div>
            </div>

            <div className="mc-step-context">
              <span>
                {project.currentPhase ||
                  "No phase set"}
              </span>

              <span>•</span>

              <span>
                {project.currentVersion ||
                  "No version set"}
              </span>
            </div>
          </section>

          <div className="mc-detail-pair">
            <section className="mc-panel mc-detail-section-v2">
              <div className="mc-section-heading-inline mc-next-steps-heading">
                <div className="mc-next-steps-title">
                  <h2>Next steps</h2>

                  <span>
                    {editingNextSteps
                      ? draftNextSteps.length
                      : project.nextSteps.length}
                  </span>
                </div>

                {!project.archived ? (
                  editingNextSteps ? (
                    <div className="mc-next-step-actions">
                      <button
                        className="mc-button mc-button-compact"
                        type="button"
                        disabled={updateNextSteps.isPending}
                        onClick={cancelNextStepsEdit}
                      >
                        Cancel
                      </button>

                      <button
                        className="mc-button mc-button-primary mc-button-compact"
                        type="button"
                        disabled={
                          updateNextSteps.isPending ||
                          !nextStepsValid
                        }
                        onClick={() =>
                          void saveNextSteps()
                        }
                      >
                        {updateNextSteps.isPending
                          ? "Saving..."
                          : "Save"}
                      </button>
                    </div>
                  ) : (
                    <button
                      className="mc-button mc-button-compact"
                      type="button"
                      onClick={beginNextStepsEdit}
                    >
                      Edit
                    </button>
                  )
                ) : null}
              </div>

              {editingNextSteps ? (
                <div className="mc-next-steps-editor">
                  {draftNextSteps.map(
                    (step, index) => (
                      <div
                        key={index}
                        className={
                          draggedStepIndex === index
                            ? "mc-next-step-edit-row is-dragging"
                            : "mc-next-step-edit-row"
                        }
                        onDragOver={(event) => {
                          event.preventDefault();
                          event.dataTransfer.dropEffect =
                            "move";
                        }}
                        onDrop={(event) =>
                          handleStepDrop(
                            event,
                            index
                          )
                        }
                      >
                        <button
                          className="mc-drag-handle"
                          type="button"
                          draggable
                          aria-label={`Drag step ${index + 1}`}
                          title="Drag to reorder"
                          onDragStart={(event) =>
                            handleStepDragStart(
                              event,
                              index
                            )
                          }
                          onDragEnd={() =>
                            setDraggedStepIndex(null)
                          }
                        >
                          <GripVertical size={15} />
                        </button>

                        <input
                          className="mc-next-step-input"
                          value={step}
                          aria-label={`Step ${index + 1}`}
                          onChange={(event) =>
                            updateDraftNextStep(
                              index,
                              event.target.value
                            )
                          }
                        />

                        <button
                          className="mc-next-step-remove"
                          type="button"
                          aria-label={`Delete step ${index + 1}`}
                          title="Delete step"
                          onClick={() =>
                            removeDraftNextStep(index)
                          }
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    )
                  )}

                  <button
                    className="mc-add-next-step-inline"
                    type="button"
                    onClick={addDraftNextStep}
                  >
                    <Plus size={14} />
                    Add step
                  </button>

                  {!nextStepsValid ? (
                    <p className="mc-next-steps-validation">
                      Steps cannot be blank.
                    </p>
                  ) : null}
                </div>
              ) : project.nextSteps.length ? (
                <ol className="mc-work-list">
                  {project.nextSteps.map(
                    (step, index) => (
                      <li key={`${step}-${index}`}>
                        <span className="mc-work-index">
                          {index + 1}
                        </span>

                        <span>{step}</span>
                      </li>
                    )
                  )}
                </ol>
              ) : (
                <p className="mc-muted">
                  No next steps yet.
                </p>
              )}
            </section>

            <section className="mc-panel mc-detail-section-v2">
              <div className="mc-section-heading-inline">
                <h2>Blockers</h2>
                <span>
                  {project.blockers.length}
                </span>
              </div>

              {project.blockers.length ? (
                <ul className="mc-work-list mc-blocker-list">
                  {project.blockers.map(
                    (blocker, index) => (
                      <li
                        key={`${blocker}-${index}`}
                      >
                        <span className="mc-blocker-dot" />
                        <span>{blocker}</span>
                      </li>
                    )
                  )}
                </ul>
              ) : (
                <div className="mc-clear-state">
                  <CheckCircle2 size={16} />
                  <span>No blockers</span>
                </div>
              )}
            </section>
          </div>

          <section className="mc-panel mc-last-completed-card">
            <div className="mc-last-completed-icon">
              <CheckCircle2 size={17} />
            </div>

            <div>
              <p className="mc-eyebrow">
                Last completed
              </p>

              <strong>
                {project.lastCompletedStep ||
                  "No completed step recorded"}
              </strong>
            </div>
          </section>
        </div>

        <aside className="mc-panel mc-project-inspector-v2">
          <div className="mc-inspector-heading">
            <div>
              <p className="mc-eyebrow">
                Inspector
              </p>

              <h2>Project details</h2>
            </div>

            <div className="mc-action-menu-anchor">
              <button
                className="mc-inspector-menu-button"
                type="button"
                aria-label="Project actions"
                title="Project actions"
                onClick={() =>
                  setActionMenuOpen(
                    (open) => !open
                  )
                }
              >
                <MoreHorizontal size={17} />
              </button>

              {actionMenuOpen ? (
                <ProjectActionsMenu
                  project={project}
                  onClose={() =>
                    setActionMenuOpen(
                      false
                    )
                  }
                  onAddStep={() =>
                    setAddingStep(true)
                  }
                  onEdit={() =>
                    setEditing(true)
                  }
                  onOpenFolder={() =>
                    void openLocalFolder()
                  }
                  onOpenRepository={() =>
                    void openRepository()
                  }
                  onArchiveToggle={() =>
                    setConfirmAction(
                      project.archived
                        ? "restore"
                        : "archive"
                    )
                  }
                  onDelete={() =>
                    setConfirmAction(
                      "delete"
                    )
                  }
                />
              ) : null}
            </div>
          </div>

          <dl className="mc-inspector-list">
            <div>
              <dt>Project status</dt>

              <dd>
                <StateBadge
                  label={
                    project.archived
                      ? "Archived"
                      : formatProjectStatus(
                          project.status
                        )
                  }
                  tone={
                    project.archived
                      ? "neutral"
                      : projectStatusTone(
                          project.status
                        )
                  }
                />
              </dd>
            </div>

            <div>
              <dt>Phase</dt>
              <dd>
                {project.currentPhase ||
                  "—"}
              </dd>
            </div>

            <div>
              <dt>Version</dt>
              <dd>
                {project.currentVersion ||
                  "—"}
              </dd>
            </div>

            <div>
              <dt>Created</dt>
              <dd>
                {formatUpdated(
                  project.createdAt
                )}
              </dd>
            </div>

            <div>
              <dt>Updated</dt>
              <dd>
                {formatUpdated(
                  project.updatedAt
                )}
              </dd>
            </div>
          </dl>

          <div className="mc-inspector-divider" />

          <div className="mc-location-block">
            <span className="mc-location-label">
              <FolderOpen size={14} />
              Local folder
            </span>

            {project.localPath ? (
              <button
                className="mc-location-link"
                type="button"
                title="Open in File Explorer"
                onClick={() =>
                  void openLocalFolder()
                }
              >
                <code>
                  {project.localPath}
                </code>
              </button>
            ) : (
              <span className="mc-muted">
                Not connected
              </span>
            )}
          </div>

          <div className="mc-location-block">
            <span className="mc-location-label">
              <ExternalLink size={14} />
              Repository
            </span>

            {project.repoUrl ? (
              <button
                className="mc-location-link"
                type="button"
                title="Open GitHub repository"
                onClick={() =>
                  void openRepository()
                }
              >
                {project.repoUrl}
              </button>
            ) : (
              <span className="mc-muted">
                Not connected
              </span>
            )}
          </div>
        </aside>
      </div>
      ) : (
        <section className="mc-panel mc-activity-panel">
          <div className="mc-activity-header">
            <div>
              <p className="mc-eyebrow">
                Activity
              </p>

              <h2>Completed steps</h2>
            </div>

            {!historyQuery.isLoading &&
            !historyQuery.isError ? (
              <span className="mc-activity-count">
                {historyQuery.data?.length ?? 0}
              </span>
            ) : null}
          </div>

          {historyQuery.isLoading ? (
            <div className="mc-activity-state">
              <p>Loading completed steps...</p>
            </div>
          ) : historyQuery.isError ? (
            <div className="mc-activity-state">
              <p>
                Could not load completed steps.
              </p>

              <button
                className="mc-button mc-button-compact"
                type="button"
                onClick={() =>
                  void historyQuery.refetch()
                }
              >
                Try again
              </button>
            </div>
          ) : historyQuery.data?.length ? (
            <div className="mc-activity-list">
              {historyQuery.data.map(
                (entry) => (
                  <article
                    key={entry.id}
                    className="mc-activity-entry"
                  >
                    <div className="mc-activity-marker">
                      <CheckCircle2 size={15} />
                    </div>

                    <div className="mc-activity-entry-body">
                      <div className="mc-activity-entry-top">
                        <div>
                          <strong>
                            {entry.step}
                          </strong>

                          <time>
                            Completed{" "}
                            {formatUpdated(
                              entry.completedAt
                            )}
                          </time>
                        </div>

                        <div className="mc-badge-row">
                          {entry.statusBefore ? (
                            <StateBadge
                              label={`Previously ${formatStepStatus(
                                entry.statusBefore
                              )}`}
                              tone={stepStatusTone(
                                entry.statusBefore
                              )}
                            />
                          ) : null}

                          {entry.priority ? (
                            <StateBadge
                              label={formatStepPriority(
                                entry.priority
                              )}
                              tone={priorityTone(
                                entry.priority
                              )}
                            />
                          ) : null}
                        </div>
                      </div>

                      {(entry.phase ||
                        entry.version) ? (
                        <div className="mc-activity-meta">
                          {entry.phase ? (
                            <span>
                              Phase: {entry.phase}
                            </span>
                          ) : null}

                          {entry.phase &&
                          entry.version ? (
                            <span>•</span>
                          ) : null}

                          {entry.version ? (
                            <span>
                              Version: {entry.version}
                            </span>
                          ) : null}
                        </div>
                      ) : null}

                      {entry.tags.length ? (
                        <div className="mc-activity-tags">
                          {entry.tags.map(
                            (tag) => (
                              <span
                                key={tag}
                                className="mc-activity-tag"
                              >
                                {tag}
                              </span>
                            )
                          )}
                        </div>
                      ) : null}
                    </div>
                  </article>
                )
              )}
            </div>
          ) : (
            <div className="mc-activity-empty">
              <CheckCircle2 size={20} />

              <h3>
                No completed steps yet.
              </h3>

              <p>
                Completed steps will appear here.
              </p>
            </div>
          )}
        </section>
      )}

      {editing && !project.archived ? (
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
                  Edit {project.name}
                </h2>
              </div>
            </div>

            <div className="mc-dialog-scroll">
              <ProjectForm
                initialValue={projectToInput(
                  project
                )}
                submitLabel="Save changes"
                busy={updateProject.isPending}
                onCancel={() =>
                  setEditing(false)
                }
                onSubmit={async (
                  input
                ) => {
                  await updateProject.mutateAsync({
                    id: project.id,
                    input
                  });

                  setEditing(false);
                }}
              />
            </div>
          </div>
        </div>
      ) : null}

      <AddNextStepDialog
        open={addingStep}
        projectName={project.name}
        busy={updateProject.isPending}
        onCancel={() =>
          setAddingStep(false)
        }
        onSubmit={addNextStep}
      />

      <ConfirmDialog
        open={
          confirmAction !== null
        }
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
        busy={confirmBusy}
        onCancel={() =>
          setConfirmAction(null)
        }
        onConfirm={() =>
          void handleConfirm()
        }
      />
    </section>
  );
}
