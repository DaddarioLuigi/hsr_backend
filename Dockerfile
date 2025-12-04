# Usa una base leggera con Python
FROM python:3.11-slim

# Impostazioni Python (meno file temporanei, log subito in console)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installiamo i pacchetti di sistema necessari a OCRmyPDF
# - tesseract-ocr: motore OCR
# - tesseract-ocr-ita / eng: lingue
# - ghostscript: gestione PDF
# - qpdf: manipolazione struttura PDF
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ita \
    tesseract-ocr-eng \
    ghostscript \
    qpdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Impostiamo la cartella di lavoro dentro il container
WORKDIR /app

# Copiamo solo requirements per sfruttare la cache Docker
COPY requirements.txt ./

# Installiamo le dipendenze Python del progetto
RUN pip install --no-cache-dir -r requirements.txt

# Ora copiamo TUTTO il resto del codice nel container
COPY . .

# Se la tua app ascolta sulla 5000, esportiamola
EXPOSE 5000

# Comando di avvio
# Se in app.py hai il solito:
#   if __name__ == "__main__":
#       app.run(host="0.0.0.0", port=5000)
# allora questo va bene:
CMD ["python", "app.py"]
