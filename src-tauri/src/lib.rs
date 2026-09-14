mod projects;

use serde::{Deserialize, Serialize};
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::Command,
    time::{SystemTime, UNIX_EPOCH},
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

const GITHUB_CLIENT_ID: &str =
    "Iv23lijc2AADzv9cAkPB";

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct GitHubAccount {
    login: String,
    avatar_url: String,
    html_url: String,
}

#[derive(Debug, Deserialize)]
struct GitHubApiUser {
    login: String,
    avatar_url: String,
    html_url: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct GitHubDeviceFlow {
    device_code: String,
    user_code: String,
    verification_uri: String,
    expires_in: u64,
    interval: u64,
}

#[derive(Debug, Deserialize)]
struct GitHubDeviceCodeResponse {
    device_code: String,
    user_code: String,
    verification_uri: String,
    expires_in: u64,
    interval: Option<u64>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct GitHubDevicePollResult {
    status: String,
    account: Option<GitHubAccount>,
    message: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GitHubCredential {
    access_token: String,
    refresh_token: Option<String>,
    expires_at: Option<u64>,
    #[serde(default)]
    account: Option<GitHubAccount>,
}

#[derive(Debug, Deserialize)]
struct GitHubTokenResponse {
    access_token: Option<String>,
    expires_in: Option<u64>,
    refresh_token: Option<String>,
    error: Option<String>,
    error_description: Option<String>,
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

fn powershell_output(
    script: &str,
) -> Result<String, String> {
    let output = Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ])
        .output()
        .map_err(|error| {
            format!(
                "Could not run PowerShell: {error}"
            )
        })?;

    if !output.status.success() {
        let message =
            String::from_utf8_lossy(
                &output.stderr
            )
            .trim()
            .to_string();

        return Err(
            if message.is_empty() {
                "PowerShell command failed."
                    .to_string()
            } else {
                message
            }
        );
    }

    Ok(
        String::from_utf8_lossy(
            &output.stdout
        )
        .trim()
        .to_string()
    )
}

fn powershell_json(
    script: &str,
) -> Result<serde_json::Value, String> {
    let output =
        powershell_output(script)?;

    serde_json::from_str(&output)
        .map_err(|error| {
            format!(
                "Unexpected JSON response: {error}"
            )
        })
}

fn ps_quote(value: &str) -> String {
    format!(
        "'{}'",
        value.replace('\'', "''")
    )
}

fn now_epoch() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[cfg(target_os = "windows")]
fn save_github_credential(
    credential: &GitHubCredential,
) -> Result<(), String> {
    let json =
        serde_json::to_string(credential)
            .map_err(|error| {
                error.to_string()
            })?;

    let payload = ps_quote(&json);

    let script = format!(
        r#"
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security

$root = Join-Path $env:LOCALAPPDATA 'MissionControl'
$path = Join-Path $root 'github-auth.bin'

New-Item `
    -ItemType Directory `
    -Path $root `
    -Force | Out-Null

$plain = [System.Text.Encoding]::UTF8.GetBytes({payload})

$protected = [System.Security.Cryptography.ProtectedData]::Protect(
    $plain,
    $null,
    [System.Security.Cryptography.DataProtectionScope]::CurrentUser
)

[System.IO.File]::WriteAllBytes(
    $path,
    $protected
)
"#
    );

    powershell_output(&script)?;
    Ok(())
}

#[cfg(not(target_os = "windows"))]
fn save_github_credential(
    _credential: &GitHubCredential,
) -> Result<(), String> {
    Err(
        "GitHub credential storage is currently supported on Windows."
            .to_string()
    )
}

#[cfg(target_os = "windows")]
fn load_github_credential(
) -> Result<Option<GitHubCredential>, String> {
    let script = r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

Add-Type -AssemblyName System.Security

$root = Join-Path $env:LOCALAPPDATA 'MissionControl'
$path = Join-Path $root 'github-auth.bin'

if (-not (Test-Path -LiteralPath $path)) {
    Write-Output 'null'
    exit 0
}

$protected = [System.IO.File]::ReadAllBytes($path)

$plain = [System.Security.Cryptography.ProtectedData]::Unprotect(
    $protected,
    $null,
    [System.Security.Cryptography.DataProtectionScope]::CurrentUser
)

[System.Text.Encoding]::UTF8.GetString($plain)
"#;

    let output =
        powershell_output(script)?;

    if output == "null" ||
        output.trim().is_empty()
    {
        return Ok(None);
    }

    let credential =
        serde_json::from_str(
            &output
        )
        .map_err(|error| {
            format!(
                "Stored GitHub authorization is invalid: {error}"
            )
        })?;

    Ok(Some(credential))
}

#[cfg(not(target_os = "windows"))]
fn load_github_credential(
) -> Result<Option<GitHubCredential>, String> {
    Ok(None)
}

#[cfg(target_os = "windows")]
fn delete_github_credential(
) -> Result<(), String> {
    let script = r#"
$ErrorActionPreference = 'Stop'

$root = Join-Path $env:LOCALAPPDATA 'MissionControl'
$path = Join-Path $root 'github-auth.bin'

if (Test-Path -LiteralPath $path) {
    Remove-Item -LiteralPath $path -Force
}
"#;

    powershell_output(script)?;
    Ok(())
}

#[cfg(not(target_os = "windows"))]
fn delete_github_credential(
) -> Result<(), String> {
    Ok(())
}

fn github_api_get(
    url: &str,
    token: Option<&str>,
) -> Result<serde_json::Value, String> {
    #[cfg(target_os = "windows")]
    {
        let url =
            ps_quote(url);

        let authorization =
            token.map(|value| {
                format!(
                    "$headers['Authorization'] = {}",
                    ps_quote(
                        &format!(
                            "Bearer {value}"
                        )
                    )
                )
            })
            .unwrap_or_default();

        let script = format!(
            r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{
    'User-Agent' = 'Mission-Control'
    'Accept' = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}}

{authorization}

try {{
    $response = Invoke-RestMethod `
        -Uri {url} `
        -Headers $headers `
        -Method Get

    ConvertTo-Json `
        -InputObject $response `
        -Compress `
        -Depth 10
}}
catch {{
    [Console]::Error.WriteLine(
        $_.Exception.Message
    )
    exit 1
}}
"#
        );

        powershell_json(&script)
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = url;
        let _ = token;

        Err(
            "GitHub integration is currently supported on Windows."
                .to_string()
        )
    }
}

fn refresh_github_credential(
    credential: &GitHubCredential,
) -> Result<GitHubCredential, String> {
    let refresh_token =
        credential
            .refresh_token
            .as_ref()
            .ok_or_else(|| {
                "GitHub authorization expired. Reconnect GitHub in Settings."
                    .to_string()
            })?;

    let client_id =
        ps_quote(GITHUB_CLIENT_ID);

    let refresh_token =
        ps_quote(refresh_token);

    let script = format!(
        r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{
    'Accept' = 'application/json'
    'User-Agent' = 'Mission-Control'
}}

$body = @{{
    client_id = {client_id}
    grant_type = 'refresh_token'
    refresh_token = {refresh_token}
}}

$response = Invoke-RestMethod `
    -Uri 'https://github.com/login/oauth/access_token' `
    -Headers $headers `
    -Method Post `
    -Body $body

ConvertTo-Json `
    -InputObject $response `
    -Compress `
    -Depth 8
"#
    );

    let response: GitHubTokenResponse =
        serde_json::from_value(
            powershell_json(&script)?
        )
        .map_err(|error| {
            format!(
                "GitHub refresh response was invalid: {error}"
            )
        })?;

    if let Some(error) = response.error {
        return Err(
            response.error_description
                .unwrap_or(error)
        );
    }

    let access_token =
        response.access_token
            .ok_or_else(|| {
                "GitHub did not return a refreshed access token."
                    .to_string()
            })?;

    let updated =
        GitHubCredential {
            access_token,
            refresh_token:
                response.refresh_token.or_else(
                    || credential.refresh_token.clone()
                ),
            expires_at:
                response.expires_in.map(
                    |seconds|
                        now_epoch() + seconds
                ),
            account:
                credential.account.clone(),
        };

    save_github_credential(
        &updated
    )?;

    Ok(updated)
}

fn fresh_github_credential(
) -> Result<Option<GitHubCredential>, String> {
    let Some(credential) =
        load_github_credential()?
    else {
        return Ok(None);
    };

    let needs_refresh =
        credential
            .expires_at
            .map(
                |expires_at|
                    expires_at <= now_epoch() + 60
            )
            .unwrap_or(false);

    if needs_refresh {
        return Ok(
            Some(
                refresh_github_credential(
                    &credential
                )?
            )
        );
    }

    Ok(Some(credential))
}

fn github_account_for_token(
    token: &str,
) -> Result<GitHubAccount, String> {
    let response =
        github_api_get(
            "https://api.github.com/user",
            Some(token),
        )?;

    let user: GitHubApiUser =
        serde_json::from_value(response)
            .map_err(|error| {
                format!(
                    "GitHub returned an unexpected user response: {error}"
                )
            })?;

    Ok(GitHubAccount {
        login: user.login,
        avatar_url: user.avatar_url,
        html_url: user.html_url,
    })
}

fn repository_preview(
    response: GitHubApiRepository,
) -> GitHubRepositoryPreview {
    GitHubRepositoryPreview {
        name: response.name,
        full_name: response.full_name,
        owner: response.owner.login,
        html_url: response.html_url,
        description: response.description,
        is_private: response.private,
        default_branch:
            response.default_branch,
    }
}

#[tauri::command]
fn github_connection_status(
) -> Result<Option<GitHubAccount>, String> {
    let Some(mut credential) =
        fresh_github_credential()?
    else {
        return Ok(None);
    };

    if let Some(account) =
        credential.account.clone()
    {
        return Ok(Some(account));
    }

    match github_account_for_token(
        &credential.access_token
    ) {
        Ok(account) => {
            credential.account =
                Some(account.clone());

            save_github_credential(
                &credential
            )?;

            Ok(Some(account))
        }

        Err(error) => {
            delete_github_credential()?;

            Err(format!(
                "Stored GitHub authorization is no longer valid: {error}"
            ))
        }
    }
}

#[tauri::command]
fn github_device_flow_start(
) -> Result<GitHubDeviceFlow, String> {
    let client_id =
        ps_quote(GITHUB_CLIENT_ID);

    let script = format!(
        r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{
    'Accept' = 'application/json'
    'User-Agent' = 'Mission-Control'
}}

$body = @{{
    client_id = {client_id}
}}

$response = Invoke-RestMethod `
    -Uri 'https://github.com/login/device/code' `
    -Headers $headers `
    -Method Post `
    -Body $body

ConvertTo-Json `
    -InputObject $response `
    -Compress `
    -Depth 8
"#
    );

    let response:
        GitHubDeviceCodeResponse =
        serde_json::from_value(
            powershell_json(&script)?
        )
        .map_err(|error| {
            format!(
                "GitHub device-flow response was invalid: {error}"
            )
        })?;

    Ok(GitHubDeviceFlow {
        device_code: response.device_code,
        user_code: response.user_code,
        verification_uri:
            response.verification_uri,
        expires_in: response.expires_in,
        interval:
            response.interval.unwrap_or(5),
    })
}

#[tauri::command]
fn github_device_flow_poll(
    device_code: String,
) -> Result<GitHubDevicePollResult, String> {
    let client_id =
        ps_quote(GITHUB_CLIENT_ID);

    let device_code =
        ps_quote(&device_code);

    let script = format!(
        r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{
    'Accept' = 'application/json'
    'User-Agent' = 'Mission-Control'
}}

$body = @{{
    client_id = {client_id}
    device_code = {device_code}
    grant_type = 'urn:ietf:params:oauth:grant-type:device_code'
}}

$response = Invoke-RestMethod `
    -Uri 'https://github.com/login/oauth/access_token' `
    -Headers $headers `
    -Method Post `
    -Body $body

ConvertTo-Json `
    -InputObject $response `
    -Compress `
    -Depth 8
"#
    );

