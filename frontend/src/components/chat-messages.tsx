// Define Message type locally if not available from a package
export interface Message {
  id: string;
  role: "user" | "assistant" | "system" | string;
  content: string;
}
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  return (
    <div className="space-y-6">
      {messages.map((message, index) => (
        <div
          key={index}
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

            {message.role !== "user" && (
              <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                <details className="group">
                  <summary className="cursor-pointer hover:text-slate-700 dark:hover:text-slate-300">
                    View sources
                  </summary>
                  <ul className="mt-2 space-y-1 pl-4">
                    <li className="flex items-center gap-1 text-xs">
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span>
                      Document 1, page 5
                    </li>
                    <li className="flex items-center gap-1 text-xs">
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span>
                      Document 3, page 12
                    </li>
                  </ul>
                </details>
              </div>
            )}
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

      {isLoading && (
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
