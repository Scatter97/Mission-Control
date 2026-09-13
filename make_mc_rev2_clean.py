from pathlib import Path
import hashlib
import json
import re

ROOT = Path(r"C:\Users\joshh\Desktop\Mission-Control")
OUT = ROOT / "mission-control-v0.1.2-rev.2.json"

VERSION = "0.1.2+rev.2"

EXPECTED = {
    "package.json":
        "9048C9B56A4DA63D436AA77A028E93C3B8547EB60B18F53C09FB72D5C2838D85",

    "package-lock.json":
        "C77E53008091FFD99E5692D55BB031FECC76A3A0146CDF324EF5FD281B13B28C",

    "src-tauri/Cargo.toml":
        "3F8681C7FFD754A7AA8F1CCB9B7337B1F46101B3C058FFE91194C7B5A8897CA9",

    "src-tauri/Cargo.lock":
        "F9A589632C24FC891993ABFA430F7ABBA73E5F247F1CF65BDFA9555EFBDECAF5",

    "src-tauri/tauri.conf.json":
        "5F249C87E5270F2F206C6AC8BA31A651E0EAE70D2DB874A7386D7130390CAA93",

    "src-tauri/src/lib.rs":
        "3C073371736058F094895CE9BEF386E9C903B299876ADABADB79AEFF614B2D41",

    "src/app/shell/AppShell.tsx":
        "B00F68337F3A3795C6F1923DD2037BB262E1103A205DFB218124210286FE172C",

    "src/modules/settings/SettingsPage.tsx":
        "EDF763A438F2C7A8FC2CC300D694D9BD6AFD5EDFA70F88A262BB6CA8704D29AE",

    "src/modules/projects/components/ProjectForm.tsx":
        "52E3BA0F9034CB707FCB3DD3D8D390CE91B939AFB40A41BB3647296800B26B7E",

    "src/styles/globals.css":
        "EAA7AD287DBF7A1684BC4B418DD0AEA8F8F14D5E90BA1F54F66E17C5C20A0044",
}


def raw(path):
    return (ROOT / path).read_bytes()


def source(path):
    return (
        raw(path)
        .decode("utf-8")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def sha(path):
    return hashlib.sha256(raw(path)).hexdigest().upper()


def replace_once(text, old, new, label):
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"{label}: expected 1 match, found {count}"
        )

    return text.replace(old, new, 1)


def file_edit(path, new_text):
    old_text = source(path)

    if old_text == new_text:
        raise RuntimeError(
            f"{path}: generated no change"
        )

    return {
        "path": path,
        "sha256": hashlib.sha256(
            raw(path)
        ).hexdigest(),
        "edits": [
            {
                "op": "replace",
                "old": old_text,
                "new": new_text
            }
        ]
    }


