import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return <main className="shell"><section className="panel login-panel" aria-labelledby="login-title"><p className="eyebrow">Administrador local</p><h1 id="login-title">Entrar no LVFI</h1><p>Use a credencial configurada localmente para acessar a aplicação.</p><LoginForm /></section></main>;
}
