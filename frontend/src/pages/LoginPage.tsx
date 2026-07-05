import { useState, type FormEvent } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { errorDetail } from "../lib/api";
import { loginPassword, loginPasskey, passkeysSupported, verifyTotp } from "../lib/auth-api";
import { Alert, Button, Card, Field, Spinner, TextInput } from "../components/ui";

type Stage = "credentials" | "totp";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/events";

  const [stage, setStage] = useState<Stage>("credentials");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function done() {
    navigate(from, { replace: true });
  }

  async function onPasskey() {
    setError(null);
    setBusy(true);
    try {
      await loginPasskey();
      done();
    } catch (err) {
      setError(await errorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  async function onPassword(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await loginPassword(email, password);
      if ("mfa_required" in res) {
        setMfaToken(res.mfa_token);
        setStage("totp");
      } else {
        done();
      }
    } catch (err) {
      setError(await errorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  async function onTotp(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await verifyTotp(code, mfaToken);
      done();
    } catch (err) {
      setError(await errorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-bold">Log in</h1>
      <Card>
        {error && (
          <div className="mb-4">
            <Alert>{error}</Alert>
          </div>
        )}

        {stage === "credentials" ? (
          <>
            {passkeysSupported() && (
              <div className="mb-5">
                <Button onClick={onPasskey} disabled={busy} className="w-full">
                  Continue with a passkey
                </Button>
                <div className="my-4 flex items-center gap-3 text-xs text-slate-400">
                  <span className="h-px flex-1 bg-slate-200" />
                  or use your password
                  <span className="h-px flex-1 bg-slate-200" />
                </div>
              </div>
            )}

            <form onSubmit={onPassword} className="flex flex-col gap-4" noValidate>
              <Field label="Email">
                {({ id, invalid }) => (
                  <TextInput
                    id={id}
                    type="email"
                    autoComplete="username webauthn"
                    required
                    value={email}
                    invalid={invalid}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                )}
              </Field>
              <Field label="Password">
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                )}
              </Field>
              <Button type="submit" disabled={busy}>
                {busy ? <Spinner label="Signing in" /> : "Log in"}
              </Button>
            </form>
          </>
        ) : (
          <form onSubmit={onTotp} className="flex flex-col gap-4" noValidate>
            <p className="text-sm text-slate-600">
              Enter the 6-digit code from your authenticator app.
            </p>
            <Field label="Authentication code">
              {({ id, invalid }) => (
                <TextInput
                  id={id}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]*"
                  maxLength={8}
                  required
                  autoFocus
                  value={code}
                  invalid={invalid}
                  onChange={(e) => setCode(e.target.value)}
                />
              )}
            </Field>
            <Button type="submit" disabled={busy}>
              {busy ? <Spinner label="Verifying" /> : "Verify"}
            </Button>
          </form>
        )}
      </Card>

      <p className="mt-4 text-center text-sm text-slate-600">
        No account?{" "}
        <Link to="/register" className="font-semibold text-brand-700 underline">
          Create one
        </Link>
      </p>
    </div>
  );
}
