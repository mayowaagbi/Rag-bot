"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@/hooks/use-chat";
import { FileUploader } from "@/components/file-uploader";
import { ChatMessages } from "@/components/chat-messages";
import { ChatInput } from "@/components/chat-input";
import { DocumentSidebar } from "@/components/document-sidebar";
import { SearchSuggestions } from "@/components/search-suggestions";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Loader2, PanelLeftClose, PanelLeftOpen, Upload } from "lucide-react";
import type { Document } from "@/types/document";
import { useMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";

export function ChatInterface() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isMobile = useMobile();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showUploader, setShowUploader] = useState(false);

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setInput,
  } = useChat({
    api: "/api/chat",
    body: {
      documentIds: documents.map((doc) => doc.id),
    },
    onResponse: () => {
      // Scroll to bottom when a new message is received
      setTimeout(() => scrollToBottom(), 100);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (files: File[]) => {
    setIsUploading(true);

    try {
      // Simulate file upload and indexing
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const newDocuments: Document[] = files.map((file) => ({
        id: Math.random().toString(36).substring(7),
        name: file.name,
        size: file.size,
        type: file.type,
        uploadedAt: new Date().toISOString(),
        pages: Math.floor(Math.random() * 20) + 1,
      }));

      setIsUploading(false);
      setIsIndexing(true);

      // Simulate indexing delay
      await new Promise((resolve) => setTimeout(resolve, 2000));

      setDocuments((prev) => [...prev, ...newDocuments]);
      setIsIndexing(false);
      setShowUploader(false);
    } catch (error) {
      console.error("Error uploading files:", error);
      setIsUploading(false);
      setIsIndexing(false);
    }
  };

  const handleDeleteDocument = (id: string) => {
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  const toggleSidebar = () => {
    if (isMobile) {
      setSidebarOpen(!sidebarOpen);
    } else {
      setSidebarCollapsed(!sidebarCollapsed);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Sidebar */}
      <DocumentSidebar
        documents={documents}
        onDeleteDocument={handleDeleteDocument}
        isOpen={!isMobile || sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b bg-white px-4 shadow-sm dark:bg-slate-900 dark:border-slate-800">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="mr-3 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            >
              {sidebarCollapsed ? (
                <PanelLeftOpen className="h-5 w-5" />
              ) : (
                <PanelLeftClose className="h-5 w-5" />
              )}
            </Button>
            <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">
              RAG-Bot
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-slate-600 dark:text-slate-300"
              onClick={() => setShowUploader(true)}
            >
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload</span>
            </Button>
            <ThemeToggle />
          </div>
        </header>

        <main className="relative flex flex-1 flex-col overflow-hidden">
          {/* Chat area */}
          <div
            className={cn(
              "flex-1 overflow-y-auto bg-white px-4 py-6 dark:bg-slate-900",
              messages.length === 0 && "pt-16"
            )}
          >
            {messages.length === 0 ? (
              <div className="flex w-full max-w-3xl flex-col items-center justify-center px-4">
                <div className="mb-8 text-center">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-8 w-8"
                    >
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                  </div>
                  <h2 className="mb-2 text-2xl font-bold text-slate-800 dark:text-slate-100">
                    Welcome to RAG-Bot
                  </h2>
                  <p className="text-slate-500 dark:text-slate-400">
                    Upload your documents and start asking questions about them.
                  </p>
                </div>

                {showUploader ? (
                  <div className="w-full max-w-md">
                    <FileUploader
                      onFilesSelected={handleFileUpload}
                      isUploading={isUploading}
                      isIndexing={isIndexing}
                    />
                  </div>
                ) : (
                  <div className="flex flex-col gap-4 w-full max-w-md">
                    <Button
                      size="lg"
                      className="w-full gap-2"
                      onClick={() => setShowUploader(true)}
                    >
                      <Upload className="h-4 w-4" />
                      Upload Documents
                    </Button>
                    <SearchSuggestions
                      onSuggestionClick={handleSuggestionClick}
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="mx-auto max-w-3xl">
                <ChatMessages messages={messages} isLoading={isLoading} />
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Status indicators */}
          {(isUploading || isIndexing) && (
            <div className="absolute inset-x-0 top-0 flex items-center justify-center bg-primary/10 p-2 text-sm font-medium text-primary">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {isUploading ? "Uploading documents..." : "Indexing documents..."}
            </div>
          )}

          {/* Chat input */}
          <div className="border-t bg-white p-4 dark:bg-slate-900 dark:border-slate-800">
            <div className="mx-auto max-w-3xl">
              <ChatInput
                input={input}
                handleInputChange={handleInputChange}
                handleSubmit={handleSubmit}
                isLoading={isLoading}
                onFileUpload={handleFileUpload}
                isUploading={isUploading}
                isIndexing={isIndexing}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
