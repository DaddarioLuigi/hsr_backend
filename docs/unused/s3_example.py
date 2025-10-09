#!/usr/bin/env python3
"""
Esempio di utilizzo dell'integrazione S3 per il caricamento di file.

Prima di eseguire questo script, assicurati di aver configurato le variabili d'ambiente:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY  
- AWS_REGION
- S3_BUCKET_NAME
"""

import os
from utils.s3_manager import S3Manager
from utils.file_manager import FileManager

def test_s3_upload():
    """Test di upload di un file su S3"""
    print("=== Test Upload S3 ===")
    
    # Inizializza S3 Manager
    s3_manager = S3Manager()
    
    if not s3_manager.s3_client:
        print("❌ Client S3 non inizializzato. Verifica le credenziali AWS.")
        return
    
    # Crea un file di test
    test_content = "Questo è un file di test per S3"
    test_file_path = "test_file.txt"
    
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    # Upload del file
    s3_key = "test/example.txt"
    result = s3_manager.upload_file(test_file_path, s3_key)
    
    if result["success"]:
        print(f"✅ File caricato con successo!")
        print(f"   URL: {result['url']}")
        print(f"   Bucket: {result['bucket']}")
        print(f"   Key: {result['key']}")
    else:
        print(f"❌ Errore nell'upload: {result['error']}")
    
    # Pulisci il file di test
    os.remove(test_file_path)

def test_file_manager_with_s3():
    """Test del FileManager con integrazione S3"""
    print("\n=== Test FileManager con S3 ===")
    
    # Inizializza FileManager
    file_manager = FileManager()
    
    # Simula un file stream
    class MockFileStream:
        def __init__(self, content):
            self.content = content.encode('utf-8')
            self.position = 0
        
        def read(self):
            return self.content
    
    # Test di salvataggio file
    test_content = "Contenuto del documento di test"
    mock_file = MockFileStream(test_content)
    
    result = file_manager.save_file(
        patient_id="test_patient_123",
        document_type="lettera_dimissione", 
        filename="test_document.pdf",
        file_stream=mock_file
    )
    
    filepath, s3_result = result
    
    print(f"✅ File salvato localmente: {filepath}")
    
    if s3_result and s3_result.get("success"):
        print(f"✅ File caricato anche su S3!")
        print(f"   URL S3: {s3_result.get('url')}")
    elif s3_result:
        print(f"⚠️  Errore S3: {s3_result.get('error')}")
    else:
        print("ℹ️  S3 non configurato")

def test_s3_operations():
    """Test delle operazioni S3 base"""
    print("\n=== Test Operazioni S3 ===")
    
    s3_manager = S3Manager()
    
    if not s3_manager.s3_client:
        print("❌ Client S3 non inizializzato")
        return
    
    # Test di esistenza file
    test_key = "test/example.txt"
    exists = s3_manager.file_exists(test_key)
    print(f"File {test_key} esiste: {exists}")
    
    # Test di generazione URL temporaneo
    url = s3_manager.get_file_url(test_key, expires_in=3600)
    if url:
        print(f"URL temporaneo generato: {url[:50]}...")
    else:
        print("❌ Impossibile generare URL temporaneo")
    
    # Test di listaggio file
    list_result = s3_manager.list_files(prefix="test/")
    if list_result["success"]:
        print(f"File trovati con prefisso 'test/': {list_result['count']}")
        for file_info in list_result["files"][:3]:  # Mostra solo i primi 3
            print(f"  - {file_info['key']} ({file_info['size']} bytes)")
    else:
        print(f"❌ Errore nel listaggio: {list_result['error']}")

if __name__ == "__main__":
    print("🚀 Test integrazione AWS S3")
    print("=" * 50)
    
    # Verifica configurazione
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variabili d'ambiente mancanti: {', '.join(missing_vars)}")
        print("Configura le variabili d'ambiente prima di eseguire i test.")
        exit(1)
    
    # Esegui test
    test_s3_upload()
    test_file_manager_with_s3()
    test_s3_operations()
    
    print("\n✅ Test completati!") 