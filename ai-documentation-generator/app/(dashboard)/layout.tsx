import { Sidebar } from "@/components/dashboard/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <div className="flex"><Sidebar /><main className="min-h-screen flex-1 p-6 md:p-10">{children}</main></div>;
}
