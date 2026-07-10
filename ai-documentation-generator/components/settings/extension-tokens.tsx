"use client";
import { useEffect, useState } from "react";
type TokenRecord = { id:string; name:string; token_prefix:string; last_used_at:string|null; revoked_at:string|null; created_at:string };
export function ExtensionTokens() {
  const [tokens,setTokens]=useState<TokenRecord[]>([]); const [created,setCreated]=useState(""); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
  async function load(){ const r=await fetch("/api/extension/tokens"); const j=await r.json(); if(r.ok)setTokens(j.tokens); }
  useEffect(()=>{void load()},[]);
  async function create(){setBusy(true);setError("");setCreated(""); const r=await fetch("/api/extension/tokens",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({name:"Chrome extension"})}); const j=await r.json(); setBusy(false); if(!r.ok){setError(j.error);return;} setCreated(j.token); await load();}
  async function revoke(id:string){await fetch(`/api/extension/tokens?id=${id}`,{method:"DELETE"});await load();}
  return <section className="rounded-2xl border bg-white p-6 space-y-4"><div><h2 className="font-semibold text-slate-950">Browser extension access</h2><p className="text-sm text-slate-600">Generate a scoped token, then paste it into the extension. The full token is shown once.</p></div>
  <button onClick={create} disabled={busy} className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{busy?"Generating…":"Generate extension token"}</button>
  {error?<p className="text-sm text-red-700">{error}</p>:null}
  {created?<div className="rounded-xl bg-amber-50 p-4"><p className="text-sm font-medium">Copy this token now:</p><code className="mt-2 block break-all text-xs">{created}</code><button className="mt-2 text-sm underline" onClick={()=>navigator.clipboard.writeText(created)}>Copy token</button></div>:null}
  <div className="space-y-2">{tokens.map(t=><div key={t.id} className="flex items-center justify-between rounded-xl border p-3 text-sm"><div><p className="font-medium">{t.name}</p><p className="text-slate-500">{t.token_prefix}… · {t.revoked_at?"Revoked":t.last_used_at?`Last used ${new Date(t.last_used_at).toLocaleString()}`:"Never used"}</p></div>{!t.revoked_at?<button className="text-red-700 underline" onClick={()=>revoke(t.id)}>Revoke</button>:null}</div>)}</div></section>;
}
