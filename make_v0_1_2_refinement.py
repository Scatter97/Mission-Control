from pathlib import Path
import json

ROOT = Path(r"C:\Users\joshh\Desktop\Mission-Control")
OUT = ROOT / "mission-control-v0.1.2-ui-refinement.json"

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def replace_file(path, new_text):
    old_text = read(path)
    if old_text == new_text:
        raise RuntimeError(f"{path} already contains the requested update")

    return {
        "path": path.replace("\\", "/"),
        "edits": [
            {
                "op": "replace",
                "old": old_text,
                "new": new_text
            }
        ]
    }

preferences = r'''import {
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
'''

shell = r'''import {
  useEffect,
  useRef,
  useState,
  type ReactNode
} from "react";
import {
  Command,
  Menu,
  Minus,
  Square,
  X
} from "lucide-react";
import {
  NavLink,
  useNavigate
} from "react-router-dom";
import { getCurrentWindow } from "@tauri-apps/api/window";

import { moduleRegistry } from "../modules/registry";
import {
  eventMatchesShortcut,
  useUiPreferences
} from "../preferences/UiPreferencesProvider";

interface AppShellProps {
  children: ReactNode;
}

const MOBILE_QUERY = "(max-width: 760px)";

type MenuName =
  | "file"
  | "view"
  | "projects"
  | "tools"
  | "help"
  | null;

export function AppShell({ children }: AppShellProps) {
  const navigation = moduleRegistry.getNavigationItems();
  const navigate = useNavigate();

  const {
    sidebarHidden,
    toggleSidebar,
    increaseUiScale,
    decreaseUiScale,
    resetUiScale,
    shortcuts
  } = useUiPreferences();

  const [mobile, setMobile] = useState(
    () => window.matchMedia(MOBILE_QUERY).matches
  );

  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeMenu, setActiveMenu] =
    useState<MenuName>(null);
  const [fullscreen, setFullscreen] = useState(false);

  const menuRef = useRef<HTMLDivElement | null>(null);
  const appWindow = getCurrentWindow();

  useEffect(() => {
    const query = window.matchMedia(MOBILE_QUERY);

    const onChange = () => {
      setMobile(query.matches);

      if (!query.matches) {
        setMobileOpen(false);
      }
    };

    query.addEventListener("change", onChange);

    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    void appWindow.isFullscreen().then(setFullscreen);
  }, []);

  useEffect(() => {
    const closeMenu = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node)
      ) {
        setActiveMenu(null);
      }
    };

    window.addEventListener("mousedown", closeMenu);

    return () => {
      window.removeEventListener("mousedown", closeMenu);
    };
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;

      const editing =
        target?.tagName === "INPUT" ||
        target?.tagName === "TEXTAREA" ||
        target?.tagName === "SELECT" ||
        target?.isContentEditable;

      const matches = (shortcut: string) =>
        eventMatchesShortcut(event, shortcut);

      if (!editing && matches(shortcuts.toggleSidebar)) {
        event.preventDefault();

        if (mobile) {
          setMobileOpen((open) => !open);
        } else {
          toggleSidebar();
        }

        return;
      }

      if (!editing && matches(shortcuts.scaleUp)) {
        event.preventDefault();
        increaseUiScale();
        return;
      }

      if (!editing && matches(shortcuts.scaleDown)) {
        event.preventDefault();
        decreaseUiScale();
        return;
      }

      if (!editing && matches(shortcuts.scaleReset)) {
        event.preventDefault();
        resetUiScale();
        return;
      }

      if (matches(shortcuts.fullscreen)) {
        event.preventDefault();
        void toggleFullscreen();
        return;
      }

      if (!editing && matches(shortcuts.newProject)) {
        event.preventDefault();
        navigate("/projects/new");
        return;
      }

      if (!editing && matches(shortcuts.settings)) {
        event.preventDefault();
        navigate("/settings");
        return;
      }

      if (!editing && matches(shortcuts.keyboardShortcuts)) {
        event.preventDefault();
        navigate("/settings?section=keyboard");
        return;
      }

      if (event.key === "Escape") {
        setActiveMenu(null);

        if (mobileOpen) {
          setMobileOpen(false);
        }
      }
    };

    window.addEventListener("keydown", onKeyDown);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [
    mobile,
    mobileOpen,
    shortcuts,
    toggleSidebar,
    increaseUiScale,
    decreaseUiScale,
    resetUiScale,
    navigate,
    fullscreen
  ]);

  const toggleFullscreen = async () => {
    const next = !fullscreen;
    await appWindow.setFullscreen(next);
    setFullscreen(next);
    setActiveMenu(null);
  };

  const handleToggleSidebar = () => {
    if (mobile) {
      setMobileOpen((open) => !open);
    } else {
      toggleSidebar();
    }
  };

  const shellClass = [
    "mc-shell",
    sidebarHidden ? "is-sidebar-hidden" : "",
    mobileOpen ? "is-mobile-sidebar-open" : "",
    fullscreen ? "is-fullscreen" : ""
  ]
    .filter(Boolean)
    .join(" ");

  const runMenuAction = (action: () => void) => {
    setActiveMenu(null);
    action();
  };

  const menuButton = (
    name: Exclude<MenuName, null>,
    label: string,
    items: ReactNode
  ) => (
    <div className="mc-menu-root">
      <button
        className={`mc-menu-button${
          activeMenu === name ? " is-active" : ""
        }`}
        type="button"
        onClick={() =>
          setActiveMenu((current) =>
            current === name ? null : name
          )
        }
      >
        {label}
      </button>

      {activeMenu === name ? (
        <div className="mc-menu-popover">
          {items}
        </div>
      ) : null}
    </div>
  );

  return (
    <div className={shellClass}>
      <div
        className="mc-titlebar"
        data-tauri-drag-region
      >
        <div className="mc-titlebar-left" ref={menuRef}>
          <button
            className="mc-titlebar-icon"
            type="button"
            aria-label="Toggle sidebar"
            title={`Toggle sidebar (${shortcuts.toggleSidebar})`}
            onClick={handleToggleSidebar}
          >
            <Menu size={14} />
          </button>

          {menuButton(
            "file",
            "File",
            <>
              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate("/projects/new")
                  )
                }
              >
                <span>New Project</span>
                <kbd>{shortcuts.newProject}</kbd>
              </button>

              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate("/settings")
                  )
                }
              >
                <span>Settings</span>
                <kbd>{shortcuts.settings}</kbd>
              </button>

              <div className="mc-menu-separator" />

              <button
                type="button"
                onClick={() => void appWindow.close()}
              >
                <span>Exit</span>
              </button>
            </>
          )}

          {menuButton(
            "view",
            "View",
            <>
              <button
                type="button"
                onClick={() =>
                  runMenuAction(handleToggleSidebar)
                }
              >
                <span>Toggle Sidebar</span>
                <kbd>{shortcuts.toggleSidebar}</kbd>
              </button>

              <div className="mc-menu-separator" />

              <button
                type="button"
                onClick={() =>
                  runMenuAction(increaseUiScale)
                }
              >
                <span>Increase Interface Scale</span>
                <kbd>{shortcuts.scaleUp}</kbd>
              </button>

              <button
                type="button"
                onClick={() =>
                  runMenuAction(decreaseUiScale)
                }
              >
                <span>Decrease Interface Scale</span>
                <kbd>{shortcuts.scaleDown}</kbd>
              </button>

              <button
                type="button"
                onClick={() =>
                  runMenuAction(resetUiScale)
                }
              >
                <span>Reset Interface Scale</span>
                <kbd>{shortcuts.scaleReset}</kbd>
              </button>

              <div className="mc-menu-separator" />

              <button
                type="button"
                onClick={() => void toggleFullscreen()}
              >
                <span>
                  {fullscreen
                    ? "Exit Fullscreen"
                    : "Enter Fullscreen"}
                </span>
                <kbd>{shortcuts.fullscreen}</kbd>
              </button>
            </>
          )}

          {menuButton(
            "projects",
            "Projects",
            <>
              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate("/projects")
                  )
                }
              >
                <span>Active Projects</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate("/projects?view=archived")
                  )
                }
              >
                <span>Archived Projects</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate("/projects/new")
                  )
                }
              >
                <span>New Project</span>
                <kbd>{shortcuts.newProject}</kbd>
              </button>
            </>
          )}

          {menuButton(
            "tools",
            "Tools",
            <>
              <button type="button" disabled>
                <span>Patch Forge</span>
                <small>Coming later</small>
              </button>

              <button type="button" disabled>
                <span>Git</span>
                <small>Coming later</small>
              </button>

              <button type="button" disabled>
                <span>Terminal</span>
                <small>Coming later</small>
              </button>
            </>
          )}

          {menuButton(
            "help",
            "Help",
            <>
              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate(
                      "/settings?section=keyboard"
                    )
                  )
                }
              >
                <span>Keyboard Shortcuts</span>
                <kbd>{shortcuts.keyboardShortcuts}</kbd>
              </button>

              <button
                type="button"
                onClick={() =>
                  runMenuAction(() =>
                    navigate("/settings?section=about")
                  )
                }
              >
                <span>About Mission Control</span>
              </button>
            </>
          )}
        </div>

        <div
          className="mc-titlebar-center"
          data-tauri-drag-region
        >
          <Command size={13} />
          <span>Mission Control</span>
        </div>

        {!fullscreen ? (
          <div className="mc-window-controls">
            <button
              type="button"
              aria-label="Minimize"
              onClick={() => void appWindow.minimize()}
            >
              <Minus size={13} />
            </button>

            <button
              type="button"
              aria-label="Maximize"
              onClick={() =>
                void appWindow.toggleMaximize()
              }
            >
              <Square size={11} />
            </button>

            <button
              className="is-close"
              type="button"
              aria-label="Close"
              onClick={() => void appWindow.close()}
            >
              <X size={13} />
            </button>
          </div>
        ) : null}
      </div>

      <aside
        className="mc-sidebar"
        aria-label="Mission Control sidebar"
      >
        <div className="mc-brand">
          <div className="mc-brand-mark">
            <Command size={17} strokeWidth={2.2} />
          </div>

          <div className="mc-brand-copy">
            <span className="mc-brand-title">
              Mission Control
            </span>
            <span className="mc-brand-version">
              v0.1.2
            </span>
          </div>
        </div>

        <nav className="mc-nav" aria-label="Mission Control">
          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.id}
                to={item.route}
                className={({ isActive }) =>
                  `mc-nav-item${
                    isActive ? " is-active" : ""
                  }`
                }
                onClick={() => {
                  if (mobile) {
                    setMobileOpen(false);
                  }
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
          <kbd>{shortcuts.toggleSidebar}</kbd>
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

      <main className="mc-main">
        {children}
      </main>
    </div>
  );
}
'''

