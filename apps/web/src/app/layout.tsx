import type { Metadata } from "next";
import { SessionControls } from "@/components/session-controls";
import "./styles.css";

export const metadata: Metadata = {
  title: "LVFI | Precificação",
  description: "Interface operacional da Linha de Valor Football Intelligence"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body><SessionControls />{children}</body></html>;
}
