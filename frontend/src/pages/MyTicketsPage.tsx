import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { myTickets } from "../lib/resources";
import { formatDateTime } from "../lib/format";
import { Alert, Button, Card, Spinner, StatusChip } from "../components/ui";
import { TicketQr } from "../components/TicketQr";

export function MyTicketsPage() {
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data, error, isLoading } = useQuery({
    queryKey: ["tickets"],
    queryFn: () => myTickets(),
    // Auto-refetch so a PAID ticket flips created → valid without a manual reload.
    refetchInterval: 60_000,
  });

  if (isLoading) return <Spinner label="Loading tickets" />;
  if (error) return <Alert>Could not load your tickets.</Alert>;

  const tickets = data?.items ?? [];

  return (
    <section aria-labelledby="tickets-heading">
      <h1 id="tickets-heading" className="mb-6 text-2xl font-bold">
        My tickets
      </h1>

      {tickets.length === 0 ? (
        <p className="text-slate-500">
          You have no tickets yet.{" "}
          <Link to="/events" className="font-semibold text-brand-700 underline">
            Browse events
          </Link>
          .
        </p>
      ) : (
        <ul className="space-y-4">
          {tickets.map((ticket) => {
            const isOpen = expanded === ticket.id;
            const canShow = ticket.status === "valid";
            return (
              <li key={ticket.id}>
                <Card>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-mono text-sm text-slate-500">
                        #{ticket.id.slice(0, 8)}
                      </p>
                      <p className="mt-1 flex items-center gap-2">
                        <StatusChip status={ticket.status} />
                        {ticket.used_at && (
                          <span className="text-xs text-slate-400">
                            used {formatDateTime(ticket.used_at)}
                          </span>
                        )}
                      </p>
                    </div>
                    <Button
                      variant="secondary"
                      aria-expanded={isOpen}
                      aria-controls={`qr-${ticket.id}`}
                      disabled={!canShow}
                      onClick={() => setExpanded(isOpen ? null : ticket.id)}
                    >
                      {isOpen ? "Hide QR" : "Show QR"}
                    </Button>
                  </div>
                  {isOpen && (
                    <div id={`qr-${ticket.id}`} className="mt-4 flex justify-center">
                      <TicketQr ticketId={ticket.id} active={canShow} />
                    </div>
                  )}
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
