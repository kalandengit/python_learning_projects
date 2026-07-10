import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="text-3xl font-bold">Create account</h1>
      <form action="/api/auth/signup" method="post" className="mt-8 space-y-4">
        <Input name="email" type="email" placeholder="Email" required />
        <Input name="password" type="password" placeholder="Password" minLength={8} required />
        <Button className="w-full" type="submit">Start free</Button>
      </form>
    </main>
  );
}
