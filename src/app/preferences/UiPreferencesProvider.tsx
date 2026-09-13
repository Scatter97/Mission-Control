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

export type ShortcutAction =
  | "toggleSidebar"
  | "scaleUp"
  | "scaleDown"
  | "scaleReset"
  | "fullscreen"
  | "newProject"
  | "settings"
  | "keyboardShortcuts";

export type ShortcutMap = Record<ShortcutAction, string>;

export const DEFAULT_SHORTCUTS: ShortcutMap = {
  toggleSidebar: "Ctrl+B",
  scaleUp: "Ctrl+=",
  scaleDown: "Ctrl+-",
  scaleReset: "Ctrl+0",
  fullscreen: "F11",
  newProject: "Ctrl+N",
  settings: "Ctrl+,",
  keyboardShortcuts: "Ctrl+/"
};

interface UiPreferencesContextValue {
  uiScale: UiScale;
  setUiScale: (scale: UiScale) => void;
  increaseUiScale: () => void;
  decreaseUiScale: () => void;
  resetUiScale: () => void;

  sidebarHidden: boolean;
  setSidebarHidden: (hidden: boolean) => void;
  toggleSidebar: () => void;

  shortcuts: ShortcutMap;
  setShortcut: (action: ShortcutAction, shortcut: string) => void;
  resetShortcut: (action: ShortcutAction) => void;
  resetShortcuts: () => void;
}

const UiPreferencesContext =
  createContext<UiPreferencesContextValue | null>(null);

const SCALE_KEY = "mission-control.ui-scale";
const SIDEBAR_KEY = "mission-control.sidebar-hidden";
const SHORTCUTS_KEY = "mission-control.shortcuts";

function readScale(): UiScale {
  const stored = Number(localStorage.getItem(SCALE_KEY));

  return UI_SCALE_OPTIONS.includes(stored as UiScale)
    ? (stored as UiScale)
    : 100;
}

function readSidebarHidden(): boolean {
  return localStorage.getItem(SIDEBAR_KEY) === "true";
}

function readShortcuts(): ShortcutMap {
  const stored = localStorage.getItem(SHORTCUTS_KEY);

  if (!stored) {
    return { ...DEFAULT_SHORTCUTS };
  }

  try {
    return {
      ...DEFAULT_SHORTCUTS,
      ...JSON.parse(stored)
    };
  } catch {
    return { ...DEFAULT_SHORTCUTS };
  }
}

export function shortcutFromEvent(event: KeyboardEvent): string {
  const parts: string[] = [];

  if (event.ctrlKey) parts.push("Ctrl");
  if (event.altKey) parts.push("Alt");
  if (event.shiftKey) parts.push("Shift");
  if (event.metaKey) parts.push("Meta");

  let key = event.key;

  if (key === " ") key = "Space";
  if (key === "Control" || key === "Alt" || key === "Shift" || key === "Meta") {
    return "";
  }

  if (key.length === 1) {
    key = key.toUpperCase();
  }

  parts.push(key);

  return parts.join("+");
}

export function eventMatchesShortcut(
  event: KeyboardEvent,
  shortcut: string
): boolean {
  return shortcutFromEvent(event).toLowerCase() === shortcut.toLowerCase();
}

export function UiPreferencesProvider({
  children
}: {
  children: ReactNode;
}) {
  const [uiScale, setUiScaleState] = useState<UiScale>(readScale);
  const [sidebarHidden, setSidebarHiddenState] =
    useState(readSidebarHidden);
  const [shortcuts, setShortcuts] =
    useState<ShortcutMap>(readShortcuts);

  useEffect(() => {
    document.documentElement.style.setProperty(
      "--mc-ui-scale",
      String(uiScale / 100)
    );

    document.documentElement.dataset.uiScale = String(uiScale);
  }, [uiScale]);

  const setUiScale = (scale: UiScale) => {
    localStorage.setItem(SCALE_KEY, String(scale));
    setUiScaleState(scale);
  };

  const moveScale = (direction: 1 | -1) => {
    const currentIndex = UI_SCALE_OPTIONS.indexOf(uiScale);

    const nextIndex = Math.max(
      0,
      Math.min(
        UI_SCALE_OPTIONS.length - 1,
        currentIndex + direction
      )
    );

    setUiScale(UI_SCALE_OPTIONS[nextIndex]);
  };

  const increaseUiScale = () => moveScale(1);
  const decreaseUiScale = () => moveScale(-1);
  const resetUiScale = () => setUiScale(100);

  const setSidebarHidden = (hidden: boolean) => {
    localStorage.setItem(SIDEBAR_KEY, String(hidden));
    setSidebarHiddenState(hidden);
  };

  const toggleSidebar = () => {
    setSidebarHidden(!sidebarHidden);
  };

  const saveShortcuts = (next: ShortcutMap) => {
    localStorage.setItem(SHORTCUTS_KEY, JSON.stringify(next));
    setShortcuts(next);
  };

  const setShortcut = (
    action: ShortcutAction,
    shortcut: string
  ) => {
    saveShortcuts({
      ...shortcuts,
      [action]: shortcut
    });
  };

  const resetShortcut = (action: ShortcutAction) => {
    setShortcut(action, DEFAULT_SHORTCUTS[action]);
  };

  const resetShortcuts = () => {
    saveShortcuts({ ...DEFAULT_SHORTCUTS });
  };

  const value = useMemo(
    () => ({
      uiScale,
      setUiScale,
      increaseUiScale,
      decreaseUiScale,
      resetUiScale,

      sidebarHidden,
      setSidebarHidden,
      toggleSidebar,

      shortcuts,
      setShortcut,
      resetShortcut,
      resetShortcuts
    }),
    [uiScale, sidebarHidden, shortcuts]
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
    throw new Error(
      "useUiPreferences must be used inside UiPreferencesProvider"
    );
  }

  return context;
}
