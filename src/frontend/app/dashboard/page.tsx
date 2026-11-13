import { redirect } from "next/navigation";
import { hasValidSession } from "@/app/lib/session";
import { DashboardShell } from "@/app/components/DashboardShell";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  if (!(await hasValidSession())) redirect("/login");
  return <DashboardShell />;
}
