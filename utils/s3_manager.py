import os
import json
import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any


class S3Manager:
    """
    Gestisce l'upload e download di file su AWS S3.
    Sostituisce la funzionalità Google Drive.
    """
    
    def __init__(self):
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.export_bucket_name = os.getenv('S3_BUCKET_EXPORT', self.bucket_name)
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            logging.warning("Credenziali AWS S3 non configurate completamente")
            self.s3_client = None
        else:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
                logging.info(f"S3 client inizializzato per bucket: {self.bucket_name}")
            except Exception as e:
                logging.error(f"Errore nell'inizializzazione del client S3: {e}")
                self.s3_client = None
    
    def upload_file(self, file_path: str, s3_key: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Carica un file su S3.
        
        Args:
            file_path: Percorso locale del file
            s3_key: Chiave S3 (path nel bucket)
            bucket_name: Nome del bucket (opzionale, usa quello di default se non specificato)
            
        Returns:
            Dict con esito dell'operazione
        """
        if not self.s3_client:
            return {"success": False, "error": "Client S3 non inizializzato"}
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.s3_client.upload_file(file_path, bucket, s3_key)
            url = f"https://{bucket}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            return {
                "success": True,
                "url": url,
                "bucket": bucket,
                "key": s3_key
            }
        except FileNotFoundError:
            return {"success": False, "error": f"File non trovato: {file_path}"}
        except NoCredentialsError:
            return {"success": False, "error": "Credenziali AWS non valide"}
        except ClientError as e:
            return {"success": False, "error": f"Errore S3: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Errore generico: {str(e)}"}
    
    def upload_file_content(self, file_content: bytes, s3_key: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Carica contenuto di file direttamente su S3.
        
        Args:
            file_content: Contenuto del file in bytes
            s3_key: Chiave S3 (path nel bucket)
            bucket_name: Nome del bucket (opzionale)
            
        Returns:
            Dict con esito dell'operazione
        """
        if not self.s3_client:
            return {"success": False, "error": "Client S3 non inizializzato"}
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=file_content
            )
            url = f"https://{bucket}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            return {
                "success": True,
                "url": url,
                "bucket": bucket,
                "key": s3_key
            }
        except NoCredentialsError:
            return {"success": False, "error": "Credenziali AWS non valide"}
        except ClientError as e:
            return {"success": False, "error": f"Errore S3: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Errore generico: {str(e)}"}
    
    def download_file(self, s3_key: str, local_path: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Scarica un file da S3.
        
        Args:
            s3_key: Chiave S3 del file
            local_path: Percorso locale dove salvare il file
            bucket_name: Nome del bucket (opzionale)
            
        Returns:
            Dict con esito dell'operazione
        """
        if not self.s3_client:
            return {"success": False, "error": "Client S3 non inizializzato"}
        
        bucket = bucket_name or self.bucket_name
        
        try:
            # Crea la directory se non esiste
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(bucket, s3_key, local_path)
            return {
                "success": True,
                "local_path": local_path,
                "bucket": bucket,
                "key": s3_key
            }
        except NoCredentialsError:
            return {"success": False, "error": "Credenziali AWS non valide"}
        except ClientError as e:
            return {"success": False, "error": f"Errore S3: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Errore generico: {str(e)}"}
    
    def delete_file(self, s3_key: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Elimina un file da S3.
        
        Args:
            s3_key: Chiave S3 del file da eliminare
            bucket_name: Nome del bucket (opzionale)
            
        Returns:
            Dict con esito dell'operazione
        """
        if not self.s3_client:
            return {"success": False, "error": "Client S3 non inizializzato"}
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=s3_key)
            return {
                "success": True,
                "bucket": bucket,
                "key": s3_key
            }
        except NoCredentialsError:
            return {"success": False, "error": "Credenziali AWS non valide"}
        except ClientError as e:
            return {"success": False, "error": f"Errore S3: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Errore generico: {str(e)}"}
    
    def file_exists(self, s3_key: str, bucket_name: Optional[str] = None) -> bool:
        """
        Verifica se un file esiste su S3.
        
        Args:
            s3_key: Chiave S3 del file
            bucket_name: Nome del bucket (opzionale)
            
        Returns:
            True se il file esiste, False altrimenti
        """
        if not self.s3_client:
            return False
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.s3_client.head_object(Bucket=bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            return False
        except Exception:
            return False
    
    def get_file_url(self, s3_key: str, bucket_name: Optional[str] = None, expires_in: int = 3600) -> Optional[str]:
        """
        Genera un URL temporaneo per accedere al file.
        
        Args:
            s3_key: Chiave S3 del file
            bucket_name: Nome del bucket (opzionale)
            expires_in: Durata dell'URL in secondi (default: 1 ora)
            
        Returns:
            URL temporaneo o None se errore
        """
        if not self.s3_client:
            return None
        
        bucket = bucket_name or self.bucket_name
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logging.error(f"Errore nella generazione dell'URL: {e}")
            return None
    
    def list_files(self, prefix: str = "", bucket_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista i file in un bucket con un prefisso specifico.
        
        Args:
            prefix: Prefisso per filtrare i file
            bucket_name: Nome del bucket (opzionale)
            
        Returns:
            Dict con lista dei file
        """
        if not self.s3_client:
            return {"success": False, "error": "Client S3 non inizializzato"}
        
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            return {
                "success": True,
                "files": files,
                "count": len(files)
            }
        except NoCredentialsError:
            return {"success": False, "error": "Credenziali AWS non valide"}
        except ClientError as e:
            return {"success": False, "error": f"Errore S3: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Errore generico: {str(e)}"} 