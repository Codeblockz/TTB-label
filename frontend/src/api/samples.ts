import apiClient from "./client";
import type { SampleLabelsResponse } from "../types/analysis";

export async function getSamples(): Promise<SampleLabelsResponse> {
  const response = await apiClient.get<SampleLabelsResponse>("/samples/");
  return response.data;
}

export async function fetchSampleImage(filename: string): Promise<File> {
  const response = await apiClient.get(`/samples/${filename}/image`, {
    responseType: "blob",
  });
  const blob: Blob = response.data;
  return new File([blob], filename, { type: blob.type });
}
