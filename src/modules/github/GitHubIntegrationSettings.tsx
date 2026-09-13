import { invoke } from "@tauri-apps/api/core";
import {
  CheckCircle2,
  ExternalLink,
  Github,
  LogOut,
  ShieldCheck
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState
} from "react";

import {
  preloadGitHubAccount,
  setCachedGitHubAccount,
  useGitHubAccount
} from "./githubAccountStore";

interface GitHubAccount {
  login: string;
  avatarUrl: string;
  htmlUrl: string;
}

interface GitHubDeviceFlow {
  deviceCode: string;
  userCode: string;
  verificationUri: string;
  expiresIn: number;
  interval: number;
}

interface GitHubDevicePollResult {
  status: string;
  account: GitHubAccount | null;
  message: string | null;
}

export function GitHubIntegrationSettings() {
  const accountState =
    useGitHubAccount() as
      | GitHubAccount
      | null
      | undefined;

  const account =
    accountState ?? null;

  const [flow, setFlow] =
    useState<GitHubDeviceFlow | null>(null);

  const [busy, setBusy] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [copied, setCopied] =
    useState(false);

  const [toastVisible, setToastVisible] =
    useState(false);

  const copyAnimationTimer =
    useRef<number | null>(null);

  const toastTimer =
    useRef<number | null>(null);

  useEffect(() => {
    void preloadGitHubAccount()
      .catch((statusError) => {
        setError(String(statusError));
      });
  }, []);

  useEffect(() => {
    return () => {
      if (copyAnimationTimer.current !== null) {
        window.clearTimeout(
          copyAnimationTimer.current
        );
      }

      if (toastTimer.current !== null) {
        window.clearTimeout(
          toastTimer.current
        );
      }
    };
  }, []);

  useEffect(() => {
    if (!flow) {
      return;
    }

    let cancelled = false;
    let timer: number | null = null;

    const poll = async () => {
      if (cancelled) {
        return;
      }

      try {
        const result =
          await invoke<GitHubDevicePollResult>(
            "github_device_flow_poll",
            {
              deviceCode: flow.deviceCode
            }
          );

        if (cancelled) {
          return;
        }

        if (
          result.status === "pending" ||
          result.status === "slow_down"
        ) {
          const extra =
            result.status === "slow_down"
              ? 5
              : 0;

          timer = window.setTimeout(
            () => void poll(),
            (flow.interval + extra) * 1000
          );

          return;
        }

        if (
          result.status === "connected" &&
          result.account
        ) {
          setCachedGitHubAccount(
            result.account
          );
          setFlow(null);
          setBusy(false);
          setError(null);
          return;
        }

        setBusy(false);
        setFlow(null);
        setError(
          result.message ||
            "GitHub authorization did not complete."
        );
      } catch (pollError) {
        if (!cancelled) {
          setBusy(false);
          setFlow(null);
          setError(String(pollError));
        }
      }
    };

    timer = window.setTimeout(
      () => void poll(),
      flow.interval * 1000
    );

    return () => {
      cancelled = true;

      if (timer !== null) {
        window.clearTimeout(timer);
      }
    };
  }, [flow]);

  async function connect() {
    try {
      setBusy(true);
      setError(null);

      const result =
        await invoke<GitHubDeviceFlow>(
          "github_device_flow_start"
        );

      setFlow(result);

      await invoke(
        "open_github_url",
        {
          url: result.verificationUri
        }
      );
    } catch (connectError) {
      setBusy(false);
      setError(String(connectError));
    }
  }

  async function disconnect() {
    try {
      setBusy(true);
      setError(null);

      await invoke("github_disconnect");

      setCachedGitHubAccount(null);
      setFlow(null);
    } catch (disconnectError) {
      setError(String(disconnectError));
    } finally {
      setBusy(false);
    }
  }

  async function manageAccess() {
    try {
      setError(null);

      await invoke(
        "open_github_url",
        {
          url: "https://github.com/settings/installations"
        }
      );
    } catch (openError) {
      setError(String(openError));
    }
  }

  async function copyCode() {
    if (!flow) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        flow.userCode
      );

      setCopied(false);

      window.requestAnimationFrame(() => {
        setCopied(true);
      });

      if (
        copyAnimationTimer.current !== null
      ) {
        window.clearTimeout(
          copyAnimationTimer.current
        );
      }

      copyAnimationTimer.current =
        window.setTimeout(() => {
          setCopied(false);
        }, 260);

      setToastVisible(true);

      if (toastTimer.current !== null) {
        window.clearTimeout(
          toastTimer.current
        );
      }

      toastTimer.current =
        window.setTimeout(() => {
          setToastVisible(false);
        }, 2200);
    } catch {
      setError(
        "Could not copy the device code."
      );
    }
  }

  return (
    <>
      <div className="mc-settings-heading">
        <h2>Integrations</h2>
        <p>
          Connect external development services to
          Mission Control.
        </p>
      </div>

      <section className="mc-panel mc-github-integration">
        <div className="mc-github-integration-header">
          <div className="mc-github-integration-icon">
            <Github size={20} />
          </div>

          <div>
            <h3>GitHub</h3>
            <p>
              Import public and authorized private
              repositories using your GitHub account.
            </p>
          </div>

          {account ? (
            <span className="mc-integration-status is-connected">
              <CheckCircle2 size={13} />
              Connected
            </span>
          ) : (
            <span className="mc-integration-status">
              Not connected
            </span>
          )}
        </div>

        {account ? (
          <div className="mc-github-account">
            <img
              src={account.avatarUrl}
              alt=""
            />

            <div>
              <strong>@{account.login}</strong>
              <span>
                GitHub authorization is stored
                securely on this Windows account.
              </span>
            </div>

            <div className="mc-github-account-actions">
              <button
                className="mc-button"
                type="button"
                onClick={() =>
                  void manageAccess()
                }
              >
                <ExternalLink size={14} />
                Manage access
              </button>

              <button
                className="mc-button"
                type="button"
                disabled={busy}
                onClick={() =>
                  void disconnect()
                }
              >
                <LogOut size={14} />
                Disconnect
              </button>
            </div>
          </div>
        ) : flow ? (
          <div className="mc-github-device-flow">
            <div>
              <span className="mc-github-device-label">
                Device code
              </span>

              <button
                className={
                  "mc-github-device-code" +
                  (copied
                    ? " is-copied"
                    : "")
                }
                type="button"
                title="Copy code"
                onClick={() =>
                  void copyCode()
                }
              >
                {flow.userCode}
              </button>
            </div>

            <div className="mc-github-device-copy">
              <strong>
                Finish authorization in GitHub
              </strong>

              <span>
                The GitHub authorization page has
                been opened. Enter the code above.
                Mission Control will detect the
                connection automatically.
              </span>
            </div>

            <button
              className="mc-button"
              type="button"
              onClick={() =>
                void invoke(
                  "open_github_url",
                  {
                    url: flow.verificationUri
                  }
                )
              }
            >
              <ExternalLink size={14} />
              Open GitHub
            </button>
          </div>
        ) : (
          <div className="mc-github-connect-row">
            <div>
              <strong>
                Connect your GitHub account
              </strong>

              <span>
                Mission Control uses GitHub Device
                Flow. No client secret or GitHub App
                private key is stored in the app.
              </span>
            </div>

            <button
              className="mc-button mc-button-primary"
              type="button"
              disabled={busy}
              onClick={() =>
                void connect()
              }
            >
              <Github size={14} />

              {busy
                ? "Connecting..."
                : "Connect GitHub"}
            </button>
          </div>
        )}

        <div className="mc-github-security-note">
          <ShieldCheck size={14} />

          <span>
            Tokens are encrypted at rest using
            Windows DPAPI for the current Windows
            user and are never exposed to the
            Mission Control frontend.
          </span>
        </div>

        {error ? (
          <p className="mc-form-error">
            {error}
          </p>
        ) : null}
      </section>

      {toastVisible ? (
        <div
          className="mc-toast mc-toast-success"
          role="status"
          aria-live="polite"
        >
          <CheckCircle2 size={14} />
          Authorization code copied
        </div>
      ) : null}
    </>
  );
}
