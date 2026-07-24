import { apiClient } from "@/lib/api/client";

export interface ReviewedDocument {
  id: string;
  document_id: string;
  review_id: string;
  version: number;
  comment_count: number;
  highlight_count: number;
  tracked_change_count: number;
  created_at: string;
}

export async function fetchReviewedDocumentsForDocument(documentId: string): Promise<ReviewedDocument[]> {
  const { data } = await apiClient.get<ReviewedDocument[]>(`/documents/${documentId}/reviewed-documents`);
  return data;
}

export async function generateReviewedDocument(reviewId: string): Promise<ReviewedDocument> {
  const { data } = await apiClient.post<ReviewedDocument>(`/reviews/${reviewId}/reviewed-document`);
  return data;
}

export async function downloadReviewedDocument(reviewedDocumentId: string, filename: string): Promise<void> {
  const response = await apiClient.get(`/reviewed-documents/${reviewedDocumentId}/download`, {
    responseType: "blob",
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
