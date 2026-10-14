import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: DefaultSession["user"];
    accessToken?: string;
    /** Absolute expiry timestamp in milliseconds — lets the client schedule a refresh ahead of expiry instead of reacting to it. */
    accessTokenExpires?: number;
    error?: "RefreshAccessTokenError";
  }

  interface User {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: "RefreshAccessTokenError";
  }
}
