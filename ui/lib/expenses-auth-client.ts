const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL ?? "http://localhost:8001";

interface AuthServiceTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  /** Absolute expiry timestamp in milliseconds (Date.now() + expires_in * 1000) */
  accessTokenExpires: number;
}

export type LoginError = "InvalidCredentials" | "LoginFailed";
export type RegisterError = "DuplicateEmail" | "RegistrationFailed";

export interface RegisterResult {
  success: boolean;
  error?: RegisterError;
}

export async function login(
  email: string,
  password: string
): Promise<AuthTokens> {
  let response: Response;
  try {
    response = await fetch(`${AUTH_SERVICE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    throw new Error("LoginFailed" satisfies LoginError);
  }

  if (response.status === 401) {
    throw new Error("InvalidCredentials" satisfies LoginError);
  }
  if (!response.ok) {
    throw new Error("LoginFailed" satisfies LoginError);
  }

  const data = (await response.json()) as AuthServiceTokenResponse;
  return normaliseTokenResponse(data);
}

/**
 * expenses-auth rotates refresh tokens on every use and permanently rejects
 * reuse of an already-rotated one (by design — see expenses-auth's README).
 * Because Next.js can fire multiple requests that each independently resolve
 * the session in quick succession (page navigation + asset fetches + the
 * CopilotKit ping all call auth() around the same time), more than one of
 * them can read the same not-yet-refreshed cookie and race to refresh with
 * the same soon-to-be-stale token. Whichever request wins rotates it; every
 * other request holding that same token would otherwise get a 401 even
 * though the session is perfectly valid. This cache makes repeat callers
 * within a short window share the winner's result instead of re-hitting
 * expenses-auth with a token that's already been consumed.
 */
const recentRefreshes = new Map<string, { result: Promise<AuthTokens>; expiresAt: number }>();
const REFRESH_DEDUP_WINDOW_MS = 10_000;

export async function refreshTokens(refreshToken: string): Promise<AuthTokens> {
  const cached = recentRefreshes.get(refreshToken);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.result;
  }

  const result = doRefresh(refreshToken);
  recentRefreshes.set(refreshToken, {
    result,
    expiresAt: Date.now() + REFRESH_DEDUP_WINDOW_MS,
  });
  // Don't cache failures — a genuinely invalid/revoked token should fail
  // every time, not just once.
  result.catch(() => recentRefreshes.delete(refreshToken));
  return result;
}

async function doRefresh(refreshToken: string): Promise<AuthTokens> {
  let response: Response;
  try {
    response = await fetch(`${AUTH_SERVICE_URL}/oauth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        refresh_token: refreshToken,
      }),
    });
  } catch {
    throw new Error("RefreshFailed");
  }

  if (!response.ok) {
    throw new Error("RefreshFailed");
  }

  const data = (await response.json()) as AuthServiceTokenResponse;
  return normaliseTokenResponse(data);
}

export async function register(
  email: string,
  password: string,
  firstName: string,
  lastName: string
): Promise<RegisterResult> {
  let response: Response;
  try {
    response = await fetch(`${AUTH_SERVICE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      }),
    });
  } catch {
    return { success: false, error: "RegistrationFailed" };
  }

  if (response.status === 201) return { success: true };
  if (response.status === 409) return { success: false, error: "DuplicateEmail" };
  return { success: false, error: "RegistrationFailed" };
}

function normaliseTokenResponse(data: AuthServiceTokenResponse): AuthTokens {
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    accessTokenExpires: Date.now() + data.expires_in * 1000,
  };
}
