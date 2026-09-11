"use client";

import { type FormEvent, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { changePassword, logout } from "@/lib/api";

export function SessionControls() {
  const pathname = usePathname();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  if (pathname === "/login") return null;

  async function signOut() {
    setBusy(true);
    try { await logout(); } finally { router.replace("/login"); router.refresh(); setBusy(false); }
  }
  async function change(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setBusy(true); setMessage(null);
    try {
      await changePassword(String(values.get("current_password") ?? ""), String(values.get("new_password") ?? ""));
      event.currentTarget.reset(); setMessage("Senha alterada. As outras sessões foram invalidadas.");
    } catch { setMessage("Não foi possível alterar a senha."); } finally { setBusy(false); }
  }
  return <aside className="session-controls" aria-label="Sessão do administrador"><button type="button" className="secondary" onClick={() => setShowPassword((visible) => !visible)}>Senha</button><button type="button" className="secondary" onClick={() => void signOut()} disabled={busy}>Sair</button>{showPassword && <form className="filters" onSubmit={(event) => void change(event)}><label>Senha atual<input aria-label="Senha atual" name="current_password" type="password" autoComplete="current-password" required minLength={12} maxLength={128} /></label><label>Nova senha<input aria-label="Nova senha" name="new_password" type="password" autoComplete="new-password" required minLength={12} maxLength={128} /></label><button type="submit" disabled={busy}>Alterar senha</button>{message && <p className="status" role="status">{message}</p>}</form>}</aside>;
}
