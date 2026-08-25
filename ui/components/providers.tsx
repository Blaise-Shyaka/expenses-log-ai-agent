"use client";

import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";
import { SessionRefresh } from "@/components/session-refresh";

export function Providers({
  session,
  children,
}: {
  session: Session | null;
  children: React.ReactNode;
}) {
  return (
    // refetchOnWindowFocus is off deliberately: SessionRefresh already
    // schedules the one refresh trigger this app needs, ahead of expiry.
    // The default window-focus refetch is a second, redundant trigger with
    // no expiry check of its own — it re-hits /api/auth/session on every
    // tab focus regardless of how much of the token's life is left.
    <SessionProvider session={session} refetchOnWindowFocus={false}>
      <SessionRefresh />
      {children}
    </SessionProvider>
  );
}
