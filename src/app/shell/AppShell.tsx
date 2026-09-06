import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { Command } from "lucide-react";

import { moduleRegistry } from "../modules/registry";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const navigation = moduleRegistry.getNavigationItems();

  return (
    <div className="mc-shell">
      <aside className="mc-sidebar">
        <div className="mc-brand">
          <div className="mc-brand-mark">
            <Command size={17} strokeWidth={2.2} />
          </div>

          <div className="mc-brand-copy">
            <span className="mc-brand-title">Mission Control</span>
            <span className="mc-brand-version">v0.1</span>
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
                  `mc-nav-item${isActive ? " is-active" : ""}`
                }
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <main className="mc-main">{children}</main>
    </div>
  );
}