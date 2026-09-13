
from pathlib import Path
import json
import sys
from textwrap import dedent

ROOT = Path.cwd()
OUT = ROOT / "mission-control-v0.1.2-concept-ui.json"

def text(value: str) -> str:
    return dedent(value).lstrip("\n").rstrip() + "\n"

def replace_entry(path: str, new_content: str) -> dict:
    target = ROOT / path
    if not target.exists():
        raise SystemExit(f"Missing expected file: {path}")
    old_content = target.read_text(encoding="utf-8")
    return {
        "path": path.replace("\\", "/"),
        "edits": [
            {
                "op": "replace",
                "old": old_content,
                "new": new_content,
            }
        ],
    }

def create_entry(path: str, content: str) -> dict:
    target = ROOT / path
    if target.exists():
        raise SystemExit(f"Refusing to create existing file: {path}")
    return {
        "path": path.replace("\\", "/"),
        "action": "create",
        "content": content,
    }

files = []

# package.json version
package_path = ROOT / "package.json"
package = json.loads(package_path.read_text(encoding="utf-8"))
package["version"] = "0.1.2"
package_new = json.dumps(package, indent=2, ensure_ascii=False) + "\n"
files.append(replace_entry("package.json", package_new))

# package-lock.json version, if present
lock_path = ROOT / "package-lock.json"
if lock_path.exists():
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["version"] = "0.1.2"
    if isinstance(lock.get("packages"), dict) and "" in lock["packages"]:
        lock["packages"][""]["version"] = "0.1.2"
    lock_new = json.dumps(lock, indent=2, ensure_ascii=False) + "\n"
    files.append(replace_entry("package-lock.json", lock_new))

files.append(replace_entry("src/main.tsx", text(r'''
import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter } from "react-router-dom";

import { App } from "./app/App";
import { BackendProvider } from "./backend/BackendProvider";
import { UiPreferencesProvider } from "./app/preferences/UiPreferencesProvider";
import { ThemeProvider } from "./app/theme/ThemeProvider";

import "./app/theme/tokens.css";
import "./styles/globals.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      retry: 1
    }
  }
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BackendProvider>
        <ThemeProvider>
          <UiPreferencesProvider>
            <HashRouter>
              <App />
            </HashRouter>
          </UiPreferencesProvider>
        </ThemeProvider>
      </BackendProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
''')))

files.append(create_entry("src/app/preferences/UiPreferencesProvider.tsx", text(r'''
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";

export const UI_SCALE_OPTIONS = [80, 90, 100, 110, 125, 150, 175, 200] as const;
export type UiScale = (typeof UI_SCALE_OPTIONS)[number];

interface UiPreferencesContextValue {
  uiScale: UiScale;
  setUiScale: (scale: UiScale) => void;
  sidebarHidden: boolean;
  setSidebarHidden: (hidden: boolean) => void;
  toggleSidebar: () => void;
}

const UiPreferencesContext = createContext<UiPreferencesContextValue | null>(null);

const SCALE_KEY = "mission-control.ui-scale";
const SIDEBAR_KEY = "mission-control.sidebar-hidden";

function readScale(): UiScale {
  const stored = Number(localStorage.getItem(SCALE_KEY));
  return UI_SCALE_OPTIONS.includes(stored as UiScale) ? (stored as UiScale) : 100;
}

function readSidebarHidden(): boolean {
  return localStorage.getItem(SIDEBAR_KEY) === "true";
}

export function UiPreferencesProvider({ children }: { children: ReactNode }) {
  const [uiScale, setUiScaleState] = useState<UiScale>(readScale);
  const [sidebarHidden, setSidebarHiddenState] = useState(readSidebarHidden);

  useEffect(() => {
    document.documentElement.style.setProperty("--mc-ui-scale", String(uiScale / 100));
    document.documentElement.dataset.uiScale = String(uiScale);
  }, [uiScale]);

  const setUiScale = (scale: UiScale) => {
    localStorage.setItem(SCALE_KEY, String(scale));
    setUiScaleState(scale);
  };

  const setSidebarHidden = (hidden: boolean) => {
    localStorage.setItem(SIDEBAR_KEY, String(hidden));
    setSidebarHiddenState(hidden);
  };

  const toggleSidebar = () => {
    setSidebarHidden(!sidebarHidden);
  };

  const value = useMemo(
    () => ({
      uiScale,
      setUiScale,
      sidebarHidden,
      setSidebarHidden,
      toggleSidebar
    }),
    [uiScale, sidebarHidden]
  );

  return (
    <UiPreferencesContext.Provider value={value}>
      {children}
    </UiPreferencesContext.Provider>
  );
}

export function useUiPreferences() {
  const context = useContext(UiPreferencesContext);

  if (!context) {
    throw new Error("useUiPreferences must be used inside UiPreferencesProvider");
  }

  return context;
}
''')))

files.append(replace_entry("src/app/shell/AppShell.tsx", text(r'''
import { useEffect, useState, type ReactNode } from "react";
import { Command, Menu, X } from "lucide-react";
import { NavLink } from "react-router-dom";

import { moduleRegistry } from "../modules/registry";
import { useUiPreferences } from "../preferences/UiPreferencesProvider";

interface AppShellProps {
  children: ReactNode;
}

const MOBILE_QUERY = "(max-width: 760px)";

export function AppShell({ children }: AppShellProps) {
  const navigation = moduleRegistry.getNavigationItems();
  const { sidebarHidden, toggleSidebar } = useUiPreferences();
  const [mobile, setMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const query = window.matchMedia(MOBILE_QUERY);
    const onChange = () => {
      setMobile(query.matches);
      if (!query.matches) setMobileOpen(false);
    };

    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === "b") {
        event.preventDefault();
        if (mobile) {
          setMobileOpen((open) => !open);
        } else {
          toggleSidebar();
        }
      }

      if (event.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobile, mobileOpen, toggleSidebar]);

  const handleToggle = () => {
    if (mobile) {
      setMobileOpen((open) => !open);
      return;
    }

    toggleSidebar();
  };

  const shellClass = [
    "mc-shell",
    sidebarHidden ? "is-sidebar-hidden" : "",
    mobileOpen ? "is-mobile-sidebar-open" : ""
  ].filter(Boolean).join(" ");

  return (
    <div className={shellClass}>
      <aside className="mc-sidebar" aria-label="Mission Control sidebar">
        <div className="mc-brand">
          <div className="mc-brand-mark">
            <Command size={17} strokeWidth={2.2} />
          </div>

          <div className="mc-brand-copy">
            <span className="mc-brand-title">Mission Control</span>
            <span className="mc-brand-version">v0.1.2</span>
          </div>

          {mobile ? (
            <button
              className="mc-icon-button mc-sidebar-close"
              type="button"
              aria-label="Close sidebar"
              onClick={() => setMobileOpen(false)}
            >
              <X size={16} />
            </button>
          ) : null}
        </div>

        <nav className="mc-nav" aria-label="Mission Control">
          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.id}
                to={item.route}
                className={({ isActive }) =>
                  `mc-nav-item${isActive ? " is-active" : ""}`
                }
                onClick={() => {
                  if (mobile) setMobileOpen(false);
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mc-sidebar-footer">
          <span>Local workspace</span>
          <kbd>Ctrl+B</kbd>
        </div>
      </aside>

      {mobileOpen ? (
        <button
          className="mc-sidebar-backdrop"
          type="button"
          aria-label="Close sidebar"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}

      <div className="mc-main-frame">
        <header className="mc-shellbar">
          <button
            className="mc-icon-button mc-sidebar-toggle"
            type="button"
            aria-label={mobileOpen || !sidebarHidden ? "Hide sidebar" : "Show sidebar"}
            title="Toggle sidebar (Ctrl+B)"
            onClick={handleToggle}
          >
            <Menu size={17} />
          </button>
          <span className="mc-shellbar-title">Mission Control</span>
        </header>

        <main className="mc-main">{children}</main>
      </div>
    </div>
  );
}
''')))

files.append(replace_entry("src/app/theme/tokens.css", text(r'''
:root {
  --mc-ui-scale: 1;
  font-size: calc(16px * var(--mc-ui-scale));

  --mc-radius-xs: 0.25rem;
  --mc-radius-sm: 0.375rem;
  --mc-radius-md: 0.5rem;
  --mc-radius-lg: 0.75rem;
  --mc-sidebar-width: 14.5rem;
  --mc-shellbar-height: 3.25rem;
  --mc-page-max: 88rem;
}

:root,
:root[data-theme="dark"] {
  --mc-bg: #090b10;
  --mc-sidebar: #0b0e14;
  --mc-surface: #0f131b;
  --mc-surface-raised: #131924;
  --mc-surface-elevated: #171e2a;
  --mc-surface-hover: #181f2b;

  --mc-border: #252d3b;
  --mc-border-subtle: #1a202b;
  --mc-border-strong: #344055;

  --mc-text-primary: #f1f4f8;
  --mc-text-secondary: #a0aaba;
  --mc-text-muted: #697486;
  --mc-text-faint: #4f5969;

  --mc-accent: #6f8fff;
  --mc-accent-hover: #83a0ff;
  --mc-accent-soft: rgba(111, 143, 255, 0.12);
  --mc-accent-border: rgba(111, 143, 255, 0.35);

  --mc-success: #59c987;
  --mc-success-soft: rgba(89, 201, 135, 0.12);
  --mc-warning: #e4b358;
  --mc-warning-soft: rgba(228, 179, 88, 0.13);
  --mc-danger: #ed6f7a;
  --mc-danger-soft: rgba(237, 111, 122, 0.12);
  --mc-info: #70a7ff;
  --mc-info-soft: rgba(112, 167, 255, 0.12);
  --mc-neutral-soft: rgba(160, 170, 186, 0.1);

  --mc-priority-low: #7f93a8;
  --mc-priority-medium: #e4b358;
  --mc-priority-high: #ed6f7a;
  --mc-priority-critical: #ff5265;

  --mc-overlay: rgba(3, 5, 8, 0.72);
  --mc-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.32);
}

:root[data-theme="light"] {
  --mc-bg: #f5f6f8;
  --mc-sidebar: #f1f3f6;
  --mc-surface: #ffffff;
  --mc-surface-raised: #fafbfc;
  --mc-surface-elevated: #ffffff;
  --mc-surface-hover: #f1f3f7;

  --mc-border: #d8dde6;
  --mc-border-subtle: #e7eaf0;
  --mc-border-strong: #c4cad5;

  --mc-text-primary: #171b22;
  --mc-text-secondary: #596273;
  --mc-text-muted: #858f9f;
  --mc-text-faint: #a3aab5;

  --mc-accent: #4969e8;
  --mc-accent-hover: #3f5fdc;
  --mc-accent-soft: rgba(73, 105, 232, 0.09);
  --mc-accent-border: rgba(73, 105, 232, 0.3);

  --mc-success: #2d9258;
  --mc-success-soft: rgba(45, 146, 88, 0.1);
  --mc-warning: #a86e12;
  --mc-warning-soft: rgba(168, 110, 18, 0.1);
  --mc-danger: #c84e5a;
  --mc-danger-soft: rgba(200, 78, 90, 0.1);
  --mc-info: #426fcb;
  --mc-info-soft: rgba(66, 111, 203, 0.1);
  --mc-neutral-soft: rgba(89, 98, 115, 0.08);

  --mc-priority-low: #667789;
  --mc-priority-medium: #a86e12;
  --mc-priority-high: #c84e5a;
  --mc-priority-critical: #b82d40;

  --mc-overlay: rgba(28, 32, 40, 0.35);
  --mc-shadow: 0 1rem 3rem rgba(40, 49, 65, 0.16);
}
''')))

