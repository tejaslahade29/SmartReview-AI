import { AxiosError } from "axios";

interface BackendErrorBody {
  error?: { code?: string; message?: string };
}

export function getErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as BackendErrorBody | undefined;
    if (body?.error?.message) {
      return body.error.message;
    }
    if (error.code === "ECONNABORTED") {
      return "The request timed out. Please try again.";
    }
    if (!error.response) {
      return "Could not reach the server. Check your connection and try again.";
    }
  }
  return fallback;
}
