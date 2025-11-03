import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Adyai - AI Professor of Adyashanti's Teachings",
  description: "A RAG-powered chatbot for exploring Adyashanti's wisdom",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