files.append(create_entry("src/shared/ui/OptionPicker.tsx", text(r'''
export type SemanticTone =
  | "neutral"
  | "accent"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "low"
  | "medium"
  | "high"
  | "critical";

export interface PickerOption<T extends string> {
  value: T;
  label: string;
  tone?: SemanticTone;
}

interface OptionPickerProps<T extends string> {
  label: string;
  value: T;
  options: Array<PickerOption<T>>;
  onChange: (value: T) => void;
  compact?: boolean;
}

export function OptionPicker<T extends string>({
  label,
  value,
  options,
  onChange,
  compact = false
}: OptionPickerProps<T>) {
  return (
    <fieldset className={`mc-option-picker${compact ? " is-compact" : ""}`}>
      <legend>{label}</legend>
      <div className="mc-option-picker-grid">
        {options.map((option) => {
          const selected = option.value === value;

          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              data-tone={option.tone ?? "neutral"}
              className={`mc-option-choice${selected ? " is-selected" : ""}`}
              onClick={() => onChange(option.value)}
            >
              <span className="mc-option-dot" />
              {option.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
''')))

files.append(create_entry("src/shared/ui/StateBadge.tsx", text(r'''
import type { SemanticTone } from "./OptionPicker";

interface StateBadgeProps {
  label: string;
  tone?: SemanticTone;
}

export function StateBadge({ label, tone = "neutral" }: StateBadgeProps) {
  return (
    <span className="mc-state-badge" data-tone={tone}>
      <span className="mc-state-dot" />
      {label}
    </span>
  );
}
''')))

files.append(create_entry("src/shared/ui/ConfirmDialog.tsx", text(r'''
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
''')))

files.append(replace_entry("src/backend/types.ts", text(r'''
import type { Project, ProjectInput } from "../modules/projects/types";

export interface BackendCapabilities {
  projects: boolean;
  settings: boolean;

  patchForge: boolean;
  git: boolean;
  terminal: boolean;
  ai: boolean;
  remote: boolean;
  bom: boolean;
}

export interface MissionControlBackend {
  capabilities(): Promise<BackendCapabilities>;

  listProjects(archived?: boolean): Promise<Project[]>;
  getProject(id: string): Promise<Project | null>;
  createProject(input: ProjectInput): Promise<Project>;
  updateProject(id: string, input: ProjectInput): Promise<Project>;
  archiveProject(id: string): Promise<void>;
  restoreProject(id: string): Promise<void>;
  deleteProject(id: string): Promise<void>;
}

export interface BackendError {
  code: string;
  message: string;
  details?: unknown;
}
''')))

files.append(replace_entry("src/backend/localBackend.ts", text(r'''
import { invoke } from "@tauri-apps/api/core";

import type { Project, ProjectInput } from "../modules/projects/types";
import type {
  BackendCapabilities,
  MissionControlBackend
} from "./types";

export class LocalBackend implements MissionControlBackend {
  capabilities(): Promise<BackendCapabilities> {
    return invoke<BackendCapabilities>("backend_capabilities");
  }

  listProjects(archived = false): Promise<Project[]> {
    return invoke<Project[]>("projects_list", { archived });
  }

  getProject(id: string): Promise<Project | null> {
    return invoke<Project | null>("projects_get", { id });
  }

  createProject(input: ProjectInput): Promise<Project> {
    return invoke<Project>("projects_create", { input });
  }

  updateProject(id: string, input: ProjectInput): Promise<Project> {
    return invoke<Project>("projects_update", { id, input });
  }

  archiveProject(id: string): Promise<void> {
    return invoke<void>("projects_archive", { id });
  }

  restoreProject(id: string): Promise<void> {
    return invoke<void>("projects_restore", { id });
  }

  deleteProject(id: string): Promise<void> {
    return invoke<void>("projects_delete", { id });
  }
}
''')))

files.append(replace_entry("src/modules/projects/types.ts", text(r'''
import type { SemanticTone } from "../../shared/ui/OptionPicker";

export type ProjectStatus =
  | "active"
  | "planning"
  | "paused"
  | "blocked"
  | "waiting"
  | "completed"
  | "archived";

export type StepStatus =
  | "todo"
  | "in_progress"
  | "blocked"
  | "waiting"
  | "done";

export type StepPriority = "low" | "medium" | "high" | "critical";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  currentVersion: string;
  currentPhase: string;
  currentStep: string;
  currentStepStatus: StepStatus;
  currentStepPriority: StepPriority;
  lastCompletedStep: string;
  nextSteps: string[];
  blockers: string[];
  localPath: string | null;
  repoUrl: string | null;
  archived: boolean;
  createdAt: number;
  updatedAt: number;
}

export interface ProjectInput {
  name: string;
  description: string;
  status: ProjectStatus;
  currentVersion: string;
  currentPhase: string;
  currentStep: string;
  currentStepStatus: StepStatus;
  currentStepPriority: StepPriority;
  lastCompletedStep: string;
  nextSteps: string[];
  blockers: string[];
  localPath: string | null;
  repoUrl: string | null;
}

export const emptyProjectInput: ProjectInput = {
  name: "",
  description: "",
  status: "active",
  currentVersion: "",
  currentPhase: "",
  currentStep: "",
  currentStepStatus: "todo",
  currentStepPriority: "medium",
  lastCompletedStep: "",
  nextSteps: [],
  blockers: [],
  localPath: null,
  repoUrl: null
};

export const PROJECT_STATUSES: ProjectStatus[] = [
  "active",
  "planning",
  "paused",
  "blocked",
  "waiting",
  "completed"
];

export const STEP_STATUSES: StepStatus[] = [
  "todo",
  "in_progress",
  "blocked",
  "waiting",
  "done"
];

export const STEP_PRIORITIES: StepPriority[] = [
  "low",
  "medium",
  "high",
  "critical"
];

export function projectToInput(project: Project): ProjectInput {
  return {
    name: project.name,
    description: project.description,
    status: project.status === "archived" ? "paused" : project.status,
    currentVersion: project.currentVersion,
    currentPhase: project.currentPhase,
    currentStep: project.currentStep,
    currentStepStatus: project.currentStepStatus,
    currentStepPriority: project.currentStepPriority,
    lastCompletedStep: project.lastCompletedStep,
    nextSteps: project.nextSteps,
    blockers: project.blockers,
    localPath: project.localPath,
    repoUrl: project.repoUrl
  };
}

export function formatLabel(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatProjectStatus(status: ProjectStatus): string {
  return formatLabel(status);
}

export function formatStepStatus(status: StepStatus): string {
  return formatLabel(status);
}

export function formatStepPriority(priority: StepPriority): string {
  return formatLabel(priority);
}

export function projectStatusTone(status: ProjectStatus): SemanticTone {
  switch (status) {
    case "active":
      return "success";
    case "blocked":
      return "danger";
    case "waiting":
      return "warning";
    case "planning":
      return "info";
    case "completed":
      return "accent";
    case "archived":
    case "paused":
    default:
      return "neutral";
  }
}

export function stepStatusTone(status: StepStatus): SemanticTone {
  switch (status) {
    case "in_progress":
      return "info";
    case "blocked":
      return "danger";
    case "waiting":
      return "warning";
    case "done":
      return "success";
    case "todo":
    default:
      return "neutral";
  }
}

export function priorityTone(priority: StepPriority): SemanticTone {
  return priority;
}
''')))

files.append(replace_entry("src/modules/projects/hooks.ts", text(r'''
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useBackend } from "../../backend/BackendProvider";
import type { ProjectInput } from "./types";

const projectKeys = {
  root: ["projects"] as const,
  list: (archived: boolean) => ["projects", "list", archived] as const,
  detail: (id: string) => ["projects", "detail", id] as const
};

export function useProjects(archived = false) {
  const backend = useBackend();

  return useQuery({
    queryKey: projectKeys.list(archived),
    queryFn: () => backend.listProjects(archived)
  });
}

export function useProject(id: string | undefined) {
  const backend = useBackend();

  return useQuery({
    queryKey: projectKeys.detail(id ?? ""),
    queryFn: () => backend.getProject(id!),
    enabled: Boolean(id)
  });
}

export function useCreateProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ProjectInput) => backend.createProject(input),
    onSuccess: (project) => {
      queryClient.setQueryData(projectKeys.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
    }
  });
}

export function useUpdateProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ProjectInput }) =>
      backend.updateProject(id, input),
    onSuccess: (project) => {
      queryClient.setQueryData(projectKeys.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
    }
  });
}

export function useArchiveProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.archiveProject(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
      void queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) });
    }
  });
}

export function useRestoreProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.restoreProject(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
      void queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) });
    }
  });
}

export function useDeleteProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.deleteProject(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: projectKeys.detail(id) });
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
    }
  });
}
''')))

files.append(replace_entry("src/modules/projects/components/ProjectForm.tsx", text(r'''
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
''')))

files.append(create_entry("src/modules/projects/pages/NewProjectPage.tsx", text(r'''
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
''')))

