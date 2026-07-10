import { ProfileForm } from "@/components/settings/profile-form";
import { getCurrentProfile } from "@/lib/profile";
import { requireUser } from "@/lib/auth/session";
import { ExtensionTokens } from "@/components/settings/extension-tokens";

export default async function SettingsPage() {
  const { user } = await requireUser();
  const profile = await getCurrentProfile();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-slate-600">Manage your profile and account context.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <ProfileForm profile={profile} />
        <aside className="rounded-2xl border bg-white p-6 text-sm text-slate-600">
          <h2 className="font-semibold text-slate-950">Account</h2>
          <p className="mt-2">Signed in as {user.email}</p>
          <p className="mt-4">Sprint 10 stores profile data in a dedicated public.profiles table protected by RLS.</p>
        </aside>
      </div>
      <ExtensionTokens />
    </div>
  );
}
