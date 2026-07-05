import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { logout } from "../lib/auth-api";
import { Button } from "./ui";

const ORGANIZER_ROLES = new Set(["SUPER_ADMIN", "EVENT_ORGANIZER"]);
const SCANNER_ROLES = new Set(["SUPER_ADMIN", "BOX_OFFICE_STAFF", "SECURITY_GUARD"]);

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "rounded-lg px-3 py-2 text-sm font-medium",
    isActive ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100",
  ].join(" ");
}

export function Layout() {
  const claims = useAuthStore((s) => s.claims);
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="min-h-full">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>
      <header className="border-b border-slate-200 bg-white">
        <nav aria-label="Primary" className="mx-auto flex max-w-5xl items-center gap-1 px-4 py-3">
          <NavLink to="/" className="mr-2 text-lg font-bold text-brand-700">
            EMS
          </NavLink>
          <NavLink to="/events" className={navClass}>
            Events
          </NavLink>
          {claims && (
            <NavLink to="/tickets" className={navClass}>
              My Tickets
            </NavLink>
          )}
          {claims && ORGANIZER_ROLES.has(claims.role) && (
            <>
              <NavLink to="/organize" className={navClass}>
                Create Event
              </NavLink>
              <NavLink to="/badges" className={navClass}>
                Badges
              </NavLink>
            </>
          )}
          {claims && SCANNER_ROLES.has(claims.role) && (
            <NavLink to="/scanner" className={navClass}>
              Scanner
            </NavLink>
          )}
          <div className="ml-auto flex items-center gap-2">
            {claims ? (
              <Button variant="secondary" onClick={onLogout}>
                Log out
              </Button>
            ) : (
              <NavLink to="/login" className={navClass}>
                Log in
              </NavLink>
            )}
          </div>
        </nav>
      </header>
      <main id="main" className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
