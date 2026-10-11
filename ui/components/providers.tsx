"use client";

import { SessionProvider } from "next-auth/react";
import { SessionRefresh } from "@/components/session-refresh";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    // No initial `session` is passed in from the server on purpose: resolving
    // it in the root layout (getServerSession) runs the jwt callback, which
    // refreshes — and rotates — the refresh token, but a Server Component
    // can't persist the resulting cookie. The browser would keep the consumed
    // token and every later refresh would be rejected. Letting the client
    // fetch /api/auth/session means the refresh happens in a route handler,
    // which can set the cookie.
    //
    // refetchOnWindowFocus is off deliberately: SessionRefresh already
    // re-checks on focus, but only refreshes when the token is actually near
    // expiry. The default window-focus refetch has no expiry check of its
    // own — it re-hits /api/auth/session on every tab focus regardless of how
    // much of the token's life is left.
    <SessionProvider refetchOnWindowFocus={false}>
      <SessionRefresh />
      {children}
    </SessionProvider>
  );
}
