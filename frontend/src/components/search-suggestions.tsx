import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface SearchSuggestionsProps {
  onSuggestionClick: (suggestion: string) => void;
}

export function SearchSuggestions({
  onSuggestionClick,
}: SearchSuggestionsProps) {
  const suggestions = [
    "What are the main points in this document?",
    "Summarize the key findings in 3 bullet points",
    "What does the document say about [topic]?",
    "Compare the information between documents",
    "Find all mentions of [keyword] in my documents",
  ];

  return (
    <div className="w-full rounded-lg border bg-white p-4 shadow-sm dark:bg-slate-800 dark:border-slate-700">
      <div className="mb-3 flex items-center gap-2">
        <Search className="h-4 w-4 text-slate-400" />
        <h3 className="text-sm font-medium text-slate-700 dark:text-slate-200">
          Try asking
        </h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            className="text-xs bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
            onClick={() => onSuggestionClick(suggestion)}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  );
}