settings = r'''import {
  Boxes,
  Database,
  FlaskConical,
  FolderKanban,
  Info,
  Keyboard,
  Laptop,
  Link2,
  Monitor,
  Moon,
  RotateCcw,
  Settings2,
  Sun
} from "lucide-react";
import {
  useEffect,
  useState,
  type KeyboardEvent as ReactKeyboardEvent
} from "react";
import { useSearchParams } from "react-router-dom";

import {
  useTheme,
  type ThemePreference
} from "../../app/theme/ThemeProvider";
import {
  DEFAULT_SHORTCUTS,
  UI_SCALE_OPTIONS,
  shortcutFromEvent,
  useUiPreferences,
  type ShortcutAction
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
  { id: "keyboard", label: "Keyboard Shortcuts", icon: Keyboard },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "data", label: "Data & Backups", icon: Database },
  { id: "advanced", label: "Advanced", icon: FlaskConical },
  { id: "about", label: "About", icon: Info }
] as const;

type SectionId = (typeof sections)[number]["id"];

const shortcutRows: Array<{
  action: ShortcutAction;
  label: string;
  description: string;
}> = [
  {
    action: "toggleSidebar",
    label: "Toggle sidebar",
    description: "Show or hide the Mission Control sidebar."
  },
  {
    action: "scaleUp",
    label: "Increase interface scale",
    description: "Move to the next larger Mission Control scale."
  },
  {
    action: "scaleDown",
    label: "Decrease interface scale",
    description: "Move to the next smaller Mission Control scale."
  },
  {
    action: "scaleReset",
    label: "Reset interface scale",
    description: "Return Mission Control to 100%."
  },
  {
    action: "fullscreen",
    label: "Toggle fullscreen",
    description: "Enter or exit fullscreen mode."
  },
  {
    action: "newProject",
    label: "New project",
    description: "Open the New Project page."
  },
  {
    action: "settings",
    label: "Open settings",
    description: "Open Mission Control settings."
  },
  {
    action: "keyboardShortcuts",
    label: "Keyboard shortcuts",
    description: "Jump directly to this settings page."
  }
];

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
      </div>
    </div>
  );
}

export function SettingsPage() {
  const { preference, setPreference } = useTheme();

  const {
    uiScale,
    setUiScale,
    shortcuts,
    setShortcut,
    resetShortcut,
    resetShortcuts
  } = useUiPreferences();

  const [searchParams, setSearchParams] = useSearchParams();

  const sectionFromUrl =
    searchParams.get("section") as SectionId | null;

  const initialSection =
    sections.some((section) => section.id === sectionFromUrl)
      ? sectionFromUrl!
      : "general";

  const [activeSection, setActiveSection] =
    useState<SectionId>(initialSection);

  const [recording, setRecording] =
    useState<ShortcutAction | null>(null);

  useEffect(() => {
    const next =
      searchParams.get("section") as SectionId | null;

    if (
      next &&
      sections.some((section) => section.id === next)
    ) {
      setActiveSection(next);
    }
  }, [searchParams]);

  const chooseSection = (section: SectionId) => {
    setActiveSection(section);

    const next = new URLSearchParams(searchParams);
    next.set("section", section);
    setSearchParams(next);
  };

  const captureShortcut = (
    event: ReactKeyboardEvent<HTMLButtonElement>,
    action: ShortcutAction
  ) => {
    if (!recording || recording !== action) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    const shortcut = shortcutFromEvent(
      event.nativeEvent
    );

    if (!shortcut) {
      return;
    }

    const conflict = Object.entries(shortcuts).find(
      ([otherAction, value]) =>
        otherAction !== action &&
        value.toLowerCase() === shortcut.toLowerCase()
    );

    if (conflict) {
      return;
    }

    setShortcut(action, shortcut);
    setRecording(null);
  };

  return (
    <section className="mc-page mc-settings-page">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Mission Control</p>
          <h1>Settings</h1>
          <p className="mc-page-description">
            Configure Mission Control's interface and application preferences.
          </p>
        </div>
      </header>

      <div className="mc-settings-layout">
        <aside className="mc-settings-nav">
          {sections.map((section) => {
            const Icon = section.icon;

            return (
              <button
                key={section.id}
                type="button"
                className={
                  activeSection === section.id
                    ? "is-active"
                    : ""
                }
                onClick={() =>
                  chooseSection(section.id)
                }
              >
                <Icon size={15} />
                <span>{section.label}</span>
              </button>
            );
          })}
        </aside>

        <div className="mc-settings-content">
          {activeSection === "general" ? (
            <PlaceholderSettings
              title="General"
              description="Startup behavior and global Mission Control defaults will live here."
            />
          ) : null}

          {activeSection === "appearance" ? (
            <>
              <div className="mc-settings-heading">
                <h2>Appearance</h2>
                <p>
                  Choose how Mission Control should look.
                </p>
              </div>

              <div className="mc-theme-grid">
                {themeChoices.map((choice) => {
                  const Icon = choice.icon;
                  const selected =
                    preference === choice.value;

                  return (
                    <button
                      key={choice.value}
                      type="button"
                      className={`mc-theme-choice${
                        selected
                          ? " is-selected"
                          : ""
                      }`}
                      onClick={() =>
                        setPreference(choice.value)
                      }
                    >
                      <Icon size={18} />

                      <span>
                        <strong>{choice.label}</strong>
                        <small>
                          {choice.description}
                        </small>
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
                <p>
                  Scale the complete Mission Control interface without changing Windows display scaling.
                </p>
              </div>

              <div className="mc-settings-group mc-panel">
                <div className="mc-scale-header">
                  <div>
                    <strong>Interface scale</strong>
                    <span>
                      Applies to navigation, text, controls, panels, forms, and future modules.
                    </span>
                  </div>

                  <strong className="mc-scale-value">
                    {uiScale}%
                  </strong>
                </div>

                <div className="mc-scale-grid">
                  {UI_SCALE_OPTIONS.map((scale) => (
                    <button
                      key={scale}
                      type="button"
                      className={`mc-scale-choice${
                        uiScale === scale
                          ? " is-selected"
                          : ""
                      }`}
                      onClick={() =>
                        setUiScale(scale)
                      }
                    >
                      {scale}%
                    </button>
                  ))}
                </div>

                <div className="mc-settings-hint">
                  Shortcuts: {shortcuts.scaleDown} smaller ·{" "}
                  {shortcuts.scaleUp} larger ·{" "}
                  {shortcuts.scaleReset} reset
                </div>
              </div>
            </>
          ) : null}

          {activeSection === "keyboard" ? (
            <>
              <div className="mc-settings-heading mc-settings-heading-row">
                <div>
                  <h2>Keyboard Shortcuts</h2>
                  <p>
                    Click a shortcut, then press the new key combination.
                  </p>
                </div>

                <button
                  className="mc-button"
                  type="button"
                  onClick={resetShortcuts}
                >
                  <RotateCcw size={14} />
                  Reset all
                </button>
              </div>

              <div className="mc-shortcut-list mc-panel">
                {shortcutRows.map((row) => {
                  const isRecording =
                    recording === row.action;

                  return (
                    <div
                      className="mc-shortcut-row"
                      key={row.action}
                    >
                      <div className="mc-shortcut-copy">
                        <strong>{row.label}</strong>
                        <span>
                          {row.description}
                        </span>
                      </div>

                      <div className="mc-shortcut-actions">
                        <button
                          className={`mc-shortcut-key${
                            isRecording
                              ? " is-recording"
                              : ""
                          }`}
                          type="button"
                          onClick={() =>
                            setRecording(
                              isRecording
                                ? null
                                : row.action
                            )
                          }
                          onKeyDown={(event) =>
                            captureShortcut(
                              event,
                              row.action
                            )
                          }
                        >
                          {isRecording
                            ? "Press shortcut..."
                            : shortcuts[row.action]}
                        </button>

                        <button
                          className="mc-icon-button"
                          type="button"
                          aria-label={`Reset ${row.label}`}
                          title={`Reset to ${DEFAULT_SHORTCUTS[row.action]}`}
                          onClick={() => {
                            resetShortcut(row.action);
                            setRecording(null);
                          }}
                        >
                          <RotateCcw size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              <p className="mc-settings-hint">
                Mission Control prevents duplicate shortcuts. Escape cancels shortcut recording.
              </p>
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
                <p>
                  Local-first project and development workflow command center.
                </p>

                <dl className="mc-about-list">
                  <div>
                    <dt>Version</dt>
                    <dd>0.1.2</dd>
                  </div>

                  <div>
                    <dt>Runtime</dt>
                    <dd>Tauri + React</dd>
                  </div>

                  <div>
                    <dt>Storage</dt>
                    <dd>SQLite</dd>
                  </div>
                </dl>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
'''

