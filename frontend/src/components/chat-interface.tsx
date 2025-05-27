import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, PanelLeftClose, PanelLeftOpen, Upload } from "lucide-react";
import type { Document } from "@/types/document";
import { useMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { FileUploader } from "@/components/file-uploader";
import { ChatMessages } from "@/components/chat-messages";
import { ChatInput } from "@/components/chat-input";
import { DocumentSidebar } from "@/components/document-sidebar";
import { SearchSuggestions } from "@/components/search-suggestions";
import { ThemeToggle } from "@/components/theme-toggle";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function ChatInterface() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isMobile = useMobile();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // Add this at the top of your ChatInterface component
  const API_BASE_URL = "http://localhost:8000";

  // Update your handleFileUpload function
  const handleFileUpload = async (files: File[]) => {
    console.log("Starting file upload with files:", files);
    setIsUploading(true);

    try {
      const formData = new FormData();
      files.forEach((file, index) => {
        console.log(`Adding file ${index}:`, file.name, file.size, file.type);
        formData.append("files", file);
      });

      console.log("Making request to", `${API_BASE_URL}/api/upload`);
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      console.log("Upload response status:", response.status);
      console.log("Upload response ok:", response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Upload failed with error:", errorText);
        console.error("Response headers:", response.headers);
        console.error("Response status:", response.status);
        console.error("Response statusText:", response.statusText);
        throw new Error(`Upload failed: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log("Upload result:", result);

      if (result.documents && result.documents.length > 0) {
        console.log("Adding documents to state:", result.documents);
        setDocuments((prev) => {
          const newDocs = [...prev, ...result.documents];
          console.log("New documents state:", newDocs);
          return newDocs;
        });
      } else {
        console.warn("No documents returned from upload");
      }

      setIsUploading(false);
      setIsIndexing(true);

      // Simulate indexing delay
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setIsIndexing(false);

      console.log("Upload process completed successfully");
    } catch (error) {
      console.error("Upload error:", error);
      setIsUploading(false);
      setIsIndexing(false);

      // Show user-friendly error
      if (error instanceof Error) {
        alert(`Upload failed: ${error.message}`);
      } else {
        alert("Upload failed: An unknown error occurred.");
      }
    }
  };

  // Update your handleSubmit function for chat
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: "user" as const,
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setStreamingMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [userMessage],
          documentIds: [],
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.replace("data: ", "");
            if (data === "[DONE]") {
              setMessages((prev) => [
                ...prev,
                {
                  id: Date.now().toString(),
                  role: "assistant",
                  content: assistantMessage,
                },
              ]);
              setStreamingMessage("");
              setIsLoading(false);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices[0].delta.content || "";
              assistantMessage += content;
              setStreamingMessage(assistantMessage);
            } catch (e) {
              console.error("Error parsing chunk:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content:
            documents.length > 0
              ? "Sorry, I couldn't process your request. Please try again."
              : "Please upload documents first to get context-aware responses.",
        },
      ]);
      setIsLoading(false);
    }
  };

  // Update the loadDocuments function in your useEffect
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/documents`);
        if (response.ok) {
          const result = await response.json();
          setDocuments(result.documents || []);
        }
      } catch (error) {
        console.error("Error loading documents:", error);
      }
    };

    loadDocuments();
  }, []);

  // Update handleDeleteDocument function
  const handleDeleteDocument = async (documentId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      } else {
        console.error("Failed to delete document");
      }
    } catch (error) {
      console.error("Error deleting document:", error);
    }
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };
  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-950">
      <DocumentSidebar
        documents={documents}
        isOpen={!isMobile || sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isCollapsed={sidebarCollapsed}
        onDeleteDocument={handleDeleteDocument}
        onToggleCollapse={toggleSidebar}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
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
              Mayovibe1's RAGBot
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </header>

        <main className="relative flex flex-1 flex-col overflow-hidden">
          <div
            className={cn(
              "flex-1 overflow-y-auto bg-white px-4 py-6 dark:bg-slate-900",
              messages.length === 0 && "pt-16"
            )}
          >
            {messages.length === 0 ? (
              <div className="flex w-full max-w-3xl flex-col items-center justify-center px-4 mx-auto">
                <div className="flex flex-col gap-4 w-full max-w-md">
                  <FileUploader
                    onFilesSelected={handleFileUpload}
                    isUploading={isUploading}
                    isIndexing={isIndexing}
                  />
                  <SearchSuggestions
                    onSuggestionClick={(suggestion) => setInput(suggestion)}
                  />
                  {documents.length === 0 && (
                    <div className="text-center text-sm text-slate-600 dark:text-slate-400 mt-4">
                      Upload documents to get started
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="mx-auto max-w-3xl">
                <ChatMessages
                  messages={messages}
                  isLoading={isLoading}
                  streamingMessage={streamingMessage}
                />
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {(isUploading || isIndexing) && (
            <div className="absolute inset-x-0 top-0 flex items-center justify-center bg-primary/10 p-2 text-sm font-medium text-primary">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {isUploading ? "Uploading documents..." : "Indexing documents..."}
            </div>
          )}

          <div className="border-t bg-white p-4 dark:bg-slate-900 dark:border-slate-800">
            <div className="mx-auto max-w-3xl">
              <ChatInput
                input={input}
                handleInputChange={(e) => setInput(e.target.value)}
                handleSubmit={handleSubmit}
                isLoading={isLoading}
                disabled={documents.length === 0}
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
