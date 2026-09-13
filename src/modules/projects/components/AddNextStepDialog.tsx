import {
  useEffect,
  useState,
  type FormEvent
} from "react";

interface AddNextStepDialogProps {
  open: boolean;
  projectName: string;
  busy?: boolean;
  onCancel: () => void;
  onSubmit: (
    step: string
  ) => Promise<void> | void;
}

export function AddNextStepDialog({
  open,
  projectName,
  busy = false,
  onCancel,
  onSubmit
}: AddNextStepDialogProps) {
  const [value, setValue] =
    useState("");

  useEffect(() => {
    if (open) {
      setValue("");
    }
  }, [open]);

  if (!open) {
    return null;
  }

  async function submit(
    event: FormEvent
  ) {
    event.preventDefault();

    const step = value.trim();

    if (!step) {
      return;
    }

    await onSubmit(step);
  }

  return (
    <div className="mc-dialog-backdrop">
      <form
        className="mc-dialog mc-quick-step-dialog"
        role="dialog"
        aria-modal="true"
        onSubmit={(event) =>
          void submit(event)
        }
      >
        <div className="mc-dialog-header">
          <div>
            <p className="mc-eyebrow">
              Next step
            </p>

            <h2>
              Add step to {projectName}
            </h2>
          </div>
        </div>

        <label className="mc-field">
          <span>Step</span>

          <input
            autoFocus
            value={value}
            placeholder="What should happen next?"
            onChange={(event) =>
              setValue(event.target.value)
            }
          />
        </label>

        <div className="mc-form-footer">
          <button
            className="mc-button"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>

          <button
            className="mc-button mc-button-primary"
            type="submit"
            disabled={
              busy ||
              !value.trim()
            }
          >
            {busy
              ? "Adding..."
              : "Add step"}
          </button>
        </div>
      </form>
    </div>
  );
}
