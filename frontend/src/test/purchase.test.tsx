import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { EventDetailPage } from "../pages/EventDetailPage";
import { useAuthStore } from "../store/auth";
import * as resources from "../lib/resources";
import type { EventOut, PurchaseResponse, TierOut } from "../lib/schemas";

vi.mock("../lib/resources");

const navigateMock = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigateMock };
});

const EVENT: EventOut = {
  id: "evt-1",
  organization_id: "org-1",
  title: "PQC Summit",
  description: "A conference.",
  starts_at: "2026-09-01T10:00:00Z",
  ends_at: "2026-09-01T18:00:00Z",
  venue_name: "Paris Expo",
  latitude: null,
  longitude: null,
  geofence_radius_m: null,
  is_published: true,
  version: 1,
  created_at: "2026-07-01T10:00:00Z",
};

function tier(overrides: Partial<TierOut> = {}): TierOut {
  return {
    id: "tier-free",
    event_id: "evt-1",
    name: "General",
    price_cents: 0,
    currency: "eur",
    capacity: 100,
    sold_count: 0,
    sales_starts_at: null,
    sales_ends_at: null,
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/events/evt-1"]}>
        <Routes>
          <Route path="/events/:eventId" element={<EventDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("purchase flow", () => {
  beforeEach(() => {
    // Authenticated attendee so the Buy control renders.
    useAuthStore.setState({
      accessToken: "a.b.c",
      refreshToken: "r",
      claims: { userId: "u1", orgId: "org-1", role: "ATTENDEE", exp: 9_999_999_999 },
    });
    vi.mocked(resources.getEvent).mockResolvedValue(EVENT);
  });

  afterEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clear();
  });

  it("FREE tier: issues instantly and navigates to My Tickets (no Stripe)", async () => {
    vi.mocked(resources.listTiers).mockResolvedValue([tier()]);
    const freeResult: PurchaseResponse = {
      payment_id: "pay-1",
      payment_status: "succeeded",
      amount_cents: 0,
      currency: "eur",
      tickets: [
        { id: "t1", event_id: "evt-1", tier_id: "tier-free", status: "valid", created_at: "x", used_at: null },
      ],
      checkout_url: null,
      reused: false,
    };
    vi.mocked(resources.purchase).mockResolvedValue(freeResult);

    renderPage();
    const buy = await screen.findByRole("button", { name: /buy/i });
    await userEvent.click(buy);

    await waitFor(() => expect(resources.purchase).toHaveBeenCalledTimes(1));
    const [tierId, qty, key] = vi.mocked(resources.purchase).mock.calls[0]!;
    expect(tierId).toBe("tier-free");
    expect(qty).toBe(1);
    expect(key).toMatch(/[0-9a-f-]{36}/); // idempotency key present
    await waitFor(() => expect(navigateMock).toHaveBeenCalledWith("/tickets"));
  });

  it("PAID tier: redirects the browser to Stripe Checkout", async () => {
    vi.mocked(resources.listTiers).mockResolvedValue([
      tier({ id: "tier-paid", name: "VIP", price_cents: 2500 }),
    ]);
    const paidResult: PurchaseResponse = {
      payment_id: "pay-2",
      payment_status: "pending",
      amount_cents: 2500,
      currency: "eur",
      tickets: [
        { id: "t2", event_id: "evt-1", tier_id: "tier-paid", status: "created", created_at: "x", used_at: null },
      ],
      checkout_url: "https://checkout.stripe.test/pay/cs_123",
      reused: false,
    };
    vi.mocked(resources.purchase).mockResolvedValue(paidResult);

    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });

    renderPage();
    const buy = await screen.findByRole("button", { name: /buy/i });
    await userEvent.click(buy);

    await waitFor(() =>
      expect(assign).toHaveBeenCalledWith("https://checkout.stripe.test/pay/cs_123"),
    );
    expect(navigateMock).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("surfaces a sold-out error without navigating", async () => {
    vi.mocked(resources.listTiers).mockResolvedValue([
      tier({ sold_count: 100, capacity: 100 }),
    ]);
    renderPage();
    await screen.findByText(/sold out/i);
    // Buy is disabled when sold out.
    expect(screen.getByRole("button", { name: /buy/i })).toBeDisabled();
  });
});