files.append(replace_entry("src/modules/projects/pages/ProjectsPage.tsx", text(r'''
import { useEffect, useMemo, useState } from "react";
import {
  Archive,
  ArrowRight,
  FolderKanban,
  Plus,
  Search
} from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { StateBadge } from "../../../shared/ui/StateBadge";
import { useProjects } from "../hooks";
import {
  formatProjectStatus,
  formatStepPriority,
  formatStepStatus,
  priorityTone,
  projectStatusTone,
  stepStatusTone,
  type Project
} from "../types";

function matchesSearch(project: Project, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;

  return [
    project.name,
    project.description,
    project.currentVersion,
    project.currentPhase,
    project.currentStep,
    project.lastCompletedStep
  ].some((value) => value.toLowerCase().includes(needle));
}

export function ProjectsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const archived = searchParams.get("view") === "archived";
  const projectsQuery = useProjects(archived);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const projects = useMemo(
    () => (projectsQuery.data ?? []).filter((project) => matchesSearch(project, query)),
    [projectsQuery.data, query]
  );

  useEffect(() => {
    if (!projects.length) {
      setSelectedId(null);
      return;
    }

    if (!projects.some((project) => project.id === selectedId)) {
      setSelectedId(projects[0].id);
    }
  }, [projects, selectedId]);

  const selectedProject = projects.find((project) => project.id === selectedId) ?? null;

  const setArchivedView = (nextArchived: boolean) => {
    const next = new URLSearchParams(searchParams);
    if (nextArchived) {
      next.set("view", "archived");
    } else {
      next.delete("view");
    }
    setSearchParams(next);
    setQuery("");
    setSelectedId(null);
  };

  return (
    <section className="mc-page mc-page-projects">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Workspace</p>
          <h1>Projects</h1>
          <p className="mc-page-description">
            Keep every project centered on its current step and the next decision.
          </p>
        </div>

        <Link className="mc-button mc-button-primary" to="/projects/new">
          <Plus size={15} />
          New project
        </Link>
      </header>

      <div className="mc-project-toolbar">
        <div className="mc-segmented-control" aria-label="Project view">
          <button
            type="button"
            className={!archived ? "is-active" : ""}
            onClick={() => setArchivedView(false)}
          >
            Active
          </button>
          <button
            type="button"
            className={archived ? "is-active" : ""}
            onClick={() => setArchivedView(true)}
          >
            <Archive size={13} />
            Archived
          </button>
        </div>

        <label className="mc-search">
          <Search size={15} />
          <input
            aria-label="Search projects"
            placeholder={archived ? "Search archived projects..." : "Search projects..."}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>

      {projectsQuery.isLoading ? (
        <div className="mc-panel mc-project-empty"><p>Loading projects...</p></div>
      ) : projectsQuery.isError ? (
        <div className="mc-panel mc-project-empty">
          <h2>Could not load projects</h2>
          <p>{String(projectsQuery.error)}</p>
        </div>
      ) : projects.length ? (
        <div className="mc-projects-workspace">
          <div className="mc-panel mc-project-table-v2">
            <div className="mc-project-table-head" aria-hidden="true">
              <span>Project</span>
              <span className="mc-col-status">Status</span>
              <span className="mc-col-step-status">Step</span>
              <span className="mc-col-priority">Priority</span>
              <span className="mc-col-version">Version</span>
              <span className="mc-col-current-step">Current step</span>
            </div>

            <div className="mc-project-table-body">
              {projects.map((project) => (
                <button
                  key={project.id}
                  type="button"
                  className={`mc-project-row-v2${selectedId === project.id ? " is-selected" : ""}`}
                  onClick={() => setSelectedId(project.id)}
                >
                  <span className="mc-project-identity">
                    <strong>{project.name}</strong>
                    <small>{project.currentPhase || project.description || "No phase set"}</small>
                  </span>

                  <span className="mc-col-status">
                    <StateBadge
                      label={formatProjectStatus(project.status)}
                      tone={projectStatusTone(project.status)}
                    />
                  </span>

                  <span className="mc-col-step-status">
                    <StateBadge
                      label={formatStepStatus(project.currentStepStatus)}
                      tone={stepStatusTone(project.currentStepStatus)}
                    />
                  </span>

                  <span className="mc-col-priority">
                    <StateBadge
                      label={formatStepPriority(project.currentStepPriority)}
                      tone={priorityTone(project.currentStepPriority)}
                    />
                  </span>

                  <span className="mc-col-version mc-project-version">
                    {project.currentVersion || "—"}
                  </span>

                  <span className="mc-col-current-step mc-current-step-cell">
                    {project.currentStep || "No current step"}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {selectedProject ? (
            <aside className="mc-panel mc-project-preview">
              <div className="mc-project-preview-heading">
                <div>
                  <p className="mc-eyebrow">{archived ? "Archived project" : "Selected project"}</p>
                  <h2>{selectedProject.name}</h2>
                </div>
                <StateBadge
                  label={formatProjectStatus(selectedProject.status)}
                  tone={projectStatusTone(selectedProject.status)}
                />
              </div>

              <p className="mc-project-preview-description">
                {selectedProject.description || "No description yet."}
              </p>

              <div className="mc-preview-current-step">
                <span>Current step</span>
                <strong>{selectedProject.currentStep || "No current step set"}</strong>
                <div className="mc-badge-row">
                  <StateBadge
                    label={formatStepStatus(selectedProject.currentStepStatus)}
                    tone={stepStatusTone(selectedProject.currentStepStatus)}
                  />
                  <StateBadge
                    label={formatStepPriority(selectedProject.currentStepPriority)}
                    tone={priorityTone(selectedProject.currentStepPriority)}
                  />
                </div>
              </div>

              <dl className="mc-inspector-list">
                <div>
                  <dt>Phase</dt>
                  <dd>{selectedProject.currentPhase || "—"}</dd>
                </div>
                <div>
                  <dt>Version</dt>
                  <dd>{selectedProject.currentVersion || "—"}</dd>
                </div>
                <div>
                  <dt>Next steps</dt>
                  <dd>{selectedProject.nextSteps.length}</dd>
                </div>
                <div>
                  <dt>Blockers</dt>
                  <dd>{selectedProject.blockers.length}</dd>
                </div>
              </dl>

              <Link className="mc-button mc-button-block" to={`/projects/${selectedProject.id}`}>
                Open project
                <ArrowRight size={14} />
              </Link>
            </aside>
          ) : null}
        </div>
      ) : (
        <div className="mc-panel mc-project-empty">
          <div className="mc-empty-icon">
            {archived ? <Archive size={27} /> : <FolderKanban size={28} />}
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
            <Link className="mc-button mc-button-primary mc-empty-action" to="/projects/new">
              <Plus size={14} />
              New project
            </Link>
          ) : null}
        </div>
      )}
    </section>
  );
}
''')))

files.append(replace_entry("src/modules/projects/pages/ProjectDetailPage.tsx", text(r'''
import { useState } from "react";
import {
  Archive,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FolderOpen,
  MoreHorizontal,
  Pencil,
  RotateCcw,
  Trash2
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ConfirmDialog } from "../../../shared/ui/ConfirmDialog";
import { StateBadge } from "../../../shared/ui/StateBadge";
import { ProjectForm } from "../components/ProjectForm";
import {
  useArchiveProject,
  useDeleteProject,
  useProject,
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
  stepStatusTone
} from "../types";

type ConfirmAction = "archive" | "restore" | "delete" | null;

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

function formatUpdated(timestamp: number): string {
  if (!timestamp) return "—";
  return new Date(timestamp * 1000).toLocaleString();
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const projectQuery = useProject(id);
  const updateProject = useUpdateProject();
  const archiveProject = useArchiveProject();
  const restoreProject = useRestoreProject();
  const deleteProject = useDeleteProject();
  const [editing, setEditing] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);

  if (projectQuery.isLoading) {
    return (
      <section className="mc-page">
        <div className="mc-panel mc-project-empty"><p>Loading project...</p></div>
      </section>
    );
  }

  const project = projectQuery.data;

  if (!project) {
    return (
      <section className="mc-page">
        <div className="mc-panel mc-project-empty"><h2>Project not found</h2></div>
      </section>
    );
  }

  const confirmConfig = confirmAction === "archive"
    ? {
        title: "Archive project?",
        description: `"${project.name}" will move to Archived Projects. You can restore it later.`,
        label: "Archive Project",
        destructive: false
      }
    : confirmAction === "restore"
      ? {
          title: "Restore project?",
          description: `"${project.name}" will return to the active Projects workspace.`,
          label: "Restore Project",
          destructive: false
        }
      : {
          title: "Delete project permanently?",
          description: `This will permanently delete "${project.name}" from Mission Control. This action cannot be undone.`,
          label: "Delete Project",
          destructive: true
        };

  const confirmBusy =
    archiveProject.isPending ||
    restoreProject.isPending ||
    deleteProject.isPending;

  const handleConfirm = async () => {
    if (!confirmAction) return;

    if (confirmAction === "archive") {
      await archiveProject.mutateAsync(project.id);
      navigate("/projects?view=archived");
    } else if (confirmAction === "restore") {
      await restoreProject.mutateAsync(project.id);
      navigate("/projects");
    } else {
      await deleteProject.mutateAsync(project.id);
      navigate(project.archived ? "/projects?view=archived" : "/projects");
    }

    setConfirmAction(null);
  };

  return (
    <section className="mc-page mc-project-detail-page">
      <Link className="mc-back-link" to={project.archived ? "/projects?view=archived" : "/projects"}>
        <ArrowLeft size={14} /> {project.archived ? "Archived Projects" : "Projects"}
      </Link>

      <header className="mc-project-detail-header">
        <div className="mc-project-title-block">
          <div className="mc-title-row">
            <h1>{project.name}</h1>
            <StateBadge
              label={project.archived ? "Archived" : formatProjectStatus(project.status)}
              tone={project.archived ? "neutral" : projectStatusTone(project.status)}
            />
          </div>
          <p>{project.description || "No description yet."}</p>

          <div className="mc-project-meta-row">
            <span>{project.currentPhase || "No phase"}</span>
            <span className="mc-meta-separator">•</span>
            <span>{project.currentVersion || "No version"}</span>
            <span className="mc-meta-separator">•</span>
            <span>Updated {formatUpdated(project.updatedAt)}</span>
          </div>
        </div>

        <div className="mc-header-actions">
          <button className="mc-button" type="button" onClick={() => setEditing(true)}>
            <Pencil size={14} /> Edit
          </button>

          {project.archived ? (
            <button className="mc-button" type="button" onClick={() => setConfirmAction("restore")}>
              <RotateCcw size={14} /> Restore
            </button>
          ) : (
            <button className="mc-button" type="button" onClick={() => setConfirmAction("archive")}>
              <Archive size={14} /> Archive
            </button>
          )}

          <button
            className="mc-icon-button mc-more-button"
            type="button"
            aria-label="Delete project"
            title="Delete project"
            onClick={() => setConfirmAction("delete")}
          >
            <Trash2 size={15} />
          </button>
        </div>
      </header>

      <div className="mc-detail-tabs" role="tablist" aria-label="Project sections">
        {detailTabs.map((tab) => (
          <button
            key={tab}
            type="button"
            className={tab === "Overview" ? "is-active" : ""}
            disabled={tab !== "Overview"}
            title={tab === "Overview" ? undefined : "Planned for a future Mission Control update"}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="mc-project-detail-grid-v2">
        <div className="mc-project-detail-main-v2">
          <section className="mc-panel mc-current-step-card">
            <div className="mc-section-topline">
              <div>
                <p className="mc-eyebrow">Current Step</p>
                <h2>{project.currentStep || "No current step set"}</h2>
              </div>
              <div className="mc-badge-row">
                <StateBadge
                  label={formatStepStatus(project.currentStepStatus)}
                  tone={stepStatusTone(project.currentStepStatus)}
                />
                <StateBadge
                  label={formatStepPriority(project.currentStepPriority)}
                  tone={priorityTone(project.currentStepPriority)}
                />
              </div>
            </div>

            <div className="mc-step-context">
              <span>{project.currentPhase || "No phase set"}</span>
              <span>•</span>
              <span>{project.currentVersion || "No version set"}</span>
            </div>
          </section>

          <div className="mc-detail-pair">
            <section className="mc-panel mc-detail-section-v2">
              <div className="mc-section-heading-inline">
                <h2>Next steps</h2>
                <span>{project.nextSteps.length}</span>
              </div>

              {project.nextSteps.length ? (
                <ol className="mc-work-list">
                  {project.nextSteps.map((step, index) => (
                    <li key={`${step}-${index}`}>
                      <span className="mc-work-index">{index + 1}</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="mc-muted">No next steps yet.</p>
              )}
            </section>

            <section className="mc-panel mc-detail-section-v2">
              <div className="mc-section-heading-inline">
                <h2>Blockers</h2>
                <span>{project.blockers.length}</span>
              </div>

              {project.blockers.length ? (
                <ul className="mc-work-list mc-blocker-list">
                  {project.blockers.map((blocker, index) => (
                    <li key={`${blocker}-${index}`}>
                      <span className="mc-blocker-dot" />
                      <span>{blocker}</span>
                    </li>
                  ))}
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
              <p className="mc-eyebrow">Last completed</p>
              <strong>{project.lastCompletedStep || "No completed step recorded"}</strong>
            </div>
          </section>
        </div>

        <aside className="mc-panel mc-project-inspector-v2">
          <div className="mc-inspector-heading">
            <div>
              <p className="mc-eyebrow">Inspector</p>
              <h2>Project details</h2>
            </div>
            <MoreHorizontal size={17} />
          </div>

          <dl className="mc-inspector-list">
            <div>
              <dt>Project status</dt>
              <dd>
                <StateBadge
                  label={project.archived ? "Archived" : formatProjectStatus(project.status)}
                  tone={project.archived ? "neutral" : projectStatusTone(project.status)}
                />
              </dd>
            </div>
            <div>
              <dt>Phase</dt>
              <dd>{project.currentPhase || "—"}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{project.currentVersion || "—"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatUpdated(project.createdAt)}</dd>
            </div>
            <div>
              <dt>Updated</dt>
              <dd>{formatUpdated(project.updatedAt)}</dd>
            </div>
          </dl>

          <div className="mc-inspector-divider" />

          <div className="mc-location-block">
            <span className="mc-location-label">
              <FolderOpen size={14} />
              Local folder
            </span>
            <code>{project.localPath || "Not connected"}</code>
          </div>

          <div className="mc-location-block">
            <span className="mc-location-label">
              <ExternalLink size={14} />
              Repository
            </span>
            {project.repoUrl ? (
              <a href={project.repoUrl} target="_blank" rel="noreferrer">
                {project.repoUrl}
              </a>
            ) : (
              <span className="mc-muted">Not connected</span>
            )}
          </div>
        </aside>
      </div>

      {editing ? (
        <div className="mc-dialog-backdrop">
          <div className="mc-dialog mc-dialog-wide" role="dialog" aria-modal="true">
            <div className="mc-dialog-header">
              <div>
                <p className="mc-eyebrow">Project</p>
                <h2>Edit {project.name}</h2>
              </div>
            </div>

            <div className="mc-dialog-scroll">
              <ProjectForm
                initialValue={projectToInput(project)}
                submitLabel="Save changes"
                busy={updateProject.isPending}
                onCancel={() => setEditing(false)}
                onSubmit={async (input) => {
                  await updateProject.mutateAsync({ id: project.id, input });
                  setEditing(false);
                }}
              />
            </div>
          </div>
        </div>
      ) : null}

      <ConfirmDialog
        open={confirmAction !== null}
        title={confirmConfig.title}
        description={confirmConfig.description}
        confirmLabel={confirmConfig.label}
        destructive={confirmConfig.destructive}
        busy={confirmBusy}
        onCancel={() => setConfirmAction(null)}
        onConfirm={handleConfirm}
      />
    </section>
  );
}
''')))

