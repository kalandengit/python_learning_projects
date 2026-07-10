import { NextResponse } from "next/server";
import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { captureEvent } from "@/lib/analytics/events";

const schema = z.object({
  organizationId: z.string().uuid(),
  eventName: z.string().min(2).max(120),
  source: z.enum(["client", "server", "worker", "webhook"]).default("client"),
  properties: z.record(z.string(), z.union([z.string(), z.number(), z.boolean(), z.null()])).default({})
});

export async function POST(request: Request) {
  const { user } = await requireUser();
  const payload = schema.parse(await request.json());
  await captureEvent({
    organizationId: payload.organizationId,
    userId: user.id,
    eventName: payload.eventName,
    source: payload.source,
    properties: payload.properties
  });
  return NextResponse.json({ ok: true });
}