for path, expected in EXPECTED.items():
    actual = sha(path)

    if actual != expected:
        raise RuntimeError(
            f"{path} does not match clean baseline.\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )


files = []


# ------------------------------------------------------------
# package.json
# ------------------------------------------------------------

path = "package.json"
text = source(path)

text = replace_once(
    text,
    '"version": "0.1.2+rev.1"',
    '"version": "0.1.2+rev.2"',
    path
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# package-lock.json (root + root package = 2)
# ------------------------------------------------------------

path = "package-lock.json"
text = source(path)

count = text.count(
    '"version": "0.1.2+rev.1"'
)

if count != 2:
    raise RuntimeError(
        f"{path}: expected 2 Mission Control version entries, found {count}"
    )

text = text.replace(
    '"version": "0.1.2+rev.1"',
    '"version": "0.1.2+rev.2"'
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Cargo.toml
# ------------------------------------------------------------

path = "src-tauri/Cargo.toml"
text = source(path)

text = replace_once(
    text,
    'version = "0.1.2+rev.1"',
    'version = "0.1.2+rev.2"',
    path
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Cargo.lock
# ------------------------------------------------------------

path = "src-tauri/Cargo.lock"
text = source(path)

pattern = (
    r'(\[\[package\]\]\n'
    r'name = "mission-control"\n'
    r'version = ")0\.1\.2\+rev\.1(")'
)

text, count = re.subn(
    pattern,
    rf'\g<1>{VERSION}\g<2>',
    text,
    count=1
)

if count != 1:
    raise RuntimeError(
        "Cargo.lock: Mission Control package entry not found."
    )

files.append(file_edit(path, text))


# ------------------------------------------------------------
# tauri.conf.json
# ------------------------------------------------------------

path = "src-tauri/tauri.conf.json"
text = source(path)

text = replace_once(
    text,
    '"version": "0.1.2+rev.1"',
    '"version": "0.1.2+rev.2"',
    path
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Rust folder picker
# Uses only std + Windows PowerShell/WinForms.
# No new Rust/npm dependency is required.
# ------------------------------------------------------------

path = "src-tauri/src/lib.rs"
text = source(path)

folder_command = r'''
#[tauri::command]
fn pick_project_folder() -> Result<Option<String>, String> {
    #[cfg(target_os = "windows")]
    {
        let script = r#"
Add-Type -AssemblyName System.Windows.Forms

$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Select project repository folder'
$dialog.ShowNewFolderButton = $true

$result = $dialog.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    Write-Output $dialog.SelectedPath
}
"#;

        let output = std::process::Command::new("powershell.exe")
            .args([
                "-NoProfile",
                "-STA",
                "-Command",
                script,
            ])
            .output()
            .map_err(|error| {
                format!("Could not open folder picker: {error}")
            })?;

        if !output.status.success() {
            let message = String::from_utf8_lossy(
                &output.stderr
            )
            .trim()
            .to_string();

            return Err(
                if message.is_empty() {
                    "Folder picker failed.".to_string()
                } else {
                    message
                }
            );
        }

        let selected = String::from_utf8_lossy(
            &output.stdout
        )
        .trim()
        .to_string();

        if selected.is_empty() {
            Ok(None)
        } else {
            Ok(Some(selected))
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err(
            "Project folder browsing is currently supported on Windows."
                .to_string()
        )
    }
}

'''

text = replace_once(
    text,
    "#[cfg_attr(mobile, tauri::mobile_entry_point)]\n",
    folder_command
    + "#[cfg_attr(mobile, tauri::mobile_entry_point)]\n",
    "lib.rs command insertion"
)

text = replace_once(
    text,
    '''        .invoke_handler(tauri::generate_handler![
            backend_capabilities,
''',
    '''        .invoke_handler(tauri::generate_handler![
            backend_capabilities,
            pick_project_folder,
''',
    "lib.rs invoke handler"
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# ProjectForm
# ------------------------------------------------------------

path = "src/modules/projects/components/ProjectForm.tsx"
text = source(path)

text = replace_once(
    text,
    'import { useState, type FormEvent } from "react";',
    '''import { invoke } from "@tauri-apps/api/core";
import { useState, type FormEvent } from "react";''',
    "ProjectForm invoke import"
)

text = replace_once(
    text,
    '''  return (
    <form className="mc-project-form-v2" onSubmit={handleSubmit}>''',
    '''  async function handleBrowseLocalFolder() {
    try {
      setError(null);

      const selected = await invoke<string | null>(
        "pick_project_folder"
      );

      if (!selected) {
        return;
      }

      setValue((current) => ({
        ...current,
        localPath: selected
      }));
    } catch (browseError) {
      setError(String(browseError));
    }
  }

  return (
    <form className="mc-project-form-v2" onSubmit={handleSubmit}>''',
    "ProjectForm browse handler"
)

old_folder = r'''          <label className="mc-field">
            <span>Local folder</span>
            <input
              value={value.localPath ?? ""}
              placeholder="C:\Projects\Mission-Control"
              onChange={(event) =>
                setValue((current) => ({ ...current, localPath: event.target.value }))
              }
            />
          </label>'''

new_folder = r'''          <label className="mc-field">
            <span>Local folder</span>

            <div className="mc-path-picker-row">
              <input
                value={value.localPath ?? ""}
                placeholder="C:\Projects\Mission-Control"
                onChange={(event) =>
                  setValue((current) => ({ ...current, localPath: event.target.value }))
                }
              />

              <button
                className="mc-button mc-path-picker-button"
                type="button"
                onClick={handleBrowseLocalFolder}
              >
                Browse…
              </button>
            </div>
          </label>'''

text = replace_once(
    text,
    old_folder,
    new_folder,
    "ProjectForm Local folder"
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# AppShell visible version
# ------------------------------------------------------------

path = "src/app/shell/AppShell.tsx"
text = source(path)

text = replace_once(
    text,
    "v0.1.2.1",
    "v0.1.2+rev.2",
    path
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Settings/About visible version
# ------------------------------------------------------------

path = "src/modules/settings/SettingsPage.tsx"
text = source(path)

text = replace_once(
    text,
    "<dd>0.1.2.1</dd>",
    "<dd>0.1.2+rev.2</dd>",
    path
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Fullscreen bottom-edge fix + folder picker layout
#
# Current shell uses 100vh then later receives top padding.
# Fix it by pinning the application surface directly to all
# four webview edges and making root/body paint the MC bg.
# ------------------------------------------------------------

path = "src/styles/globals.css"
text = source(path)

addition = r'''

/* 0.1.2+rev.2 fullscreen coverage + folder picker */

html,
body,
#root {
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  padding: 0;
  margin: 0;
  overflow: hidden;
  background: var(--mc-bg);
}

.mc-shell {
  position: fixed;
  inset: 0;
  width: auto;
  height: auto;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--mc-bg);
}

.mc-sidebar,
.mc-main {
  min-height: 0;
  height: 100%;
  max-height: 100%;
}

.mc-shell.is-fullscreen {
  inset: 0;
  width: auto;
  height: auto;
  background: var(--mc-bg);
}

.mc-path-picker-row {
  display: flex;
  width: 100%;
  min-width: 0;
  align-items: stretch;
  gap: 0.5rem;
}

.mc-path-picker-row > input {
  min-width: 0;
  flex: 1 1 auto;
}

.mc-path-picker-button {
  flex: 0 0 auto;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .mc-path-picker-row {
    flex-direction: column;
  }

  .mc-path-picker-button {
    width: 100%;
  }
}
'''

if "/* 0.1.2+rev.2 fullscreen coverage + folder picker */" in text:
    raise RuntimeError(
        "rev.2 CSS already exists."
    )

text = text.rstrip() + "\n" + addition.strip() + "\n"

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Final Patch Forge spec
# ------------------------------------------------------------

patch = {
    "version": 2,
    "name": "Mission Control 0.1.2+rev.2",

    "files": files,

    "missionControl": {
        "configPath": ".mission-control.json",
        "createIfMissing": True,

        "set": {
            "schemaVersion": 1,
            "name": "Mission Control",
            "version": VERSION,
            "status": "active",

            "currentPhase":
                "Repository integration",

            "currentStep":
                "Add GitHub repository import",

            "currentStepStatus":
                "todo",

            "currentStepPriority":
                "medium",

            "lastCompletedStep":
                "Add native project-folder selection and "
                "Patch Forge Mission Control metadata support",

            "nextSteps": [
                "Add GitHub repository import",
                "Sync GitHub repository metadata",
                "Load project state from .mission-control.json",
                "Build file-content clipboard helper"
            ],

            "blockers": [],

            "repository": {
                "provider": "github",
                "url":
                    "https://github.com/Scatter97/Mission-Control"
            }
        }
    },

    "build": [
        {
            "type": "command",
            "name": "Frontend build",
            "command": "npm run build",
            "timeout_seconds": 180
        },
        {
            "type": "command",
            "name": "Rust check",
            "command":
                "cargo check --manifest-path src-tauri/Cargo.toml",
            "timeout_seconds": 300
        }
    ],

    "verify": [
        {
            "type": "file_exists",
            "name": "Mission Control config",
            "path": ".mission-control.json"
        }
    ],

    "options": {
        "rollback_on_verify_failure": True
    }
}

OUT.write_text(
    json.dumps(
        patch,
        indent=2,
        ensure_ascii=False,
    ) + "\n",
    encoding="utf-8",
)

print(f"Created: {OUT}")
print(f"Version: {VERSION}")
print(f"Code file changes: {len(files)}")
print("Metadata: .mission-control.json")