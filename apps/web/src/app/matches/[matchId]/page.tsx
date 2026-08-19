import { PricingWorkspace } from "@/components/pricing-workspace";

export default async function MatchPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = await params;
  return <PricingWorkspace matchId={Number(matchId)} />;
}
