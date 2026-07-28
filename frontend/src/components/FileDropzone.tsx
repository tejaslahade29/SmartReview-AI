"use client";

import { useRef, useState } from "react";
import { FileUp, Loader2 } from "lucide-react";

const ACCEPTED_EXTENSION = ".docx";

export function FileDropzone({
  onFileSelected,
  isUploading,
  progress,
}: {
  onFileSelected: (file: File) => void;
  isUploading: boolean;
  progress: number;
}) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(ACCEPTED_EXTENSION)) {
      onFileSelected(file); // let the parent surface the "only .docx" error via the API
      return;
    }
    onFileSelected(file);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragActive(true);
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragActive(false);
        handleFiles(e.dataTransfer.files);
      }}
      className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
        isDragActive
          ? "border-foreground/40 bg-black/5 dark:bg-white/10"
          : "border-black/15 dark:border-white/20"
      }`}
    >
      {isUploading ? (
        <div className="flex w-full max-w-xs flex-col items-center gap-2">
          <Loader2 className="mb-1 h-6 w-6 animate-spin text-foreground/50" />
          <p className="text-sm font-medium">Uploading and parsing…</p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
            <div
              className="h-full rounded-full bg-foreground transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-foreground/60">{progress}%</p>
        </div>
      ) : (
        <>
          <div className="mb-1 flex h-11 w-11 items-center justify-center rounded-full bg-black/5 text-foreground/50 dark:bg-white/10">
            <FileUp className="h-5 w-5" />
          </div>
          <p className="text-sm font-medium">Drag & drop a DOCX contract here</p>
          <p className="text-xs text-foreground/60">or</p>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-md border border-black/15 px-3 py-1.5 text-sm font-medium hover:bg-black/5 dark:border-white/20 dark:hover:bg-white/10"
          >
            Browse file
          </button>
          <p className="mt-1 text-xs text-foreground/50">.docx only, up to 25MB</p>
        </>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSION}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
}
