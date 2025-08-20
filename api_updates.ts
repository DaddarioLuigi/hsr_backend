// Nuove funzioni API per il flusso unificato

// Upload documento con flusso unificato (process_as_packet)
export async function uploadDocumentAsPacket(file: File, patientId?: string) {
  const formData = new FormData();
  formData.append("file", file);
  if (patientId) formData.append("patient_id", patientId);
  formData.append("process_as_packet", "true");

  const res = await fetch(`${BASE_URL}/api/upload-document`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  if (!res.ok) throw new Error("Errore upload documento come pacchetto");
  return res.json() as Promise<{
    filename: string;
    patient_id: string;
    status: "processing_as_packet";
    message: string;
  }>;
}

// Stato processing del pacchetto unificato
export async function fetchDocumentPacketStatus(patientId: string) {
  const res = await fetch(`${BASE_URL}/api/document-packet-status/${encodeURIComponent(patientId)}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Errore lettura stato pacchetto");
  return res.json() as Promise<{
    patient_id: string;
    status: "ocr_start" | "segmenting" | "processing_sections" | "completed" | "completed_with_errors" | "failed";
    message: string;
    progress: number;
    filename: string;
    sections_found: string[];
    sections_missing: string[];
    documents_created: Array<{
      document_id: string;
      document_type: string;
      filename: string;
      status: "processed";
      entities_count: number;
    }>;
    errors: string[];
  }>;
}

// Testo OCR estratto
export async function fetchDocumentOCRText(patientId: string) {
  const res = await fetch(`${BASE_URL}/api/document-ocr-text/${encodeURIComponent(patientId)}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Errore lettura testo OCR");
  return res.json() as Promise<{
    patient_id: string;
    filename: string;
    ocr_text: string;
    metadata: {
      original_filename: string;
      upload_date: string;
      content_type: string;
    };
  }>;
} 