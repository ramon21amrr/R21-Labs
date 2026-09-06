import Link from "next/link";

import { MatchBrowser } from "@/components/match-browser";

export default function HomePage() {
  return <main className="shell"><header className="app-header"><p className="eyebrow">Linha de Valor Football Intelligence</p><h1>Precificação histórica</h1><p>Selecione uma partida para consultar as amostras e executar o Método 1.</p><p><Link className="back-link" href="/administration">Abrir administração de dados →</Link></p></header><MatchBrowser /></main>;
}