    let response:
        GitHubTokenResponse =
        serde_json::from_value(
            powershell_json(&script)?
        )
        .map_err(|error| {
            format!(
                "GitHub token response was invalid: {error}"
            )
        })?;

    if let Some(error) =
        response.error
    {
        let message =
            response
                .error_description
                .clone();

        return Ok(
            GitHubDevicePollResult {
                status: match error.as_str() {
                    "authorization_pending" =>
                        "pending",
                    "slow_down" =>
                        "slow_down",
                    "expired_token" =>
                        "expired",
                    "access_denied" =>
                        "denied",
                    _ => "error",
                }
                .to_string(),

                account: None,

                message:
                    if error ==
                        "authorization_pending" ||
                        error == "slow_down"
                    {
                        None
                    } else {
                        message.or(Some(error))
                    },
            }
        );
    }

    let access_token =
        response.access_token
            .ok_or_else(|| {
                "GitHub authorization completed without an access token."
                    .to_string()
            })?;

    let account =
        github_account_for_token(
            &access_token
        )?;

    let credential =
        GitHubCredential {
            access_token,
            refresh_token:
                response.refresh_token,
            expires_at:
                response.expires_in.map(
                    |seconds|
                        now_epoch() + seconds
                ),
            account:
                Some(account.clone()),
        };

