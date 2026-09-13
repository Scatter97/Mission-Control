import {
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

    if (event.key === "Escape") {
      setRecording(null);
      return;
    }

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
                    <dd>0.1.2+rev.2</dd>
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
