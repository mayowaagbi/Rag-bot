import type React from "react";
import type { FormEvent, ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { PaperclipIcon, SendIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  input: string;
  handleInputChange: (e: ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
  onFileUpload: (files: File[]) => void;
  isUploading: boolean;
  isIndexing: boolean;
}

export function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  onFileUpload,
  isUploading,
  isIndexing,
}: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        const form = e.currentTarget.form;
        if (form) form.requestSubmit();
      }
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(Array.from(e.target.files));
      e.target.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="overflow-hidden rounded-lg border bg-white shadow-sm focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2 dark:bg-slate-800 dark:border-slate-700">
        <Textarea
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
          className="min-h-[60px] w-full resize-none border-0 bg-transparent p-3 pr-20 focus-visible:ring-0 focus-visible:ring-offset-0 dark:placeholder:text-slate-400"
          disabled={isLoading || isUploading || isIndexing}
        />
        <div className="absolute bottom-2 right-2 flex space-x-2">
          <label htmlFor="file-upload">
            <Button
              type="button"
              size="icon"
              variant="ghost"
              className={cn(
                "h-8 w-8 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100",
                (isLoading || isUploading || isIndexing) && "opacity-50"
              )}
              disabled={isLoading || isUploading || isIndexing}
            >
              <PaperclipIcon className="h-4 w-4" />
              <span className="sr-only">Attach files</span>
            </Button>
            <input
              id="file-upload"
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={handleFileChange}
              disabled={isLoading || isUploading || isIndexing}
            />
          </label>
          <Button
            type="submit"
            size="icon"
            className="h-8 w-8 rounded-full"
            disabled={!input.trim() || isLoading || isUploading || isIndexing}
          >
            <SendIcon className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
      </div>
    </form>
  );
}
