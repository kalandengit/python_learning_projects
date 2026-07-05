import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { errorDetail } from "../lib/api";
import { register } from "../lib/auth-api";
import { Alert, Button, Card, Field, Spinner, TextInput } from "../components/ui";

export function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }
    setBusy(true);
    try {
      await register({
        email,
        password,
        ...(fullName ? { full_name: fullName } : {}),
        ...(orgName ? { organization_name: orgName } : {}),
        marketing_consent: consent,
      });
      navigate("/events", { replace: true });
    } catch (err) {
      setError(await errorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-bold">Create your account</h1>
      <Card>
        {error && (
          <div className="mb-4">
            <Alert>{error}</Alert>
          </div>
        )}
        <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
          <Field label="Full name">
            {({ id }) => (
              <TextInput
                id={id}
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            )}
          </Field>
          <Field label="Email">
            {({ id, invalid }) => (
              <TextInput
                id={id}
                type="email"
                autoComplete="email"
                required
                value={email}
                invalid={invalid}
                onChange={(e) => setEmail(e.target.value)}
              />
            )}
          </Field>
          <Field label="Password" hint="At least 12 characters.">
            {({ id, describedBy, invalid }) => (
              <TextInput
                id={id}
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                aria-describedby={describedBy}
                value={password}
                invalid={invalid}
                onChange={(e) => setPassword(e.target.value)}
              />
            )}
          </Field>
          <Field
            label="Organization name (optional)"
            hint="Provide this to register as an event organizer."
          >
            {({ id, describedBy }) => (
              <TextInput
                id={id}
                aria-describedby={describedBy}
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />
            )}
          </Field>
          <label className="flex items-start gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              className="mt-1"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <span>Send me occasional product updates (optional).</span>
          </label>
          <Button type="submit" disabled={busy}>
            {busy ? <Spinner label="Creating account" /> : "Create account"}
          </Button>
        </form>
      </Card>
      <p className="mt-4 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-brand-700 underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
