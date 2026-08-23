import type { NextAuthOptions } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { login, refreshTokens } from "@/lib/auth-service-client";

// Refresh a bit before the access token actually expires, not after — the
// client schedules its own proactive refresh off accessTokenExpires (see
// components/session-refresh.tsx), but this buffer is what makes that
// scheduling meaningful: without it, a client trigger that lands a few
// seconds early would just get the same still-valid token back and
// contribute nothing.
const REFRESH_BUFFER_MS = 2 * 60 * 1000;

export const authOptions: NextAuthOptions = {
  secret: process.env.AUTH_SECRET,
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        if (!credentials?.email || !credentials?.password) return null;
        try {
          const tokens = await login(
            credentials.email as string,
            credentials.password as string
          );
          return {
            id: "authenticated",
            email: credentials.email as string,
            accessToken: tokens.accessToken,
            refreshToken: tokens.refreshToken,
            accessTokenExpires: tokens.accessTokenExpires,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user && "accessToken" in user) {
        return {
          ...token,
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
          accessTokenExpires: user.accessTokenExpires,
          error: undefined,
        };
      }

      const expires =
        typeof token.accessTokenExpires === "number"
          ? token.accessTokenExpires
          : undefined;

      if (expires !== undefined && Date.now() < expires - REFRESH_BUFFER_MS) {
        return token;
      }

      const refreshToken =
        typeof token.refreshToken === "string" ? token.refreshToken : undefined;

      if (!refreshToken) {
        return { ...token, error: "RefreshAccessTokenError" as const };
      }

      try {
        const tokens = await refreshTokens(refreshToken);
        return {
          ...token,
          accessToken: tokens.accessToken,
          refreshToken: tokens.refreshToken,
          accessTokenExpires: tokens.accessTokenExpires,
          error: undefined,
        };
      } catch {
        return { ...token, error: "RefreshAccessTokenError" as const };
      }
    },
    session: ({ session, token }) => ({
      ...session,
      accessToken: token.accessToken,
      accessTokenExpires:
        typeof token.accessTokenExpires === "number"
          ? token.accessTokenExpires
          : undefined,
      error: token.error,
    }),
  },
};
