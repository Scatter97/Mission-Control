import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useBackend } from "../../backend/BackendProvider";
import type { ProjectInput } from "./types";

const projectKeys = {
  root: ["projects"] as const,
  list: (archived: boolean) => ["projects", "list", archived] as const,
  detail: (id: string) => ["projects", "detail", id] as const,
  history: (id: string) => ["projects", "history", id] as const
};

export function useProjects(archived = false) {
  const backend = useBackend();

  return useQuery({
    queryKey: projectKeys.list(archived),
    queryFn: () => backend.listProjects(archived)
  });
}

export function useProject(id: string | undefined) {
  const backend = useBackend();

  return useQuery({
    queryKey: projectKeys.detail(id ?? ""),
    queryFn: () => backend.getProject(id!),
    enabled: Boolean(id)
  });
}

export function useProjectStepHistory(
  id: string | undefined,
  enabled = true
) {
  const backend = useBackend();

  return useQuery({
    queryKey: projectKeys.history(id ?? ""),
    queryFn: () =>
      backend.getProjectStepHistory(id!),
    enabled: Boolean(id) && enabled
  });
}

export function useCreateProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ProjectInput) => backend.createProject(input),
    onSuccess: (project) => {
      queryClient.setQueryData(projectKeys.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
    }
  });
}

export function useUpdateProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ProjectInput }) =>
      backend.updateProject(id, input),
    onSuccess: (project) => {
      queryClient.setQueryData(projectKeys.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
    }
  });
}

export function useUpdateProjectNextSteps() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      nextSteps
    }: {
      id: string;
      nextSteps: string[];
    }) =>
      backend.updateProjectNextSteps(
        id,
        nextSteps
      ),
    onSuccess: (project) => {
      queryClient.setQueryData(
        projectKeys.detail(project.id),
        project
      );

      void queryClient.invalidateQueries({
        queryKey: projectKeys.root
      });
    }
  });
}

export function useArchiveProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.archiveProject(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
      void queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) });
    }
  });
}

export function useRestoreProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.restoreProject(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
      void queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) });
    }
  });
}

export function useDeleteProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.deleteProject(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: projectKeys.detail(id) });
      void queryClient.invalidateQueries({ queryKey: projectKeys.root });
    }
  });
}
