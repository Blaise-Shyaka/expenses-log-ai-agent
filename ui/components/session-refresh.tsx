"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";

/**
 * Schedules a single refresh right before the access token expires, instead
 * of waiting for a request to notice it's already stale. auth.ts's jwt
 * callback has its own buffer and does the actual refresh decision — this
 * just makes sure something proactively asks, so a real user-facing request
 * essentially never has to.
 *
 * Deliberately single-tab only for now: this timer is per-tab, and multiple
 * tabs each running their own can still race each other. That's a known,
 * separate problem (needs cross-tab coordination, e.g. the Web Locks API) —
 * not solved here.
 */
export function SessionRefresh() {
  const { data: session, status, update } = useSession();
  const accessTokenExpires = session?.accessTokenExpires;

  useEffect(() => {
    if (status !== "authenticated" || !accessTokenExpires) return;

    const REFRESH_MARGIN_MS = 60 * 1000;
    const delay = Math.max(0, accessTokenExpires - Date.now() - REFRESH_MARGIN_MS);

    const timer = setTimeout(() => {
      update();
    }, delay);

    return () => clearTimeout(timer);
  }, [status, accessTokenExpires, update]);

  return null;
}
