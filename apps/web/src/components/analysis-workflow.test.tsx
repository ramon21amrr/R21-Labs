import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { approveAnalysis, calculateAnalysis, createAnalysis, createPdfArtifact, getAnalysis, getAnalysisSnapshot, listAnalyses, listPdfArtifacts, reviewAnalysis } from "@/lib/api";
import { AnalysisWorkflow } from "@/components/analysis-workflow";

vi.mock("@/lib/api", async (importOriginal) => ({ ...(await importOriginal<typeof import("@/lib/api")>()), approveAnalysis: vi.fn(), calculateAnalysis: vi.fn(), createAnalysis: vi.fn(), createPdfArtifact: vi.fn(), getAnalysis: vi.fn(), getAnalysisSnapshot: vi.fn(), listAnalyses: vi.fn(), listPdfArtifacts: vi.fn(), reviewAnalysis: vi.fn() }));

const analysisId = "00000000-0000-4000-8000-000000000001";
const executionId = "00000000-0000-4000-8000-000000000002";
const draft = { analysis_id: analysisId, match_id: 11, status: "draft" as const, created_at: "2026-09-10T00:00:00Z", events: [] };
const calculated = { ...draft, status: "calculated" as const, events: [{ event_id: 1, event_type: "calculated" as const, execution_id: executionId, actor: null, reason: null, created_at: "2026-09-10T00:01:00Z" }] };
const reviewed = { ...calculated, events: [...calculated.events, { event_id: 2, event_type: "reviewed" as const, execution_id: null, actor: "reviewer", reason: "evidence checked", created_at: "2026-09-10T00:02:00Z" }] };
const approved = { ...reviewed, status: "approved" as const, events: [...reviewed.events, { event_id: 3, event_type: "approved" as const, execution_id: null, actor: "approver", reason: "approved", created_at: "2026-09-10T00:03:00Z" }] };
const snapshot = { snapshot_id: "00000000-0000-4000-8000-000000000003", analysis_id: analysisId, payload: { execution: { execution_id: executionId }, warnings: ["public_warning"] }, snapshot_hash: "a".repeat(64), created_at: "2026-09-10T00:03:00Z" };
const artifact = { artifact_id: "00000000-0000-4000-8000-000000000004", snapshot_id: snapshot.snapshot_id, template_version: "lvfi-summary-1", sha256: "b".repeat(64), created_at: "2026-09-10T00:04:00Z" };

describe("AnalysisWorkflow", () => {
  beforeEach(() => { vi.mocked(listAnalyses).mockResolvedValue({ analyses: [] }); vi.mocked(listPdfArtifacts).mockResolvedValue({ artifacts: [] }); });
  afterEach(() => vi.restoreAllMocks());

  it("drives draft, calculation, review, approval and immutable snapshot through API DTOs", async () => {
    vi.mocked(createAnalysis).mockResolvedValue(draft);
    vi.mocked(calculateAnalysis).mockResolvedValue(calculated);
    vi.mocked(reviewAnalysis).mockResolvedValue(reviewed);
    vi.mocked(approveAnalysis).mockResolvedValue({ analysis: approved, snapshot });
    render(<AnalysisWorkflow matchId={11} />);
    await screen.findByText("Ainda não há análises para esta partida.");
    fireEvent.click(screen.getByRole("button", { name: "Criar rascunho" }));
    await waitFor(() => expect(createAnalysis).toHaveBeenCalledWith(11));
    fireEvent.change(screen.getByLabelText("Execution ID concluída"), { target: { value: executionId } });
    fireEvent.click(screen.getByRole("button", { name: "Vincular e calcular" }));
    await waitFor(() => expect(calculateAnalysis).toHaveBeenCalledWith(analysisId, executionId));
    fireEvent.change(screen.getByLabelText("Justificativa da revisão"), { target: { value: "evidence checked" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar revisão" }));
    await waitFor(() => expect(reviewAnalysis).toHaveBeenCalledWith(analysisId, { reason: "evidence checked" }));
    fireEvent.change(screen.getByLabelText("Justificativa da aprovação"), { target: { value: "approved" } });
    fireEvent.click(screen.getByRole("button", { name: "Aprovar e criar snapshot" }));
    await waitFor(() => expect(approveAnalysis).toHaveBeenCalledWith(analysisId, { reason: "approved" }));
    expect(await screen.findByRole("heading", { name: "Snapshot imutável" })).toBeTruthy();
    expect(screen.getByText("public_warning")).toBeTruthy();
    expect(screen.getByText("O payload, hash e evidências abaixo foram congelados pela API após a aprovação; o navegador não os recalcula.")).toBeTruthy();
  });

  it("loads an approved analysis and its persisted snapshot from history", async () => {
    vi.mocked(listAnalyses).mockResolvedValue({ analyses: [approved] });
    vi.mocked(getAnalysis).mockResolvedValue(approved);
    vi.mocked(getAnalysisSnapshot).mockResolvedValue(snapshot);
    vi.mocked(listPdfArtifacts).mockResolvedValue({ artifacts: [artifact] });
    render(<AnalysisWorkflow matchId={11} />);
    fireEvent.click(await screen.findByRole("button", { name: "Consultar" }));
    await waitFor(() => expect(getAnalysis).toHaveBeenCalledWith(analysisId));
    await waitFor(() => expect(getAnalysisSnapshot).toHaveBeenCalledWith(analysisId));
    expect(await screen.findByText(snapshot.snapshot_hash)).toBeTruthy();
    expect(await screen.findByText(artifact.sha256)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Baixar PDF" }).getAttribute("href")).toBe(`/api/analysis-pdfs/${artifact.artifact_id}/download`);
  });

  it("asks the API to generate a PDF only from the loaded approved snapshot", async () => {
    vi.mocked(getAnalysis).mockResolvedValue(approved);
    vi.mocked(getAnalysisSnapshot).mockResolvedValue(snapshot);
    vi.mocked(createPdfArtifact).mockResolvedValue(artifact);
    vi.mocked(listAnalyses).mockResolvedValue({ analyses: [approved] });
    vi.mocked(listPdfArtifacts).mockResolvedValueOnce({ artifacts: [] }).mockResolvedValueOnce({ artifacts: [artifact] });
    render(<AnalysisWorkflow matchId={11} />);
    fireEvent.click(await screen.findByRole("button", { name: "Consultar" }));
    await screen.findByRole("button", { name: "Gerar PDF-resumo" });
    fireEvent.click(screen.getByRole("button", { name: "Gerar PDF-resumo" }));
    await waitFor(() => expect(createPdfArtifact).toHaveBeenCalledWith(snapshot.snapshot_id));
    expect(await screen.findByText(artifact.sha256)).toBeTruthy();
  });
});
