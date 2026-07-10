import Link from "next/link";
import { markAllNotificationsReadAction, markNotificationReadAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import type { Notification } from "@/lib/types";

export function NotificationList({ notifications }: { notifications: Notification[] }) {
  const unreadCount = notifications.filter((item) => !item.read_at).length;
  return (
    <div className="space-y-4">
      <form action={markAllNotificationsReadAction}>
        <Button type="submit" variant="secondary" disabled={unreadCount === 0}>Mark all read</Button>
      </form>
      <div className="space-y-3">
        {notifications.length === 0 ? <p className="rounded-2xl border bg-white p-6 text-slate-600">No notifications yet.</p> : null}
        {notifications.map((item) => (
          <article key={item.id} className="rounded-2xl border bg-white p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-semibold">{item.title}</p>
                <p className="mt-1 text-sm text-slate-600">{item.message}</p>
                {item.href ? <Link className="mt-2 inline-block text-sm font-medium text-slate-950 underline" href={item.href}>Open</Link> : null}
              </div>
              <div className="text-right text-xs text-slate-500">
                <p>{new Date(item.created_at).toLocaleString()}</p>
                {!item.read_at ? (
                  <form action={markNotificationReadAction} className="mt-2">
                    <input type="hidden" name="notification_id" value={item.id} />
                    <Button type="submit" variant="secondary">Mark read</Button>
                  </form>
                ) : <span className="mt-2 inline-block rounded-full bg-slate-100 px-2 py-1">Read</span>}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
