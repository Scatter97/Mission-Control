import {
  Laptop,
  Moon,
  Sun
} from "lucide-react";

import {
  useTheme,
  type ThemePreference
} from "../../app/theme/ThemeProvider";

const choices: Array<{
  value: ThemePreference;
  label: string;
  description: string;
  icon: typeof Moon;
}> = [
  {
    value: "dark",
    label: "Dark",
    description: "Mission Control's primary visual theme.",
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

export function SettingsPage() {
  const { preference, setPreference } = useTheme();

  return (
    <section className="mc-page">
      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">Mission Control</p>
          <h1>Settings</h1>
          <p className="mc-page-description">
            Configure global Mission Control preferences.
          </p>
        </div>
      </header>

      <div className="mc-settings-section">
        <div className="mc-section-heading">
          <h2>Appearance</h2>
          <p>Choose how Mission Control should look.</p>
        </div>

        <div className="mc-theme-grid">
          {choices.map((choice) => {
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
      </div>
    </section>
  );
}