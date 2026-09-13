import { invoke } from "@tauri-apps/api/core";
import {
  CheckCircle2,
  FolderOpen,
  Github,
  GitBranch,
  Lock,
  Search,
  Unlock
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
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
import {
  useGitHubAccount
} from "../../github/githubAccountStore";

interface GitHubRepositoryPreview {
  name: string;
  fullName: string;
  owner: string;
  htmlUrl: string;
  description: string | null;
  isPrivate: boolean;
  defaultBranch: string;
}


interface GitHubAccount {
  login: string;
  avatarUrl: string;
  htmlUrl: string;
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

function looksLikeGitHubRepositoryUrl(
  value: string
): boolean {
  return /^https?:\/\/(?:www\.)?github\.com\/[^/\s]+\/[^/\s]+\/?(?:\.git)?$/i.test(
    value.trim()
  );
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
      ""
    ),

    currentStep: configString(
      config,
      "currentStep",
      ""
    ),

    currentStepStatus:
      configStepStatus(config),

    currentStepPriority:
      configStepPriority(config),

    lastCompletedStep: configString(
      config,
      "lastCompletedStep",
      ""
    ),

    nextSteps: configStrings(
      config,
      "nextSteps",
      []
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

  const accountState =
    useGitHubAccount() as
      | GitHubAccount
      | null
      | undefined;

  const account =
    accountState ?? null;

  const [repositories, setRepositories] =
    useState<GitHubRepositoryPreview[]>([]);

  const [repositorySearch, setRepositorySearch] =
    useState("");

  const [
    loadingRepositories,
    setLoadingRepositories
  ] = useState(false);

  const [
    repositoriesLoaded,
    setRepositoriesLoaded
  ] = useState(false);

  const [
    manualUrlOpen,
    setManualUrlOpen
  ] = useState(false);

  const urlRequestId =
    useRef(0);

  const [error, setError] =
    useState<string | null>(null);

  const filteredRepositories =
    useMemo(() => {
      const query =
        repositorySearch
          .trim()
          .toLowerCase();

      if (!query) {
        return repositories;
      }

      return repositories.filter(
        (item) =>
          item.fullName
            .toLowerCase()
            .includes(query) ||
          (item.description ?? "")
            .toLowerCase()
            .includes(query)
      );
    }, [
      repositories,
      repositorySearch
    ]);

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

  async function loadRepositoryUrl(
    value: string,
    requestId?: number
  ) {
    try {
      setError(null);
      setLoadingRepository(true);

      const result =
        await invoke<GitHubRepositoryPreview>(
          "github_repository_preview",
          {
            url: value.trim()
          }
        );

      if (
        requestId !== undefined &&
        requestId !== urlRequestId.current
      ) {
        return;
      }

      setRepository(result);
      setRepoUrl(result.htmlUrl);
    } catch (loadError) {
      if (
        requestId !== undefined &&
        requestId !== urlRequestId.current
      ) {
        return;
      }

      setRepository(null);
      setError(String(loadError));
    } finally {
      if (
        requestId === undefined ||
        requestId === urlRequestId.current
      ) {
        setLoadingRepository(false);
      }
    }
  }

  async function handleBrowseRepositories() {
    try {
      setError(null);
      setLoadingRepositories(true);

      const result =
        await invoke<GitHubRepositoryPreview[]>(
          "github_repositories"
        );

      setRepositories(result);
      setRepositorySearch("");
      setRepositoriesLoaded(true);
    } catch (browseError) {
      setError(String(browseError));
    } finally {
      setLoadingRepositories(false);
    }
  }

  function selectRepository(
    selected: GitHubRepositoryPreview
  ) {
    setRepository(selected);
    setRepoUrl(selected.htmlUrl);
    setManualUrlOpen(false);
    setError(null);
  }

  useEffect(() => {
    if (
      !account ||
      repositoriesLoaded ||
      loadingRepositories
    ) {
      return;
    }

    void handleBrowseRepositories();
  }, [
    account,
    repositoriesLoaded,
    loadingRepositories
  ]);

  useEffect(() => {
    if (!manualUrlOpen) {
      return;
    }

    const value = repoUrl.trim();

    if (!looksLikeGitHubRepositoryUrl(value)) {
      return;
    }

    const requestId =
      ++urlRequestId.current;

    const timer =
      window.setTimeout(() => {
        void loadRepositoryUrl(
          value,
          requestId
        );
      }, 450);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    repoUrl,
    manualUrlOpen
  ]);

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
        "Choose a GitHub repository before importing it."
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
          {account ? (
            <>
              <div className="mc-github-connected-row">
                <div>
                  <img
                    className="mc-github-connected-avatar"
                    src={account.avatarUrl}
                    alt=""
                  />

                  <span>
                    Connected as
                    <strong>
                      @{account.login}
                    </strong>
                  </span>
                </div>

                <span className="mc-github-repository-count">
                  {loadingRepositories
                    ? "Loading repositories..."
                    : repositoriesLoaded
                      ? `${repositories.length} repositories`
                      : ""}
                </span>
              </div>

              <div className="mc-github-repository-browser mc-github-primary-browser">
                <div className="mc-github-browser-heading">
                  <div>
                    <strong>
                      Choose repository
                    </strong>

                    <span>
                      Select an authorized GitHub repository.
                    </span>
                  </div>

                  <button
                    className="mc-button"
                    type="button"
                    disabled={loadingRepositories}
                    onClick={() =>
                      void handleBrowseRepositories()
                    }
                  >
                    {loadingRepositories
                      ? "Refreshing..."
                      : "Refresh"}
                  </button>
                </div>

                <label className="mc-github-repository-search">
                  <Search size={14} />

                  <input
                    autoFocus
                    value={repositorySearch}
                    placeholder="Search repositories..."
                    onChange={(event) =>
                      setRepositorySearch(
                        event.target.value
                      )
                    }
                  />
                </label>

                <div className="mc-github-repository-list">
                  {loadingRepositories &&
                  !repositoriesLoaded ? (
                    <p className="mc-muted mc-github-list-message">
                      Loading repositories…
                    </p>
                  ) : filteredRepositories.length ? (
                    filteredRepositories.map(
                      (item) => (
                        <button
                          key={item.fullName}
                          className={
                            repository?.fullName ===
                            item.fullName
                              ? "is-selected"
                              : ""
                          }
                          type="button"
                          onClick={() =>
                            selectRepository(item)
                          }
                        >
                          <span>
                            <strong>
                              {item.fullName}
                            </strong>

                            <small>
                              {item.description ||
                                "No repository description."}
                            </small>
                          </span>

                          <span className="mc-github-repository-visibility">
                            {item.isPrivate ? (
                              <Lock size={12} />
                            ) : (
                              <Unlock size={12} />
                            )}

                            {item.isPrivate
                              ? "Private"
                              : "Public"}
                          </span>
                        </button>
                      )
                    )
                  ) : (
                    <p className="mc-muted mc-github-list-message">
                      {repositorySearch
                        ? "No repositories match this search."
                        : "No authorized repositories were found."}
                    </p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <p className="mc-form-hint">
              Connect GitHub in Settings → Integrations
              to browse authorized repositories.
            </p>
          )}

          <div className="mc-github-manual-import">
            <button
              className="mc-github-secondary-toggle"
              type="button"
              onClick={() =>
                setManualUrlOpen(
                  (open) => !open
                )
              }
            >
              <Github size={14} />

              <span>
                Import by URL
              </span>

              <small>
                Secondary option
              </small>
            </button>

            {manualUrlOpen ? (
              <label className="mc-field">
                <span>
                  GitHub repository URL
                </span>

                <input
                  value={repoUrl}
                  placeholder="https://github.com/owner/repository"
                  onChange={(event) => {
                    urlRequestId.current += 1;
                    setRepoUrl(
                      event.target.value
                    );
                    setRepository(null);
                    setError(null);
                  }}
                />

                <small className="mc-field-help">
                  Paste a valid GitHub repository URL.
                  Mission Control loads it automatically.
                  {loadingRepository
                    ? " Loading…"
                    : ""}
                </small>
              </label>
            ) : null}
          </div>

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