files.append(replace_entry("src/modules/projects/module.tsx", text(r'''
import { FolderKanban } from "lucide-react";

import type { MissionControlModule } from "../../app/modules/types";
import { NewProjectPage } from "./pages/NewProjectPage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { ProjectsPage } from "./pages/ProjectsPage";

export const projectsModule: MissionControlModule = {
  id: "projects",
  name: "Projects",

  navigation: [
    {
      id: "projects",
      label: "Projects",
      route: "/projects",
      icon: FolderKanban,
      order: 10
    }
  ],

  routes: [
    {
      path: "/projects",
      component: ProjectsPage
    },
    {
      path: "/projects/new",
      component: NewProjectPage
    },
    {
      path: "/projects/:id",
      component: ProjectDetailPage
    }
  ]
};
''')))

files.append(replace_entry("src/modules/settings/module.tsx", text(r'''
import { Settings } from "lucide-react";

import type { MissionControlModule } from "../../app/modules/types";
import { SettingsPage } from "./SettingsPage";

export const settingsModule: MissionControlModule = {
  id: "settings",
  name: "Settings",

  navigation: [
    {
      id: "settings",
      label: "Settings",
      route: "/settings",
      icon: Settings,
      order: 1000
    }
  ],

  routes: [
    {
      path: "/settings",
      component: SettingsPage
    },
    {
      path: "/settings/:section",
      component: SettingsPage
    }
  ]
};
''')))

files.append(replace_entry("src/modules/settings/SettingsPage.tsx", text(r'''
import {
  Boxes,
  Database,
  FlaskConical,
  FolderKanban,
  Info,
  Laptop,
  Link2,
  Monitor,
  Moon,
  Settings2,
  Sun
} from "lucide-react";
import { NavLink, useParams } from "react-router-dom";

import {
  useTheme,
  type ThemePreference
} from "../../app/theme/ThemeProvider";
import {
  UI_SCALE_OPTIONS,
  useUiPreferences
} from "../../app/preferences/UiPreferencesProvider";

const themeChoices: Array<{
  value: ThemePreference;
  label: string;
  description: string;
  icon: typeof Moon;
}> = [
  {
    value: "dark",
    label: "Dark",
    description: "Mission Control's graphite dark appearance.",
    icon: Moon
  },
  {
    value: "light",
    label: "Light",
    description: "Use the dedicated light appearance.",
    icon: Sun
  },
  {
    value: "system",
    label: "System",
    description: "Follow your operating system appearance.",
    icon: Laptop
  }
];

const sections = [
  { id: "general", label: "General", icon: Settings2 },
  { id: "appearance", label: "Appearance", icon: Moon },
  { id: "display", label: "Display & Scale", icon: Monitor },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "data", label: "Data & Backups", icon: Database },
  { id: "advanced", label: "Advanced", icon: FlaskConical },
  { id: "about", label: "About", icon: Info }
] as const;

type SectionId = (typeof sections)[number]["id"];

function PlaceholderSettings({
  title,
  description
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mc-settings-content-card mc-panel">
      <div className="mc-settings-card-icon">
        <Boxes size={18} />
      </div>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
        <span className="mc-coming-soon">Reserved for a future Mission Control update</span>
      </div>
    </div>
  );
}

export function SettingsPage() {
  const { section } = useParams();
  const activeSection: SectionId = sections.some((item) => item.id === section)
    ? (section as SectionId)
    : "general";

  const { preference, setPreference } = useTheme();
  const { uiScale, setUiScale, sidebarHidden, setSidebarHidden } = useUiPreferences();

  return (
    <section className="mc-page mc-settings-page">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Mission Control</p>
          <h1>Settings</h1>
          <p className="mc-page-description">
            Configure the application shell, appearance, and workspace behavior.
          </p>
        </div>
      </header>

      <div className="mc-settings-layout">
        <nav className="mc-settings-nav" aria-label="Settings sections">
          {sections.map((item) => {
            const Icon = item.icon;
            const route = item.id === "general" ? "/settings" : `/settings/${item.id}`;

            return (
              <NavLink
                key={item.id}
                to={route}
                end={item.id === "general"}
                className={({ isActive }) =>
                  `mc-settings-nav-item${isActive ? " is-active" : ""}`
                }
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mc-settings-content">
          {activeSection === "general" ? (
            <>
              <div className="mc-settings-heading">
                <h2>General</h2>
                <p>Core Mission Control application behavior.</p>
              </div>

              <div className="mc-settings-group mc-panel">
                <div className="mc-setting-row">
                  <div>
                    <strong>Sidebar</strong>
                    <span>Choose whether the desktop sidebar starts visible.</span>
                  </div>
                  <button
                    className={`mc-toggle${!sidebarHidden ? " is-on" : ""}`}
                    type="button"
                    role="switch"
                    aria-checked={!sidebarHidden}
                    onClick={() => setSidebarHidden(!sidebarHidden)}
                  >
                    <span />
                  </button>
                </div>

                <div className="mc-setting-row is-static">
                  <div>
                    <strong>Keyboard shortcut</strong>
                    <span>Show or hide the sidebar from anywhere in Mission Control.</span>
                  </div>
                  <kbd>Ctrl+B</kbd>
                </div>
              </div>
            </>
          ) : null}

          {activeSection === "appearance" ? (
            <>
              <div className="mc-settings-heading">
                <h2>Appearance</h2>
                <p>Choose how Mission Control should look.</p>
              </div>

              <div className="mc-theme-grid">
                {themeChoices.map((choice) => {
                  const Icon = choice.icon;
                  const selected = preference === choice.value;

                  return (
                    <button
                      key={choice.value}
                      type="button"
                      className={`mc-theme-choice${selected ? " is-selected" : ""}`}
                      onClick={() => setPreference(choice.value)}
                    >
                      <Icon size={18} />
                      <span>
                        <strong>{choice.label}</strong>
                        <small>{choice.description}</small>
                      </span>
                    </button>
                  );
                })}
              </div>
            </>
          ) : null}

          {activeSection === "display" ? (
            <>
              <div className="mc-settings-heading">
                <h2>Display & Scale</h2>
                <p>Scale the complete Mission Control interface without changing OS display scaling.</p>
              </div>

              <div className="mc-settings-group mc-panel">
                <div className="mc-scale-header">
                  <div>
                    <strong>Interface scale</strong>
                    <span>Applies to navigation, text, controls, panels, forms, and future modules.</span>
                  </div>
                  <strong className="mc-scale-value">{uiScale}%</strong>
                </div>

                <div className="mc-scale-grid">
                  {UI_SCALE_OPTIONS.map((scale) => (
                    <button
                      key={scale}
                      type="button"
                      className={`mc-scale-choice${uiScale === scale ? " is-selected" : ""}`}
                      onClick={() => setUiScale(scale)}
                    >
                      {scale}%
                    </button>
                  ))}
                </div>

                <div className="mc-setting-note">
                  100% uses Mission Control's normal size on top of your Windows or Linux display scaling.
                </div>
              </div>
            </>
          ) : null}

          {activeSection === "projects" ? (
            <PlaceholderSettings
              title="Project defaults"
              description="Default project folders, creation templates, and project behavior will live here."
            />
          ) : null}

          {activeSection === "integrations" ? (
            <PlaceholderSettings
              title="Integrations"
              description="GitHub, Patch Forge, local AI providers, and other integrations will be configured here."
            />
          ) : null}

          {activeSection === "data" ? (
            <PlaceholderSettings
              title="Data & Backups"
              description="Database location, backup, import, and export controls will be added here."
            />
          ) : null}

          {activeSection === "advanced" ? (
            <PlaceholderSettings
              title="Advanced"
              description="Developer diagnostics and experimental options will be isolated here."
            />
          ) : null}

          {activeSection === "about" ? (
            <div className="mc-about-card mc-panel">
              <div className="mc-brand-mark mc-about-mark">
                <Settings2 size={19} />
              </div>
              <div>
                <h2>Mission Control</h2>
                <p>Local-first project and development workflow command center.</p>
                <dl className="mc-about-list">
                  <div><dt>Version</dt><dd>0.1.2</dd></div>
                  <div><dt>Runtime</dt><dd>Tauri + React + TypeScript</dd></div>
                  <div><dt>Storage</dt><dd>SQLite</dd></div>
                </dl>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
''')))

