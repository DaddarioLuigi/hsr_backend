#!/usr/bin/env python3
"""
Test script per verificare il nuovo flusso unificato di upload documenti.
Questo script simula l'upload di un documento con process_as_packet=true.
"""

import requests
import json
import time
import os

# Configurazione
BASE_URL = "http://localhost:5000"
TEST_PDF_PATH = "test_document.pdf"  # Sostituisci con il percorso di un PDF di test

def test_unified_flow():
    """Test del flusso unificato di upload documento come pacchetto clinico."""
    
    print("=== Test Flusso Unificato Upload Documento ===")
    
    # 1. Upload del documento con process_as_packet=true
    print("\n1. Upload documento come pacchetto clinico...")
    
    if not os.path.exists(TEST_PDF_PATH):
        print(f"❌ File di test non trovato: {TEST_PDF_PATH}")
        print("Crea un file PDF di test o modifica TEST_PDF_PATH")
        return
    
    with open(TEST_PDF_PATH, 'rb') as f:
        files = {'file': f}
        data = {
            'patient_id': 'test_patient_001',
            'process_as_packet': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/upload-document", files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ Errore upload: {response.status_code}")
        print(response.text)
        return
    
    upload_result = response.json()
    print(f"✅ Upload completato: {upload_result}")
    
    patient_id = upload_result.get('patient_id')
    if not patient_id:
        print("❌ Patient ID non trovato nella risposta")
        return
    
    # 2. Monitoraggio dello stato del processing
    print(f"\n2. Monitoraggio stato processing per patient_id: {patient_id}")
    
    max_attempts = 30  # 30 tentativi con intervallo di 2 secondi = 1 minuto
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/api/document-packet-status/{patient_id}")
            
            if response.status_code == 200:
                status = response.json()
                print(f"   Tentativo {attempt + 1}: {status.get('status')} - {status.get('message')} ({status.get('progress', 0)}%)")
                
                # Se il processing è completato, mostra i risultati
                if status.get('status') in ['completed', 'completed_with_errors', 'failed']:
                    print(f"\n✅ Processing completato con status: {status.get('status')}")
                    print(f"   Sezioni trovate: {status.get('sections_found', [])}")
                    print(f"   Sezioni mancanti: {status.get('sections_missing', [])}")
                    print(f"   Documenti creati: {len(status.get('documents_created', []))}")
                    
                    if status.get('errors'):
                        print(f"   Errori: {status.get('errors')}")
                    
                    # 3. Ottieni il testo OCR
                    print(f"\n3. Recupero testo OCR...")
                    ocr_response = requests.get(f"{BASE_URL}/api/document-ocr-text/{patient_id}")
                    
                    if ocr_response.status_code == 200:
                        ocr_data = ocr_response.json()
                        print(f"✅ Testo OCR recuperato: {len(ocr_data.get('ocr_text', ''))} caratteri")
                        print(f"   File: {ocr_data.get('filename')}")
                    else:
                        print(f"❌ Errore recupero testo OCR: {ocr_response.status_code}")
                    
                    # 4. Verifica documenti creati nella dashboard
                    print(f"\n4. Verifica documenti nella dashboard...")
                    patient_response = requests.get(f"{BASE_URL}/api/patient/{patient_id}")
                    
                    if patient_response.status_code == 200:
                        patient_data = patient_response.json()
                        print(f"✅ Dati paziente recuperati")
                        print(f"   Nome: {patient_data.get('name')}")
                        print(f"   Documenti: {len(patient_data.get('documents', []))}")
                        
                        for doc in patient_data.get('documents', []):
                            print(f"     - {doc.get('document_type')}: {doc.get('filename')} ({doc.get('status')})")
                    else:
                        print(f"❌ Errore recupero dati paziente: {patient_response.status_code}")
                    
                    return
                    
            elif response.status_code == 404:
                print(f"   Tentativo {attempt + 1}: Documento non ancora trovato, attendo...")
            else:
                print(f"   Tentativo {attempt + 1}: Errore {response.status_code}")
                
        except Exception as e:
            print(f"   Tentativo {attempt + 1}: Errore di connessione: {e}")
        
        time.sleep(2)  # Attendi 2 secondi tra i tentativi
    
    print(f"\n❌ Timeout: Il processing non è stato completato entro {max_attempts * 2} secondi")

def test_regular_flow():
    """Test del flusso originale per confronto."""
    
    print("\n=== Test Flusso Originale (per confronto) ===")
    
    if not os.path.exists(TEST_PDF_PATH):
        print(f"❌ File di test non trovato: {TEST_PDF_PATH}")
        return
    
    with open(TEST_PDF_PATH, 'rb') as f:
        files = {'file': f}
        data = {
            'patient_id': 'test_patient_002',
            'process_as_packet': 'false'  # Flusso originale
        }
        
        response = requests.post(f"{BASE_URL}/api/upload-document", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload flusso originale completato: {result}")
    else:
        print(f"❌ Errore upload flusso originale: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Test del nuovo flusso unificato di upload documenti")
    print("=" * 60)
    
    # Test del flusso unificato
    test_unified_flow()
    
    # Test del flusso originale per confronto
    test_regular_flow()
    
    print("\n" + "=" * 60)
    print("Test completati!") 