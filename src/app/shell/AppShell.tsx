import {
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
import { preloadGitHubAccount } from "../../modules/github/githubAccountStore";
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
    void preloadGitHubAccount(true)
      .catch(() => undefined);
  }, []);

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
              v0.1.4
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
