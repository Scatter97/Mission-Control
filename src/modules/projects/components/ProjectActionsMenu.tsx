import {
  Archive,
  ArrowRight,
  ExternalLink,
  FolderOpen,
  ListPlus,
  Pencil,
  RotateCcw,
  Trash2
} from "lucide-react";
import {
  useEffect,
  useRef
} from "react";

import type { Project } from "../types";

interface MenuPosition {
  x: number;
  y: number;
}

interface ProjectActionsMenuProps {
  project: Project;
  includeOpen?: boolean;
  position?: MenuPosition;
  onClose: () => void;
  onOpen?: () => void;
  onAddStep: () => void;
  onEdit: () => void;
  onOpenFolder: () => void;
  onOpenRepository: () => void;
  onArchiveToggle: () => void;
  onDelete: () => void;
}

export function ProjectActionsMenu({
  project,
  includeOpen = false,
  position,
  onClose,
  onOpen,
  onAddStep,
  onEdit,
  onOpenFolder,
  onOpenRepository,
  onArchiveToggle,
  onDelete
}: ProjectActionsMenuProps) {
  const ref =
    useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handlePointerDown = (
      event: PointerEvent
    ) => {
      if (
        ref.current &&
        !ref.current.contains(
          event.target as Node
        )
      ) {
        onClose();
      }
    };

    const handleKeyDown = (
      event: KeyboardEvent
    ) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener(
      "pointerdown",
      handlePointerDown
    );

    window.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      window.removeEventListener(
        "pointerdown",
        handlePointerDown
      );

      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, [onClose]);

  const run = (
    action: () => void
  ) => {
    onClose();
    action();
  };

  return (
    <div
      ref={ref}
      className={
        "mc-project-action-menu" +
        (position ? " is-context" : "")
      }
      style={
        position
          ? {
              left: position.x,
              top: position.y
            }
          : undefined
      }
      role="menu"
      onContextMenu={(event) =>
        event.preventDefault()
      }
    >
      {includeOpen && onOpen ? (
        <button
          type="button"
          role="menuitem"
          onClick={() => run(onOpen)}
        >
          <ArrowRight size={14} />
          Open project
        </button>
      ) : null}

      {!project.archived ? (
        <>
          <button
            type="button"
            role="menuitem"
            onClick={() => run(onAddStep)}
          >
            <ListPlus size={14} />
            Add next step
          </button>

          <button
            type="button"
            role="menuitem"
            onClick={() => run(onEdit)}
          >
            <Pencil size={14} />
            Edit project
          </button>

          <div className="mc-action-menu-divider" />
        </>
      ) : null}

      <button
        type="button"
        role="menuitem"
        disabled={!project.localPath}
        onClick={() => run(onOpenFolder)}
      >
        <FolderOpen size={14} />
        Open local folder
      </button>

      <button
        type="button"
        role="menuitem"
        disabled={!project.repoUrl}
        onClick={() =>
          run(onOpenRepository)
        }
      >
        <ExternalLink size={14} />
        Open GitHub repository
      </button>

      <div className="mc-action-menu-divider" />

      <button
        type="button"
        role="menuitem"
        onClick={() =>
          run(onArchiveToggle)
        }
      >
        {project.archived ? (
          <RotateCcw size={14} />
        ) : (
          <Archive size={14} />
        )}

        {project.archived
          ? "Restore project"
          : "Archive project"}
      </button>

      <button
        className="is-danger"
        type="button"
        role="menuitem"
        onClick={() => run(onDelete)}
      >
        <Trash2 size={14} />
        Delete project…
      </button>
    </div>
  );
}
