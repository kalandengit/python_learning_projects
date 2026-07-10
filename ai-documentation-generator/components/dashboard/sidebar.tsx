import Link from "next/link";
import { BarChart3, Bell, CreditCard, FileText, FolderKanban, Home, Settings, Shield, Upload, Images, Users, Rocket } from "lucide-react";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/onboarding", label: "Onboarding", icon: Rocket },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/uploads", label: "Uploads", icon: Images },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/team", label: "Team", icon: Users, Rocket },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/billing", label: "Billing", icon: CreditCard },
  { href: "/admin", label: "Admin", icon: Shield }
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 border-r bg-white p-6 md:block">
      <Link href="/" className="text-lg font-bold">DocuPilot AI</Link>
      <nav className="mt-8 space-y-2">
        {items.map((item) => (
          <Link key={item.href} href={item.href} className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm hover:bg-slate-100">
            <item.icon className="h-4 w-4" /> {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
