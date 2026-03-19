"use client";

import { CopilotKit, CopilotChat } from "@copilotkit/react-core/v2";

export default function Home() {
  return (
    <CopilotKit agent="chat" runtimeUrl="/api/copilotkit">
      <main className="flex justify-center items-center h-full" style={{ height: '100vh' }} >
        <CopilotChat
          labels={{
            welcomeMessageText: "Hi, I'm an expense tracker assistant. Any expenses to log today?"
          }}
          className="h-full rounded-2xl max-w-6xl mx-auto"
        />
      </main>
    </CopilotKit>

  );
}
