import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";

// A minimal JWT with a decodable payload so the store can derive claims.
function fakeJwt(sub: string): string {
  const header = btoa(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const payload = btoa(
    JSON.stringify({ sub, org: "org-1", role: "ATTENDEE", exp: 9_999_999_999 }),
  );
  return `${header}.${payload}.sig`;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client refresh-rotation", () => {
  beforeEach(() => {
    useAuthStore.getState().setTokens(fakeJwt("user-1"), "refresh-old");
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clear();
    localStorage.clear();
  });

  it("refreshes on 401, rotates the refresh token, and retries once", async () => {
    let refreshCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
      const req = input as Request;
      const url = req.url;
      const auth = req.headers.get("Authorization");
      if (url.endsWith("/auth/refresh")) {
        refreshCalls += 1;
        return jsonResponse({
          access_token: fakeJwt("user-1"),
          refresh_token: "refresh-new",
          token_type: "bearer",
          expires_in: 900,
        });
      }
      // Protected resource: 401 until presented with the refreshed access token.
      if (auth === "Bearer refresh-old") return jsonResponse({ detail: "x" }, 401);
      if (auth?.startsWith("Bearer ")) return jsonResponse({ items: [], next_cursor: null });
      return jsonResponse({ detail: "no auth" }, 401);
    });
    vi.stubGlobal("fetch", fetchMock);

    // The explicit stale bearer makes the mock's 401 branch deterministic; the
    // interceptor should refresh, rotate, and replay with the new access token.
    const result = await api
      .get("tickets/mine", { headers: { Authorization: "Bearer refresh-old" } })
      .json();

    expect(result).toEqual({ items: [], next_cursor: null });
    expect(refreshCalls).toBe(1);
    // Refresh token rotated in the store.
    expect(useAuthStore.getState().refreshToken).toBe("refresh-new");
  });

  it("logs out when the refresh call fails (reuse/expiry)", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
      const req = input as Request;
      if (req.url.endsWith("/auth/refresh")) return jsonResponse({ detail: "reuse" }, 401);
      return jsonResponse({ detail: "unauthorized" }, 401);
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      api.get("tickets/mine", { headers: { Authorization: "Bearer refresh-old" } }).json(),
    ).rejects.toThrow();

    // Failed refresh clears the session so the router can redirect to login.
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().refreshToken).toBeNull();
  });

  it("coalesces concurrent 401s into a single refresh (single-flight)", async () => {
    let refreshCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
      const req = input as Request;
      const auth = req.headers.get("Authorization");
      if (req.url.endsWith("/auth/refresh")) {
        refreshCalls += 1;
        await new Promise((r) => setTimeout(r, 10));
        return jsonResponse({
          access_token: fakeJwt("user-1"),
          refresh_token: `refresh-${refreshCalls}`,
          token_type: "bearer",
          expires_in: 900,
        });
      }
      if (auth === "Bearer refresh-old") return jsonResponse({ detail: "x" }, 401);
      return jsonResponse({ ok: true });
    });
    vi.stubGlobal("fetch", fetchMock);

    const opts = { headers: { Authorization: "Bearer refresh-old" } } as const;
    const [a, b] = await Promise.all([
      api.get("tickets/mine", opts).json(),
      api.get("badges", opts).json(),
    ]);

    expect(a).toEqual({ ok: true });
    expect(b).toEqual({ ok: true });
    expect(refreshCalls).toBe(1); // both waited on one refresh
  });
});
