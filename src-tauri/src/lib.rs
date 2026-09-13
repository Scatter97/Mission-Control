mod projects;

use serde::{Deserialize, Serialize};
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
};
use tauri::Manager;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendCapabilities {
    projects: bool,
    settings: bool,
    patch_forge: bool,
    git: bool,
    terminal: bool,
    ai: bool,
    remote: bool,
    bom: bool,
}

#[tauri::command]
fn backend_capabilities() -> BackendCapabilities {
    BackendCapabilities {
        projects: true,
        settings: true,
        patch_forge: false,
        git: false,
        terminal: false,
        ai: false,
        remote: false,
        bom: false,
    }
}



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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            let database_path = data_dir.join("mission-control.sqlite3");
            let store = projects::ProjectStore::open(&database_path)?;
            app.manage(store);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            backend_capabilities,
            github_repository_preview,
            project_config_read,
            project_config_write_if_missing,
            pick_project_folder,
            projects::projects_list,
            projects::projects_get,
            projects::projects_create,
            projects::projects_update,
            projects::projects_archive,
            projects::projects_restore,
            projects::projects_delete
        ])
        .run(tauri::generate_context!())
        .expect("error while running Mission Control");
}
