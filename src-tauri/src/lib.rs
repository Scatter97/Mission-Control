use serde::Serialize;

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
        .invoke_handler(tauri::generate_handler![
            backend_capabilities
        ])
        .run(tauri::generate_context!())
        .expect("error while running Mission Control");
}