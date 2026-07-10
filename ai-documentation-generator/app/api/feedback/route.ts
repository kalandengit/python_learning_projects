import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { z } from "zod";

const feedbackSchema = z.object({
  type: z.string().min(1).max(80).default("contact"),
  email: z.string().email(),
  company: z.string().max(160).optional().nullable(),
  message: z.string().min(5).max(5000)
});

export async function POST(request: Request) {
  const formData = await request.formData();
  const parsed = feedbackSchema.safeParse({
    type: formData.get("type") ?? "contact",
    email: formData.get("email"),
    company: formData.get("company"),
    message: formData.get("message")
  });

  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid feedback payload", details: parsed.error.flatten() }, { status: 400 });
  }

  const supabase = await createClient();
  const { error } = await supabase.from("feedback_submissions").insert({
    type: parsed.data.type,
    email: parsed.data.email,
    company: parsed.data.company,
    message: parsed.data.message
  });

  if (error) {
    return NextResponse.json({ error: "Could not save feedback" }, { status: 500 });
  }

  return NextResponse.redirect(new URL("/beta?submitted=true", request.url), 303);
}
