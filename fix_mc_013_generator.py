from pathlib import Path

path = Path(
    r"C:\Users\joshh\Desktop\Mission-Control\make_mc_013_github_import.py"
)

text = path.read_text(encoding="utf-8")

old = """$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$headers = @{{"""

new = """$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$headers = @{{"""

if text.count(old) != 1:
    raise RuntimeError(
        "Could not find GitHub PowerShell encoding insertion point."
    )

text = text.replace(old, new, 1)

old = """function configStepPriority(
  config: ProjectConfig | null
): StepPriority {
  const value = config?.currentStepPriority;

  return typeof value === "string" &&
    STEP_PRIORITIES.includes(value as StepPriority)
    ? (value as StepPriority)
    : "medium";
}

function buildInput("""

new = """function configStepPriority(
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
  return value
    .trim()
    .replace(/\.git$/i, "")
    .replace(/\/$/, "")
    .toLowerCase();
}

function buildInput("""

if text.count(old) != 1:
    raise RuntimeError(
        "Could not find config helper insertion point."
    )

text = text.replace(old, new, 1)

old = """      let input = buildInput(
        repository,
        normalizedLocalPath,
        config
      );

      if (normalizedLocalPath && !config) {"""

new = """      if (config) {
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

      if (normalizedLocalPath && !config) {"""

if text.count(old) != 1:
    raise RuntimeError(
        "Could not find config validation insertion point."
    )

text = text.replace(old, new, 1)

path.write_text(
    text,
    encoding="utf-8"
)

print("Updated 0.1.3 generator.")
print("  + UTF-8 GitHub API output")
print("  + Repository mismatch protection")