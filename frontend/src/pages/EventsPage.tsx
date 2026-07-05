import { useInfiniteQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listEvents } from "../lib/resources";
import { formatDateTime } from "../lib/format";
import { Alert, Button, Card, Spinner } from "../components/ui";

export function EventsPage() {
  const { data, error, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ["events"],
      queryFn: ({ pageParam }) => listEvents(pageParam),
      initialPageParam: undefined as string | undefined,
      getNextPageParam: (last) => last.next_cursor ?? undefined,
    });

  const events = data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <section aria-labelledby="events-heading">
      <h1 id="events-heading" className="mb-6 text-2xl font-bold">
        Upcoming events
      </h1>

      {isLoading && <Spinner label="Loading events" />}
      {error && <Alert>Could not load events. Please try again.</Alert>}

      {!isLoading && events.length === 0 && !error && (
        <p className="text-slate-500">No published events yet.</p>
      )}

      <ul className="grid gap-4 sm:grid-cols-2">
        {events.map((event) => (
          <li key={event.id}>
            <Card className="h-full">
              <article className="flex h-full flex-col">
                <h2 className="text-lg font-semibold">
                  <Link
                    to={`/events/${event.id}`}
                    className="text-brand-700 underline-offset-2 hover:underline"
                  >
                    {event.title}
                  </Link>
                </h2>
                <p className="mt-1 text-sm text-slate-500">{formatDateTime(event.starts_at)}</p>
                {event.venue_name && (
                  <p className="text-sm text-slate-500">{event.venue_name}</p>
                )}
                {event.description && (
                  <p className="mt-3 line-clamp-3 text-sm text-slate-600">{event.description}</p>
                )}
              </article>
            </Card>
          </li>
        ))}
      </ul>

      {hasNextPage && (
        <div className="mt-6 flex justify-center">
          <Button
            variant="secondary"
            onClick={() => void fetchNextPage()}
            disabled={isFetchingNextPage}
          >
            {isFetchingNextPage ? <Spinner label="Loading" /> : "Load more"}
          </Button>
        </div>
      )}
    </section>
  );
}
