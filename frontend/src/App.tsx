import React from "react";
import { ChatInterface } from "@/components/chat-interface";
import { ThemeProvider } from "./context/theme-context";
import { useDialogAccessibilityFix } from "./hooks/use-dialog-accessibility";

const App: React.FC = () => {
  // Global fix for dialog accessibility issues
  useDialogAccessibilityFix();

  return (
    <ThemeProvider>
      <div className="flex min-h-screen flex-col">
        <main className="flex-1">
          <ChatInterface />
        </main>
      </div>
    </ThemeProvider>
  );
};

export default App;
