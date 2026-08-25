"use server";

import { register } from "@/lib/expenses-auth-client";

export type ActionState = { error: string } | null;

export async function registerAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;
  const firstName = formData.get("first_name") as string;
  const lastName = formData.get("last_name") as string;

  const result = await register(email, password, firstName, lastName);

  if (!result.success) {
    if (result.error === "DuplicateEmail") {
      return { error: "An account with this email already exists." };
    }
    return { error: "Registration failed. Please try again." };
  }

  return null;
}
