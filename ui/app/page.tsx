"use client";

import { useCallback, useRef, useState } from "react";
import { CopilotKitProvider, CopilotChat } from "@copilotkit/react-core/v2";
import { getSession, useSession } from "next-auth/react";
import { logout } from "@/lib/auth-client";

// CopilotKit's onError has no dedicated auth code. A 401 from our own runtime
// route arrives as error.status; a 401 raised by the agent is flattened into a
// RUN_ERROR event whose message is "HTTP 401: {...}" (and there's never a
// context.response to read a status from).
const isAuthError = (error: unknown) => {
  const e = error as { status?: number; message?: string } | undefined;
  return e?.status === 401 || /\bHTTP 401\b/.test(e?.message ?? "");
};

export default function Home() {
  const { data: session, update } = useSession();
  const runtimeUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/api/copilotkit`
      : "/api/copilotkit";
  const timezone =
    typeof window !== "undefined"
      ? Intl.DateTimeFormat().resolvedOptions().timeZone
      : undefined;

  // Shown in place of the error banner the v1 `CopilotKit` wrapper used to
  // render; the v2 provider surfaces nothing on its own.
  const [chatError, setChatError] = useState<string | null>(null);

  // Last-resort recovery: try a refresh now, force logout only if that fails.
  // One failed run can emit several error events, so only let one recovery
  // attempt run at a time.
  const recovering = useRef(false);
  const handleCopilotError = useCallback(
    async ({ error, code }: { error: unknown; code?: string }) => {
      if (!isAuthError(error)) {
        // Supplying onError replaces CopilotKit's default console logging.
        console.error(`[CopilotKit] Error (${code}):`, error);
        setChatError("Something went wrong. Please try again.");
        return;
      }
      if (recovering.current) return;
      recovering.current = true;
      try {
        // update() returns undefined if next-auth is mid-load, so fall back to
        // a plain session fetch (also runs the jwt callback) before giving up.
        const refreshed = (await update()) ?? (await getSession());
        if (!refreshed || refreshed.error === "RefreshAccessTokenError") {
          await logout();
        } else {
          // The failed message isn't re-sent automatically.
          setChatError("Your session was refreshed. Please send your message again.");
        }
      } finally {
        recovering.current = false;
      }
    },
    [update]
  );

  // The session is fetched client-side (see components/providers.tsx). Gate on
  // `session` rather than `status`: status flips to "loading" during every
  // update(), which would unmount the chat mid-conversation on each refresh.
  if (!session) return null;

  return (
    // Not `CopilotKit`: that export is the deprecated v1 wrapper, which drops
    // onError unless a Copilot Cloud publicApiKey is set — so the handler
    // above would never run.
    <CopilotKitProvider
      runtimeUrl={runtimeUrl}
      headers={
        session?.accessToken
          ? { Authorization: `Bearer ${session.accessToken}` }
          : {}
      }
      properties={timezone ? { timezone } : {}}
      onError={handleCopilotError}
    >
      <main
        className="flex justify-center items-center"
        style={{ height: "100dvh" }}
      >
        <CopilotChat
          agentId="chat"
          // CopilotKit lifts the input by the on-screen keyboard's height, but
          // mobile browsers already scroll the focused field above the
          // keyboard — the two add up and push the input to the top of the
          // screen. Zeroing it leaves positioning to the browser.
          input={{ keyboardHeight: 0 }}
          labels={{
            welcomeMessageText:
              "Hi, I'm Reddington, an expense tracker. How can I help you today?",
          }}
          className="h-full rounded-2xl max-w-6xl mx-auto"
        >
          {({ scrollView, input }) => (
            <div
              style={{ display: "flex", flexDirection: "column", height: "100%" }}
            >
              <header
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "1rem",
                  borderBottom: "1px solid #e5e7eb",
                }}
              >
                <span
                  style={{
                    fontSize: "0.9375rem",
                    fontWeight: 500,
                    color: "#111827",
                    letterSpacing: "-0.01em",
                    fontFamily: "var(--font-geist-sans)",
                  }}
                >
                  ExpenseLog
                </span>
                <form action={logout}>
                  <button
                    type="submit"
                    style={{
                      padding: "0.375rem 0.75rem",
                      backgroundColor: "transparent",
                      border: "1px solid #d1d5db",
                      borderRadius: "6px",
                      color: "#6b7280",
                      fontSize: "0.75rem",
                      cursor: "pointer",
                      fontFamily: "var(--font-geist-sans)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.border = "1px solid #9ca3af";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.border = "1px solid #d1d5db";
                    }}
                  >
                    Sign out
                  </button>
                </form>
              </header>
              {chatError && (
                <div
                  role="alert"
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "0.75rem",
                    margin: "0.75rem 1rem 0",
                    padding: "0.625rem 0.875rem",
                    backgroundColor: "#fef2f2",
                    border: "1px solid #fecaca",
                    borderRadius: "8px",
                    fontSize: "0.8125rem",
                    color: "#dc2626",
                    fontFamily: "var(--font-geist-sans)",
                  }}
                >
                  <span>{chatError}</span>
                  <button
                    type="button"
                    aria-label="Dismiss"
                    onClick={() => setChatError(null)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "inherit",
                      cursor: "pointer",
                      fontSize: "1rem",
                      lineHeight: 1,
                    }}
                  >
                    ×
                  </button>
                </div>
              )}
              {scrollView}
              {input}
            </div>
          )}
        </CopilotChat>
      </main>
    </CopilotKitProvider>
  );
}