    save_github_credential(
        &credential
    )?;

    Ok(GitHubDevicePollResult {
        status: "connected".to_string(),
        account: Some(account),
        message: None,
    })
}

#[tauri::command]
fn github_disconnect(
) -> Result<(), String> {
    delete_github_credential()
}

fn github_api_get_repository_list(
    url: &str,
    token: &str,
) -> Result<serde_json::Value, String> {
    #[cfg(target_os = "windows")]
    {
        let url =
            ps_quote(url);

        let authorization =
            ps_quote(
                &format!(
                    "Bearer {token}"
                )
            );

        let script = format!(
            r#"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{
    'User-Agent' = 'Mission-Control'
    'Accept' = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
    'Authorization' = {authorization}
}}

try {{
    $response = Invoke-RestMethod `
        -Uri {url} `
        -Headers $headers `
        -Method Get

    $repositories = @($response)

    ConvertTo-Json `
        -InputObject $repositories `
        -Compress `
        -Depth 10
}}
catch {{
    [Console]::Error.WriteLine(
        $_.Exception.Message
    )
    exit 1
}}
"#
        );

        powershell_json(&script)
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = url;
        let _ = token;

        Err(
            "GitHub integration is currently supported on Windows."
                .to_string()
        )
    }
}

fn github_json_shape(
    value: &serde_json::Value,
) -> String {
    match value {
        serde_json::Value::Array(items) => {
            format!(
                "array with {} item(s)",
                items.len()
            )
        }

        serde_json::Value::Object(map) => {
            let mut keys:
                Vec<&str> =
                map.keys()
                    .map(String::as_str)
                    .collect();

            keys.sort_unstable();

            format!(
                "object with keys: {}",
                keys.join(", ")
            )
        }

        serde_json::Value::Null =>
            "null".to_string(),

        serde_json::Value::Bool(_) =>
            "boolean".to_string(),

        serde_json::Value::Number(_) =>
            "number".to_string(),

        serde_json::Value::String(_) =>
            "string".to_string(),
    }
}

