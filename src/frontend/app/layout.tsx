import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mandate — African SME payables, verified",
  description: "Connect supplier invoice workflows to policy-controlled XRPL settlement and reconciliation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
