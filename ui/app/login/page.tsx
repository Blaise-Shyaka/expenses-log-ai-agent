"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginWithCredentials, type AuthActionState } from "@/lib/auth-client";

const initialState: AuthActionState = null;

export default function LoginPage() {
  const router = useRouter();

  async function loginAction(
    _prevState: AuthActionState,
    formData: FormData
  ): Promise<AuthActionState> {
    const result = await loginWithCredentials(
      formData.get("email") as string,
      formData.get("password") as string
    );
    if (result) return result;
    router.push("/");
    return null;
  }

  const [state, formAction, isPending] = useActionState(
    loginAction,
    initialState
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0a0a0a",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "var(--font-geist-sans)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          padding: "0 1.5rem",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <h1
            style={{
              fontSize: "1.125rem",
              fontWeight: 500,
              color: "#ffffff",
              marginBottom: "0.5rem",
              letterSpacing: "-0.01em",
            }}
          >
            Expense Tracker
          </h1>
          <p style={{ fontSize: "0.8125rem", color: "#6b7280" }}>
            Sign in to continue
          </p>
        </div>

        <div
          style={{
            backgroundColor: "#111111",
            border: "1px solid #1f1f1f",
            borderRadius: "12px",
            padding: "2rem",
          }}
        >
          <form action={formAction}>
            <div style={{ marginBottom: "1.25rem" }}>
              <label
                htmlFor="email"
                style={{
                  display: "block",
                  fontSize: "0.8125rem",
                  color: "#9ca3af",
                  marginBottom: "0.5rem",
                  fontWeight: 500,
                }}
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                style={{
                  width: "100%",
                  padding: "0.625rem 0.875rem",
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #2a2a2a",
                  borderRadius: "8px",
                  color: "#ffffff",
                  fontSize: "0.875rem",
                  outline: "none",
                  boxSizing: "border-box",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.border = "1px solid #404040";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.border = "1px solid #2a2a2a";
                }}
              />
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <label
                htmlFor="password"
                style={{
                  display: "block",
                  fontSize: "0.8125rem",
                  color: "#9ca3af",
                  marginBottom: "0.5rem",
                  fontWeight: 500,
                }}
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                autoComplete="current-password"
                style={{
                  width: "100%",
                  padding: "0.625rem 0.875rem",
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #2a2a2a",
                  borderRadius: "8px",
                  color: "#ffffff",
                  fontSize: "0.875rem",
                  outline: "none",
                  boxSizing: "border-box",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.border = "1px solid #404040";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.border = "1px solid #2a2a2a";
                }}
              />
            </div>

            {state?.error && (
              <div
                style={{
                  marginBottom: "1.25rem",
                  padding: "0.625rem 0.875rem",
                  backgroundColor: "#1f0a0a",
                  border: "1px solid #3a1010",
                  borderRadius: "8px",
                  fontSize: "0.8125rem",
                  color: "#f87171",
                }}
              >
                {state.error}
              </div>
            )}

            <button
              type="submit"
              disabled={isPending}
              style={{
                width: "100%",
                padding: "0.625rem",
                backgroundColor: isPending ? "#2a2a2a" : "#ffffff",
                color: isPending ? "#6b7280" : "#0a0a0a",
                border: "none",
                borderRadius: "8px",
                fontSize: "0.875rem",
                fontWeight: 500,
                cursor: isPending ? "not-allowed" : "pointer",
                transition: "background-color 0.15s ease",
                fontFamily: "var(--font-geist-sans)",
              }}
            >
              {isPending ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>

        <p
          style={{
            textAlign: "center",
            marginTop: "1.5rem",
            fontSize: "0.8125rem",
            color: "#6b7280",
          }}
        >
          No account?{" "}
          <Link
            href="/register"
            style={{ color: "#d1d5db", textDecoration: "none" }}
          >
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
