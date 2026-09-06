import {
  createContext,
  useContext,
  useMemo,
  type ReactNode
} from "react";

import { LocalBackend } from "./localBackend";
import type { MissionControlBackend } from "./types";

const BackendContext = createContext<MissionControlBackend | null>(null);

export function BackendProvider({ children }: { children: ReactNode }) {
  const backend = useMemo(() => new LocalBackend(), []);

  return (
    <BackendContext.Provider value={backend}>
      {children}
    </BackendContext.Provider>
  );
}

export function useBackend(): MissionControlBackend {
  const backend = useContext(BackendContext);

  if (!backend) {
    throw new Error("useBackend must be used inside BackendProvider");
  }

  return backend;
}