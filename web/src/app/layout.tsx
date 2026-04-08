import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SocialScope – Social Intelligence Dashboard",
  description: "Monitor social platform sentiment and trends",
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