css_addition = r'''

/* v0.1.2 desktop shell + semantic refinement */

.mc-titlebar {
  position: fixed;
  z-index: 100;
  inset: 0 0 auto 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  height: 2.25rem;
  border-bottom: 1px solid var(--mc-border-subtle);
  background: color-mix(in srgb, var(--mc-bg) 94%, #ffffff 6%);
  user-select: none;
}

.mc-titlebar-left {
  display: flex;
  align-items: stretch;
  height: 100%;
  justify-self: start;
}

.mc-titlebar-center {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--mc-text-muted);
  font-size: 0.72rem;
  pointer-events: none;
}

.mc-titlebar-icon,
.mc-menu-button,
.mc-window-controls button {
  border: 0;
  background: transparent;
  color: var(--mc-text-secondary);
}

.mc-titlebar-icon {
  display: grid;
  place-items: center;
  width: 2.35rem;
  height: 100%;
  cursor: pointer;
}

.mc-titlebar-icon:hover,
.mc-menu-button:hover,
.mc-menu-button.is-active {
  background: var(--mc-surface-hover);
  color: var(--mc-text-primary);
}

.mc-menu-root {
  position: relative;
  height: 100%;
}

.mc-menu-button {
  height: 100%;
  padding: 0 0.7rem;
  font-size: 0.76rem;
  cursor: pointer;
}

.mc-menu-popover {
  position: absolute;
  top: calc(100% + 0.2rem);
  left: 0.2rem;
  width: 16rem;
  padding: 0.3rem;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface-elevated);
  box-shadow: var(--mc-shadow);
}

.mc-menu-popover > button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  width: 100%;
  min-height: 2rem;
  padding: 0.3rem 0.55rem;
  border: 0;
  border-radius: var(--mc-radius-sm);
  background: transparent;
  color: var(--mc-text-secondary);
  text-align: left;
  cursor: pointer;
}

.mc-menu-popover > button:hover:not(:disabled) {
  background: var(--mc-surface-hover);
  color: var(--mc-text-primary);
}

.mc-menu-popover > button:disabled {
  cursor: default;
  opacity: 0.5;
}

.mc-menu-popover small {
  color: var(--mc-text-muted);
  font-size: 0.68rem;
}

.mc-menu-popover kbd {
  color: var(--mc-text-muted);
  font-size: 0.67rem;
}

.mc-menu-separator {
  height: 1px;
  margin: 0.25rem 0.35rem;
  background: var(--mc-border-subtle);
}

.mc-window-controls {
  display: flex;
  align-self: stretch;
  justify-self: end;
}

.mc-window-controls button {
  display: grid;
  place-items: center;
  width: 2.85rem;
  cursor: pointer;
}

.mc-window-controls button:hover {
  background: var(--mc-surface-hover);
  color: var(--mc-text-primary);
}

.mc-window-controls button.is-close:hover {
  background: #c42b1c;
  color: #ffffff;
}

.mc-shell {
  padding-top: 2.25rem;
}

.mc-sidebar {
  height: calc(100vh - 2.25rem);
}

.mc-main {
  height: calc(100vh - 2.25rem);
}

/* stronger semantic status / priority styling */

.mc-option-choice[data-tone="success"].is-selected,
.mc-state-badge[data-tone="success"] {
  border-color: color-mix(in srgb, var(--mc-success) 52%, transparent);
  background: var(--mc-success-soft);
  color: var(--mc-success);
}

.mc-option-choice[data-tone="info"].is-selected,
.mc-state-badge[data-tone="info"] {
  border-color: color-mix(in srgb, var(--mc-info) 52%, transparent);
  background: var(--mc-info-soft);
  color: var(--mc-info);
}

.mc-option-choice[data-tone="warning"].is-selected,
.mc-state-badge[data-tone="warning"] {
  border-color: color-mix(in srgb, var(--mc-warning) 55%, transparent);
  background: var(--mc-warning-soft);
  color: var(--mc-warning);
}

.mc-option-choice[data-tone="danger"].is-selected,
.mc-state-badge[data-tone="danger"] {
  border-color: color-mix(in srgb, var(--mc-danger) 58%, transparent);
  background: var(--mc-danger-soft);
  color: var(--mc-danger);
}

.mc-option-choice[data-tone="accent"].is-selected,
.mc-state-badge[data-tone="accent"] {
  border-color: var(--mc-accent-border);
  background: var(--mc-accent-soft);
  color: var(--mc-accent);
}

.mc-option-choice[data-tone="low"].is-selected,
.mc-state-badge[data-tone="low"] {
  border-color: color-mix(in srgb, var(--mc-priority-low) 55%, transparent);
  background: color-mix(in srgb, var(--mc-priority-low) 13%, transparent);
  color: var(--mc-priority-low);
}

.mc-option-choice[data-tone="medium"].is-selected,
.mc-state-badge[data-tone="medium"] {
  border-color: color-mix(in srgb, var(--mc-priority-medium) 58%, transparent);
  background: color-mix(in srgb, var(--mc-priority-medium) 13%, transparent);
  color: var(--mc-priority-medium);
}

.mc-option-choice[data-tone="high"].is-selected,
.mc-state-badge[data-tone="high"] {
  border-color: color-mix(in srgb, var(--mc-priority-high) 60%, transparent);
  background: color-mix(in srgb, var(--mc-priority-high) 13%, transparent);
  color: var(--mc-priority-high);
}

.mc-option-choice[data-tone="critical"].is-selected,
.mc-state-badge[data-tone="critical"] {
  border-color: var(--mc-priority-critical);
  background: color-mix(in srgb, var(--mc-priority-critical) 16%, transparent);
  color: var(--mc-priority-critical);
}

.mc-option-choice.is-selected .mc-option-dot,
.mc-state-badge .mc-state-dot {
  background: currentColor;
  box-shadow: 0 0 0 2px color-mix(in srgb, currentColor 20%, transparent);
}

/* keyboard shortcut settings */

.mc-settings-heading-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.mc-shortcut-list {
  overflow: hidden;
}

.mc-shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  min-height: 4rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--mc-border-subtle);
}

.mc-shortcut-row:last-child {
  border-bottom: 0;
}

.mc-shortcut-copy {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.mc-shortcut-copy strong {
  font-size: 0.8rem;
  font-weight: 600;
}

.mc-shortcut-copy span {
  color: var(--mc-text-muted);
  font-size: 0.72rem;
}

.mc-shortcut-actions {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.mc-shortcut-key {
  min-width: 7rem;
  min-height: 2rem;
  padding: 0 0.65rem;
  border: 1px solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface-raised);
  color: var(--mc-text-secondary);
  font-family: inherit;
  font-size: 0.72rem;
  cursor: pointer;
}

.mc-shortcut-key:hover {
  border-color: var(--mc-border-strong);
  color: var(--mc-text-primary);
}

.mc-shortcut-key.is-recording {
  border-color: var(--mc-accent);
  background: var(--mc-accent-soft);
  color: var(--mc-accent);
}

.mc-settings-hint {
  margin-top: 0.75rem;
  color: var(--mc-text-muted);
  font-size: 0.72rem;
}

@media (max-width: 760px) {
  .mc-titlebar {
    grid-template-columns: 1fr auto;
  }

  .mc-titlebar-center {
    display: none;
  }

  .mc-menu-button {
    padding-inline: 0.45rem;
  }

  .mc-window-controls {
    display: none;
  }

  .mc-shortcut-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .mc-shortcut-actions {
    width: 100%;
  }

  .mc-shortcut-key {
    flex: 1;
  }
}
'''