fn github_repository_from_value(
    value: serde_json::Value,
    context: &str,
) -> Result<GitHubApiRepository, String> {
    let shape =
        github_json_shape(&value);

    serde_json::from_value(value)
        .map_err(|error| {
            format!(
                "{context}: {error}. Response shape: {shape}"
            )
        })
}

fn github_repository_list_from_value(
    value: serde_json::Value,
) -> Result<Vec<GitHubApiRepository>, String> {
    match value {
        serde_json::Value::Array(items) => {
            items
                .into_iter()
                .enumerate()
                .map(|(index, item)| {
                    github_repository_from_value(
                        item,
                        &format!(
                            "GitHub repository item {index} was invalid"
                        ),
                    )
                })
                .collect()
        }

        serde_json::Value::Object(mut map) => {
            for key in [
                "repositories",
                "items",
                "value",
            ] {
                if let Some(collection) =
                    map.remove(key)
                {
                    if collection.is_array() {
                        return github_repository_list_from_value(
                            collection
                        );
                    }
                }
            }

            let value =
                serde_json::Value::Object(map);

            if value
                .get("name")
                .is_some() &&
                value
                    .get("full_name")
                    .is_some()
            {
                return Ok(vec![
                    github_repository_from_value(
                        value,
                        "GitHub repository was invalid",
                    )?
                ]);
            }

            Err(format!(
                "Unexpected GitHub repository response. {}",
                github_json_shape(&value)
            ))
        }

        serde_json::Value::Null =>
            Ok(Vec::new()),

        other => Err(format!(
            "Unexpected GitHub repository response. {}",
            github_json_shape(&other)
        )),
    }
}


