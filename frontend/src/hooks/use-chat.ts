// hooks/use-chat.ts
import { useState } from "react";

type Message = {
  id: string;
  content: string;
  role: "user" | "assistant";
};

export function useChat(options: {
  api: string;
  body: { documentIds: string[] };
  onResponse?: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: "user",
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate AI response after a delay
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: `This is a mock response to: "${input}". In a real implementation, this would call ${
          options.api
        } with document IDs: ${options.body.documentIds.join(", ")}`,
        role: "assistant",
      };

      setMessages((prev) => [...prev, aiResponse]);
      setIsLoading(false);
      options.onResponse?.();
    }, 1000);
  };

  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setInput,
  };
}
