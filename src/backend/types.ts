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
}

export interface BackendError {
  code: string;
  message: string;
  details?: unknown;
}