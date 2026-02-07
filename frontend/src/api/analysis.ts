import apiClient from "./client";
import type {
  AnalysisResponse,
  AnalysisListResponse,
  BatchDetailResponse,
  ApplicationDetails,
} from "../types/analysis";

export async function uploadSingle(
  file: File,
  applicationDetails: ApplicationDetails,
): Promise<{ analysis_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  for (const [key, value] of Object.entries(applicationDetails)) {
    if (value) {
      formData.append(key, value);
    }
  }
  const response = await apiClient.post<{ analysis_id: string }>(
    "/analysis/single",
    formData,
  );
  return response.data;
}

export async function getAnalysis(id: string): Promise<AnalysisResponse> {
  const response = await apiClient.get<AnalysisResponse>(`/analysis/${id}`);
  return response.data;
}

export async function getHistory(
  page: number,
  pageSize: number,
  verdict?: string,
): Promise<AnalysisListResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (verdict) {
    params.verdict = verdict;
  }
  const response = await apiClient.get<AnalysisListResponse>("/analysis/", {
    params,
  });
  return response.data;
}

export async function uploadBatch(
  files: File[],
  csvFile: File,
): Promise<{ batch_id: string; total_labels: number }> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  formData.append("csv_file", csvFile);
  const response = await apiClient.post<{
    batch_id: string;
    total_labels: number;
  }>("/batch/upload", formData);
  return response.data;
}

export async function getBatch(id: string): Promise<BatchDetailResponse> {
  const response = await apiClient.get<BatchDetailResponse>(`/batch/${id}`);
  return response.data;
}
