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
