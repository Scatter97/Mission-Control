import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useBackend } from "../../backend/BackendProvider";
import type { ProjectInput } from "./types";

const projectKeys = {
  all: ["projects"] as const,
  detail: (id: string) => ["projects", id] as const
};

export function useProjects() {
  const backend = useBackend();

  return useQuery({
    queryKey: projectKeys.all,
    queryFn: () => backend.listProjects()
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

export function useCreateProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ProjectInput) => backend.createProject(input),
    onSuccess: (project) => {
      queryClient.setQueryData(projectKeys.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: projectKeys.all });
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
      void queryClient.invalidateQueries({ queryKey: projectKeys.all });
    }
  });
}

export function useArchiveProject() {
  const backend = useBackend();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => backend.archiveProject(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: projectKeys.detail(id) });
      void queryClient.invalidateQueries({ queryKey: projectKeys.all });
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
      void queryClient.invalidateQueries({ queryKey: projectKeys.all });
    }
  });
}
