import { MatchCenter } from "@/components/match-center";

export default async function MatchPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = await params;
  return <MatchCenter matchId={Number(matchId)} />;
}
