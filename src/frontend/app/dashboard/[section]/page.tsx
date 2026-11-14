import { notFound, redirect } from "next/navigation";
import { hasValidSession } from "@/app/lib/session";
import { DashboardShell } from "@/app/components/DashboardShell";

export const dynamic = "force-dynamic";

const sections = new Set(["payments", "suppliers", "policy", "audit"]);

export default async function DashboardSectionPage({ params }: { params: Promise<{ section: string }> }) {
  if (!(await hasValidSession())) redirect("/login");
  const { section } = await params;
  if (!sections.has(section)) notFound();
  return <DashboardShell />;
}
