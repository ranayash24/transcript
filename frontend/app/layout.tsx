import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Video Scene Intelligence",
  description: "Upload videos and query their content with natural language",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen antialiased">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-emerald-500 flex items-center justify-center">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-white">
              <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
              <path
                clipRule="evenodd"
                fillRule="evenodd"
                d="M14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"
              />
            </svg>
          </div>
          <span className="font-semibold text-white tracking-tight">Video Scene Intelligence</span>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
