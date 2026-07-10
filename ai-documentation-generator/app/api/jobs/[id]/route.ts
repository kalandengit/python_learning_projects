import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase } = await requireUser();

  const { data, error } = await supabase
    .from("ai_jobs")
    .select("id,status,document_id,error_message,attempts,max_attempts,started_at,completed_at,created_at,updated_at")
    .eq("id", id)
    .single();

  if (error || !data) {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }

  return NextResponse.json({ job: data });
}
