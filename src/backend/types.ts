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

  listProjects(): Promise<Project[]>;
  getProject(id: string): Promise<Project | null>;
  createProject(input: ProjectInput): Promise<Project>;
  updateProject(id: string, input: ProjectInput): Promise<Project>;
  archiveProject(id: string): Promise<void>;
  deleteProject(id: string): Promise<void>;
}

export interface BackendError {
  code: string;
  message: string;
  details?: unknown;
}