import { useEffect } from "react";
import { AlertTriangle, X } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  busy?: boolean;
  destructive?: boolean;
  onCancel: () => void;
  onConfirm: () => void | Promise<void>;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  busy = false,
  destructive = false,
  onCancel,
  onConfirm
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) {
        onCancel();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, busy, onCancel]);

  if (!open) return null;

  return (
    <div className="mc-dialog-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !busy) onCancel();
    }}>
      <div className="mc-dialog mc-confirm-dialog" role="alertdialog" aria-modal="true">
        <div className={`mc-confirm-icon${destructive ? " is-danger" : ""}`}>
          <AlertTriangle size={19} />
        </div>

        <div className="mc-confirm-copy">
          <h2>{title}</h2>
          <p>{description}</p>
        </div>

        <button
          className="mc-icon-button mc-dialog-close"
          type="button"
          aria-label="Close"
          disabled={busy}
          onClick={onCancel}
        >
          <X size={15} />
        </button>

        <div className="mc-dialog-actions">
          <button className="mc-button" type="button" disabled={busy} onClick={onCancel}>
            Cancel
          </button>
          <button
            className={`mc-button${destructive ? " mc-button-danger-solid" : " mc-button-primary"}`}
            type="button"
            disabled={busy}
            autoFocus
            onClick={() => void onConfirm()}
          >
            {busy ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
