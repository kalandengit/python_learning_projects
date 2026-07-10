import { createHash, randomBytes } from "node:crypto";
import { createAdminClient } from "@/lib/supabase/admin";

export const EXTENSION_TOKEN_PREFIX = "adg_ext_";
export const DEFAULT_EXTENSION_SCOPES = ["capture:write", "projects:read", "jobs:read"] as const;

export function hashExtensionToken(token: string) {
  return createHash("sha256").update(token).digest("hex");
}

export function createExtensionTokenValue() {
  return `${EXTENSION_TOKEN_PREFIX}${randomBytes(32).toString("base64url")}`;
}

export type ExtensionPrincipal = {
  tokenId: string;
  userId: string;
  organizationId: string;
  scopes: string[];
};

export async function authenticateExtensionRequest(request: Request, requiredScope?: string): Promise<ExtensionPrincipal> {
  const authorization = request.headers.get("authorization") ?? "";
  const token = authorization.startsWith("Bearer ") ? authorization.slice(7).trim() : "";
  if (!token.startsWith(EXTENSION_TOKEN_PREFIX)) throw new Error("UNAUTHORIZED");

  const admin = createAdminClient();
  const { data, error } = await admin.from("extension_tokens")
    .select("id,user_id,organization_id,scopes,expires_at,revoked_at")
    .eq("token_hash", hashExtensionToken(token)).maybeSingle();
  if (error || !data || data.revoked_at || (data.expires_at && new Date(data.expires_at) <= new Date())) {
    throw new Error("UNAUTHORIZED");
  }
  const scopes = Array.isArray(data.scopes) ? data.scopes : [];
  if (requiredScope && !scopes.includes(requiredScope)) throw new Error("FORBIDDEN");
  await admin.from("extension_tokens").update({ last_used_at: new Date().toISOString() }).eq("id", data.id);
  return { tokenId: data.id, userId: data.user_id, organizationId: data.organization_id, scopes };
}

export function extensionErrorResponse(error: unknown) {
  const message = error instanceof Error ? error.message : "UNKNOWN";
  if (message === "UNAUTHORIZED") return Response.json({ error: "Invalid or expired extension token." }, { status: 401 });
  if (message === "FORBIDDEN") return Response.json({ error: "The token does not have the required scope." }, { status: 403 });
  console.error("Extension API error", error);
  return Response.json({ error: error instanceof Error ? error.message : "Unexpected server error." }, { status: 500 });
}