files.append(replace_entry("src-tauri/src/projects.rs", text(r'''
use rusqlite::{params, Connection, OptionalExtension, Row};
use serde::{Deserialize, Serialize};
use std::{
    fs,
    path::Path,
    sync::Mutex,
    time::{SystemTime, UNIX_EPOCH},
};
use tauri::State;
use uuid::Uuid;

const SCHEMA_VERSION: i64 = 2;
const PROJECT_STATUSES: &[&str] = &[
    "active",
    "planning",
    "paused",
    "blocked",
    "waiting",
    "completed",
];
const STEP_STATUSES: &[&str] = &["todo", "in_progress", "blocked", "waiting", "done"];
const STEP_PRIORITIES: &[&str] = &["low", "medium", "high", "critical"];

pub struct ProjectStore {
    connection: Mutex<Connection>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Project {
    id: String,
    name: String,
    description: String,
    status: String,
    current_version: String,
    current_phase: String,
    current_step: String,
    current_step_status: String,
    current_step_priority: String,
    last_completed_step: String,
    next_steps: Vec<String>,
    blockers: Vec<String>,
    local_path: Option<String>,
    repo_url: Option<String>,
    archived: bool,
    created_at: i64,
    updated_at: i64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectInput {
    name: String,
    description: String,
    status: String,
    current_version: String,
    current_phase: String,
    current_step: String,
    current_step_status: String,
    current_step_priority: String,
    last_completed_step: String,
    next_steps: Vec<String>,
    blockers: Vec<String>,
    local_path: Option<String>,
    repo_url: Option<String>,
}

impl ProjectStore {
    pub fn open(path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let connection = Connection::open(path)?;
        connection.execute_batch(
            r#"
            PRAGMA journal_mode = WAL;
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                current_version TEXT NOT NULL DEFAULT '',
                current_phase TEXT NOT NULL DEFAULT '',
                current_step TEXT NOT NULL DEFAULT '',
                current_step_status TEXT NOT NULL DEFAULT 'todo',
                current_step_priority TEXT NOT NULL DEFAULT 'medium',
                last_completed_step TEXT NOT NULL DEFAULT '',
                next_steps_json TEXT NOT NULL DEFAULT '[]',
                blockers_json TEXT NOT NULL DEFAULT '[]',
                local_path TEXT,
                repo_url TEXT,
                archived INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            "#,
        )?;

        let had_step_status = column_exists(&connection, "projects", "current_step_status")?;
        let had_step_priority = column_exists(&connection, "projects", "current_step_priority")?;

        if !had_step_status {
            connection.execute(
                "ALTER TABLE projects ADD COLUMN current_step_status TEXT NOT NULL DEFAULT 'todo'",
                [],
            )?;
        }

        if !had_step_priority {
            connection.execute(
                "ALTER TABLE projects ADD COLUMN current_step_priority TEXT NOT NULL DEFAULT 'medium'",
                [],
            )?;

            if column_exists(&connection, "projects", "priority")? {
                connection.execute(
                    "UPDATE projects
                     SET current_step_priority = CASE
                       WHEN priority IN ('low','medium','high','critical') THEN priority
                       ELSE 'medium'
                     END",
                    [],
                )?;
            }
        }

        connection.pragma_update(None, "user_version", SCHEMA_VERSION)?;

        Ok(Self {
            connection: Mutex::new(connection),
        })
    }
}

fn column_exists(
    connection: &Connection,
    table: &str,
    column: &str,
) -> Result<bool, rusqlite::Error> {
    let sql = format!("PRAGMA table_info({table})");
    let mut statement = connection.prepare(&sql)?;
    let names = statement.query_map([], |row| row.get::<_, String>(1))?;

    for name in names {
        if name? == column {
            return Ok(true);
        }
    }

    Ok(false)
}

fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

fn validate_input(input: &ProjectInput) -> Result<(), String> {
    if input.name.trim().is_empty() {
        return Err("Project name is required".into());
    }

    if !PROJECT_STATUSES.contains(&input.status.as_str()) {
        return Err("Invalid project status".into());
    }

    if !STEP_STATUSES.contains(&input.current_step_status.as_str()) {
        return Err("Invalid current step status".into());
    }

    if !STEP_PRIORITIES.contains(&input.current_step_priority.as_str()) {
        return Err("Invalid current step priority".into());
    }

    Ok(())
}

fn row_to_project(row: &Row<'_>) -> rusqlite::Result<Project> {
    let next_steps: String = row.get("next_steps_json")?;
    let blockers: String = row.get("blockers_json")?;

    Ok(Project {
        id: row.get("id")?,
        name: row.get("name")?,
        description: row.get("description")?,
        status: row.get("status")?,
        current_version: row.get("current_version")?,
        current_phase: row.get("current_phase")?,
        current_step: row.get("current_step")?,
        current_step_status: row.get("current_step_status")?,
        current_step_priority: row.get("current_step_priority")?,
        last_completed_step: row.get("last_completed_step")?,
        next_steps: serde_json::from_str(&next_steps).unwrap_or_default(),
        blockers: serde_json::from_str(&blockers).unwrap_or_default(),
        local_path: row.get("local_path")?,
        repo_url: row.get("repo_url")?,
        archived: row.get::<_, i64>("archived")? != 0,
        created_at: row.get("created_at")?,
        updated_at: row.get("updated_at")?,
    })
}

fn get(connection: &Connection, id: &str) -> Result<Option<Project>, String> {
    connection
        .query_row(
            "SELECT * FROM projects WHERE id = ?1",
            [id],
            row_to_project,
        )
        .optional()
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn projects_list(
    archived: bool,
    store: State<'_, ProjectStore>,
) -> Result<Vec<Project>, String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    let mut statement = connection
        .prepare("SELECT * FROM projects WHERE archived = ?1 ORDER BY updated_at DESC")
        .map_err(|error| error.to_string())?;

    let rows = statement
        .query_map([if archived { 1 } else { 0 }], row_to_project)
        .map_err(|error| error.to_string())?;

    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn projects_get(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<Option<Project>, String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;
    get(&connection, &id)
}

#[tauri::command]
pub fn projects_create(
    input: ProjectInput,
    store: State<'_, ProjectStore>,
) -> Result<Project, String> {
    validate_input(&input)?;

    let id = Uuid::new_v4().to_string();
    let timestamp = now();
    let next_steps = serde_json::to_string(&input.next_steps).map_err(|e| e.to_string())?;
    let blockers = serde_json::to_string(&input.blockers).map_err(|e| e.to_string())?;
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "INSERT INTO projects (
                id,name,description,status,priority,current_version,current_phase,current_step,
                current_step_status,current_step_priority,last_completed_step,next_steps_json,
                blockers_json,local_path,repo_url,archived,created_at,updated_at
             ) VALUES (
                ?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,0,?16,?17
             )",
            params![
                id,
                input.name.trim(),
                input.description,
                input.status,
                input.current_step_priority,
                input.current_version,
                input.current_phase,
                input.current_step,
                input.current_step_status,
                input.current_step_priority,
                input.last_completed_step,
                next_steps,
                blockers,
                input.local_path,
                input.repo_url,
                timestamp,
                timestamp
            ],
        )
        .map_err(|e| e.to_string())?;

    get(&connection, &id)?.ok_or_else(|| "Project not found after creation".into())
}

#[tauri::command]
pub fn projects_update(
    id: String,
    input: ProjectInput,
    store: State<'_, ProjectStore>,
) -> Result<Project, String> {
    validate_input(&input)?;

    let next_steps = serde_json::to_string(&input.next_steps).map_err(|e| e.to_string())?;
    let blockers = serde_json::to_string(&input.blockers).map_err(|e| e.to_string())?;
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "UPDATE projects SET
                name=?2,
                description=?3,
                status=?4,
                priority=?5,
                current_version=?6,
                current_phase=?7,
                current_step=?8,
                current_step_status=?9,
                current_step_priority=?10,
                last_completed_step=?11,
                next_steps_json=?12,
                blockers_json=?13,
                local_path=?14,
                repo_url=?15,
                updated_at=?16
             WHERE id=?1",
            params![
                id,
                input.name.trim(),
                input.description,
                input.status,
                input.current_step_priority,
                input.current_version,
                input.current_phase,
                input.current_step,
                input.current_step_status,
                input.current_step_priority,
                input.last_completed_step,
                next_steps,
                blockers,
                input.local_path,
                input.repo_url,
                now()
            ],
        )
        .map_err(|e| e.to_string())?;

    get(&connection, &id)?.ok_or_else(|| "Project not found".into())
}

#[tauri::command]
pub fn projects_archive(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<(), String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "UPDATE projects SET archived=1,updated_at=?2 WHERE id=?1",
            params![id, now()],
        )
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub fn projects_restore(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<(), String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "UPDATE projects
             SET archived=0,
                 status=CASE WHEN status='archived' THEN 'active' ELSE status END,
                 updated_at=?2
             WHERE id=?1",
            params![id, now()],
        )
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub fn projects_delete(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<(), String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute("DELETE FROM projects WHERE id=?1", [id])
        .map_err(|e| e.to_string())?;

    Ok(())
}
''')))

