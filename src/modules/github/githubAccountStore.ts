import { invoke } from "@tauri-apps/api/core";
import { useSyncExternalStore } from "react";

export interface GitHubAccount {
  login: string;
  avatarUrl: string;
  htmlUrl: string;
}

const STORAGE_KEY =
  "mission-control.github.account";

type AccountSnapshot =
  GitHubAccount | null | undefined;

const listeners =
  new Set<() => void>();

let account: AccountSnapshot =
  readStoredAccount();

let request:
  Promise<GitHubAccount | null> | null =
  null;

function validAccount(
  value: unknown
): value is GitHubAccount {
  if (
    !value ||
    typeof value !== "object"
  ) {
    return false;
  }

  const candidate =
    value as Record<string, unknown>;

  return (
    typeof candidate.login === "string" &&
    typeof candidate.avatarUrl === "string" &&
    typeof candidate.htmlUrl === "string"
  );
}

function readStoredAccount(): AccountSnapshot {
  try {
    const raw =
      window.localStorage.getItem(
        STORAGE_KEY
      );

    if (raw === null) {
      return undefined;
    }

    if (raw === "null") {
      return null;
    }

    const parsed: unknown =
      JSON.parse(raw);

    if (validAccount(parsed)) {
      return parsed;
    }

    window.localStorage.removeItem(
      STORAGE_KEY
    );

    return undefined;
  } catch {
    return undefined;
  }
}

function persistAccount(
  value: GitHubAccount | null
) {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      value === null
        ? "null"
        : JSON.stringify(value)
    );
  } catch {
    // The in-memory cache still works if
    // localStorage is unavailable.
  }
}

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setCachedGitHubAccount(
  value: GitHubAccount | null
) {
  account = value;
  persistAccount(value);
  emit();
}

export function getGitHubAccountSnapshot() {
  return account;
}

export async function preloadGitHubAccount(
  force = false
): Promise<GitHubAccount | null> {
  if (
    !force &&
    account !== undefined
  ) {
    return account;
  }

  if (request) {
    return request;
  }

  request =
    invoke<GitHubAccount | null>(
      "github_connection_status"
    )
      .then((result) => {
        setCachedGitHubAccount(result);
        return result;
      })
      .catch((error) => {
        setCachedGitHubAccount(null);
        throw error;
      })
      .finally(() => {
        request = null;
      });

  return request;
}

export function useGitHubAccount() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);

      return () => {
        listeners.delete(listener);
      };
    },
    getGitHubAccountSnapshot,
    getGitHubAccountSnapshot
  );
}
