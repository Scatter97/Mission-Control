use rusqlite::{params, Connection, OptionalExtension, Row};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{
    fs,
    path::Path,
    sync::Mutex,
    time::{SystemTime, UNIX_EPOCH},
};
use tauri::State;
use uuid::Uuid;

const SCHEMA_VERSION: i64 = 3;
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

            CREATE TABLE IF NOT EXISTS project_step_history (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                transition_key TEXT NOT NULL,
                step TEXT NOT NULL,
                status_before TEXT,
                priority TEXT,
                tags_json TEXT NOT NULL DEFAULT '[]',
                phase TEXT,
                version TEXT,
                completed_at INTEGER NOT NULL,
                UNIQUE(project_id, transition_key),
                FOREIGN KEY(project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_project_step_history_project
                ON project_step_history(project_id, completed_at DESC);
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


fn transition_string(
    object: &serde_json::Map<String, Value>,
    key: &str,
    context: &str,
) -> Result<String, String> {
    object
        .get(key)
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .map(str::to_string)
        .ok_or_else(|| format!("{context}.{key} must be a non-empty string"))
}

fn transition_string_array(
    value: Option<&Value>,
    context: &str,
) -> Result<Vec<String>, String> {
    let Some(value) = value else {
        return Ok(Vec::new());
    };

    let array = value
        .as_array()
        .ok_or_else(|| format!("{context} must be an array"))?;

    array
        .iter()
        .enumerate()
        .map(|(index, value)| {
            value
                .as_str()
                .filter(|value| !value.trim().is_empty())
                .map(str::to_string)
                .ok_or_else(|| {
                    format!("{context}[{index}] must be a non-empty string")
                })
        })
        .collect()
}

#[tauri::command]
pub fn projects_consume_step_transition(
    id: String,
    store: State<'_, ProjectStore>,
) -> Result<bool, String> {
    let connection = store
        .connection
        .lock()
        .map_err(|_| "Database lock failed".to_string())?;

    let project = match get(&connection, &id)? {
        Some(project) => project,
        None => return Ok(false),
    };

    let local_path = match project.local_path.as_deref() {
        Some(path) if !path.trim().is_empty() => path,
        _ => return Ok(false),
    };

    let config_path =
        Path::new(local_path).join(".mission-control.json");

    if !config_path.exists() {
        return Ok(false);
    }

    let config_text =
        fs::read_to_string(&config_path)
            .map_err(|error| {
                format!(
                    "Could not read {}: {error}",
                    config_path.display()
                )
            })?;

    let mut config: Value =
        serde_json::from_str(&config_text)
            .map_err(|error| {
                format!(
                    "Invalid {}: {error}",
                    config_path.display()
                )
            })?;

    let root = config
        .as_object_mut()
        .ok_or_else(|| {
            ".mission-control.json must contain a JSON object."
                .to_string()
        })?;

    let transition = match root.get("stepTransition") {
        Some(value) => value.clone(),
        None => return Ok(false),
    };

    let transition_object = transition
        .as_object()
        .ok_or_else(|| {
            "stepTransition must be an object".to_string()
        })?;

    if transition_object
        .get("action")
        .and_then(Value::as_str)
        != Some("complete_current_step")
    {
        return Err(
            "Unsupported stepTransition action.".to_string()
        );
    }

    let completed = transition_object
        .get("completedStep")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            "stepTransition.completedStep must be an object"
                .to_string()
        })?;

    let next = transition_object
        .get("nextStep")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            "stepTransition.nextStep must be an object"
                .to_string()
        })?;

    let completed_step =
        transition_string(
            completed,
            "step",
            "stepTransition.completedStep",
        )?;

    let next_step =
        transition_string(
            next,
            "step",
            "stepTransition.nextStep",
        )?;

    let next_status =
        transition_string(
            next,
            "status",
            "stepTransition.nextStep",
        )?;

    if !STEP_STATUSES.contains(&next_status.as_str()) {
        return Err(
            "stepTransition.nextStep.status is invalid"
                .to_string()
        );
    }

    let next_priority =
        transition_string(
            next,
            "priority",
            "stepTransition.nextStep",
        )?;

    if !STEP_PRIORITIES.contains(&next_priority.as_str()) {
        return Err(
            "stepTransition.nextStep.priority is invalid"
                .to_string()
        );
    }

    let next_tags =
        transition_string_array(
            next.get("tags"),
            "stepTransition.nextStep.tags",
        )?;

    let completed_tags =
        transition_string_array(
            completed.get("tags"),
            "stepTransition.completedStep.tags",
        )?;

    let blocker_transition = transition_object
        .get("blockers")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            "stepTransition.blockers must be an object"
                .to_string()
        })?;

    let clear_all = blocker_transition
        .get("clearAll")
        .and_then(Value::as_bool)
        .unwrap_or(false);

    let remove_blockers =
        transition_string_array(
            blocker_transition.get("remove"),
            "stepTransition.blockers.remove",
        )?;

    let add_blockers =
        transition_string_array(
            blocker_transition.get("add"),
            "stepTransition.blockers.add",
        )?;

    let mut blockers = root
        .get("blockers")
        .and_then(Value::as_array)
        .map(|values| {
            values
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_else(|| project.blockers.clone());

    if clear_all {
        blockers.clear();
    } else {
        for blocker in &remove_blockers {
            blockers.retain(|existing| existing != blocker);
        }
    }

    for blocker in add_blockers {
        if !blockers.contains(&blocker) {
            blockers.push(blocker);
        }
    }

    let mut next_steps = root
        .get("nextSteps")
        .and_then(Value::as_array)
        .map(|values| {
            values
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_else(|| project.next_steps.clone());

    if let Some(index) =
        next_steps.iter().position(|step| step == &next_step)
    {
        next_steps.remove(index);
    }

    let transition_key =
        serde_json::to_string(&transition)
            .map_err(|error| error.to_string())?;

    let completed_status = completed
        .get("status")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();

    let completed_priority = completed
        .get("priority")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();

    let completed_phase = completed
        .get("phase")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();

    let completed_version = completed
        .get("version")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();

    let completed_tags_json =
        serde_json::to_string(&completed_tags)
            .map_err(|error| error.to_string())?;

    connection
        .execute(
            "INSERT OR IGNORE INTO project_step_history (
                id,
                project_id,
                transition_key,
                step,
                status_before,
                priority,
                tags_json,
                phase,
                version,
                completed_at
             ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
            params![
                Uuid::new_v4().to_string(),
                id,
                transition_key,
                completed_step,
                completed_status,
                completed_priority,
                completed_tags_json,
                completed_phase,
                completed_version,
                now()
            ],
        )
        .map_err(|error| error.to_string())?;

    let next_steps_json =
        serde_json::to_string(&next_steps)
            .map_err(|error| error.to_string())?;

    let blockers_json =
        serde_json::to_string(&blockers)
            .map_err(|error| error.to_string())?;

    connection
        .execute(
            "UPDATE projects SET
                current_step=?2,
                current_step_status=?3,
                current_step_priority=?4,
                last_completed_step=?5,
                next_steps_json=?6,
                blockers_json=?7,
                updated_at=?8
             WHERE id=?1",
            params![
                id,
                next_step,
                next_status,
                next_priority,
                completed_step,
                next_steps_json,
                blockers_json,
                now()
            ],
        )
        .map_err(|error| error.to_string())?;

    root.insert(
        "lastCompletedStep".to_string(),
        Value::String(completed_step),
    );

    root.insert(
        "currentStep".to_string(),
        Value::String(next_step),
    );

    root.insert(
        "currentStepStatus".to_string(),
        Value::String(next_status),
    );

    root.insert(
        "currentStepPriority".to_string(),
        Value::String(next_priority),
    );

    root.insert(
        "currentStepTags".to_string(),
        Value::Array(
            next_tags
                .into_iter()
                .map(Value::String)
                .collect()
        ),
    );

    root.insert(
        "nextSteps".to_string(),
        Value::Array(
            next_steps
                .into_iter()
                .map(Value::String)
                .collect()
        ),
    );

    root.insert(
        "blockers".to_string(),
        Value::Array(
            blockers
                .into_iter()
                .map(Value::String)
                .collect()
        ),
    );

    root.remove("stepTransition");

    let output =
        serde_json::to_string_pretty(&config)
            .map_err(|error| error.to_string())?
        + "\n";

    fs::write(&config_path, output)
        .map_err(|error| {
            format!(
                "Could not write {}: {error}",
                config_path.display()
            )
        })?;

    Ok(true)
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
