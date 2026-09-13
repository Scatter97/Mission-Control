use rusqlite::{params, Connection, OptionalExtension, Row};
use serde::{Deserialize, Serialize};
use std::{
    fs,
    path::Path,
    sync::Mutex,
    time::{SystemTime, UNIX_EPOCH},
};
use tauri::State;
use uuid::Uuid;

const SCHEMA_VERSION: i64 = 2;
const PROJECT_STATUSES: &[&str] = &[
    "active",
    "planning",
    "paused",
    "blocked",
    "waiting",
    "completed",
];
const STEP_STATUSES: &[&str] = &["todo", "in_progress", "blocked", "waiting", "done"];
const STEP_PRIORITIES: &[&str] = &["low", "medium", "high", "critical"];

pub struct ProjectStore {
    connection: Mutex<Connection>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Project {
    id: String,
    name: String,
    description: String,
    status: String,
    current_version: String,
    current_phase: String,
    current_step: String,
    current_step_status: String,
    current_step_priority: String,
    last_completed_step: String,
    next_steps: Vec<String>,
    blockers: Vec<String>,
    local_path: Option<String>,
    repo_url: Option<String>,
    archived: bool,
    created_at: i64,
    updated_at: i64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectInput {
    name: String,
    description: String,
    status: String,
    current_version: String,
    current_phase: String,
    current_step: String,
    current_step_status: String,
    current_step_priority: String,
    last_completed_step: String,
    next_steps: Vec<String>,
    blockers: Vec<String>,
    local_path: Option<String>,
    repo_url: Option<String>,
}

impl ProjectStore {
    pub fn open(path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let connection = Connection::open(path)?;
        connection.execute_batch(
            r#"
            PRAGMA journal_mode = WAL;
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                current_version TEXT NOT NULL DEFAULT '',
                current_phase TEXT NOT NULL DEFAULT '',
                current_step TEXT NOT NULL DEFAULT '',
                current_step_status TEXT NOT NULL DEFAULT 'todo',
                current_step_priority TEXT NOT NULL DEFAULT 'medium',
                last_completed_step TEXT NOT NULL DEFAULT '',
                next_steps_json TEXT NOT NULL DEFAULT '[]',
                blockers_json TEXT NOT NULL DEFAULT '[]',
                local_path TEXT,
                repo_url TEXT,
                archived INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            "#,
        )?;

        let had_step_status = column_exists(&connection, "projects", "current_step_status")?;
        let had_step_priority = column_exists(&connection, "projects", "current_step_priority")?;

        if !had_step_status {
            connection.execute(
                "ALTER TABLE projects ADD COLUMN current_step_status TEXT NOT NULL DEFAULT 'todo'",
                [],
            )?;
        }

        if !had_step_priority {
            connection.execute(
                "ALTER TABLE projects ADD COLUMN current_step_priority TEXT NOT NULL DEFAULT 'medium'",
                [],
            )?;

            if column_exists(&connection, "projects", "priority")? {
                connection.execute(
                    "UPDATE projects
                     SET current_step_priority = CASE
                       WHEN priority IN ('low','medium','high','critical') THEN priority
                       ELSE 'medium'
                     END",
                    [],
                )?;
            }
        }

        connection.pragma_update(None, "user_version", SCHEMA_VERSION)?;

        Ok(Self {
            connection: Mutex::new(connection),
        })
    }
}

fn column_exists(
    connection: &Connection,
    table: &str,
    column: &str,
) -> Result<bool, rusqlite::Error> {
    let sql = format!("PRAGMA table_info({table})");
    let mut statement = connection.prepare(&sql)?;
    let names = statement.query_map([], |row| row.get::<_, String>(1))?;

    for name in names {
        if name? == column {
            return Ok(true);
        }
    }

    Ok(false)
}

fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

fn validate_input(input: &ProjectInput) -> Result<(), String> {
    if input.name.trim().is_empty() {
        return Err("Project name is required".into());
    }

    if !PROJECT_STATUSES.contains(&input.status.as_str()) {
        return Err("Invalid project status".into());
    }

    if !STEP_STATUSES.contains(&input.current_step_status.as_str()) {
        return Err("Invalid current step status".into());
    }

    if !STEP_PRIORITIES.contains(&input.current_step_priority.as_str()) {
        return Err("Invalid current step priority".into());
    }

    Ok(())
}

fn row_to_project(row: &Row<'_>) -> rusqlite::Result<Project> {
    let next_steps: String = row.get("next_steps_json")?;
    let blockers: String = row.get("blockers_json")?;

    Ok(Project {
        id: row.get("id")?,
        name: row.get("name")?,
        description: row.get("description")?,
        status: row.get("status")?,
        current_version: row.get("current_version")?,
        current_phase: row.get("current_phase")?,
        current_step: row.get("current_step")?,
        current_step_status: row.get("current_step_status")?,
        current_step_priority: row.get("current_step_priority")?,
        last_completed_step: row.get("last_completed_step")?,
        next_steps: serde_json::from_str(&next_steps).unwrap_or_default(),
        blockers: serde_json::from_str(&blockers).unwrap_or_default(),
        local_path: row.get("local_path")?,
        repo_url: row.get("repo_url")?,
        archived: row.get::<_, i64>("archived")? != 0,
        created_at: row.get("created_at")?,
        updated_at: row.get("updated_at")?,
    })
}

fn get(connection: &Connection, id: &str) -> Result<Option<Project>, String> {
    connection
        .query_row(
            "SELECT * FROM projects WHERE id = ?1",
            [id],
            row_to_project,
        )
        .optional()
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn projects_list(
    archived: bool,
    store: State<'_, ProjectStore>,
) -> Result<Vec<Project>, String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    let mut statement = connection
        .prepare("SELECT * FROM projects WHERE archived = ?1 ORDER BY updated_at DESC")
        .map_err(|error| error.to_string())?;

    let rows = statement
        .query_map([if archived { 1 } else { 0 }], row_to_project)
        .map_err(|error| error.to_string())?;

    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn projects_get(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<Option<Project>, String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;
    get(&connection, &id)
}

#[tauri::command]
pub fn projects_create(
    input: ProjectInput,
    store: State<'_, ProjectStore>,
) -> Result<Project, String> {
    validate_input(&input)?;

    let id = Uuid::new_v4().to_string();
    let timestamp = now();
    let next_steps = serde_json::to_string(&input.next_steps).map_err(|e| e.to_string())?;
    let blockers = serde_json::to_string(&input.blockers).map_err(|e| e.to_string())?;
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "INSERT INTO projects (
                id,name,description,status,priority,current_version,current_phase,current_step,
                current_step_status,current_step_priority,last_completed_step,next_steps_json,
                blockers_json,local_path,repo_url,archived,created_at,updated_at
             ) VALUES (
                ?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,0,?16,?17
             )",
            params![
                id,
                input.name.trim(),
                input.description,
                input.status,
                input.current_step_priority,
                input.current_version,
                input.current_phase,
                input.current_step,
                input.current_step_status,
                input.current_step_priority,
                input.last_completed_step,
                next_steps,
                blockers,
                input.local_path,
                input.repo_url,
                timestamp,
                timestamp
            ],
        )
        .map_err(|e| e.to_string())?;

    get(&connection, &id)?.ok_or_else(|| "Project not found after creation".into())
}

#[tauri::command]
pub fn projects_update(
    id: String,
    input: ProjectInput,
    store: State<'_, ProjectStore>,
) -> Result<Project, String> {
    validate_input(&input)?;

    let next_steps = serde_json::to_string(&input.next_steps).map_err(|e| e.to_string())?;
    let blockers = serde_json::to_string(&input.blockers).map_err(|e| e.to_string())?;
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "UPDATE projects SET
                name=?2,
                description=?3,
                status=?4,
                priority=?5,
                current_version=?6,
                current_phase=?7,
                current_step=?8,
                current_step_status=?9,
                current_step_priority=?10,
                last_completed_step=?11,
                next_steps_json=?12,
                blockers_json=?13,
                local_path=?14,
                repo_url=?15,
                updated_at=?16
             WHERE id=?1",
            params![
                id,
                input.name.trim(),
                input.description,
                input.status,
                input.current_step_priority,
                input.current_version,
                input.current_phase,
                input.current_step,
                input.current_step_status,
                input.current_step_priority,
                input.last_completed_step,
                next_steps,
                blockers,
                input.local_path,
                input.repo_url,
                now()
            ],
        )
        .map_err(|e| e.to_string())?;

    get(&connection, &id)?.ok_or_else(|| "Project not found".into())
}

#[tauri::command]
pub fn projects_archive(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<(), String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "UPDATE projects SET archived=1,updated_at=?2 WHERE id=?1",
            params![id, now()],
        )
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub fn projects_restore(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<(), String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute(
            "UPDATE projects
             SET archived=0,
                 status=CASE WHEN status='archived' THEN 'active' ELSE status END,
                 updated_at=?2
             WHERE id=?1",
            params![id, now()],
        )
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub fn projects_delete(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<(), String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    connection
        .execute("DELETE FROM projects WHERE id=?1", [id])
        .map_err(|e| e.to_string())?;

    Ok(())
}