#[tauri::command]
fn github_repositories(
) -> Result<Vec<GitHubRepositoryPreview>, String> {
    let credential =
        fresh_github_credential()?
            .ok_or_else(|| {
                "Connect GitHub in Settings before browsing private repositories."
                    .to_string()
            })?;

    let mut repositories = Vec::new();

    for page in 1..=10 {
        let url = format!(
            "https://api.github.com/user/repos?per_page=100&page={page}&sort=updated&direction=desc&visibility=all"
        );

        let value =
            github_api_get_repository_list(
                &url,
                &credential.access_token,
            )?;

        let page_repositories =
            github_repository_list_from_value(
                value
            )?;

        let count =
            page_repositories.len();

        repositories.extend(
            page_repositories
                .into_iter()
                .map(repository_preview)
        );

        if count < 100 {
            break;
        }
    }

    Ok(repositories)
}

#[tauri::command]
fn github_repository_preview(
    url: String,
) -> Result<GitHubRepositoryPreview, String> {
    let (owner, repository) =
        github_repository_parts(&url)?;

    let credential =
        fresh_github_credential()?;

    let endpoint = format!(
        "https://api.github.com/repos/{owner}/{repository}"
    );

    let response =
        github_api_get(
            &endpoint,
            credential
                .as_ref()
                .map(
                    |credential|
                        credential.access_token.as_str()
                ),
        )?;

    let repository:
        GitHubApiRepository =
        serde_json::from_value(
            response
        )
        .map_err(|error| {
            format!(
                "GitHub returned an unexpected repository response: {error}"
            )
        })?;

    Ok(repository_preview(repository))
}

#[tauri::command]
fn open_github_url(
    url: String,
) -> Result<(), String> {
    let allowed =
        url == "https://github.com/login/device" ||
        url == "https://github.com/settings/installations";

    if !allowed {
        return Err(
            "Mission Control refused to open an unsupported GitHub URL."
                .to_string()
        );
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args([
                "/C",
                "start",
                "",
                &url,
            ])
            .spawn()
            .map_err(|error| {
                format!(
                    "Could not open GitHub: {error}"
                )
            })?;

        Ok(())
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err(
            "Opening GitHub is currently supported on Windows."
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
fn open_local_folder(
    path: String,
) -> Result<(), String> {
    let folder =
        Path::new(&path);

    if !folder.exists() {
        return Err(
            "Local project folder does not exist."
                .to_string()
        );
    }

    if !folder.is_dir() {
        return Err(
            "Local project path is not a folder."
                .to_string()
        );
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer.exe")
            .arg(folder)
            .spawn()
            .map_err(|error| {
                format!(
                    "Could not open File Explorer: {error}"
                )
            })?;

        Ok(())
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err(
            "Opening project folders is currently supported on Windows."
                .to_string()
        )
    }
}

#[tauri::command]
fn open_repository_url(
    url: String,
) -> Result<(), String> {
    let (owner, repository) =
        github_repository_parts(
            &url
        )?;

    let safe_url =
        format!(
            "https://github.com/{owner}/{repository}"
        );

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args([
                "/C",
                "start",
                "",
                &safe_url,
            ])
            .spawn()
            .map_err(|error| {
                format!(
                    "Could not open GitHub repository: {error}"
                )
            })?;

        Ok(())
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err(
            "Opening repository links is currently supported on Windows."
                .to_string()
        )
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
            github_connection_status,
            github_device_flow_start,
            github_device_flow_poll,
            github_disconnect,
            github_repositories,
            github_repository_preview,
            open_github_url,
            project_config_read,
            project_config_write_if_missing,
            open_local_folder,
            open_repository_url,
            pick_project_folder,
            projects::projects_list,
            projects::projects_get,
            projects::projects_step_history,
            projects::projects_create,
            projects::projects_update,
            projects::projects_update_next_steps,
            projects::projects_consume_step_transition,
            projects::projects_archive,
            projects::projects_restore,
            projects::projects_delete
        ])
        .run(tauri::generate_context!())
        .expect("error while running Mission Control");
}
