import {
  Boxes,
  Database,
  FlaskConical,
  FolderKanban,
  Info,
  Laptop,
  Link2,
  Monitor,
  Moon,
  Settings2,
  Sun
} from "lucide-react";
import { NavLink, useParams } from "react-router-dom";

import {
  useTheme,
  type ThemePreference
} from "../../app/theme/ThemeProvider";
import {
  UI_SCALE_OPTIONS,
  useUiPreferences
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
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "data", label: "Data & Backups", icon: Database },
  { id: "advanced", label: "Advanced", icon: FlaskConical },
  { id: "about", label: "About", icon: Info }
] as const;

type SectionId = (typeof sections)[number]["id"];

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
        <span className="mc-coming-soon">Reserved for a future Mission Control update</span>
      </div>
    </div>
  );
}

export function SettingsPage() {
  const { section } = useParams();
  const activeSection: SectionId = sections.some((item) => item.id === section)
    ? (section as SectionId)
    : "general";

  const { preference, setPreference } = useTheme();
  const { uiScale, setUiScale, sidebarHidden, setSidebarHidden } = useUiPreferences();

  return (
    <section className="mc-page mc-settings-page">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Mission Control</p>
          <h1>Settings</h1>
          <p className="mc-page-description">
            Configure the application shell, appearance, and workspace behavior.
          </p>
        </div>
      </header>

      <div className="mc-settings-layout">
        <nav className="mc-settings-nav" aria-label="Settings sections">
          {sections.map((item) => {
            const Icon = item.icon;
            const route = item.id === "general" ? "/settings" : `/settings/${item.id}`;

            return (
              <NavLink
                key={item.id}
                to={route}
                end={item.id === "general"}
                className={({ isActive }) =>
                  `mc-settings-nav-item${isActive ? " is-active" : ""}`
                }
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mc-settings-content">
          {activeSection === "general" ? (
            <>
              <div className="mc-settings-heading">
                <h2>General</h2>
                <p>Core Mission Control application behavior.</p>
              </div>

              <div className="mc-settings-group mc-panel">
                <div className="mc-setting-row">
                  <div>
                    <strong>Sidebar</strong>
                    <span>Choose whether the desktop sidebar starts visible.</span>
                  </div>
                  <button
                    className={`mc-toggle${!sidebarHidden ? " is-on" : ""}`}
                    type="button"
                    role="switch"
                    aria-checked={!sidebarHidden}
                    onClick={() => setSidebarHidden(!sidebarHidden)}
                  >
                    <span />
                  </button>
                </div>

                <div className="mc-setting-row is-static">
                  <div>
                    <strong>Keyboard shortcut</strong>
                    <span>Show or hide the sidebar from anywhere in Mission Control.</span>
                  </div>
                  <kbd>Ctrl+B</kbd>
                </div>
              </div>
            </>
          ) : null}

          {activeSection === "appearance" ? (
            <>
              <div className="mc-settings-heading">
                <h2>Appearance</h2>
                <p>Choose how Mission Control should look.</p>
              </div>

              <div className="mc-theme-grid">
                {themeChoices.map((choice) => {
                  const Icon = choice.icon;
                  const selected = preference === choice.value;

                  return (
                    <button
                      key={choice.value}
                      type="button"
                      className={`mc-theme-choice${selected ? " is-selected" : ""}`}
                      onClick={() => setPreference(choice.value)}
                    >
                      <Icon size={18} />
                      <span>
                        <strong>{choice.label}</strong>
                        <small>{choice.description}</small>
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
                <p>Scale the complete Mission Control interface without changing OS display scaling.</p>
              </div>

              <div className="mc-settings-group mc-panel">
                <div className="mc-scale-header">
                  <div>
                    <strong>Interface scale</strong>
                    <span>Applies to navigation, text, controls, panels, forms, and future modules.</span>
                  </div>
                  <strong className="mc-scale-value">{uiScale}%</strong>
                </div>

                <div className="mc-scale-grid">
                  {UI_SCALE_OPTIONS.map((scale) => (
                    <button
                      key={scale}
                      type="button"
                      className={`mc-scale-choice${uiScale === scale ? " is-selected" : ""}`}
                      onClick={() => setUiScale(scale)}
                    >
                      {scale}%
                    </button>
                  ))}
                </div>

                <div className="mc-setting-note">
                  100% uses Mission Control's normal size on top of your Windows or Linux display scaling.
                </div>
              </div>
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
                <p>Local-first project and development workflow command center.</p>
                <dl className="mc-about-list">
                  <div><dt>Version</dt><dd>0.1.2</dd></div>
                  <div><dt>Runtime</dt><dd>Tauri + React + TypeScript</dd></div>
                  <div><dt>Storage</dt><dd>SQLite</dd></div>
                </dl>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
