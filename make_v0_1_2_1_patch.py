from pathlib import Path
import json
import re

ROOT = Path(r"C:\Users\joshh\Desktop\Mission-Control")
OUT = ROOT / "mission-control-v0.1.2.1-fixes.json"

DISPLAY_VERSION = "0.1.2.1"
SEMVER_VERSION = "0.1.2+rev.1"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def replace_file(path, new_text):
    old_text = read(path)

    if old_text == new_text:
        raise RuntimeError(f"{path}: no changes produced")

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


def replace_once(text, old, new, label):
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly 1 match, found {count}"
        )

    return text.replace(old, new, 1)


files = []


# ------------------------------------------------------------
# package.json
# ------------------------------------------------------------

package_path = "package.json"
package = json.loads(read(package_path))
package["version"] = SEMVER_VERSION

package_new = json.dumps(
    package,
    indent=2,
    ensure_ascii=False
) + "\n"

files.append(replace_file(package_path, package_new))


# ------------------------------------------------------------
# package-lock.json
# ------------------------------------------------------------

lock_path = "package-lock.json"
lock = json.loads(read(lock_path))

lock["version"] = SEMVER_VERSION

if "" in lock.get("packages", {}):
    lock["packages"][""]["version"] = SEMVER_VERSION
else:
    raise RuntimeError("package-lock.json: root package entry missing")

lock_new = json.dumps(
    lock,
    indent=2,
    ensure_ascii=False
) + "\n"

files.append(replace_file(lock_path, lock_new))


# ------------------------------------------------------------
# Cargo.toml
# ------------------------------------------------------------

cargo_path = "src-tauri/Cargo.toml"
cargo = read(cargo_path)

cargo_new = replace_once(
    cargo,
    'version = "0.1.2"',
    f'version = "{SEMVER_VERSION}"',
    cargo_path
)

files.append(replace_file(cargo_path, cargo_new))


# ------------------------------------------------------------
# Cargo.lock
# ------------------------------------------------------------

cargo_lock_path = "src-tauri/Cargo.lock"
cargo_lock = read(cargo_lock_path)

pattern = (
    r'(\[\[package\]\]\s*'
    r'name = "mission-control"\s*'
    r'version = ")0\.1\.2(")'
)

cargo_lock_new, count = re.subn(
    pattern,
    rf'\g<1>{SEMVER_VERSION}\g<2>',
    cargo_lock,
    count=1
)

if count != 1:
    raise RuntimeError(
        f"{cargo_lock_path}: could not find Mission Control 0.1.2 package entry"
    )

files.append(
    replace_file(cargo_lock_path, cargo_lock_new)
)


# ------------------------------------------------------------
# tauri.conf.json
# ------------------------------------------------------------

tauri_path = "src-tauri/tauri.conf.json"
tauri = json.loads(read(tauri_path))
tauri["version"] = SEMVER_VERSION

# Keep the custom title bar.
window = tauri["app"]["windows"][0]
window["decorations"] = False

tauri_new = json.dumps(
    tauri,
    indent=2,
    ensure_ascii=False
) + "\n"

files.append(replace_file(tauri_path, tauri_new))


# ------------------------------------------------------------
# AppShell
# ------------------------------------------------------------

shell_path = "src/app/shell/AppShell.tsx"
shell = read(shell_path)

shell = replace_once(
    shell,
    '<span className="mc-brand-version">\n              v0.1.2\n            </span>',
    f'<span className="mc-brand-version">\n              v{DISPLAY_VERSION}\n            </span>',
    "AppShell visible version"
)

# Remove the visible Ctrl+B badge from the sidebar footer.
old_footer = '''        <div className="mc-sidebar-footer">
          <span>Local workspace</span>
          <kbd>{shortcuts.toggleSidebar}</kbd>
        </div>'''

new_footer = '''        <div className="mc-sidebar-footer">
          <span>Local workspace</span>
        </div>'''

shell = replace_once(
    shell,
    old_footer,
    new_footer,
    "AppShell sidebar footer"
)

files.append(replace_file(shell_path, shell))


# ------------------------------------------------------------
# Settings page
# ------------------------------------------------------------

settings_path = "src/modules/settings/SettingsPage.tsx"
settings = read(settings_path)

settings = replace_once(
    settings,
    "<dd>0.1.2</dd>",
    f"<dd>{DISPLAY_VERSION}</dd>",
    "Settings About version"
)

# The UI says Escape cancels shortcut recording, so make it true.
old_capture = '''    event.preventDefault();
    event.stopPropagation();

    const shortcut = shortcutFromEvent(
      event.nativeEvent
    );'''

new_capture = '''    event.preventDefault();
    event.stopPropagation();

    if (event.key === "Escape") {
      setRecording(null);
      return;
    }

    const shortcut = shortcutFromEvent(
      event.nativeEvent
    );'''

settings = replace_once(
    settings,
    old_capture,
    new_capture,
    "Keyboard shortcut Escape handling"
)

files.append(replace_file(settings_path, settings))


# ------------------------------------------------------------
# CSS fixes
# ------------------------------------------------------------

css_path = "src/styles/globals.css"
css = read(css_path)

marker = "/* v0.1.2.1 polish fixes */"

if marker in css:
    raise RuntimeError("v0.1.2.1 CSS already exists")

