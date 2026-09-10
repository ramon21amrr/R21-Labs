import { ConfigurationCatalogWorkspace } from "@/components/configuration-workspace";
import { OperationalDataWorkspace } from "@/components/operational-data-workspace";

export default function AdministrationPage() {
  return <><OperationalDataWorkspace /><ConfigurationCatalogWorkspace /></>;
}
