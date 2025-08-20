"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { 
  uploadPacketOCR, 
  uploadDocumentAsPacket,
  fetchPatients, 
  fetchPacketStatus,
  fetchDocumentPacketStatus,
  fetchDocumentOCRText
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { Upload, FileText, AlertCircle, Eye, Info } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function UploadPacketPage() {
  const router = useRouter();
  const search = useSearchParams();
  const prefillPatientId = search.get("patient_id") ?? "";

  const [patientId, setPatientId] = useState(prefillPatientId);
  const [file, setFile] = useState<File | null>(null);
  const [useUnifiedFlow, setUseUnifiedFlow] = useState(false); // Nuovo: flusso unificato
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [pendingId, setPendingId] = useState<string | null>(null);
  const [percent, setPercent] = useState<number>(0);
  const [stage, setStage] = useState<string>("idle");
  const [message, setMessage] = useState<string>("");
  const [sectionsFound, setSectionsFound] = useState<string[]>([]);
  const [sectionsMissing, setSectionsMissing] = useState<string[]>([]);
  const [documentsCreated, setDocumentsCreated] = useState<any[]>([]);
  const [showOCRText, setShowOCRText] = useState(false);
  const [ocrText, setOcrText] = useState<string>("");
  
  const pollTimer = useRef<any>(null);

  const [patients, setPatients] = useState<{ id: string; name: string }[]>([]);
  useEffect(() => {
    fetchPatients().then((list: any[]) => {
      setPatients(list.map((p: any) => ({ id: p.id, name: p.name })));
    }).catch(() => {});
  }, []);

  function stageLabel(s: string) {
    switch (s) {
      case "upload_ok": return "Upload completato";
      case "ocr_start": return "OCR in esecuzione";
      case "ocr_done": return "OCR completato";
      case "segmenting": return "Segmentazione documenti";
      case "segmented": return "Sezioni individuate";
      case "extracting": return "Estrazione entità";
      case "processing_sections": return "Elaborazione sezioni";
      case "consolidating": return "Consolidamento dati";
      case "completed": return "Completato";
      case "completed_with_errors": return "Completato con errori";
      case "failed": return "Errore";
      default: return "In attesa…";
    }
  }

  // Polling per il flusso originale
  async function startPollingOriginal(id: string) {
    if (pollTimer.current) clearInterval(pollTimer.current);
    pollTimer.current = setInterval(async () => {
      try {
        const s = await fetchPacketStatus(id);
        setPercent(s.percent ?? 0);
        setStage(s.stage ?? "unknown");
        setMessage(s.message ?? "");
        if (s.stage === "completed") {
          clearInterval(pollTimer.current);
          const pid = s.final_patient_id || patientId || id;
          setPercent(100);
          router.push(`/patient/${pid}?msg=estrazione_completata`);
        } else if (s.stage === "failed") {
          clearInterval(pollTimer.current);
          setError(s.message || "Elaborazione fallita");
        }
      } catch {
        // ignora errori temporanei
      }
    }, 1500);
  }

  // Polling per il flusso unificato
  async function startPollingUnified(patientId: string) {
    if (pollTimer.current) clearInterval(pollTimer.current);
    pollTimer.current = setInterval(async () => {
      try {
        const s = await fetchDocumentPacketStatus(patientId);
        setPercent(s.progress ?? 0);
        setStage(s.status ?? "unknown");
        setMessage(s.message ?? "");
        setSectionsFound(s.sections_found ?? []);
        setSectionsMissing(s.sections_missing ?? []);
        setDocumentsCreated(s.documents_created ?? []);
        
        if (s.status === "completed" || s.status === "completed_with_errors") {
          clearInterval(pollTimer.current);
          setPercent(100);
          // Non redirect automatico, mostra risultati
        } else if (s.status === "failed") {
          clearInterval(pollTimer.current);
          setError(s.message || "Elaborazione fallita");
        }
      } catch {
        // ignora errori temporanei
      }
    }, 2000);
  }

  useEffect(() => () => pollTimer.current && clearInterval(pollTimer.current), []);

  async function handleSubmit() {
    setError(null);
    if (!file) return setError("Seleziona un PDF della cartella clinica");
    if (!file.name.toLowerCase().endsWith(".pdf")) return setError("Il file deve essere un PDF");

    setSubmitting(true);
    try {
      if (useUnifiedFlow) {
        // Nuovo flusso unificato
        const resp = await uploadDocumentAsPacket(file, patientId || undefined);
        const id = resp.patient_id;
        setPendingId(id);
        setStage("ocr_start");
        setMessage("File caricato, elaborazione avviata…");
        setPercent(5);
        await startPollingUnified(id);
      } else {
        // Flusso originale
        const resp = await uploadPacketOCR(file, patientId || undefined);
        const id = resp.pending_id || patientId || "_unknown";
        setPendingId(id);
        setStage("upload_ok");
        setMessage("File caricato, elaborazione avviata…");
        setPercent(5);
        await startPollingOriginal(id);
      }
    } catch (e: any) {
      setError(e.message || "Errore durante l'upload");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleViewOCRText() {
    if (!pendingId) return;
    try {
      const ocrData = await fetchDocumentOCRText(pendingId);
      setOcrText(ocrData.ocr_text);
      setShowOCRText(true);
    } catch (e: any) {
      setError("Errore nel recupero del testo OCR");
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Carica Cartella Clinica
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Selezione flusso */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="unifiedFlow"
                checked={useUnifiedFlow}
                onCheckedChange={(checked) => setUseUnifiedFlow(checked as boolean)}
                disabled={!!pendingId}
              />
              <Label htmlFor="unifiedFlow" className="text-sm font-medium">
                Tratta come pacchetto clinico completo (nuovo flusso)
              </Label>
            </div>
            {useUnifiedFlow && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Ogni sezione identificata verrà gestita come documento indipendente nella dashboard.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="patientId">ID Paziente (opzionale)</Label>
            <Input
              id="patientId"
              placeholder="Es. 2025-0001 (oppure lascia vuoto)"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              disabled={!!pendingId}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="file">PDF della cartella clinica</Label>
            <Input
              id="file"
              type="file"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              disabled={!!pendingId}
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" /> {error}
            </div>
          )}

          <div className="flex gap-3">
            <Button disabled={submitting || !!pendingId} onClick={handleSubmit}>
              <Upload className="h-4 w-4 mr-2" />
              {useUnifiedFlow ? "Avvia Elaborazione Unificata" : "Avvia OCR & Estrazione"}
            </Button>
            <Button variant="outline" onClick={() => router.back()} disabled={submitting}>
              Annulla
            </Button>
          </div>

          {/* Progress e stato */}
          {!!pendingId && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                {stageLabel(stage)} — {message}
              </div>
              <Progress value={percent} />
              <div className="text-xs text-muted-foreground">{percent}%</div>
              
              {/* Sezioni trovate/mancanti (solo per flusso unificato) */}
              {useUnifiedFlow && (sectionsFound.length > 0 || sectionsMissing.length > 0) && (
                <div className="space-y-2">
                  {sectionsFound.length > 0 && (
                    <div className="text-sm">
                      <span className="font-medium text-green-600">Sezioni trovate:</span> {sectionsFound.join(", ")}
                    </div>
                  )}
                  {sectionsMissing.length > 0 && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <span className="font-medium">Sezioni mancanti:</span> {sectionsMissing.join(", ")}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Documenti creati (solo per flusso unificato) */}
              {useUnifiedFlow && documentsCreated.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">Documenti creati:</div>
                  <div className="space-y-1">
                    {documentsCreated.map((doc, idx) => (
                      <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                        {doc.document_type}: {doc.filename} ({doc.entities_count} entità)
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Pulsanti azioni (solo per flusso unificato completato) */}
              {useUnifiedFlow && (stage === "completed" || stage === "completed_with_errors") && (
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleViewOCRText}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Visualizza Testo OCR
                  </Button>
                  <Button 
                    size="sm"
                    onClick={() => router.push(`/patient/${pendingId}`)}
                  >
                    Vai alla Dashboard
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal per testo OCR */}
      {showOCRText && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Testo OCR Estratto</h3>
              <Button variant="outline" size="sm" onClick={() => setShowOCRText(false)}>
                Chiudi
              </Button>
            </div>
            <div className="flex-1 overflow-auto">
              <pre className="text-sm whitespace-pre-wrap">{ocrText}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 