globals_path = "src/styles/globals.css"
globals_old = read(globals_path)

marker = "/* v0.1.2 desktop shell + semantic refinement */"

if marker in globals_old:
    raise RuntimeError("The refinement CSS already exists")

globals_new = globals_old.rstrip() + "\n" + css_addition.strip() + "\n"

tauri_path = ROOT / "src-tauri" / "tauri.conf.json"
tauri_data = json.loads(
    tauri_path.read_text(encoding="utf-8")
)

window = tauri_data["app"]["windows"][0]
window["decorations"] = False

tauri_new = json.dumps(
    tauri_data,
    indent=2,
    ensure_ascii=False
) + "\n"

files = [
    replace_file(
        "src/app/preferences/UiPreferencesProvider.tsx",
        preferences
    ),
    replace_file(
        "src/app/shell/AppShell.tsx",
        shell
    ),
    replace_file(
        "src/modules/settings/SettingsPage.tsx",
        settings
    ),
    replace_file(
        globals_path,
        globals_new
    ),
    replace_file(
        "src-tauri/tauri.conf.json",
        tauri_new
    )
]

patch = {
    "version": 2,
    "name": "Mission Control v0.1.2 desktop UI refinement",
    "files": files,
    "options": {
        "rollback_on_verify_failure": True
    }
}

OUT.write_text(
    json.dumps(
        patch,
        indent=2,
        ensure_ascii=False
    ) + "\n",
    encoding="utf-8"
)

print(f"Created: {OUT}")
print(f"Patch contains {len(files)} file operations.")