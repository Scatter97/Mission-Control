import { useEffect, useState, type ReactNode } from "react";
import { Command, Menu, X } from "lucide-react";
import { NavLink } from "react-router-dom";

import { moduleRegistry } from "../modules/registry";
import { useUiPreferences } from "../preferences/UiPreferencesProvider";

interface AppShellProps {
  children: ReactNode;
}

const MOBILE_QUERY = "(max-width: 760px)";

export function AppShell({ children }: AppShellProps) {
  const navigation = moduleRegistry.getNavigationItems();
  const { sidebarHidden, toggleSidebar } = useUiPreferences();
  const [mobile, setMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const query = window.matchMedia(MOBILE_QUERY);
    const onChange = () => {
      setMobile(query.matches);
      if (!query.matches) setMobileOpen(false);
    };

    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === "b") {
        event.preventDefault();
        if (mobile) {
          setMobileOpen((open) => !open);
        } else {
          toggleSidebar();
        }
      }

      if (event.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobile, mobileOpen, toggleSidebar]);

  const handleToggle = () => {
    if (mobile) {
      setMobileOpen((open) => !open);
      return;
    }

    toggleSidebar();
  };

  const shellClass = [
    "mc-shell",
    sidebarHidden ? "is-sidebar-hidden" : "",
    mobileOpen ? "is-mobile-sidebar-open" : ""
  ].filter(Boolean).join(" ");

  return (
    <div className={shellClass}>
      <aside className="mc-sidebar" aria-label="Mission Control sidebar">
        <div className="mc-brand">
          <div className="mc-brand-mark">
            <Command size={17} strokeWidth={2.2} />
          </div>

          <div className="mc-brand-copy">
            <span className="mc-brand-title">Mission Control</span>
            <span className="mc-brand-version">v0.1.2</span>
          </div>

          {mobile ? (
            <button
              className="mc-icon-button mc-sidebar-close"
              type="button"
              aria-label="Close sidebar"
              onClick={() => setMobileOpen(false)}
            >
              <X size={16} />
            </button>
          ) : null}
        </div>

        <nav className="mc-nav" aria-label="Mission Control">
          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.id}
                to={item.route}
                className={({ isActive }) =>
                  `mc-nav-item${isActive ? " is-active" : ""}`
                }
                onClick={() => {
                  if (mobile) setMobileOpen(false);
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
          <kbd>Ctrl+B</kbd>
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

      <div className="mc-main-frame">
        <header className="mc-shellbar">
          <button
            className="mc-icon-button mc-sidebar-toggle"
            type="button"
            aria-label={mobileOpen || !sidebarHidden ? "Hide sidebar" : "Show sidebar"}
            title="Toggle sidebar (Ctrl+B)"
            onClick={handleToggle}
          >
            <Menu size={17} />
          </button>
          <span className="mc-shellbar-title">Mission Control</span>
        </header>

        <main className="mc-main">{children}</main>
      </div>
    </div>
  );
}
