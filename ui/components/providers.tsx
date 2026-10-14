"use client";

import { SessionProvider } from "next-auth/react";
import { SessionRefresh } from "@/components/session-refresh";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    // No initial `session` is passed in from the server on purpose.The client's
    // fetch /api/auth/session means the refresh happens in a route handler,
    // which can set the cookie.
    //
    // refetchOnWindowFocus is off deliberately: SessionRefresh already
    // re-checks on focus, but only refreshes when the token is actually near
    // expiry.
    <SessionProvider refetchOnWindowFocus={false}>
      <SessionRefresh />
      {children}
    </SessionProvider>
  );
}
