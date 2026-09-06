import { invoke } from "@tauri-apps/api/core";

import type {
  BackendCapabilities,
  MissionControlBackend
} from "./types";

export class LocalBackend implements MissionControlBackend {
  capabilities(): Promise<BackendCapabilities> {
    return invoke<BackendCapabilities>("backend_capabilities");
  }
}