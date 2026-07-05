import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { Spinner } from "./components/ui";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { EventsPage } from "./pages/EventsPage";
import { EventDetailPage } from "./pages/EventDetailPage";
import { MyTicketsPage } from "./pages/MyTicketsPage";
import { CheckoutCancelPage, CheckoutSuccessPage } from "./pages/CheckoutResultPage";

// Role-gated features are code-split — attendees never download the organizer,
// badge-admin or scanner bundles.
const OrganizerWizardPage = lazy(() =>
  import("./pages/OrganizerWizardPage").then((m) => ({ default: m.OrganizerWizardPage })),
);
const BadgeAdminPage = lazy(() =>
  import("./pages/BadgeAdminPage").then((m) => ({ default: m.BadgeAdminPage })),
);
const ScannerPage = lazy(() =>
  import("./pages/ScannerPage").then((m) => ({ default: m.ScannerPage })),
);

const ORGANIZER = ["SUPER_ADMIN", "EVENT_ORGANIZER"] as const;
const SCANNER = ["SUPER_ADMIN", "BOX_OFFICE_STAFF", "SECURITY_GUARD"] as const;

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<Layout />}>
        <Route index element={<Navigate to="/events" replace />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="events/:eventId" element={<EventDetailPage />} />
        <Route path="checkout/success" element={<CheckoutSuccessPage />} />
        <Route path="checkout/cancel" element={<CheckoutCancelPage />} />

        <Route
          path="tickets"
          element={
            <RequireAuth>
              <MyTicketsPage />
            </RequireAuth>
          }
        />
        <Route
          path="organize"
          element={
            <RequireAuth roles={[...ORGANIZER]}>
              <Suspense fallback={<Spinner />}>
                <OrganizerWizardPage />
              </Suspense>
            </RequireAuth>
          }
        />
        <Route
          path="badges"
          element={
            <RequireAuth roles={[...ORGANIZER]}>
              <Suspense fallback={<Spinner />}>
                <BadgeAdminPage />
              </Suspense>
            </RequireAuth>
          }
        />
        <Route
          path="scanner"
          element={
            <RequireAuth roles={[...SCANNER]}>
              <Suspense fallback={<Spinner />}>
                <ScannerPage />
              </Suspense>
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/events" replace />} />
      </Route>
    </Routes>
  );
}
