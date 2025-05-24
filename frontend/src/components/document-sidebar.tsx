import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import {
  ChevronDown,
  ChevronRight,
  ChevronUp,
  FileText,
  FileIcon as FilePdf,
  FileType,
  FileSpreadsheet,
  Trash2,
  X,
  FolderOpen,
} from "lucide-react";
import type { Document } from "@/types/document";
import { formatFileSize, formatDate } from "@/lib/utils";
import { useMobile } from "@/hooks/use-mobile";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface DocumentSidebarProps {
  documents: Document[];
  onDeleteDocument: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function DocumentSidebar({
  documents,
  onDeleteDocument,
  isOpen,
  onClose,
  isCollapsed = false,
  onToggleCollapse,
}: DocumentSidebarProps) {
  const isMobile = useMobile();
  const [expandedDocId, setExpandedDocId] = useState<string | null>(null);
  const [isDocListExpanded, setIsDocListExpanded] = useState(true);

  const toggleDocumentDetails = (id: string) => {
    setExpandedDocId(expandedDocId === id ? null : id);
  };

  const getFileIcon = (type: string) => {
    if (type.includes("pdf"))
      return <FilePdf className="h-4 w-4 text-red-500" />;
    if (type.includes("word") || type.includes("docx"))
      return <FileText className="h-4 w-4 text-blue-500" />;
    if (type.includes("sheet") || type.includes("excel"))
      return <FileSpreadsheet className="h-4 w-4 text-green-500" />;
    return <FileType className="h-4 w-4 text-slate-400" />;
  };

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b p-4 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <FolderOpen className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
            Documents
          </h2>
        </div>
        {isMobile && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-slate-500"
          >
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>

      <div className="flex-1 overflow-auto">
        <div className="p-4">
          <Collapsible
            open={isDocListExpanded}
            onOpenChange={setIsDocListExpanded}
            className="w-full"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium text-slate-800 dark:text-slate-200">
                  Files
                </h3>
                <Badge variant="outline" className="text-xs font-normal">
                  {documents.length}
                </Badge>
              </div>
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-slate-500"
                >
                  {isDocListExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                  <span className="sr-only">Toggle documents</span>
                </Button>
              </CollapsibleTrigger>
            </div>

            <CollapsibleContent className="mt-2">
              <ScrollArea className="h-[calc(100vh-180px)]">
                {documents.length === 0 ? (
                  <div className="flex h-32 flex-col items-center justify-center rounded-lg border border-dashed p-4 text-center text-slate-400 dark:border-slate-700">
                    <FileText className="mb-2 h-8 w-8 opacity-50" />
                    <p className="text-sm">No documents uploaded yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="overflow-hidden rounded-lg border bg-white transition-all hover:shadow-sm dark:bg-slate-800 dark:border-slate-700"
                      >
                        <div
                          className="flex cursor-pointer items-center justify-between p-3"
                          onClick={() => toggleDocumentDetails(doc.id)}
                        >
                          <div className="flex items-center space-x-3 overflow-hidden">
                            {getFileIcon(doc.type)}
                            <div className="overflow-hidden">
                              <p className="truncate font-medium text-slate-700 dark:text-slate-200">
                                {doc.name}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">
                                {formatFileSize(doc.size)} •{" "}
                                {formatDate(doc.uploadedAt)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteDocument(doc.id);
                              }}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              <span className="sr-only">Delete</span>
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                            >
                              {expandedDocId === doc.id ? (
                                <ChevronUp className="h-3.5 w-3.5" />
                              ) : (
                                <ChevronDown className="h-3.5 w-3.5" />
                              )}
                            </Button>
                          </div>
                        </div>

                        {expandedDocId === doc.id && (
                          <div className="border-t bg-slate-50 p-3 text-sm dark:bg-slate-800/50 dark:border-slate-700">
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                  Type
                                </p>
                                <p className="text-slate-700 dark:text-slate-300">
                                  {doc.type.split("/").pop()?.toUpperCase() ||
                                    "Unknown"}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                  Pages
                                </p>
                                <p className="text-slate-700 dark:text-slate-300">
                                  {doc.pages}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                  Uploaded
                                </p>
                                <p className="text-slate-700 dark:text-slate-300">
                                  {new Date(
                                    doc.uploadedAt
                                  ).toLocaleDateString()}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                  Size
                                </p>
                                <p className="text-slate-700 dark:text-slate-300">
                                  {formatFileSize(doc.size)}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent side="left" className="w-[300px] p-0">
          {sidebarContent}
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <TooltipProvider>
      <div
        className={`hidden border-r bg-white transition-all duration-300 dark:bg-slate-900 dark:border-slate-800 md:block ${
          isCollapsed ? "w-[60px]" : "w-[300px]"
        }`}
      >
        {isCollapsed ? (
          // Collapsed sidebar view
          <div className="flex h-full flex-col items-center py-4">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onToggleCollapse}
                  className="text-slate-500"
                >
                  <ChevronRight className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            </Tooltip>

            <Separator className="my-4" />

            <div className="flex flex-col items-center gap-6 mt-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex flex-col items-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                      <FolderOpen className="h-5 w-5 text-primary" />
                    </div>
                    <span className="mt-1 text-xs font-medium text-slate-600 dark:text-slate-400">
                      {documents.length}
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  {documents.length} documents
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        ) : (
          // Expanded sidebar content
          sidebarContent
        )}
      </div>
    </TooltipProvider>
  );
}
