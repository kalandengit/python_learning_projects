import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase } = await requireUser();
  const { data, error } = await supabase
    .from("ai_jobs")
    .select("id,status,provider,model,total_tokens,estimated_cost_usd,error_message,document_id,created_at,started_at,completed_at")
    .eq("id", id)
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 404 });
  return NextResponse.json({ job: data });
}
