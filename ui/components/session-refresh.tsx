"use client";

import { useEffect, useRef } from "react";
import { signOut, useSession } from "next-auth/react";

// Ask for a refresh once the token is within this long of expiring. Kept below
// auth.ts's REFRESH_BUFFER_MS so the jwt callback always agrees it's due.
const REFRESH_MARGIN_MS = 60 * 1000;
const POLL_INTERVAL_MS = 30 * 1000;
// update() flips next-auth's status to "loading" and back, which re-runs the
// effect below; without a gap a failing refresh (e.g. offline) would retry in
// a tight loop instead of at the poll cadence.
const MIN_RETRY_GAP_MS = 10 * 1000;

/**
 * Keeps the access token fresh, and ends the session when it can't be.
 *
 * Expiry is checked against the wall clock on mount, on an interval, and
 * whenever the user comes back (tab visible / window focused / network back).
 * A single long setTimeout can't do this job: it's delayed or lost when the
 * machine sleeps or the tab is throttled, and one failed attempt (the network
 * often isn't back yet on wake) would never be retried.
 *
 * auth.ts's jwt callback has its own buffer and does the actual refresh
 * decision — this just makes sure something asks, so a real user-facing
 * request essentially never has to.
 *
 * A failed refresh surfaces as session.error. Sign out then, rather than
 * leaving a chat on screen that will 401 on the first message.
 *
 * Deliberately single-tab only for now: each tab runs its own checks, and
 * multiple tabs can still race each other. That's a known, separate problem
 * (needs cross-tab coordination, e.g. the Web Locks API) — not solved here.
 */
export function SessionRefresh() {
  const { data: session, update } = useSession();
  const hasSession = session != null;

  // update()'s identity changes on every session/loading change (next-auth
  // internals) — depending on it directly re-arms the effect below in a loop.
  const updateRef = useRef(update);
  const expiresRef = useRef<number | undefined>(undefined);
  const lastAttemptRef = useRef(0);
  useEffect(() => {
    updateRef.current = update;
    expiresRef.current = session?.accessTokenExpires;
  });

  useEffect(() => {
    if (session?.error === "RefreshAccessTokenError") {
      void signOut({ callbackUrl: "/login" });
    }
  }, [session?.error]);

  useEffect(() => {
    if (!hasSession) return;

    const check = () => {
      const expires = expiresRef.current;
      const due =
        expires === undefined || Date.now() >= expires - REFRESH_MARGIN_MS;
      if (!due || Date.now() - lastAttemptRef.current < MIN_RETRY_GAP_MS) {
        return;
      }
      lastAttemptRef.current = Date.now();
      void updateRef.current();
    };
    const onVisible = () => {
      if (document.visibilityState === "visible") check();
    };

    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", check);
    window.addEventListener("online", check);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", check);
      window.removeEventListener("online", check);
    };
  }, [hasSession]);

  return null;
}
