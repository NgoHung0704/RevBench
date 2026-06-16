import type { Metadata } from "next";
import { Fraunces, Manrope, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
});
const sans = Manrope({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "RevBench — AI decision support for blue-chip stocks",
  description: "Multi-agent + ML signals fused into explainable recommendations. Not financial advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body className="font-sans">
        <div className="mx-auto flex min-h-screen max-w-content flex-col px-5 sm:px-8">
          <Nav />
          <main className="flex-1 pb-24">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}

function Nav() {
  return (
    <header className="sticky top-0 z-40 -mx-5 mb-2 border-b border-line/60 bg-ink/70 px-5 py-4 backdrop-blur-md sm:-mx-8 sm:px-8">
      <div className="flex items-center justify-between">
        <Link href="/" className="group flex items-center gap-3">
          <span className="grid h-8 w-8 place-items-center rounded-lg border border-gold/30 bg-gold/10 font-display text-gold">
            R
          </span>
          <span className="font-display text-lg tracking-tight text-text">
            Rev<span className="text-gold">Bench</span>
          </span>
        </Link>
        <nav className="hidden items-center gap-1 text-sm text-muted sm:flex">
          <Link href="/" className="rounded-lg px-3 py-1.5 transition hover:bg-surface-2/70 hover:text-text">
            Dashboard
          </Link>
          <Link href="/ticker/AAPL" className="rounded-lg px-3 py-1.5 transition hover:bg-surface-2/70 hover:text-text">
            Tickers
          </Link>
          <span className="chip ml-2 border-gold/25 bg-gold/5 text-gold">Research preview</span>
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-auto border-t border-line/60 py-6 text-xs text-faint">
      <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center">
        <p>
          <span className="font-medium text-muted">Not financial advice.</span> RevBench is a student
          research project (INSA Lyon 4IF). Signals are experimental and unvalidated.
        </p>
        <p className="tnum">batch-first · read-only · DeepSeek V4 + LightGBM</p>
      </div>
    </footer>
  );
}