files.append(replace_entry("src-tauri/src/lib.rs", text(r'''
mod projects;

use serde::Serialize;
use tauri::Manager;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendCapabilities {
    projects: bool,
    settings: bool,
    patch_forge: bool,
    git: bool,
    terminal: bool,
    ai: bool,
    remote: bool,
    bom: bool,
}

#[tauri::command]
fn backend_capabilities() -> BackendCapabilities {
    BackendCapabilities {
        projects: true,
        settings: true,
        patch_forge: false,
        git: false,
        terminal: false,
        ai: false,
        remote: false,
        bom: false,
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            let database_path = data_dir.join("mission-control.sqlite3");
            let store = projects::ProjectStore::open(&database_path)?;
            app.manage(store);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            backend_capabilities,
            projects::projects_list,
            projects::projects_get,
            projects::projects_create,
            projects::projects_update,
            projects::projects_archive,
            projects::projects_restore,
            projects::projects_delete
        ])
        .run(tauri::generate_context!())
        .expect("error while running Mission Control");
}
''')))

# Cargo.toml version only, preserve existing file formatting.
cargo_path = ROOT / "src-tauri/Cargo.toml"
cargo_old = cargo_path.read_text(encoding="utf-8")
cargo_new = cargo_old.replace('version = "0.1.0"', 'version = "0.1.2"', 1)
if cargo_new == cargo_old:
    raise SystemExit("Could not find Cargo.toml version 0.1.0")
files.append(replace_entry("src-tauri/Cargo.toml", cargo_new))

# Tauri config version + lower minimum window for responsive layouts.
tauri_path = ROOT / "src-tauri/tauri.conf.json"
tauri_config = json.loads(tauri_path.read_text(encoding="utf-8"))
tauri_config["version"] = "0.1.2"
window = tauri_config["app"]["windows"][0]
window["minWidth"] = 640
window["minHeight"] = 520
tauri_new = json.dumps(tauri_config, indent=2, ensure_ascii=False) + "\n"
files.append(replace_entry("src-tauri/tauri.conf.json", tauri_new))

