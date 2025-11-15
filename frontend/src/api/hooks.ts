import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "./client";
import type { Property, Unit, Citation } from "./types";

export function useProperties(params?: Record<string, any>) {
  return useQuery({
    queryKey: ["properties", params],
    queryFn: async () => (await api.get<{results: Property[]; count: number}>("/properties/", { params })).data,
  });
}

export function useUnits(params?: Record<string, any>) {
  return useQuery({
    queryKey: ["units", params],
    queryFn: async () => (await api.get<{results: Unit[]; count: number}>("/units/", { params })).data,
  });
}

export function useUpload() {
  return useMutation({
    mutationFn: async (payload: { file: File; doc_type: "flyer" | "rent_roll" }) => {
      const form = new FormData();
      form.append("file", payload.file);
      form.append("doc_type", payload.doc_type);
      return (await api.post("/upload/", form)).data as { document_id: number };
    },
  });
}

export function useCitations(model: string, id: number) {
  return useQuery({
    queryKey: ["citations", model, id],
    enabled: !!id,
    queryFn: async () => (await api.get<Citation[]>(`/citations/${model}/${id}/`)).data,
  });
}

export function useSearch(q: string) {
  const enabled = q.trim().length > 0;
  return useQuery({
    enabled,
    queryKey: ["search", q],
    queryFn: async (): Promise<{ properties: Property[]; units: Unit[] }> => {
      const { data } = await api.get("/search/", { params: { q } });
      return data;
    },
    staleTime: 30_000,
  });
}
