import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Syne } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "react-hot-toast";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Apulu Studio - Social Media Command Center",
  description: "All-in-one social media management for solopreneurs",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
    apple: "/apple-touch-icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${plusJakarta.variable} ${syne.variable} font-sans antialiased`}>
        <Providers>
          {children}
          <Toaster
            position="bottom-right"
            toastOptions={{
              className: "!rounded-xl !shadow-xl !border !border-gray-100 !text-sm",
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
