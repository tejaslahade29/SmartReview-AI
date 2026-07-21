import { apiClient } from "@/lib/api/client";

export interface HealthResponse {
  status: string;
  environment: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}
