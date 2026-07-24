import { apiClient } from "@/lib/api/client";

export interface DocumentSummary {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: string;
  section_count: number;
  table_count: number;
  paragraph_count: number;
  word_count: number;
  created_at: string;
}

export interface DocumentListItem extends DocumentSummary {
  agreement_type: string | null;
  latest_review_id: string | null;
  review_status: string | null;
  has_reviewed_document: boolean;
}

export interface DocumentRun {
  text: string;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  font_name: string | null;
  font_size_pt: number | null;
}

export interface DocumentParagraph {
  id: string;
  section_id: string | null;
  table_id: string | null;
  location: string;
  paragraph_type: string;
  order_index: number;
  row_index: number | null;
  col_index: number | null;
  heading_level: number | null;
  list_level: number | null;
  style_name: string | null;
  text: string;
  runs: DocumentRun[];
}

export interface DocumentStructure {
  document: DocumentSummary;
  sections: { id: string; order_index: number; start_type: string | null }[];
  tables: { id: string; section_id: string | null; order_index: number; row_count: number; col_count: number }[];
  paragraphs: DocumentParagraph[];
}

export async function fetchDocuments(): Promise<DocumentListItem[]> {
  const { data } = await apiClient.get<DocumentListItem[]>("/documents");
  return data;
}

export async function fetchDocument(documentId: string): Promise<DocumentSummary> {
  const { data } = await apiClient.get<DocumentSummary>(`/documents/${documentId}`);
  return data;
}

export async function fetchDocumentStructure(documentId: string): Promise<DocumentStructure> {
  const { data } = await apiClient.get<DocumentStructure>(`/documents/${documentId}/structure`);
  return data;
}

export async function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await apiClient.post<DocumentSummary>("/documents", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return data;
}
