import { apiClient } from "@/lib/api/client";

export interface PartyMappingEntry {
  original_name: string;
  normalized_role: string;
}

export interface ReviewFinding {
  id: string;
  finding_id: string;
  paragraph_id: string;
  issue_type: string;
  severity: "critical" | "high" | "medium" | "low";
  explanation: string;
  suggested_text: string | null;
  confidence: number;
}

export interface Review {
  id: string;
  document_id: string;
  agreement_type: string;
  status: string;
  model_used: string;
  party_mapping: PartyMappingEntry[];
  created_at: string;
  findings: ReviewFinding[];
}

export async function fetchReviewsForDocument(documentId: string): Promise<Review[]> {
  const { data } = await apiClient.get<Review[]>(`/documents/${documentId}/reviews`);
  return data;
}

export async function fetchReview(reviewId: string): Promise<Review> {
  const { data } = await apiClient.get<Review>(`/reviews/${reviewId}`);
  return data;
}

export async function startReview(documentId: string): Promise<Review> {
  const { data } = await apiClient.post<Review>(`/documents/${documentId}/review`, undefined, {
    // The backend's AI call can run up to 120s per attempt, plus retries.
    timeout: 240000,
  });
  return data;
}
