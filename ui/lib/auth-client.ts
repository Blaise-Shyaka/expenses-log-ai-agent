"use client";

import { signIn, signOut } from "next-auth/react";

export type AuthActionState = { error: string } | null;

export async function loginWithCredentials(
  email: string,
  password: string
): Promise<AuthActionState> {
  const result = await signIn("credentials", {
    email,
    password,
    redirect: false,
  });

  if (result?.error) {
    return { error: "Invalid email or password." };
  }
  return null;
}

export async function logout(): Promise<void> {
  await signOut({ callbackUrl: "/login" });
}