css_addition = r'''

/* v0.1.2.1 polish fixes */

/* Settings navigation: remove native/default gray button appearance. */

.mc-settings-nav {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.2rem;
}

.mc-settings-nav button {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: 100%;
  min-height: 2.25rem;
  padding: 0.45rem 0.65rem;
  border: 1px solid transparent;
  border-radius: var(--mc-radius-sm);
  background: transparent;
  color: var(--mc-text-secondary);
  text-align: left;
  font: inherit;
  font-size: 0.78rem;
  cursor: pointer;
  transition:
    background 120ms ease,
    border-color 120ms ease,
    color 120ms ease;
}

.mc-settings-nav button:hover {
  background: var(--mc-surface-hover);
  color: var(--mc-text-primary);
}

.mc-settings-nav button.is-active {
  border-color: var(--mc-accent-border);
  background: var(--mc-accent-soft);
  color: var(--mc-text-primary);
}

.mc-settings-nav button.is-active svg {
  color: var(--mc-accent);
}


/*
 * Semantic dots are always colored.
 * Selection still adds the stronger border/background/text treatment.
 */

.mc-option-choice[data-tone="neutral"] .mc-option-dot {
  background: var(--mc-text-muted);
}

.mc-option-choice[data-tone="accent"] .mc-option-dot {
  background: var(--mc-accent);
}

.mc-option-choice[data-tone="success"] .mc-option-dot {
  background: var(--mc-success);
}

.mc-option-choice[data-tone="warning"] .mc-option-dot {
  background: var(--mc-warning);
}

.mc-option-choice[data-tone="danger"] .mc-option-dot {
  background: var(--mc-danger);
}

.mc-option-choice[data-tone="info"] .mc-option-dot {
  background: var(--mc-info);
}

.mc-option-choice[data-tone="low"] .mc-option-dot {
  background: var(--mc-priority-low);
}

.mc-option-choice[data-tone="medium"] .mc-option-dot {
  background: var(--mc-priority-medium);
}

.mc-option-choice[data-tone="high"] .mc-option-dot {
  background: var(--mc-priority-high);
}

.mc-option-choice[data-tone="critical"] .mc-option-dot {
  background: var(--mc-priority-critical);
}


/* Give every semantic dot a subtle halo, even while unselected. */

.mc-option-choice .mc-option-dot {
  box-shadow:
    0 0 0 2px
    color-mix(in srgb, currentColor 8%, transparent);
}


/* Selected states remain visibly stronger. */

.mc-option-choice[data-tone="success"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-success) 58%, transparent);
  background: var(--mc-success-soft);
  color: var(--mc-success);
}

.mc-option-choice[data-tone="info"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-info) 58%, transparent);
  background: var(--mc-info-soft);
  color: var(--mc-info);
}

.mc-option-choice[data-tone="warning"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-warning) 60%, transparent);
  background: var(--mc-warning-soft);
  color: var(--mc-warning);
}

.mc-option-choice[data-tone="danger"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-danger) 62%, transparent);
  background: var(--mc-danger-soft);
  color: var(--mc-danger);
}

.mc-option-choice[data-tone="accent"].is-selected {
  border-color: var(--mc-accent-border);
  background: var(--mc-accent-soft);
  color: var(--mc-accent);
}

.mc-option-choice[data-tone="low"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-priority-low) 58%, transparent);
  background:
    color-mix(in srgb, var(--mc-priority-low) 13%, transparent);
  color: var(--mc-priority-low);
}

.mc-option-choice[data-tone="medium"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-priority-medium) 62%, transparent);
  background:
    color-mix(in srgb, var(--mc-priority-medium) 14%, transparent);
  color: var(--mc-priority-medium);
}

.mc-option-choice[data-tone="high"].is-selected {
  border-color:
    color-mix(in srgb, var(--mc-priority-high) 64%, transparent);
  background:
    color-mix(in srgb, var(--mc-priority-high) 14%, transparent);
  color: var(--mc-priority-high);
}

.mc-option-choice[data-tone="critical"].is-selected {
  border-color: var(--mc-priority-critical);
  background:
    color-mix(in srgb, var(--mc-priority-critical) 17%, transparent);
  color: var(--mc-priority-critical);
}


/* Sidebar footer no longer reserves room for a shortcut badge. */

.mc-sidebar-footer {
  justify-content: flex-start;
}
'''

css_new = css.rstrip() + "\n" + css_addition.strip() + "\n"

files.append(replace_file(css_path, css_new))


# ------------------------------------------------------------
# Tauri capability permissions for custom window controls
# ------------------------------------------------------------

capability_path = ROOT / "src-tauri" / "capabilities" / "default.json"

required_permissions = [
    "core:window:allow-close",
    "core:window:allow-minimize",
    "core:window:allow-toggle-maximize",
    "core:window:allow-set-fullscreen",
    "core:window:allow-is-fullscreen",
    "core:window:allow-start-dragging"
]

if capability_path.exists():
    rel = capability_path.relative_to(ROOT).as_posix()

    capability = json.loads(
        capability_path.read_text(encoding="utf-8")
    )

    permissions = capability.setdefault(
        "permissions",
        []
    )

    for permission in required_permissions:
        if permission not in permissions:
            permissions.append(permission)

    capability_new = json.dumps(
        capability,
        indent=2,
        ensure_ascii=False
    ) + "\n"

    files.append(
        replace_file(rel, capability_new)
    )

else:
    capability_new = {
        "$schema": "../gen/schemas/desktop-schema.json",
        "identifier": "default",
        "description": "Default Mission Control desktop capability",
        "windows": ["main"],
        "permissions": [
            "core:default",
            *required_permissions
        ]
    }

    files.append({
        "path": "src-tauri/capabilities/default.json",
        "action": "create",
        "content": json.dumps(
            capability_new,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    })


patch = {
    "version": 2,
    "name": "Mission Control v0.1.2.1 polish fixes",
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
print(f"Display version: {DISPLAY_VERSION}")
print(f"Internal SemVer: {SEMVER_VERSION}")