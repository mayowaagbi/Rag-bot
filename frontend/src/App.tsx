import React from "react";
import { ChatInterface } from "@/components/chat-interface";
import { ThemeProvider } from "./context/theme-context";

interface MetadataProps {
  title: string;
  description: string;
}

const metadata: MetadataProps = {
  title: "RAG-Bot",
  description: "Chat with your documents using AI",
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <div className="flex min-h-screen flex-col">
        {/* <header className="flex justify-end p-4">
          <ThemeToggle />
        </header> */}
        <main className="flex-1">
          <ChatInterface />
        </main>
      </div>
    </ThemeProvider>
  );
};

export default App;
