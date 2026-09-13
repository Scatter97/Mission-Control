from pathlib import Path
import hashlib
import json
import re

ROOT = Path(r"C:\Users\joshh\Desktop\Mission-Control")
OUT = ROOT / "mission-control-v0.1.3-github-import.json"

VERSION = "0.1.3"

EXPECTED = {
    "package.json":
        "5939D84F3D8ACA2F322FEEB81969D611CE311FE4BCCC44BD2104C3B99F10EB87",

    "package-lock.json":
        "759CC9A06F9897FD200BA999A1D67C2277D8E84396E80306AA9E72C85DBE4378",

    "src-tauri/Cargo.toml":
        "CA4D0BBD7DE16DD4FE797351EE1404F4344C1256F870F539490BBFB9B4264DE7",

    "src-tauri/Cargo.lock":
        "0BCEC7958C5E80FC5003983A5AFA0BA5924574C90B9D5A0925F11F40A6211D43",

    "src-tauri/tauri.conf.json":
        "A82D85F5CCC3120B038D054134653007B70C495D2B991187DFC8886EF395AD49",

    "src-tauri/src/lib.rs":
        "AE103841C6B63F0F91812D4E904FDE210C062DB2F8B0F555F9B971CD21AC1E78",

    "src/app/shell/AppShell.tsx":
        "3E71ED23EE5DC6B4EC987816B9197DED1B65C77EA821F1D083E1A58EC771AE72",

    "src/modules/settings/SettingsPage.tsx":
        "F68074587B52C76710EDA86EFE17C06DF3E89496006E326AF7EE48CF07608D53",

    "src/modules/projects/pages/NewProjectPage.tsx":
        "28C30468F5DF14AF59B4B72DA1E9B289EFBDC4EA046096E055564368A2C1D112",

    "src/styles/globals.css":
        "CDD2F424D2625E1FED38F8FD2086E8234511147508C0C48017273B2D2EBFC600",
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
            f"{path} does not match expected 0.1.2+rev.2 baseline.\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )


new_component_path = (
    ROOT
    / "src/modules/projects/components/GitHubImportForm.tsx"
)

if new_component_path.exists():
    raise RuntimeError(
        "GitHubImportForm.tsx already exists."
    )


files = []


# ------------------------------------------------------------
# Version files
# ------------------------------------------------------------

path = "package.json"
text = source(path)
text = replace_once(
    text,
    '"version": "0.1.2+rev.2"',
    '"version": "0.1.3"',
    path,
)
files.append(file_edit(path, text))


path = "package-lock.json"
text = source(path)

count = text.count(
    '"version": "0.1.2+rev.2"'
)

if count != 2:
    raise RuntimeError(
        f"{path}: expected 2 version entries, found {count}"
    )

text = text.replace(
    '"version": "0.1.2+rev.2"',
    '"version": "0.1.3"',
)

files.append(file_edit(path, text))


path = "src-tauri/Cargo.toml"
text = source(path)
text = replace_once(
    text,
    'version = "0.1.2+rev.2"',
    'version = "0.1.3"',
    path,
)
files.append(file_edit(path, text))


path = "src-tauri/Cargo.lock"
text = source(path)

pattern = (
    r'(\[\[package\]\]\n'
    r'name = "mission-control"\n'
    r'version = ")0\.1\.2\+rev\.2(")'
)

text, count = re.subn(
    pattern,
    r'\g<1>0.1.3\g<2>',
    text,
    count=1,
)

if count != 1:
    raise RuntimeError(
        "Cargo.lock Mission Control entry not found."
    )

files.append(file_edit(path, text))


path = "src-tauri/tauri.conf.json"
text = source(path)
text = replace_once(
    text,
    '"version": "0.1.2+rev.2"',
    '"version": "0.1.3"',
    path,
)
files.append(file_edit(path, text))


# ------------------------------------------------------------
# AppShell visible version
# ------------------------------------------------------------

path = "src/app/shell/AppShell.tsx"
text = source(path)
text = replace_once(
    text,
    "v0.1.2+rev.2",
    "v0.1.3",
    path,
)
files.append(file_edit(path, text))


# ------------------------------------------------------------
# Settings visible version
# ------------------------------------------------------------

path = "src/modules/settings/SettingsPage.tsx"
text = source(path)
text = replace_once(
    text,
    "<dd>0.1.2+rev.2</dd>",
    "<dd>0.1.3</dd>",
    path,
)
files.append(file_edit(path, text))


# ------------------------------------------------------------
# Rust backend:
# - GitHub public repository metadata
# - .mission-control.json read/create
# ------------------------------------------------------------

path = "src-tauri/src/lib.rs"
text = source(path)

text = replace_once(
    text,
    "use serde::Serialize;\n",
    '''use serde::{Deserialize, Serialize};
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
};
''',
    "lib.rs imports",
)

backend_addition = r'''
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct GitHubRepositoryPreview {
    name: String,
    full_name: String,
    owner: String,
    html_url: String,
    description: Option<String>,
    is_private: bool,
    default_branch: String,
}

#[derive(Debug, Deserialize)]
struct GitHubApiOwner {
    login: String,
}

#[derive(Debug, Deserialize)]
struct GitHubApiRepository {
    name: String,
    full_name: String,
    html_url: String,
    description: Option<String>,
    private: bool,
    default_branch: String,
    owner: GitHubApiOwner,
}

fn valid_github_component(value: &str) -> bool {
    !value.is_empty()
        && value.chars().all(|character| {
            character.is_ascii_alphanumeric()
                || character == '-'
                || character == '_'
                || character == '.'
        })
}

fn github_repository_parts(
    value: &str,
) -> Result<(String, String), String> {
    let mut normalized = value.trim().trim_end_matches('/').to_string();

    if let Some(value) = normalized.strip_prefix("https://") {
        normalized = value.to_string();
    } else if let Some(value) = normalized.strip_prefix("http://") {
        normalized = value.to_string();
    }

    if let Some(value) = normalized.strip_prefix("www.") {
        normalized = value.to_string();
    }

    let path = normalized
        .strip_prefix("github.com/")
        .ok_or_else(|| {
            "Enter a GitHub repository URL such as https://github.com/owner/repository."
                .to_string()
        })?;

    let segments = path
        .split('/')
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>();

    if segments.len() != 2 {
        return Err(
            "GitHub URL must point directly to a repository."
                .to_string()
        );
    }

    let owner = segments[0].to_string();
    let repository = segments[1]
        .strip_suffix(".git")
        .unwrap_or(segments[1])
        .to_string();

    if !valid_github_component(&owner)
        || !valid_github_component(&repository)
    {
        return Err(
            "GitHub owner or repository name contains unsupported characters."
                .to_string()
        );
    }

    Ok((owner, repository))
}

#[tauri::command]
fn github_repository_preview(
    url: String,
) -> Result<GitHubRepositoryPreview, String> {
    let (owner, repository) = github_repository_parts(&url)?;

    #[cfg(target_os = "windows")]
    {
        let script = format!(
            r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{
    'User-Agent' = 'Mission-Control'
    'Accept' = 'application/vnd.github+json'
}}

try {{
    $response = Invoke-RestMethod `
        -Uri 'https://api.github.com/repos/{owner}/{repository}' `
        -Headers $headers `
        -Method Get

    $response | ConvertTo-Json -Compress -Depth 6
}}
catch {{
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}}
"#
        );

        let output = std::process::Command::new("powershell.exe")
            .args([
                "-NoProfile",
                "-Command",
                &script,
            ])
            .output()
            .map_err(|error| {
                format!(
                    "Could not contact GitHub: {error}"
                )
            })?;

        if !output.status.success() {
            let message = String::from_utf8_lossy(
                &output.stderr
            )
            .trim()
            .to_string();

            return Err(
                if message.is_empty() {
                    "GitHub repository could not be loaded."
                        .to_string()
                } else {
                    format!(
                        "GitHub repository could not be loaded: {message}"
                    )
                }
            );
        }

        let response: GitHubApiRepository =
            serde_json::from_slice(&output.stdout)
                .map_err(|error| {
                    format!(
                        "GitHub returned an unexpected response: {error}"
                    )
                })?;

        Ok(GitHubRepositoryPreview {
            name: response.name,
            full_name: response.full_name,
            owner: response.owner.login,
            html_url: response.html_url,
            description: response.description,
            is_private: response.private,
            default_branch: response.default_branch,
        })
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = owner;
        let _ = repository;

        Err(
            "GitHub repository import is currently supported on Windows."
                .to_string()
        )
    }
}

fn mission_control_config_path(
    local_path: &str,
) -> Result<PathBuf, String> {
    let root = Path::new(local_path);

    if !root.exists() {
        return Err(
            "Selected local project folder does not exist."
                .to_string()
        );
    }

    if !root.is_dir() {
        return Err(
            "Selected local project path is not a folder."
                .to_string()
        );
    }

    Ok(root.join(".mission-control.json"))
}

#[tauri::command]
fn project_config_read(
    local_path: String,
) -> Result<Option<serde_json::Value>, String> {
    let path = mission_control_config_path(&local_path)?;

    if !path.exists() {
        return Ok(None);
    }

    let text = fs::read_to_string(&path)
        .map_err(|error| {
            format!(
                "Could not read {}: {error}",
                path.display()
            )
        })?;

    let value: serde_json::Value =
        serde_json::from_str(&text)
            .map_err(|error| {
                format!(
                    "Invalid {}: {error}",
                    path.display()
                )
            })?;

    if !value.is_object() {
        return Err(
            ".mission-control.json must contain a JSON object."
                .to_string()
        );
    }

    Ok(Some(value))
}

#[tauri::command]
fn project_config_write_if_missing(
    local_path: String,
    config: serde_json::Value,
) -> Result<bool, String> {
    if !config.is_object() {
        return Err(
            "Mission Control project config must be a JSON object."
                .to_string()
        );
    }

    let path = mission_control_config_path(&local_path)?;

    let text = serde_json::to_string_pretty(&config)
        .map_err(|error| error.to_string())?
        + "\n";

    let mut file = match OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
    {
        Ok(file) => file,

        Err(error)
            if error.kind()
                == std::io::ErrorKind::AlreadyExists =>
        {
            return Ok(false);
        }

        Err(error) => {
            return Err(
                format!(
                    "Could not create {}: {error}",
                    path.display()
                )
            );
        }
    };

    file.write_all(text.as_bytes())
        .map_err(|error| {
            format!(
                "Could not write {}: {error}",
                path.display()
            )
        })?;

    Ok(true)
}

'''

marker = "#[tauri::command]\nfn pick_project_folder()"

if marker not in text:
    raise RuntimeError(
        "Could not find folder picker command insertion point."
    )

text = text.replace(
    marker,
    backend_addition + marker,
    1,
)

text = replace_once(
    text,
    '''            backend_capabilities,
            pick_project_folder,
''',
    '''            backend_capabilities,
            github_repository_preview,
            project_config_read,
            project_config_write_if_missing,
            pick_project_folder,
''',
    "lib.rs invoke handler",
)

files.append(file_edit(path, text))


# ------------------------------------------------------------
# GitHub import component
# ------------------------------------------------------------

github_component = r'''import { invoke } from "@tauri-apps/api/core";
import {
  CheckCircle2,
  FolderOpen,
  Github,
  GitBranch,
  Lock,
  Unlock
} from "lucide-react";
import {
  useState,
  type FormEvent
} from "react";

import {
  PROJECT_STATUSES,
  STEP_PRIORITIES,
  STEP_STATUSES,
  emptyProjectInput,
  type ProjectInput,
  type ProjectStatus,
  type StepPriority,
  type StepStatus
} from "../types";

interface GitHubRepositoryPreview {
  name: string;
  fullName: string;
  owner: string;
  htmlUrl: string;
  description: string | null;
  isPrivate: boolean;
  defaultBranch: string;
}

interface GitHubImportFormProps {
  busy?: boolean;
  onCancel: () => void;
  onSubmit: (input: ProjectInput) => Promise<void> | void;
}

type ProjectConfig = Record<string, unknown>;

function configString(
  config: ProjectConfig | null,
  key: string,
  fallback: string
): string {
  const value = config?.[key];
  return typeof value === "string" ? value : fallback;
}

function configStrings(
  config: ProjectConfig | null,
  key: string,
  fallback: string[]
): string[] {
  const value = config?.[key];

  if (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string")
  ) {
    return value;
  }

  return fallback;
}

function configProjectStatus(
  config: ProjectConfig | null
): ProjectStatus {
  const value = config?.status;

  return typeof value === "string" &&
    PROJECT_STATUSES.includes(value as ProjectStatus)
    ? (value as ProjectStatus)
    : "active";
}

function configStepStatus(
  config: ProjectConfig | null
): StepStatus {
  const value = config?.currentStepStatus;

  return typeof value === "string" &&
    STEP_STATUSES.includes(value as StepStatus)
    ? (value as StepStatus)
    : "todo";
}

function configStepPriority(
  config: ProjectConfig | null
): StepPriority {
  const value = config?.currentStepPriority;

  return typeof value === "string" &&
    STEP_PRIORITIES.includes(value as StepPriority)
    ? (value as StepPriority)
    : "medium";
}

function configRepositoryUrl(
  config: ProjectConfig | null
): string | null {
  const repository = config?.repository;

  if (
    !repository ||
    typeof repository !== "object" ||
    Array.isArray(repository)
  ) {
    return null;
  }

  const url = (
    repository as Record<string, unknown>
  ).url;

  return typeof url === "string"
    ? url
    : null;
}

function normalizedRepositoryUrl(
  value: string
): string {
  let normalized = value
    .trim()
    .toLowerCase();

  while (normalized.endsWith("/")) {
    normalized = normalized.slice(0, -1);
  }

  if (normalized.endsWith(".git")) {
    normalized = normalized.slice(0, -4);
  }

  return normalized;
}
function buildInput(
  repository: GitHubRepositoryPreview,
  localPath: string | null,
  config: ProjectConfig | null
): ProjectInput {
  return {
    ...emptyProjectInput,

    name: configString(
      config,
      "name",
      repository.name
    ),

    description:
      repository.description ?? "",

    status: configProjectStatus(config),

    currentVersion: configString(
      config,
      "version",
      ""
    ),

    currentPhase: configString(
      config,
      "currentPhase",
      "Repository integration"
    ),

    currentStep: configString(
      config,
      "currentStep",
      "Sync GitHub repository metadata"
    ),

    currentStepStatus:
      configStepStatus(config),

    currentStepPriority:
      configStepPriority(config),

    lastCompletedStep: configString(
      config,
      "lastCompletedStep",
      "Imported GitHub repository"
    ),

    nextSteps: configStrings(
      config,
      "nextSteps",
      [
        "Add authenticated GitHub account connection",
        "Sync GitHub repository metadata automatically"
      ]
    ),

    blockers: configStrings(
      config,
      "blockers",
      []
    ),

    localPath,
    repoUrl: repository.htmlUrl
  };
}

function configForInput(
  input: ProjectInput,
  repository: GitHubRepositoryPreview
): ProjectConfig {
  return {
    schemaVersion: 1,
    name: input.name,
    version: input.currentVersion,
    status: input.status,
    currentPhase: input.currentPhase,
    currentStep: input.currentStep,
    currentStepStatus: input.currentStepStatus,
    currentStepPriority: input.currentStepPriority,
    lastCompletedStep: input.lastCompletedStep,
    nextSteps: input.nextSteps,
    blockers: input.blockers,

    repository: {
      provider: "github",
      url: repository.htmlUrl
    }
  };
}

export function GitHubImportForm({
  busy = false,
  onCancel,
  onSubmit
}: GitHubImportFormProps) {
  const [repoUrl, setRepoUrl] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [repository, setRepository] =
    useState<GitHubRepositoryPreview | null>(null);

  const [existingConfig, setExistingConfig] =
    useState<ProjectConfig | null>(null);

  const [configDetected, setConfigDetected] =
    useState(false);

  const [loadingRepository, setLoadingRepository] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  async function readConfig(
    path: string
  ): Promise<ProjectConfig | null> {
    if (!path.trim()) {
      setExistingConfig(null);
      setConfigDetected(false);
      return null;
    }

    const config = await invoke<ProjectConfig | null>(
      "project_config_read",
      {
        localPath: path.trim()
      }
    );

    setExistingConfig(config);
    setConfigDetected(Boolean(config));

    return config;
  }

  async function handleLoadRepository() {
    if (!repoUrl.trim()) {
      setError("GitHub repository URL is required.");
      return;
    }

    try {
      setError(null);
      setLoadingRepository(true);

      const result =
        await invoke<GitHubRepositoryPreview>(
          "github_repository_preview",
          {
            url: repoUrl.trim()
          }
        );

      setRepository(result);
      setRepoUrl(result.htmlUrl);
    } catch (loadError) {
      setRepository(null);
      setError(String(loadError));
    } finally {
      setLoadingRepository(false);
    }
  }

  async function handleBrowseLocalFolder() {
    try {
      setError(null);

      const selected =
        await invoke<string | null>(
          "pick_project_folder"
        );

      if (!selected) {
        return;
      }

      setLocalPath(selected);
      await readConfig(selected);
    } catch (browseError) {
      setError(String(browseError));
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!repository) {
      setError(
        "Load a GitHub repository before importing it."
      );
      return;
    }

    try {
      setError(null);

      const normalizedLocalPath =
        localPath.trim() || null;

      let config = existingConfig;

      if (normalizedLocalPath) {
        config = await readConfig(
          normalizedLocalPath
        );
      }

      if (config) {
        const configuredRepository =
          configRepositoryUrl(config);

        if (
          configuredRepository &&
          normalizedRepositoryUrl(
            configuredRepository
          ) !==
            normalizedRepositoryUrl(
              repository.htmlUrl
            )
        ) {
          throw new Error(
            "This folder's .mission-control.json belongs to a different GitHub repository."
          );
        }
      }

      let input = buildInput(
        repository,
        normalizedLocalPath,
        config
      );

      if (normalizedLocalPath && !config) {
        const created =
          await invoke<boolean>(
            "project_config_write_if_missing",
            {
              localPath: normalizedLocalPath,
              config: configForInput(
                input,
                repository
              )
            }
          );

        if (!created) {
          const discovered =
            await readConfig(
              normalizedLocalPath
            );

          input = buildInput(
            repository,
            normalizedLocalPath,
            discovered
          );
        }
      }

      await onSubmit(input);
    } catch (submitError) {
      setError(String(submitError));
    }
  }

  return (
    <form
      className="mc-project-form-v2"
      onSubmit={handleSubmit}
    >
      <section className="mc-form-section">
        <div className="mc-form-section-copy">
          <p className="mc-eyebrow">
            GitHub
          </p>

          <h2>Repository</h2>

          <p>
            Import a real GitHub repository into
            Mission Control. Public repositories are
            supported in this version.
          </p>
        </div>

        <div className="mc-form-section-fields">
          <label className="mc-field">
            <span>GitHub repository URL</span>

            <div className="mc-github-url-row">
              <input
                autoFocus
                value={repoUrl}
                placeholder="https://github.com/owner/repository"
                onChange={(event) => {
                  setRepoUrl(event.target.value);
                  setRepository(null);
                }}
              />

              <button
                className="mc-button"
                type="button"
                disabled={loadingRepository}
                onClick={() =>
                  void handleLoadRepository()
                }
              >
                <Github size={14} />

                {loadingRepository
                  ? "Loading..."
                  : "Load repository"}
              </button>
            </div>
          </label>

          {repository ? (
            <div className="mc-github-preview">
              <div className="mc-github-preview-heading">
                <div className="mc-github-repo-mark">
                  <Github size={18} />
                </div>

                <div>
                  <strong>
                    {repository.fullName}
                  </strong>

                  <span>
                    {repository.description ||
                      "No repository description."}
                  </span>
                </div>

                <CheckCircle2
                  className="mc-github-loaded"
                  size={17}
                />
              </div>

              <dl className="mc-github-meta">
                <div>
                  <dt>Owner</dt>
                  <dd>{repository.owner}</dd>
                </div>

                <div>
                  <dt>Default branch</dt>
                  <dd>
                    <GitBranch size={12} />
                    {repository.defaultBranch}
                  </dd>
                </div>

                <div>
                  <dt>Visibility</dt>
                  <dd>
                    {repository.isPrivate ? (
                      <Lock size={12} />
                    ) : (
                      <Unlock size={12} />
                    )}

                    {repository.isPrivate
                      ? "Private"
                      : "Public"}
                  </dd>
                </div>
              </dl>
            </div>
          ) : null}

          <p className="mc-form-hint">
            GitHub sign-in and private repository
            access will be added in the next
            integration step.
          </p>
        </div>
      </section>

      <section className="mc-form-section">
        <div className="mc-form-section-copy">
          <p className="mc-eyebrow">
            Local workspace
          </p>

          <h2>Project folder</h2>

          <p>
            Optionally connect the imported repository
            to a local checkout.
          </p>
        </div>

        <div className="mc-form-section-fields">
          <label className="mc-field">
            <span>Local folder</span>

            <div className="mc-path-picker-row">
              <input
                value={localPath}
                placeholder="C:\Projects\repository"
                onChange={(event) => {
                  setLocalPath(event.target.value);
                  setExistingConfig(null);
                  setConfigDetected(false);
                }}
              />

              <button
                className="mc-button mc-path-picker-button"
                type="button"
                onClick={() =>
                  void handleBrowseLocalFolder()
                }
              >
                <FolderOpen size={14} />
                Browse…
              </button>
            </div>
          </label>

          {configDetected ? (
            <div className="mc-config-detected">
              <CheckCircle2 size={14} />

              <span>
                Existing .mission-control.json
                detected. Its project state will be
                loaded during import.
              </span>
            </div>
          ) : localPath.trim() ? (
            <p className="mc-form-hint">
              If this folder does not already contain
              .mission-control.json, Mission Control
              will create it during import.
            </p>
          ) : null}
        </div>
      </section>

      {error ? (
        <p className="mc-form-error">
          {error}
        </p>
      ) : null}

      <div className="mc-form-footer">
        <button
          className="mc-button"
          type="button"
          onClick={onCancel}
        >
          Cancel
        </button>

        <button
          className="mc-button mc-button-primary"
          type="submit"
          disabled={
            busy ||
            loadingRepository ||
            !repository
          }
        >
          {busy
            ? "Importing..."
            : "Import repository"}
        </button>
      </div>
    </form>
  );
}
'''

files.append({
    "path":
        "src/modules/projects/components/GitHubImportForm.tsx",

    "action": "create",
    "content": github_component
})


# ------------------------------------------------------------
# New Project page
# ------------------------------------------------------------

path = "src/modules/projects/pages/NewProjectPage.tsx"

new_page = r'''import { useState } from "react";
import {
  ArrowLeft,
  Github,
  PencilLine
} from "lucide-react";
import {
  Link,
  useNavigate
} from "react-router-dom";

import { GitHubImportForm } from "../components/GitHubImportForm";
import { ProjectForm } from "../components/ProjectForm";
import { useCreateProject } from "../hooks";

type CreateMode = "manual" | "github";

export function NewProjectPage() {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  const [mode, setMode] =
    useState<CreateMode>("manual");

  const create = async (
    input: Parameters<
      typeof createProject.mutateAsync
    >[0]
  ) => {
    const project =
      await createProject.mutateAsync(input);

    navigate(`/projects/${project.id}`);
  };

  return (
    <section className="mc-page mc-page-form">
      <Link
        className="mc-back-link"
        to="/projects"
      >
        <ArrowLeft size={14} />
        Projects
      </Link>

      <header className="mc-page-header">
        <div>
          <p className="mc-eyebrow">
            Projects
          </p>

          <h1>New project</h1>

          <p className="mc-page-description">
            Create a project manually or import a
            repository directly from GitHub.
          </p>
        </div>
      </header>

      <div
        className="mc-create-mode"
        role="tablist"
        aria-label="Project creation method"
      >
        <button
          className={
            mode === "manual"
              ? "is-active"
              : ""
          }
          type="button"
          role="tab"
          aria-selected={mode === "manual"}
          onClick={() => setMode("manual")}
        >
          <PencilLine size={14} />

          <span>
            <strong>Create manually</strong>
            <small>
              Enter project state yourself
            </small>
          </span>
        </button>

        <button
          className={
            mode === "github"
              ? "is-active"
              : ""
          }
          type="button"
          role="tab"
          aria-selected={mode === "github"}
          onClick={() => setMode("github")}
        >
          <Github size={14} />

          <span>
            <strong>Import from GitHub</strong>
            <small>
              Load repository metadata
            </small>
          </span>
        </button>
      </div>

      {mode === "manual" ? (
        <ProjectForm
          submitLabel="Create project"
          busy={createProject.isPending}
          onCancel={() =>
            navigate("/projects")
          }
          onSubmit={create}
        />
      ) : (
        <GitHubImportForm
          busy={createProject.isPending}
          onCancel={() =>
            navigate("/projects")
          }
          onSubmit={create}
        />
      )}
    </section>
  );
}
'''

files.append(
    file_edit(
        path,
        new_page
    )
)


# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------

path = "src/styles/globals.css"
text = source(path)

css = r'''

/* 0.1.3 GitHub repository import */

.mc-create-mode {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.625rem;
  margin-bottom: 0.875rem;
}

.mc-create-mode > button {
  display: flex;
  min-width: 0;
  min-height: 4.5rem;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface);
  color: var(--mc-text-secondary);
  text-align: left;
  cursor: pointer;
}

.mc-create-mode > button:hover {
  background: var(--mc-surface-hover);
}

.mc-create-mode > button.is-active {
  border-color: var(--mc-accent-border);
  background: var(--mc-accent-soft);
  color: var(--mc-accent);
  box-shadow: inset 0 0 0 0.0625rem var(--mc-accent-border);
}

.mc-create-mode > button > svg {
  flex: 0 0 auto;
  margin-top: 0.125rem;
}

.mc-create-mode > button > span {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.25rem;
}

.mc-create-mode strong {
  color: var(--mc-text-primary);
  font-size: 0.8125rem;
}

.mc-create-mode small {
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
}

.mc-github-url-row {
  display: flex;
  min-width: 0;
  gap: 0.5rem;
}

.mc-github-url-row > input {
  min-width: 0;
  flex: 1 1 auto;
}

.mc-github-url-row > button {
  flex: 0 0 auto;
  white-space: nowrap;
}

.mc-github-preview {
  overflow: hidden;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-md);
  background: var(--mc-surface-raised);
}

.mc-github-preview-heading {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.875rem;
}

.mc-github-repo-mark {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border: 0.0625rem solid var(--mc-border);
  border-radius: var(--mc-radius-sm);
  background: var(--mc-surface);
  color: var(--mc-text-secondary);
}

.mc-github-preview-heading > div:nth-child(2) {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.25rem;
}

.mc-github-preview-heading strong {
  overflow: hidden;
  color: var(--mc-text-primary);
  font-size: 0.8125rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-github-preview-heading span {
  color: var(--mc-text-muted);
  font-size: 0.75rem;
  line-height: 1.45;
}

.mc-github-loaded {
  color: var(--mc-success);
}

.mc-github-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  border-top: 0.0625rem solid var(--mc-border-subtle);
}

.mc-github-meta > div {
  min-width: 0;
  padding: 0.75rem 0.875rem;
  border-right: 0.0625rem solid var(--mc-border-subtle);
}

.mc-github-meta > div:last-child {
  border-right: 0;
}

.mc-github-meta dt {
  margin-bottom: 0.25rem;
  color: var(--mc-text-muted);
  font-size: 0.625rem;
  text-transform: uppercase;
  letter-spacing: 0.045em;
}

.mc-github-meta dd {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.375rem;
  overflow: hidden;
  margin: 0;
  color: var(--mc-text-secondary);
  font-size: 0.75rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-form-hint {
  margin: 0;
  color: var(--mc-text-muted);
  font-size: 0.6875rem;
  line-height: 1.45;
}

.mc-config-detected {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.625rem 0.75rem;
  border: 0.0625rem solid color-mix(
    in srgb,
    var(--mc-success) 28%,
    transparent
  );
  border-radius: var(--mc-radius-sm);
  background: var(--mc-success-soft);
  color: var(--mc-success);
  font-size: 0.75rem;
  line-height: 1.45;
}

.mc-config-detected svg {
  flex: 0 0 auto;
  margin-top: 0.0625rem;
}

@media (max-width: 640px) {
  .mc-create-mode,
  .mc-github-meta {
    grid-template-columns: 1fr;
  }

  .mc-github-url-row {
    flex-direction: column;
  }

  .mc-github-url-row > button {
    width: 100%;
  }

  .mc-github-meta > div {
    border-right: 0;
    border-bottom: 0.0625rem solid var(--mc-border-subtle);
  }

  .mc-github-meta > div:last-child {
    border-bottom: 0;
  }
}
'''

if "/* 0.1.3 GitHub repository import */" in text:
    raise RuntimeError(
        "0.1.3 GitHub CSS already exists."
    )

text = text.rstrip() + "\n" + css.strip() + "\n"

files.append(file_edit(path, text))


# ------------------------------------------------------------
# Final patch
# ------------------------------------------------------------

patch = {
    "version": 2,
    "name": "Mission Control 0.1.3 GitHub repository import",

    "files": files,

    "missionControl": {
        "configPath": ".mission-control.json",
        "createIfMissing": False,

        "replace": {
            "version": VERSION,
            "status": "active",

            "currentPhase":
                "Repository integration",

            "currentStep":
                "Add authenticated GitHub account connection",

            "currentStepStatus":
                "todo",

            "currentStepPriority":
                "medium",

            "lastCompletedStep":
                "Add GitHub repository import with local project config discovery",

            "nextSteps": [
                "Add authenticated GitHub account connection",
                "Add private repository access",
                "Sync GitHub repository metadata automatically"
            ],

            "blockers": []
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
            "name": "GitHub import component",
            "path":
                "src/modules/projects/components/GitHubImportForm.tsx"
        },
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
        ensure_ascii=False
    ) + "\n",
    encoding="utf-8"
)

print(f"Created: {OUT}")
print(f"Version: {VERSION}")
print(f"Code file changes: {len(files)}")
print("New feature: GitHub repository import")
print("Config: read existing or create if missing")