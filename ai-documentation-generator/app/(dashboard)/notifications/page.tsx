import { NotificationList } from "@/components/notifications/notification-list";
import { listNotifications } from "@/lib/notifications/notifications";
import type { Notification } from "@/lib/types";

export default async function NotificationsPage() {
  const notifications = (await listNotifications(50)) as Notification[];
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Notifications</h1>
        <p className="text-slate-600">Operational updates for team actions, billing, and documents.</p>
      </div>
      <NotificationList notifications={notifications} />
    </div>
  );
}
