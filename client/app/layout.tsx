import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Socratic AI Tutor",
  description: "AI-powered Socratic video tutor with real-time avatar",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
