import type { Metadata } from "next";
import { Hanken_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { getCost, getUniverse } from "@/lib/api";
import { MotionProvider } from "@/components/fx/MotionProvider";
import { TopBar } from "@/components/TopBar";
import { Disclaimer } from "@/components/Disclaimer";

const sans = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700", "800"],
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "RevBench — AI decision support for blue-chip stocks",
  description:
    "Multi-agent + ML signals fused into explainable recommendations. Not financial advice.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Fetched once per request, server-side (the API is internal-only). The cost
  // meter + as-of stamp live in the global top bar; null degrades gracefully.
  const [universe, cost] = await Promise.all([getUniverse(), getCost()]);
  const asOf = universe?.[0]?.rec.asOf?.slice(0, 10) ?? null;

  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body className="min-h-screen pb-[60px] font-sans">
        <MotionProvider>
          <TopBar cost={cost} asOf={asOf} />
          <main>{children}</main>
        </MotionProvider>
        <Disclaimer />
      </body>
    </html>
  );
}
