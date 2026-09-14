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

export interface ProjectStepHistoryEntry {
  id: string;
  projectId: string;
  step: string;
  statusBefore: StepStatus | null;
  priority: StepPriority | null;
  tags: string[];
  phase: string | null;
  version: string | null;
  completedAt: number;
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
