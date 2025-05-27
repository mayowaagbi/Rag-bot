import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  streamingMessage: string;
}

export function ChatMessages({
  messages,
  isLoading,
  streamingMessage,
}: ChatMessagesProps) {
  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn(
            "flex items-start gap-3",
            message.role === "user" ? "justify-end" : "justify-start"
          )}
        >
          {message.role !== "user" && (
            <Avatar className="h-8 w-8 border bg-primary/10 text-primary">
              <AvatarFallback>
                <Bot className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
          )}

          <div
            className={cn(
              "max-w-[85%] rounded-lg px-4 py-3",
              message.role === "user"
                ? "bg-primary text-primary-foreground"
                : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
            )}
          >
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>

          {message.role === "user" && (
            <Avatar className="h-8 w-8 border bg-slate-200 dark:bg-slate-700">
              <AvatarFallback>
                <User className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
          )}
        </div>
      ))}

      {isLoading && streamingMessage && (
        <div className="flex items-start gap-3">
          <Avatar className="h-8 w-8 border bg-primary/10 text-primary">
            <AvatarFallback>
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[85%] rounded-lg bg-slate-100 px-4 py-3 dark:bg-slate-800">
            <div className="whitespace-pre-wrap">{streamingMessage}</div>
          </div>
        </div>
      )}

      {isLoading && !streamingMessage && (
        <div className="flex items-start gap-3">
          <Avatar className="h-8 w-8 border bg-primary/10 text-primary">
            <AvatarFallback>
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[85%] space-y-2 rounded-lg bg-slate-100 p-4 dark:bg-slate-800">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
            <Skeleton className="h-4 w-[150px]" />
          </div>
        </div>
      )}
    </div>
  );
}
