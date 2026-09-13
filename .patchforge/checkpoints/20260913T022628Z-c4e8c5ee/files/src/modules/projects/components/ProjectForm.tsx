import { useState, type FormEvent } from "react";

import { OptionPicker } from "../../../shared/ui/OptionPicker";
import {
  PROJECT_STATUSES,
  STEP_PRIORITIES,
  STEP_STATUSES,
  emptyProjectInput,
  formatProjectStatus,
  formatStepPriority,
  formatStepStatus,
  priorityTone,
  projectStatusTone,
  stepStatusTone,
  type ProjectInput
} from "../types";

interface ProjectFormProps {
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
    <form className="mc-project-form-v2" onSubmit={handleSubmit}>
      <section className="mc-form-section">
        <div className="mc-form-section-copy">
          <p className="mc-eyebrow">Project</p>
          <h2>Project identity</h2>
          <p>Name the project and set its overall state.</p>
        </div>

        <div className="mc-form-section-fields">
          <label className="mc-field">
            <span>Name</span>
            <input
              autoFocus
              value={value.name}
              placeholder="Mission Control"
              onChange={(event) =>
                setValue((current) => ({ ...current, name: event.target.value }))
              }
            />
          </label>

          <label className="mc-field">
            <span>Description</span>
            <textarea
              rows={3}
              value={value.description}
              placeholder="What is this project responsible for?"
              onChange={(event) =>
                setValue((current) => ({ ...current, description: event.target.value }))
              }
            />
          </label>

          <OptionPicker
            label="Project status"
            value={value.status}
            options={PROJECT_STATUSES.map((status) => ({
              value: status,
              label: formatProjectStatus(status),
              tone: projectStatusTone(status)
            }))}
            onChange={(status) => setValue((current) => ({ ...current, status }))}
          />
        </div>
      </section>

      <section className="mc-form-section">
        <div className="mc-form-section-copy">
          <p className="mc-eyebrow">Current work</p>
          <h2>Current step</h2>
          <p>Keep the immediate action distinct from the overall project state.</p>
        </div>

        <div className="mc-form-section-fields">
          <label className="mc-field">
            <span>Current step</span>
            <input
              value={value.currentStep}
              placeholder="What are you doing right now?"
              onChange={(event) =>
                setValue((current) => ({ ...current, currentStep: event.target.value }))
              }
            />
          </label>

          <div className="mc-form-split">
            <OptionPicker
              compact
              label="Step status"
              value={value.currentStepStatus}
              options={STEP_STATUSES.map((status) => ({
                value: status,
                label: formatStepStatus(status),
                tone: stepStatusTone(status)
              }))}
              onChange={(currentStepStatus) =>
                setValue((current) => ({ ...current, currentStepStatus }))
              }
            />

            <OptionPicker
              compact
              label="Step priority"
              value={value.currentStepPriority}
              options={STEP_PRIORITIES.map((priority) => ({
                value: priority,
                label: formatStepPriority(priority),
                tone: priorityTone(priority)
              }))}
              onChange={(currentStepPriority) =>
                setValue((current) => ({ ...current, currentStepPriority }))
              }
            />
          </div>

          <div className="mc-form-split">
            <label className="mc-field">
              <span>Current phase</span>
              <input
                value={value.currentPhase}
                placeholder="Planning, implementation..."
                onChange={(event) =>
                  setValue((current) => ({ ...current, currentPhase: event.target.value }))
                }
              />
            </label>

            <label className="mc-field">
              <span>Current version</span>
              <input
                value={value.currentVersion}
                placeholder="v0.1.2"
                onChange={(event) =>
                  setValue((current) => ({ ...current, currentVersion: event.target.value }))
                }
              />
            </label>
          </div>

          <label className="mc-field">
            <span>Last completed step</span>
            <input
              value={value.lastCompletedStep}
              placeholder="Most recent completed action"
              onChange={(event) =>
                setValue((current) => ({ ...current, lastCompletedStep: event.target.value }))
              }
            />
          </label>
        </div>
      </section>

      <section className="mc-form-section">
        <div className="mc-form-section-copy">
          <p className="mc-eyebrow">Queue</p>
          <h2>Next steps & blockers</h2>
          <p>One item per line. These stay lightweight until the Tasks module arrives.</p>
        </div>

        <div className="mc-form-section-fields mc-form-split">
          <label className="mc-field">
            <span>Next steps</span>
            <textarea
              rows={6}
              value={nextSteps}
              onChange={(event) => setNextSteps(event.target.value)}
              placeholder={"Implement settings shell\nVerify Windows build"}
            />
          </label>

          <label className="mc-field">
            <span>Blockers</span>
            <textarea
              rows={6}
              value={blockers}
              onChange={(event) => setBlockers(event.target.value)}
              placeholder="One blocker per line"
            />
          </label>
        </div>
      </section>

      <section className="mc-form-section">
        <div className="mc-form-section-copy">
          <p className="mc-eyebrow">Location</p>
          <h2>Project location</h2>
          <p>Connect the project to its local workspace and repository.</p>
        </div>

        <div className="mc-form-section-fields mc-form-split">
          <label className="mc-field">
            <span>Local folder</span>
            <input
              value={value.localPath ?? ""}
              placeholder="C:\Projects\Mission-Control"
              onChange={(event) =>
                setValue((current) => ({ ...current, localPath: event.target.value }))
              }
            />
          </label>

          <label className="mc-field">
            <span>Repository</span>
            <input
              value={value.repoUrl ?? ""}
              placeholder="https://github.com/..."
              onChange={(event) =>
                setValue((current) => ({ ...current, repoUrl: event.target.value }))
              }
            />
          </label>
        </div>
      </section>

      {error ? <p className="mc-form-error">{error}</p> : null}

      <div className="mc-form-footer">
        <button className="mc-button" type="button" onClick={onCancel}>
          Cancel
        </button>
        <button className="mc-button mc-button-primary" type="submit" disabled={busy}>
          {busy ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
