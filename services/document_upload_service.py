"""
Document Upload Service
Gestisce la logica di business per l'upload e processing dei documenti.
"""

import os
import io
import json
import logging
import pdfplumber
from typing import Optional, Dict, Any
from werkzeug.datastructures import FileStorage

from services.document_type_detector import DocumentTypeDetector
from controller.controller import DocumentController

logger = logging.getLogger(__name__)


class DocumentUploadResult:
    """Risultato dell'upload di un documento."""
    
    def __init__(
        self,
        success: bool,
        document_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        document_type: Optional[str] = None,
        filename: Optional[str] = None,
        error: Optional[str] = None,
        status: str = "processing"
    ):
        self.success = success
        self.document_id = document_id
        self.patient_id = patient_id
        self.document_type = document_type
        self.filename = filename
        self.error = error
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il risultato in un dizionario per la risposta JSON."""
        if self.success:
            return {
                "document_id": self.document_id,
                "patient_id": self.patient_id,
                "document_type": self.document_type,
                "filename": self.filename,
                "status": self.status
            }
        else:
            return {
                "filename": self.filename,
                "error": self.error
            }


class DocumentUploadService:
    """
    Servizio per gestire l'upload e il processing dei documenti.
    """
    
    def __init__(self, controller: DocumentController, upload_folder: str):
        self.controller = controller
        self.upload_folder = upload_folder
        self.type_detector = DocumentTypeDetector()
    
    def process_upload(
        self,
        file: FileStorage,
        patient_id: Optional[str] = None
    ) -> DocumentUploadResult:
        """
        Processa l'upload di un singolo documento.
        
        Args:
            file: File da processare
            patient_id: ID paziente (opzionale per lettera_dimissione)
            
        Returns:
            DocumentUploadResult con il risultato dell'operazione
        """
        filename = file.filename
        
        # Determina il tipo di documento
        document_type = self.type_detector.detect(filename)
        logger.debug(f"Tipo documento rilevato: {document_type} per file {filename}")
        
        # Leggi PDF in memoria
        file.stream.seek(0)
        file_bytes = file.read()
        file.stream.seek(0)
        
        # Estrai testo per eventuale estrazione LLM
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            logger.debug(f"Testo estratto, lunghezza: {len(text)}")
        except Exception as e:
            logger.error(f"Errore estrazione testo da PDF {filename}: {e}")
            return DocumentUploadResult(
                success=False,
                filename=filename,
                error=f"Errore lettura PDF: {str(e)}"
            )
        
        # Determina patient_id_final
        patient_id_final = self._determine_patient_id(
            document_type=document_type,
            patient_id=patient_id,
            text=text,
            filename=filename
        )
        
        if not patient_id_final:
            return DocumentUploadResult(
                success=False,
                filename=filename,
                error="Non è stato possibile determinare il patient_id"
            )
        
        # Verifica se esiste già un documento dello stesso tipo
        patient_folder = os.path.join(self.upload_folder, patient_id_final, document_type)
        if os.path.isdir(patient_folder):
            existing_pdfs = [f for f in os.listdir(patient_folder) if f.lower().endswith(".pdf")]
            if existing_pdfs:
                return DocumentUploadResult(
                    success=False,
                    filename=filename,
                    error=f"Esiste già un documento di tipo '{document_type}' per il paziente {patient_id_final}"
                )
        
        # Salva il file su disco
        try:
            filepath, _ = self.controller.file_manager.save_file(
                patient_id_final,
                document_type,
                filename,
                file
            )
            logger.info(f"File salvato in: {filepath}")
        except Exception as e:
            logger.error(f"Errore salvataggio file {filename}: {e}")
            return DocumentUploadResult(
                success=False,
                filename=filename,
                error=f"Errore salvataggio file: {str(e)}"
            )
        
        # Leggi anagrafica esistente se disponibile
        provided_anagraphic = None
        if document_type != "lettera_dimissione":
            provided_anagraphic = self.controller.file_manager.read_existing_entities(
                patient_id_final, "lettera_dimissione"
            )
        
        # Avvia processing in background
        from threading import Thread
        
        def process_with_error_logging():
            try:
                self.controller.process_document_and_entities(
                    filepath, patient_id_final, document_type, provided_anagraphic
                )
            except Exception as e:
                logger.exception(f"Errore critico nel processing di {filename}: {e}")
        
        Thread(target=process_with_error_logging, daemon=True).start()
        
        # Costruisci document_id
        file_noext = os.path.splitext(filename)[0]
        document_id = f"doc_{patient_id_final}_{document_type}_{file_noext}"
        
        return DocumentUploadResult(
            success=True,
            document_id=document_id,
            patient_id=patient_id_final,
            document_type=document_type,
            filename=filename,
            status="processing"
        )
    
    def _determine_patient_id(
        self,
        document_type: str,
        patient_id: Optional[str],
        text: str,
        filename: str
    ) -> Optional[str]:
        """
        Determina il patient_id finale per il documento.
        
        Returns:
            patient_id finale o None se non determinabile
        """
        # Per lettera_dimissione: estrai da LLM se necessario
        if document_type == "lettera_dimissione":
            if patient_id:
                return str(patient_id)
            
            # Tenta estrazione LLM per n_cartella
            try:
                response_str = self.controller.llm.get_response_from_document(
                    text, document_type, model=self.controller.model_name
                )
                extracted_json = json.loads(response_str)
                extracted_id = extracted_json.get("n_cartella")
                
                if extracted_id:
                    return str(extracted_id)
                else:
                    logger.warning(f"Nessun n_cartella trovato in {filename}")
                    return None
            except Exception as e:
                logger.error(f"Errore estrazione patient_id da LLM per {filename}: {e}")
                return None
        else:
            # Per altri tipi di documento, patient_id è obbligatorio
            if not patient_id:
                logger.warning(f"patient_id obbligatorio per tipo {document_type}")
                return None
            return str(patient_id)

