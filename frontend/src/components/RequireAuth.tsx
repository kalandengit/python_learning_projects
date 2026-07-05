import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import type { UserRole } from "../lib/schemas";

export function RequireAuth({ children, roles }: { children: ReactNode; roles?: UserRole[] }) {
  const claims = useAuthStore((s) => s.claims);
  const location = useLocation();

  if (!claims) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  if (roles && !roles.includes(claims.role)) {
    return <Navigate to="/events" replace />;
  }
  return <>{children}</>;
}