files.append(replace_entry("src/styles/globals.css", text(r'''
* {
  box-sizing: border-box;
}

html,
body,
#root {
  width: 100%;
  min-width: 100%;
  min-height: 100%;
  margin: 0;
}

html,
body {
  height: 100%;
}

body {
  overflow: hidden;
  background: var(--mc-bg);
  color: var(--mc-text-primary);
  font-family:
    Inter,
    ui-sans-serif,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
  font-size: 0.875rem;
  text-rendering: optimizeLegibility;
}

button,
input,
textarea {
  font: inherit;
}

button {
  color: inherit;
}

a {
  color: inherit;
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 0.125rem solid var(--mc-accent);
  outline-offset: 0.125rem;
}

kbd {
  padding: 0.15rem 0.35rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-xs);
  background: var(--mc-surface-raised);
  color: var(--mc-text-muted);
  font-family: inherit;
  font-size: 0.6875rem;
}

.mc-shell {
  display: grid;
  grid-template-columns: var(--mc-sidebar-width) minmax(0, 1fr);
  width: 100vw;
  height: 100vh;
  background: var(--mc-bg);
  transition: grid-template-columns 150ms ease;
}

.mc-shell.is-sidebar-hidden {
  grid-template-columns: 0 minmax(0, 1fr);
}

.mc-sidebar {
  position: relative;
  z-index: 30;
  display: flex;
  min-width: 0;
  flex-direction: column;
  overflow: hidden;
  padding: 0.75rem 0.625rem;
  border-right: 0.0625rem solid var(--mc-border-subtle);
  background: var(--mc-sidebar);
  transition:
    transform 150ms ease,
    opacity 120ms ease;
}

.mc-shell.is-sidebar-hidden .mc-sidebar {
  pointer-events: none;
  opacity: 0;
  transform: translateX(-100%);
}

.mc-brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-height: 2.5rem;
  padding: 0 0.5rem;
  margin-bottom: 0.875rem;
}

.mc-brand-mark {
  display: grid;
  width: 1.8125rem;
  height: 1.8125rem;
  flex: 0 0 auto;
  place-items: center;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface-raised);
  color: var(--mc-accent);
}

.mc-brand-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}

.mc-brand-title {
  overflow: hidden;
  font-size: 0.8125rem;
  font-weight: 680;
  letter-spacing: -0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-brand-version {
  margin-top: 0.125rem;
  color: var(--mc-text-muted);
  font-size: 0.625rem;
}

.mc-sidebar-close {
  margin-left: auto;
}

.mc-nav {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.1875rem;
}

.mc-nav-item {
  display: flex;
  height: 2.25rem;
  align-items: center;
  gap: 0.625rem;
  padding: 0 0.625rem;
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-secondary);
  text-decoration: none;
  transition:
    background 120ms ease,
    color 120ms ease;
}

.mc-nav-item:hover {
  background: var(--mc-surface-hover);
  color: var(--mc-text-primary);
}

.mc-nav-item.is-active {
  background: var(--mc-accent-soft);
  color: var(--mc-text-primary);
}

.mc-nav-item.is-active svg {
  color: var(--mc-accent);
}

.mc-sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.75rem 0.625rem 0.25rem;
  border-top: 0.0625rem solid var(--mc-border-subtle);
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-main-frame {
  display: flex;
  min-width: 0;
  height: 100vh;
  flex-direction: column;
}

.mc-shellbar {
  display: flex;
  min-height: var(--mc-shellbar-height);
  flex: 0 0 var(--mc-shellbar-height);
  align-items: center;
  gap: 0.625rem;
  padding: 0 0.875rem;
  border-bottom: 0.0625rem solid var(--mc-border-subtle);
  background: color-mix(in srgb, var(--mc-bg) 86%, transparent);
}

.mc-shellbar-title {
  color: var(--mc-text-muted);
  font-size: 0.75rem;
  font-weight: 600;
}

.mc-main {
  min-width: 0;
  flex: 1;
  overflow: auto;
}

.mc-page {
  width: min(var(--mc-page-max), calc(100% - 4rem));
  margin: 0 auto;
  padding: 2rem 0 5rem;
}

.mc-page-form {
  max-width: 72rem;
}

.mc-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.75rem;
}

.mc-eyebrow {
  margin: 0 0 0.4375rem;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
  font-weight: 650;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mc-page-header h1,
.mc-project-detail-header h1 {
  margin: 0;
  font-size: clamp(1.375rem, 2.1vw, 1.75rem);
  font-weight: 680;
  letter-spacing: -0.035em;
}

.mc-page-description {
  max-width: 38rem;
  margin: 0.5rem 0 0;
  color: var(--mc-text-secondary);
  line-height: 1.55;
}

.mc-button {
  display: inline-flex;
  min-height: 2.125rem;
  align-items: center;
  justify-content: center;
  gap: 0.4375rem;
  padding: 0 0.75rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
  color: var(--mc-text-primary);
  text-decoration: none;
  cursor: pointer;
  transition:
    border-color 120ms ease,
    background 120ms ease;
}

.mc-button:hover:not(:disabled) {
  border-color: var(--mc-border-strong);
  background: var(--mc-surface-hover);
}

.mc-button:disabled,
.mc-icon-button:disabled {
  opacity: 0.55;
  cursor: default;
}

.mc-button-primary {
  border-color: transparent;
  background: var(--mc-accent);
  color: #fff;
}

.mc-button-primary:hover:not(:disabled) {
  border-color: transparent;
  background: var(--mc-accent-hover);
}

.mc-button-danger-solid {
  border-color: transparent;
  background: var(--mc-danger);
  color: #fff;
}

.mc-button-block {
  width: 100%;
}

.mc-icon-button {
  display: grid;
  width: 2rem;
  height: 2rem;
  flex: 0 0 auto;
  place-items: center;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
  cursor: pointer;
}

.mc-icon-button:hover:not(:disabled) {
  background: var(--mc-surface-hover);
}

.mc-panel {
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface);
}

.mc-muted {
  color: var(--mc-text-muted);
}

.mc-back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  margin-bottom: 1.25rem;
  color: var(--mc-text-secondary);
  text-decoration: none;
}

.mc-back-link:hover {
  color: var(--mc-text-primary);
}

.mc-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.mc-state-badge {
  --badge-color: var(--mc-text-secondary);
  --badge-bg: var(--mc-neutral-soft);
  display: inline-flex;
  min-height: 1.5rem;
  align-items: center;
  gap: 0.375rem;
  padding: 0.1875rem 0.4375rem;
  border: 0.0625rem solid color-mix(in srgb, var(--badge-color) 26%, transparent);
  border-radius: 999px;
  background: var(--badge-bg);
  color: var(--badge-color);
  font-size: 0.6875rem;
  font-weight: 620;
  line-height: 1;
  white-space: nowrap;
}

.mc-state-dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 50%;
  background: currentColor;
}

[data-tone="accent"] {
  --badge-color: var(--mc-accent);
  --badge-bg: var(--mc-accent-soft);
}

[data-tone="success"] {
  --badge-color: var(--mc-success);
  --badge-bg: var(--mc-success-soft);
}

[data-tone="warning"],
[data-tone="medium"] {
  --badge-color: var(--mc-priority-medium);
  --badge-bg: var(--mc-warning-soft);
}

[data-tone="danger"],
[data-tone="high"] {
  --badge-color: var(--mc-priority-high);
  --badge-bg: var(--mc-danger-soft);
}

[data-tone="critical"] {
  --badge-color: var(--mc-priority-critical);
  --badge-bg: var(--mc-danger-soft);
}

[data-tone="info"] {
  --badge-color: var(--mc-info);
  --badge-bg: var(--mc-info-soft);
}

[data-tone="low"] {
  --badge-color: var(--mc-priority-low);
  --badge-bg: var(--mc-neutral-soft);
}

/* Projects */

.mc-project-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.875rem;
}

.mc-segmented-control {
  display: inline-flex;
  padding: 0.1875rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface);
}

.mc-segmented-control button {
  display: inline-flex;
  min-height: 1.875rem;
  align-items: center;
  gap: 0.375rem;
  padding: 0 0.625rem;
  border: 0;
  border-radius: 0.25rem;
  background: transparent;
  color: var(--mc-text-muted);
  cursor: pointer;
}

.mc-segmented-control button.is-active {
  background: var(--mc-surface-elevated);
  color: var(--mc-text-primary);
  box-shadow: 0 0 0 0.0625rem var(--mc-border);
}

.mc-search {
  display: flex;
  width: min(22rem, 42vw);
  height: 2.125rem;
  align-items: center;
  gap: 0.5rem;
  padding: 0 0.625rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface);
  color: var(--mc-text-muted);
}

.mc-search:focus-within {
  border-color: var(--mc-accent-border);
}

.mc-search input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--mc-text-primary);
}

.mc-projects-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 20rem;
  gap: 0.875rem;
  align-items: start;
}

.mc-project-table-v2 {
  min-width: 0;
  overflow: hidden;
}

.mc-project-table-head,
.mc-project-row-v2 {
  display: grid;
  grid-template-columns:
    minmax(11rem, 1.35fr)
    6.25rem
    7.25rem
    6.5rem
    5rem
    minmax(11rem, 1fr);
  gap: 0.75rem;
  align-items: center;
}

.mc-project-table-head {
  min-height: 2.375rem;
  padding: 0 0.875rem;
  border-bottom: 0.0625rem solid var(--mc-border);
  background: var(--mc-surface-raised);
  color: var(--mc-text-muted);
  font-size: 0.625rem;
  font-weight: 650;
  letter-spacing: 0.045em;
  text-transform: uppercase;
}

.mc-project-row-v2 {
  width: 100%;
  min-height: 4rem;
  padding: 0.625rem 0.875rem;
  border: 0;
  border-bottom: 0.0625rem solid var(--mc-border-subtle);
  background: transparent;
  color: var(--mc-text-secondary);
  text-align: left;
  cursor: pointer;
}

.mc-project-row-v2:last-child {
  border-bottom: 0;
}

.mc-project-row-v2:hover,
.mc-project-row-v2.is-selected {
  background: var(--mc-surface-hover);
}

.mc-project-row-v2.is-selected {
  box-shadow: inset 0.125rem 0 0 var(--mc-accent);
}

.mc-project-identity {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.mc-project-identity strong {
  overflow: hidden;
  color: var(--mc-text-primary);
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-project-identity small {
  overflow: hidden;
  margin-top: 0.25rem;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-current-step-cell {
  overflow: hidden;
  color: var(--mc-text-secondary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-project-version {
  color: var(--mc-text-muted);
  font-size: 0.75rem;
}

.mc-project-preview {
  position: sticky;
  top: 1rem;
  padding: 1rem;
}

.mc-project-preview-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.mc-project-preview-heading h2 {
  margin: 0;
  font-size: 1rem;
}

.mc-project-preview-description {
  margin: 0.875rem 0 1rem;
  color: var(--mc-text-secondary);
  font-size: 0.8125rem;
  line-height: 1.55;
}

.mc-preview-current-step {
  padding: 0.875rem;
  margin-bottom: 1rem;
  border: 0.0625rem solid var(--mc-border-subtle);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
}

.mc-preview-current-step > span {
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-preview-current-step strong {
  display: block;
  margin: 0.375rem 0 0.625rem;
  font-size: 0.875rem;
  line-height: 1.4;
}

.mc-badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.mc-inspector-list {
  margin: 0 0 1rem;
}

.mc-inspector-list > div {
  display: flex;
  min-height: 2.25rem;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 0.0625rem solid var(--mc-border-subtle);
}

.mc-inspector-list > div:last-child {
  border-bottom: 0;
}

.mc-inspector-list dt {
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-inspector-list dd {
  margin: 0;
  color: var(--mc-text-secondary);
  font-size: 0.75rem;
  text-align: right;
}

.mc-project-empty {
  display: flex;
  min-height: 22rem;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.mc-empty-icon {
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  place-items: center;
  margin-bottom: 1rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-lg);
  background: var(--mc-surface-raised);
  color: var(--mc-text-muted);
}

.mc-project-empty h2 {
  margin: 0;
  font-size: 0.9375rem;
}

.mc-project-empty p {
  max-width: 28rem;
  margin: 0.5rem 0 0;
  color: var(--mc-text-secondary);
  line-height: 1.55;
}

.mc-empty-action {
  margin-top: 1rem;
}

/* Project detail */

.mc-project-detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
}

.mc-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.mc-project-title-block > p {
  max-width: 44rem;
  margin: 0.5rem 0 0;
  color: var(--mc-text-secondary);
  line-height: 1.5;
}

.mc-project-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4375rem;
  margin-top: 0.75rem;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-meta-separator {
  color: var(--mc-text-faint);
}

.mc-more-button {
  color: var(--mc-danger);
}

.mc-detail-tabs {
  display: flex;
  gap: 0.125rem;
  overflow-x: auto;
  margin: 0 -0.25rem 1rem;
  padding: 0 0.25rem 0.625rem;
  border-bottom: 0.0625rem solid var(--mc-border-subtle);
}

.mc-detail-tabs button {
  flex: 0 0 auto;
  padding: 0.4375rem 0.625rem;
  border: 0;
  border-radius: var(--mc-radius-sm);
  background: transparent;
  color: var(--mc-text-muted);
  font-size: 0.75rem;
  cursor: pointer;
}

.mc-detail-tabs button.is-active {
  background: var(--mc-surface-raised);
  color: var(--mc-text-primary);
}

.mc-detail-tabs button:disabled {
  opacity: 0.42;
  cursor: default;
}

.mc-project-detail-grid-v2 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 19rem;
  gap: 0.875rem;
  align-items: start;
}

.mc-project-detail-main-v2 {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.875rem;
}

.mc-current-step-card {
  padding: 1.25rem;
  border-color: var(--mc-accent-border);
  background:
    linear-gradient(180deg, var(--mc-accent-soft), transparent 70%),
    var(--mc-surface);
}

.mc-section-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.mc-current-step-card h2 {
  max-width: 48rem;
  margin: 0;
  font-size: clamp(1.125rem, 2vw, 1.5rem);
  line-height: 1.3;
}

.mc-step-context {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4375rem;
  margin-top: 1rem;
  color: var(--mc-text-muted);
  font-size: 0.75rem;
}

.mc-detail-pair {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.875rem;
}

.mc-detail-section-v2 {
  min-height: 14rem;
  padding: 1rem;
}

.mc-section-heading-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.mc-section-heading-inline h2 {
  margin: 0;
  font-size: 0.875rem;
}

.mc-section-heading-inline > span {
  display: grid;
  min-width: 1.5rem;
  height: 1.5rem;
  place-items: center;
  border-radius: 999px;
  background: var(--mc-surface-raised);
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-work-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  margin: 0;
  list-style: none;
}

.mc-work-list li {
  display: flex;
  min-height: 2.5rem;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.625rem 0;
  border-bottom: 0.0625rem solid var(--mc-border-subtle);
  color: var(--mc-text-secondary);
  line-height: 1.45;
}

.mc-work-list li:last-child {
  border-bottom: 0;
}

.mc-work-index {
  display: grid;
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 auto;
  place-items: center;
  border: 0.0625rem solid var(--mc-border);
  border-radius: 50%;
  color: var(--mc-text-muted);
  font-size: 0.625rem;
}

.mc-blocker-dot {
  width: 0.4375rem;
  height: 0.4375rem;
  flex: 0 0 auto;
  margin-top: 0.4rem;
  border-radius: 50%;
  background: var(--mc-danger);
}

.mc-clear-state {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--mc-success);
  font-size: 0.8125rem;
}

.mc-last-completed-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
}

.mc-last-completed-icon {
  display: grid;
  width: 2rem;
  height: 2rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--mc-success-soft);
  color: var(--mc-success);
}

.mc-last-completed-card strong {
  font-size: 0.8125rem;
}

.mc-project-inspector-v2 {
  position: sticky;
  top: 1rem;
  padding: 1rem;
}

.mc-inspector-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.625rem;
}

.mc-inspector-heading h2 {
  margin: 0;
  font-size: 0.9375rem;
}

.mc-inspector-heading svg {
  color: var(--mc-text-muted);
}

.mc-inspector-divider {
  height: 0.0625rem;
  margin: 0.875rem 0;
  background: var(--mc-border-subtle);
}

.mc-location-block + .mc-location-block {
  margin-top: 1rem;
}

.mc-location-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-bottom: 0.375rem;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-location-block code,
.mc-location-block a {
  display: block;
  overflow: hidden;
  color: var(--mc-text-secondary);
  font-family: inherit;
  font-size: 0.6875rem;
  line-height: 1.45;
  text-overflow: ellipsis;
  text-decoration: none;
  word-break: break-all;
}

.mc-location-block a:hover {
  color: var(--mc-accent);
}

/* Forms */

.mc-project-form-v2 {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.mc-form-section {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 2rem;
  padding: 1.25rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface);
}

.mc-form-section-copy h2 {
  margin: 0;
  font-size: 0.9375rem;
}

.mc-form-section-copy > p:last-child {
  margin: 0.5rem 0 0;
  color: var(--mc-text-muted);
  font-size: 0.75rem;
  line-height: 1.5;
}

.mc-form-section-fields {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1rem;
}

.mc-form-split {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.875rem;
}

.mc-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.375rem;
}

.mc-field > span,
.mc-option-picker legend {
  color: var(--mc-text-secondary);
  font-size: 0.6875rem;
  font-weight: 600;
}

.mc-field input,
.mc-field textarea {
  width: 100%;
  padding: 0.625rem 0.6875rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  outline: 0;
  background: var(--mc-surface-raised);
  color: var(--mc-text-primary);
}

.mc-field input {
  min-height: 2.375rem;
}

.mc-field textarea {
  resize: vertical;
  line-height: 1.5;
}

.mc-field input:focus,
.mc-field textarea:focus {
  border-color: var(--mc-accent-border);
  box-shadow: 0 0 0 0.125rem var(--mc-accent-soft);
}

.mc-field input::placeholder,
.mc-field textarea::placeholder {
  color: var(--mc-text-faint);
}

.mc-option-picker {
  min-width: 0;
  padding: 0;
  margin: 0;
  border: 0;
}

.mc-option-picker legend {
  padding: 0;
  margin-bottom: 0.4375rem;
}

.mc-option-picker-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.mc-option-choice {
  --badge-color: var(--mc-text-secondary);
  --badge-bg: var(--mc-neutral-soft);
  display: inline-flex;
  min-height: 2rem;
  align-items: center;
  gap: 0.375rem;
  padding: 0 0.625rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
  color: var(--mc-text-secondary);
  cursor: pointer;
}

.mc-option-choice:hover {
  border-color: var(--mc-border-strong);
}

.mc-option-choice.is-selected {
  border-color: color-mix(in srgb, var(--badge-color) 42%, var(--mc-border));
  background: var(--badge-bg);
  color: var(--badge-color);
}

.mc-option-dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 50%;
  background: currentColor;
}

.mc-form-error {
  padding: 0.75rem 0.875rem;
  margin: 0;
  border: 0.0625rem solid color-mix(in srgb, var(--mc-danger) 35%, transparent);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-danger-soft);
  color: var(--mc-danger);
}

.mc-form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.25rem;
}

/* Dialogs */

.mc-dialog-backdrop {
  position: fixed;
  z-index: 100;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: var(--mc-overlay);
}

.mc-dialog {
  position: relative;
  width: min(30rem, 100%);
  max-height: calc(100vh - 3rem);
  overflow: hidden;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-lg);
  background: var(--mc-surface-elevated);
  box-shadow: var(--mc-shadow);
}

.mc-dialog-wide {
  width: min(68rem, 100%);
}

.mc-dialog-header {
  padding: 1rem 1.125rem;
  border-bottom: 0.0625rem solid var(--mc-border);
}

.mc-dialog-header h2,
.mc-confirm-copy h2 {
  margin: 0;
  font-size: 1rem;
}

.mc-dialog-scroll {
  max-height: calc(100vh - 9rem);
  overflow: auto;
  padding: 1rem;
}

.mc-confirm-dialog {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.875rem;
  padding: 1.125rem;
}

.mc-confirm-icon {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  place-items: center;
  border-radius: 50%;
  background: var(--mc-warning-soft);
  color: var(--mc-warning);
}

.mc-confirm-icon.is-danger {
  background: var(--mc-danger-soft);
  color: var(--mc-danger);
}

.mc-confirm-copy p {
  margin: 0.4375rem 0 0;
  color: var(--mc-text-secondary);
  font-size: 0.8125rem;
  line-height: 1.5;
}

.mc-dialog-close {
  border: 0;
  background: transparent;
}

.mc-dialog-actions {
  display: flex;
  grid-column: 2 / -1;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.375rem;
}

/* Settings */

.mc-settings-layout {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}

.mc-settings-nav {
  display: flex;
  flex-direction: column;
  gap: 0.1875rem;
}

.mc-settings-nav-item {
  display: flex;
  min-height: 2.25rem;
  align-items: center;
  gap: 0.625rem;
  padding: 0 0.625rem;
  border-radius: var(--mc-radius-sm);
  color: var(--mc-text-secondary);
  text-decoration: none;
}

.mc-settings-nav-item:hover {
  background: var(--mc-surface-hover);
  color: var(--mc-text-primary);
}

.mc-settings-nav-item.is-active {
  background: var(--mc-accent-soft);
  color: var(--mc-text-primary);
}

.mc-settings-content {
  min-width: 0;
  max-width: 58rem;
}

.mc-settings-heading {
  margin-bottom: 1rem;
}

.mc-settings-heading h2 {
  margin: 0;
  font-size: 1rem;
}

.mc-settings-heading p {
  margin: 0.375rem 0 0;
  color: var(--mc-text-muted);
  font-size: 0.75rem;
}

.mc-settings-group {
  overflow: hidden;
}

.mc-setting-row,
.mc-scale-header {
  display: flex;
  min-height: 4rem;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0.875rem 1rem;
  border-bottom: 0.0625rem solid var(--mc-border-subtle);
}

.mc-setting-row:last-child {
  border-bottom: 0;
}

.mc-setting-row > div,
.mc-scale-header > div {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.mc-setting-row strong,
.mc-scale-header strong {
  font-size: 0.8125rem;
}

.mc-setting-row span,
.mc-scale-header span {
  color: var(--mc-text-muted);
  font-size: 0.75rem;
  line-height: 1.45;
}

.mc-toggle {
  position: relative;
  width: 2.375rem;
  height: 1.375rem;
  flex: 0 0 auto;
  padding: 0;
  border: 0.0625rem solid var(--mc-border);
  border-radius: 999px;
  background: var(--mc-surface-raised);
  cursor: pointer;
}

.mc-toggle span {
  position: absolute;
  top: 0.1875rem;
  left: 0.1875rem;
  width: 0.875rem;
  height: 0.875rem;
  border-radius: 50%;
  background: var(--mc-text-muted);
  transition: transform 140ms ease;
}

.mc-toggle.is-on {
  border-color: var(--mc-accent);
  background: var(--mc-accent);
}

.mc-toggle.is-on span {
  background: #fff;
  transform: translateX(1rem);
}

.mc-theme-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.625rem;
}

.mc-theme-choice {
  display: flex;
  min-height: 6rem;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface);
  text-align: left;
  cursor: pointer;
}

.mc-theme-choice:hover {
  background: var(--mc-surface-hover);
}

.mc-theme-choice.is-selected {
  border-color: var(--mc-accent);
  box-shadow: inset 0 0 0 0.0625rem var(--mc-accent);
}

.mc-theme-choice svg {
  margin-top: 0.0625rem;
  color: var(--mc-text-secondary);
}

.mc-theme-choice.is-selected svg {
  color: var(--mc-accent);
}

.mc-theme-choice > span {
  display: flex;
  flex-direction: column;
}

.mc-theme-choice strong {
  font-size: 0.8125rem;
}

.mc-theme-choice small {
  margin-top: 0.3125rem;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
  line-height: 1.45;
}

.mc-scale-value {
  color: var(--mc-accent);
}

.mc-scale-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem;
  padding: 1rem;
}

.mc-scale-choice {
  min-height: 2.5rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
  color: var(--mc-text-secondary);
  cursor: pointer;
}

.mc-scale-choice:hover {
  background: var(--mc-surface-hover);
}

.mc-scale-choice.is-selected {
  border-color: var(--mc-accent);
  background: var(--mc-accent-soft);
  color: var(--mc-accent);
  font-weight: 650;
}

.mc-setting-note {
  padding: 0.75rem 1rem;
  border-top: 0.0625rem solid var(--mc-border-subtle);
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
  line-height: 1.5;
}

.mc-settings-content-card,
.mc-about-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
}

.mc-settings-card-icon {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
  color: var(--mc-text-muted);
}

.mc-settings-content-card h2,
.mc-about-card h2 {
  margin: 0;
  font-size: 0.9375rem;
}

.mc-settings-content-card p,
.mc-about-card p {
  margin: 0.375rem 0 0;
  color: var(--mc-text-secondary);
  line-height: 1.5;
}

.mc-coming-soon {
  display: inline-block;
  margin-top: 0.75rem;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-about-mark {
  width: 2.75rem;
  height: 2.75rem;
}

.mc-about-list {
  margin: 1rem 0 0;
}

.mc-about-list > div {
  display: grid;
  grid-template-columns: 6rem minmax(0, 1fr);
  padding: 0.375rem 0;
}

.mc-about-list dt {
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-about-list dd {
  margin: 0;
  color: var(--mc-text-secondary);
  font-size: 0.75rem;
}

/* Responsive behavior */

.mc-sidebar-backdrop {
  display: none;
}

@media (max-width: 1200px) {
  .mc-projects-workspace {
    grid-template-columns: minmax(0, 1fr) 17rem;
  }

  .mc-project-table-head,
  .mc-project-row-v2 {
    grid-template-columns:
      minmax(11rem, 1.3fr)
      6.25rem
      7rem
      minmax(10rem, 1fr);
  }

  .mc-col-priority,
  .mc-col-version {
    display: none;
  }
}

@media (max-width: 1000px) {
  .mc-page {
    width: calc(100% - 2.5rem);
  }

  .mc-projects-workspace,
  .mc-project-detail-grid-v2 {
    grid-template-columns: 1fr;
  }

  .mc-project-preview,
  .mc-project-inspector-v2 {
    position: static;
  }

  .mc-project-preview {
    order: -1;
  }

  .mc-settings-layout {
    grid-template-columns: 11rem minmax(0, 1fr);
  }
}

@media (max-width: 820px) {
  .mc-page-header,
  .mc-project-detail-header {
    flex-direction: column;
  }

  .mc-project-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .mc-search {
    width: 100%;
  }

  .mc-detail-pair,
  .mc-form-split,
  .mc-theme-grid {
    grid-template-columns: 1fr;
  }

  .mc-form-section {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .mc-settings-layout {
    grid-template-columns: 1fr;
  }

  .mc-settings-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 0.375rem;
  }

  .mc-settings-nav-item {
    flex: 0 0 auto;
  }

  .mc-scale-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .mc-shell,
  .mc-shell.is-sidebar-hidden {
    grid-template-columns: 1fr;
  }

  .mc-sidebar,
  .mc-shell.is-sidebar-hidden .mc-sidebar {
    position: fixed;
    z-index: 60;
    inset: 0 auto 0 0;
    width: min(17rem, calc(100vw - 3.5rem));
    pointer-events: none;
    opacity: 1;
    transform: translateX(-100%);
    box-shadow: var(--mc-shadow);
  }

  .mc-shell.is-mobile-sidebar-open .mc-sidebar {
    pointer-events: auto;
    transform: translateX(0);
  }

  .mc-sidebar-backdrop {
    position: fixed;
    z-index: 50;
    inset: 0;
    display: block;
    border: 0;
    background: var(--mc-overlay);
  }

  .mc-shellbar-title {
    display: none;
  }

  .mc-page {
    width: calc(100% - 1.5rem);
    padding-top: 1.25rem;
  }

  .mc-project-table-head {
    display: none;
  }

  .mc-project-row-v2 {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.75rem;
    min-height: 4.25rem;
  }

  .mc-col-status {
    display: block;
  }

  .mc-col-step-status,
  .mc-col-priority,
  .mc-col-version,
  .mc-col-current-step {
    display: none;
  }

  .mc-project-preview {
    display: none;
  }

  .mc-section-topline {
    flex-direction: column;
  }

  .mc-dialog-backdrop {
    padding: 0.75rem;
  }

  .mc-dialog-wide {
    width: 100%;
    max-height: calc(100vh - 1.5rem);
  }

  .mc-dialog-scroll {
    max-height: calc(100vh - 6rem);
  }
}

@media (max-width: 520px) {
  .mc-page {
    width: calc(100% - 1rem);
  }

  .mc-segmented-control {
    width: 100%;
  }

  .mc-segmented-control button {
    flex: 1;
    justify-content: center;
  }

  .mc-form-section {
    padding: 1rem;
  }

  .mc-scale-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mc-confirm-dialog {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .mc-dialog-close {
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
  }

  .mc-dialog-actions {
    grid-column: 1 / -1;
  }
}
''')))

patch = {
    "version": 2,
    "name": "Mission Control v0.1.2 concept UI and workflow refinement",
    "files": files,
    "build": [
        "npm run build",
        "cargo check --manifest-path src-tauri/Cargo.toml"
    ],
    "options": {
        "rollback_on_verify_failure": True
    }
}

OUT.write_text(json.dumps(patch, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Created {OUT}")
print(f"Patch contains {len(files)} file operations.")
