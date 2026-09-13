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
