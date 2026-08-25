import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "@copilotkit/react-ui/v2/styles.css";
import { getServerSession } from "next-auth";
import { authOptions } from "@/auth";
import { Providers } from "@/components/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Expense Tracker | Assistant UI",
  description: "Log your expenses, categorize them, and get reports.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getServerSession(authOptions);

  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <Providers session={session}>{children}</Providers>
      </body>
    </html>
  );
}
