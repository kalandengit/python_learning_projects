import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import { createExtensionTokenValue, DEFAULT_EXTENSION_SCOPES, hashExtensionToken } from "@/lib/extension/tokens";

export async function GET() {
  const { supabase, user } = await requireUser();
  const { data, error } = await supabase.from("extension_tokens")
    .select("id,name,token_prefix,scopes,last_used_at,expires_at,revoked_at,created_at")
    .eq("user_id", user.id).order("created_at", { ascending: false });
  if (error) return Response.json({ error: error.message }, { status: 400 });
  return Response.json({ tokens: data ?? [] });
}

const schema = z.object({ name: z.string().trim().min(2).max(80).default("Chrome extension") });
export async function POST(request: Request) {
  const { supabase, user } = await requireUser();
  const parsed = schema.safeParse(await request.json().catch(() => ({})));
  if (!parsed.success) return Response.json({ error: parsed.error.issues[0]?.message }, { status: 400 });
  const org = await getOrCreateDefaultOrganization();
  const token = createExtensionTokenValue();
  const { data, error } = await supabase.from("extension_tokens").insert({
    organization_id: org.id, user_id: user.id, name: parsed.data.name,
    token_prefix: token.slice(0, 16), token_hash: hashExtensionToken(token), scopes: [...DEFAULT_EXTENSION_SCOPES]
  }).select("id,name,token_prefix,scopes,created_at").single();
  if (error) return Response.json({ error: error.message }, { status: 400 });
  return Response.json({ token, record: data }, { status: 201 });
}

export async function DELETE(request: Request) {
  const { supabase, user } = await requireUser();
  const id = new URL(request.url).searchParams.get("id");
  if (!id) return Response.json({ error: "Missing token id." }, { status: 400 });
  const { error } = await supabase.from("extension_tokens").update({ revoked_at: new Date().toISOString() }).eq("id", id).eq("user_id", user.id);
  if (error) return Response.json({ error: error.message }, { status: 400 });
  return Response.json({ ok: true });
}
