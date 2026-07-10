"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function CustomerPortalButton() {
  const [loading, setLoading] = useState(false);

  async function openPortal() {
    setLoading(true);
    const response = await fetch("/api/billing/portal", { method: "POST" });
    const data = await response.json();
    setLoading(false);
    if (data.url) window.location.href = data.url;
    else alert(data.error ?? "No billing portal available yet.");
  }

  return <Button onClick={openPortal} disabled={loading}>{loading ? "Opening..." : "Manage billing"}</Button>;
}
