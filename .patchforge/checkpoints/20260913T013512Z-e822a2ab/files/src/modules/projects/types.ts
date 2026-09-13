export type ProjectStatus =
  | "active"
  | "planning"
  | "paused"
  | "blocked"
  | "waiting"
  | "completed"
  | "archived";

export type ProjectPriority = "low" | "medium" | "high" | "critical";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  currentVersion: string;
  currentPhase: string;
  currentStep: string;
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
  priority: ProjectPriority;
  currentVersion: string;
  currentPhase: string;
  currentStep: string;
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
  priority: "medium",
  currentVersion: "",
  currentPhase: "",
  currentStep: "",
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

export const PROJECT_PRIORITIES: ProjectPriority[] = [
  "low",
  "medium",
  "high",
  "critical"
];

export function projectToInput(project: Project): ProjectInput {
  return {
    name: project.name,
    description: project.description,
    status: project.status,
    priority: project.priority,
    currentVersion: project.currentVersion,
    currentPhase: project.currentPhase,
    currentStep: project.currentStep,
    lastCompletedStep: project.lastCompletedStep,
    nextSteps: project.nextSteps,
    blockers: project.blockers,
    localPath: project.localPath,
    repoUrl: project.repoUrl
  };
}

export function formatProjectStatus(status: ProjectStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function formatProjectPriority(priority: ProjectPriority): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}
