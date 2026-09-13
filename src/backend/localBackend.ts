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
