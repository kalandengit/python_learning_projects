import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { getEvent, listTiers, purchase } from "../lib/resources";
import { formatDateTime, formatMoney, newIdempotencyKey } from "../lib/format";
import { errorDetail } from "../lib/api";
import { useAuthStore } from "../store/auth";
import { queryClient } from "../lib/query";
import { Alert, Button, Card, Field, Spinner, TextInput } from "../components/ui";
import type { TierOut } from "../lib/schemas";

export function EventDetailPage() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const claims = useAuthStore((s) => s.claims);

  const eventQuery = useQuery({ queryKey: ["event", eventId], queryFn: () => getEvent(eventId) });
  const tiersQuery = useQuery({
    queryKey: ["event", eventId, "tiers"],
    queryFn: () => listTiers(eventId),
  });

  if (eventQuery.isLoading) return <Spinner label="Loading event" />;
  if (eventQuery.error || !eventQuery.data)
    return <Alert>Event not found or unavailable.</Alert>;

  const event = eventQuery.data;

  return (
    <article className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold">{event.title}</h1>
        <p className="mt-2 text-slate-600">
          {formatDateTime(event.starts_at)} — {formatDateTime(event.ends_at)}
        </p>
        {event.venue_name && <p className="text-slate-600">{event.venue_name}</p>}
      </header>

      {event.description && <p className="max-w-2xl text-slate-700">{event.description}</p>}

      <section aria-labelledby="tiers-heading" className="space-y-4">
        <h2 id="tiers-heading" className="text-xl font-semibold">
          Tickets
        </h2>
        {tiersQuery.isLoading && <Spinner label="Loading tickets" />}
        {tiersQuery.data?.length === 0 && (
          <p className="text-slate-500">Tickets are not on sale yet.</p>
        )}
        <ul className="space-y-3">
          {tiersQuery.data?.map((tier) => (
            <li key={tier.id}>
              <TierRow
                tier={tier}
                canBuy={Boolean(claims)}
                onNeedsLogin={() => navigate("/login", { state: { from: `/events/${eventId}` } })}
              />
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}

function TierRow({
  tier,
  canBuy,
  onNeedsLogin,
}: {
  tier: TierOut;
  canBuy: boolean;
  onNeedsLogin: () => void;
}) {
  const navigate = useNavigate();
  const [quantity, setQuantity] = useState(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const soldOut = tier.sold_count >= tier.capacity;
  const remaining = Math.max(tier.capacity - tier.sold_count, 0);

  const buy = useMutation({
    mutationFn: () => purchase(tier.id, quantity, newIdempotencyKey()),
    onMutate: () => setErrorMsg(null),
    onSuccess: (res) => {
      if (res.checkout_url) {
        // PAID → hand off to Stripe-hosted Checkout.
        window.location.assign(res.checkout_url);
      } else {
        // FREE → tickets are already valid.
        void queryClient.invalidateQueries({ queryKey: ["tickets"] });
        navigate("/tickets");
      }
    },
    onError: async (err) => setErrorMsg(await errorDetail(err)),
  });

  return (
    <Card>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h3 className="font-semibold">{tier.name}</h3>
          <p className="text-sm text-slate-600">{formatMoney(tier.price_cents, tier.currency)}</p>
          <p className="text-xs text-slate-400">
            {soldOut ? "Sold out" : `${remaining} remaining`}
          </p>
        </div>

        {!canBuy ? (
          <Button variant="secondary" onClick={onNeedsLogin}>
            Log in to buy
          </Button>
        ) : (
          <div className="flex items-end gap-3">
            <div className="w-24">
              <Field label="Qty">
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="number"
                    min={1}
                    max={Math.min(10, remaining || 1)}
                    value={quantity}
                    disabled={soldOut}
                    onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                  />
                )}
              </Field>
            </div>
            <Button onClick={() => buy.mutate()} disabled={soldOut || buy.isPending}>
              {buy.isPending ? <Spinner label="Processing" /> : "Buy"}
            </Button>
          </div>
        )}
      </div>
      {errorMsg && (
        <div className="mt-3">
          <Alert>{errorMsg}</Alert>
        </div>
      )}
    </Card>
  );
}
