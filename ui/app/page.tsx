"use client";

import { CopilotKit, CopilotChat } from "@copilotkit/react-core/v2";
import { useSession } from "next-auth/react";
import { logout } from "@/lib/auth-client";

export default function Home() {
  const { data: session } = useSession();

  return (
    <CopilotKit
      agent="chat"
      runtimeUrl="/api/copilotkit"
      headers={
        session?.accessToken
          ? { Authorization: `Bearer ${session.accessToken}` }
          : {}
      }
    >
      <main
        className="flex justify-center items-center h-full"
        style={{ height: "100vh", position: "relative" }}
      >
        <form
          action={logout}
          style={{ position: "absolute", top: "1rem", right: "1rem", zIndex: 10 }}
        >
          <button
            type="submit"
            style={{
              padding: "0.375rem 0.75rem",
              backgroundColor: "transparent",
              border: "1px solid #2a2a2a",
              borderRadius: "6px",
              color: "#6b7280",
              fontSize: "0.75rem",
              cursor: "pointer",
              fontFamily: "var(--font-geist-sans)",
            }}
          >
            Sign out
          </button>
        </form>
        <CopilotChat
          labels={{
            welcomeMessageText:
              "Hi, I'm an expense tracker assistant. Any expenses to log today?",
          }}
          className="h-full rounded-2xl max-w-6xl mx-auto"
        />
      </main>
    </CopilotKit>
  );
}
