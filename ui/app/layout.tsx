import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "@copilotkit/react-ui/v2/styles.css";
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
  title: "ExpenseLog | Assistant UI",
  description: "Log your expenses, categorize them, and get reports.",
};

// resizes-content makes Android shrink the page when the keyboard opens, so
// the 100dvh chat fits above it with the header still visible. Safari ignores
// it; page.tsx's keyboardHeight override covers iOS.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  interactiveWidget: "resizes-content",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable}`}
        // No CSS reset in this app — the default 8px margin makes the 100dvh
        // chat overflow the screen and the page scroll.
        style={{ margin: 0 }}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
