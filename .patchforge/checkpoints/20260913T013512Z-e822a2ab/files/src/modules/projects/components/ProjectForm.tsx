import { useState, type FormEvent } from "react";
import { X } from "lucide-react";

import {
  PROJECT_PRIORITIES,
  PROJECT_STATUSES,
  emptyProjectInput,
  formatProjectPriority,
  formatProjectStatus,
  type ProjectInput
} from "../types";

interface ProjectFormProps {
  title: string;
  initialValue?: ProjectInput;
  submitLabel: string;
  busy?: boolean;
  onCancel: () => void;
  onSubmit: (input: ProjectInput) => Promise<void> | void;
}

function linesToItems(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ProjectForm({
  title,
  initialValue = emptyProjectInput,
  submitLabel,
  busy = false,
  onCancel,
  onSubmit
}: ProjectFormProps) {
  const [value, setValue] = useState<ProjectInput>(initialValue);
  const [nextSteps, setNextSteps] = useState(initialValue.nextSteps.join("\n"));
  const [blockers, setBlockers] = useState(initialValue.blockers.join("\n"));
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!value.name.trim()) {
      setError("Project name is required.");
      return;
    }

    setError(null);

    try {
      await onSubmit({
        ...value,
        name: value.name.trim(),
        description: value.description.trim(),
        currentVersion: value.currentVersion.trim(),
        currentPhase: value.currentPhase.trim(),
        currentStep: value.currentStep.trim(),
        lastCompletedStep: value.lastCompletedStep.trim(),
        nextSteps: linesToItems(nextSteps),
        blockers: linesToItems(blockers),
        localPath: value.localPath?.trim() || null,
        repoUrl: value.repoUrl?.trim() || null
      });
    } catch (submitError) {
      setError(String(submitError));
    }
  }

  return (
    <div className="mc-modal-backdrop">
      <div className="mc-modal" role="dialog" aria-modal="true">
        <div className="mc-modal-header">
          <div>
            <p className="mc-eyebrow">Project</p>
            <h2>{title}</h2>
          </div>

          <button className="mc-icon-button" type="button" onClick={onCancel}>
            <X size={16} />
          </button>
        </div>

        <form className="mc-project-form" onSubmit={handleSubmit}>
          <label className="mc-field mc-field-wide">
            <span>Name</span>
            <input
              autoFocus
              value={value.name}
              onChange={(event) =>
                setValue((current) => ({ ...current, name: event.target.value }))
              }
            />
          </label>

          <label className="mc-field mc-field-wide">
            <span>Description</span>
            <textarea
              rows={3}
              value={value.description}
              onChange={(event) =>
                setValue((current) => ({ ...current, description: event.target.value }))
              }
            />
          </label>

          <label className="mc-field">
            <span>Status</span>
            <select
              value={value.status}
              onChange={(event) =>
                setValue((current) => ({
                  ...current,
                  status: event.target.value as ProjectInput["status"]
                }))
              }
            >
              {PROJECT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {formatProjectStatus(status)}
                </option>
              ))}
            </select>
          </label>

          <label className="mc-field">
            <span>Priority</span>
            <select
              value={value.priority}
              onChange={(event) =>
                setValue((current) => ({
                  ...current,
                  priority: event.target.value as ProjectInput["priority"]
                }))
              }
            >
              {PROJECT_PRIORITIES.map((priority) => (
                <option key={priority} value={priority}>
                  {formatProjectPriority(priority)}
                </option>
              ))}
            </select>
          </label>

          <label className="mc-field">
            <span>Current version</span>
            <input
              value={value.currentVersion}
              onChange={(event) =>
                setValue((current) => ({ ...current, currentVersion: event.target.value }))
              }
            />
          </label>

          <label className="mc-field">
            <span>Current phase</span>
            <input
              value={value.currentPhase}
              onChange={(event) =>
                setValue((current) => ({ ...current, currentPhase: event.target.value }))
              }
            />
          </label>

          <label className="mc-field mc-field-wide">
            <span>Current Step</span>
            <input
              value={value.currentStep}
              onChange={(event) =>
                setValue((current) => ({ ...current, currentStep: event.target.value }))
              }
            />
          </label>

          <label className="mc-field mc-field-wide">
            <span>Last completed step</span>
            <input
              value={value.lastCompletedStep}
              onChange={(event) =>
                setValue((current) => ({ ...current, lastCompletedStep: event.target.value }))
              }
            />
          </label>

          <label className="mc-field mc-field-wide">
            <span>Next steps</span>
            <textarea
              rows={4}
              value={nextSteps}
              onChange={(event) => setNextSteps(event.target.value)}
              placeholder="One step per line"
            />
          </label>

          <label className="mc-field mc-field-wide">
            <span>Blockers</span>
            <textarea
              rows={3}
              value={blockers}
              onChange={(event) => setBlockers(event.target.value)}
              placeholder="One blocker per line"
            />
          </label>

          <label className="mc-field">
            <span>Local path</span>
            <input
              value={value.localPath ?? ""}
              onChange={(event) =>
                setValue((current) => ({ ...current, localPath: event.target.value }))
              }
            />
          </label>

          <label className="mc-field">
            <span>Repository URL</span>
            <input
              value={value.repoUrl ?? ""}
              onChange={(event) =>
                setValue((current) => ({ ...current, repoUrl: event.target.value }))
              }
            />
          </label>

          {error ? <p className="mc-form-error">{error}</p> : null}

          <div className="mc-modal-actions">
            <button className="mc-button" type="button" onClick={onCancel}>
              Cancel
            </button>
            <button className="mc-button mc-button-primary" type="submit" disabled={busy}>
              {busy ? "Saving..." : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
