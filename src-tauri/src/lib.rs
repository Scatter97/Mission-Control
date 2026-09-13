mod projects;

use serde::Serialize;
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
