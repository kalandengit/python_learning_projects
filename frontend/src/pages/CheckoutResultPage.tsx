import { Link } from "react-router-dom";
import { Alert, Button, Card } from "../components/ui";

export function CheckoutSuccessPage() {
  return (
    <div className="mx-auto max-w-md text-center">
      <Card>
        <Alert tone="success">Payment received — your tickets are being issued.</Alert>
        <p className="mt-4 text-sm text-slate-600">
          Tickets become valid the moment Stripe confirms the payment (usually a
          few seconds). They will appear under My Tickets.
        </p>
        <div className="mt-6">
          <Link to="/tickets">
            <Button>View my tickets</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}

export function CheckoutCancelPage() {
  return (
    <div className="mx-auto max-w-md text-center">
      <Card>
        <Alert tone="info">Checkout cancelled — you have not been charged.</Alert>
        <div className="mt-6">
          <Link to="/events">
            <Button variant="secondary">Back to events</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
