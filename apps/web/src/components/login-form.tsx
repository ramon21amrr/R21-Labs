"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, login } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(null);
    try {
      await login(password);
      setPassword("");
      router.replace("/");
      router.refresh();
    } catch (reason) {
      setPassword("");
      setError(reason instanceof ApiError ? "Não foi possível autenticar." : "Não foi possível autenticar.");
    } finally { setBusy(false); }
  }
  return <form className="filters" onSubmit={(event) => void submit(event)}><label>Senha<input aria-label="Senha" autoComplete="current-password" type="password" minLength={12} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} /></label>{error && <p className="status error" role="alert">{error}</p>}<button type="submit" disabled={busy}>{busy ? "Entrando…" : "Entrar"}</button></form>;
}
