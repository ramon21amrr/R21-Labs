import { AnalysisWorkflow } from "@/components/analysis-workflow";
import { EffectiveConfigurationPanel } from "@/components/configuration-workspace";
import { PricingWorkspace } from "@/components/pricing-workspace";
import { StatisticsWorkspace } from "@/components/statistics-workspace";

export default async function MatchPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = await params;
  return <><PricingWorkspace matchId={Number(matchId)} /><AnalysisWorkflow matchId={Number(matchId)} /><StatisticsWorkspace matchId={Number(matchId)} /><EffectiveConfigurationPanel matchId={Number(matchId)} /></>;
}
