import { updateProfileAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Props = {
  profile: {
    full_name: string | null;
    job_title: string | null;
    timezone: string | null;
  };
};

/** Simple server-action profile form. Later this can become a client form with optimistic save. */
export function ProfileForm({ profile }: Props) {
  return (
    <form action={updateProfileAction} className="space-y-4 rounded-2xl border bg-white p-6">
      <div>
        <label className="text-sm font-medium">Full name</label>
        <Input name="full_name" defaultValue={profile.full_name ?? ""} placeholder="Jane Smith" />
      </div>
      <div>
        <label className="text-sm font-medium">Job title</label>
        <Input name="job_title" defaultValue={profile.job_title ?? ""} placeholder="Product Manager" />
      </div>
      <div>
        <label className="text-sm font-medium">Timezone</label>
        <Input name="timezone" defaultValue={profile.timezone ?? "UTC"} placeholder="Europe/Paris" />
      </div>
      <Button type="submit">Save profile</Button>
    </form>
  );
}
