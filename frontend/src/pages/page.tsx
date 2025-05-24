import React from "react";
import { ChatInterface } from "@/components/chat-interface";

interface MetadataProps {
  title: string;
  description: string;
}

const metadata: MetadataProps = {
  title: "RAG-Bot",
  description: "Chat with your documents using AI",
};

const Home: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col">
      <ChatInterface />
    </div>
  );
};

export default Home;
