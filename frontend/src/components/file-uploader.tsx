import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { FileText, Upload, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploaderProps {
  onFilesSelected: (files: File[]) => void;
  isUploading: boolean;
  isIndexing: boolean;
}

export function FileUploader({
  onFilesSelected,
  isUploading,
  isIndexing,
}: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles?.length > 0 && !isUploading && !isIndexing) {
        setSelectedFiles(acceptedFiles);
      }
    },
    [isUploading, isIndexing]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "text/plain": [".txt"],
    },
    disabled: isUploading || isIndexing,
  });

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      onFilesSelected(selectedFiles);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="w-full space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          "relative flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center transition-colors",
          isDragActive
            ? "border-primary/50 bg-primary/5"
            : "border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50",
          (isUploading || isIndexing) && "opacity-60"
        )}
      >
        <input {...getInputProps()} />

        <div className="mb-4 rounded-full bg-primary/10 p-3 text-primary">
          {isUploading || isIndexing ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <Upload className="h-6 w-6" />
          )}
        </div>

        <h3 className="mb-1 text-lg font-semibold text-slate-800 dark:text-slate-100">
          {isUploading
            ? "Uploading..."
            : isIndexing
            ? "Indexing..."
            : "Upload your documents"}
        </h3>

        <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
          {isUploading || isIndexing
            ? "This may take a moment"
            : "Drag and drop or click to upload"}
        </p>

        {!isUploading && !isIndexing && (
          <>
            <p className="mb-2 text-xs text-slate-400 dark:text-slate-500">
              Supported formats: PDF, DOCX, TXT
            </p>

            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={(e) => {
                e.stopPropagation();
                document.getElementById("file-input")?.click();
              }}
            >
              <FileText className="mr-2 h-4 w-4" />
              Select files
            </Button>
          </>
        )}
      </div>

      {selectedFiles.length > 0 && !isUploading && !isIndexing && (
        <div className="space-y-3">
          <div className="rounded-lg border bg-white p-3 dark:bg-slate-800 dark:border-slate-700">
            <h4 className="mb-2 text-sm font-medium text-slate-800 dark:text-slate-100">
              Selected Files ({selectedFiles.length})
            </h4>
            <ul className="space-y-2">
              {selectedFiles.map((file, index) => (
                <li
                  key={index}
                  className="flex items-center justify-between rounded-md bg-slate-50 p-2 text-sm dark:bg-slate-700"
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span className="truncate">{file.name}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-3 w-3" />
                    <span className="sr-only">Remove</span>
                  </Button>
                </li>
              ))}
            </ul>
          </div>

          <Button className="w-full" onClick={handleUpload}>
            Upload {selectedFiles.length}{" "}
            {selectedFiles.length === 1 ? "file" : "files"}
          </Button>
        </div>
      )}
    </div>
  );
}
