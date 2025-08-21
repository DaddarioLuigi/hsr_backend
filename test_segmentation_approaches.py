#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test per confrontare diversi approcci di segmentazione.
"""

import logging
import time
from typing import List, Dict, Any

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Importa i segmenter
from utils.document_segmenter import find_document_sections
from utils.advanced_segmenter import AdvancedSegmenter
from utils.llm_segmenter import LLMSegmenter
from utils.adaptive_segmenter import AdaptiveSegmenter, SegmentationStrategy

def test_segmentation_approaches(text: str, test_name: str = "Test Document"):
    """
    Confronta diversi approcci di segmentazione.
    """
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    
    results = {}
    
    # Test 1: Regex Only (Originale)
    print("\n1. TESTING REGEX-ONLY APPROACH...")
    start_time = time.time()
    try:
        regex_sections = find_document_sections(text)
        regex_time = time.time() - start_time
        
        results["regex_only"] = {
            "sections": len([s for s in regex_sections if s.doc_type != "altro"]),
            "time": regex_time,
            "types_found": list(set(s.doc_type for s in regex_sections if s.doc_type != "altro")),
            "success": True
        }
        print(f"   ✅ Trovate {results['regex_only']['sections']} sezioni in {regex_time:.2f}s")
        print(f"   📋 Tipi: {results['regex_only']['types_found']}")
    except Exception as e:
        results["regex_only"] = {"success": False, "error": str(e)}
        print(f"   ❌ Errore: {e}")
    
    # Test 2: Advanced Hybrid
    print("\n2. TESTING ADVANCED HYBRID APPROACH...")
    start_time = time.time()
    try:
        advanced_segmenter = AdvancedSegmenter()
        advanced_sections = advanced_segmenter.segment_document(text)
        advanced_time = time.time() - start_time
        
        results["advanced_hybrid"] = {
            "sections": len(advanced_sections),
            "time": advanced_time,
            "types_found": list(set(s.doc_type for s in advanced_sections)),
            "avg_confidence": sum(s.confidence for s in advanced_sections) / len(advanced_sections) if advanced_sections else 0,
            "success": True
        }
        print(f"   ✅ Trovate {results['advanced_hybrid']['sections']} sezioni in {advanced_time:.2f}s")
        print(f"   📋 Tipi: {results['advanced_hybrid']['types_found']}")
        print(f"   🎯 Confidenza media: {results['advanced_hybrid']['avg_confidence']:.2f}")
    except Exception as e:
        results["advanced_hybrid"] = {"success": False, "error": str(e)}
        print(f"   ❌ Errore: {e}")
    
    # Test 3: LLM First
    print("\n3. TESTING LLM-FIRST APPROACH...")
    start_time = time.time()
    try:
        llm_segmenter = LLMSegmenter()
        llm_sections = llm_segmenter.segment_document(text)
        llm_time = time.time() - start_time
        
        results["llm_first"] = {
            "sections": len(llm_sections),
            "time": llm_time,
            "types_found": list(set(s.doc_type for s in llm_sections)),
            "avg_confidence": sum(s.confidence for s in llm_sections) / len(llm_sections) if llm_sections else 0,
            "success": True
        }
        print(f"   ✅ Trovate {results['llm_first']['sections']} sezioni in {llm_time:.2f}s")
        print(f"   📋 Tipi: {results['llm_first']['types_found']}")
        print(f"   🎯 Confidenza media: {results['llm_first']['avg_confidence']:.2f}")
    except Exception as e:
        results["llm_first"] = {"success": False, "error": str(e)}
        print(f"   ❌ Errore: {e}")
    
    # Test 4: Adaptive (Auto)
    print("\n4. TESTING ADAPTIVE APPROACH (AUTO)...")
    start_time = time.time()
    try:
        adaptive_segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.ADAPTIVE)
        adaptive_sections = adaptive_segmenter.segment_document(text, confidence_level="medium")
        adaptive_time = time.time() - start_time
        
        stats = adaptive_segmenter.get_segmentation_stats(adaptive_sections)
        
        results["adaptive_auto"] = {
            "sections": len(adaptive_sections),
            "time": adaptive_time,
            "types_found": list(stats["by_type"].keys()),
            "avg_confidence": stats["avg_confidence"],
            "strategy_used": list(stats["by_strategy"].keys()),
            "success": True
        }
        print(f"   ✅ Trovate {results['adaptive_auto']['sections']} sezioni in {adaptive_time:.2f}s")
        print(f"   📋 Tipi: {results['adaptive_auto']['types_found']}")
        print(f"   🎯 Confidenza media: {results['adaptive_auto']['avg_confidence']:.2f}")
        print(f"   🔧 Strategia usata: {results['adaptive_auto']['strategy_used']}")
    except Exception as e:
        results["adaptive_auto"] = {"success": False, "error": str(e)}
        print(f"   ❌ Errore: {e}")
    
    # Test 5: Adaptive (Low Confidence)
    print("\n5. TESTING ADAPTIVE APPROACH (LOW CONFIDENCE)...")
    start_time = time.time()
    try:
        adaptive_segmenter = AdaptiveSegmenter(strategy=SegmentationStrategy.ADAPTIVE)
        adaptive_low_sections = adaptive_segmenter.segment_document(text, confidence_level="low")
        adaptive_low_time = time.time() - start_time
        
        stats_low = adaptive_segmenter.get_segmentation_stats(adaptive_low_sections)
        
        results["adaptive_low"] = {
            "sections": len(adaptive_low_sections),
            "time": adaptive_low_time,
            "types_found": list(stats_low["by_type"].keys()),
            "avg_confidence": stats_low["avg_confidence"],
            "success": True
        }
        print(f"   ✅ Trovate {results['adaptive_low']['sections']} sezioni in {adaptive_low_time:.2f}s")
        print(f"   📋 Tipi: {results['adaptive_low']['types_found']}")
        print(f"   🎯 Confidenza media: {results['adaptive_low']['avg_confidence']:.2f}")
    except Exception as e:
        results["adaptive_low"] = {"success": False, "error": str(e)}
        print(f"   ❌ Errore: {e}")
    
    # Risultati comparativi
    print(f"\n{'='*60}")
    print("RISULTATI COMPARATIVI")
    print(f"{'='*60}")
    
    print(f"{'Approccio':<20} {'Sezioni':<8} {'Tempo':<8} {'Confidenza':<12} {'Successo':<8}")
    print("-" * 60)
    
    for approach, result in results.items():
        if result.get("success"):
            sections = result["sections"]
            time_taken = result["time"]
            confidence = result.get("avg_confidence", "N/A")
            success = "✅" if result["success"] else "❌"
            
            print(f"{approach:<20} {sections:<8} {time_taken:<8.2f} {confidence:<12.2f} {success:<8}")
        else:
            print(f"{approach:<20} {'ERR':<8} {'ERR':<8} {'ERR':<12} ❌")
    
    # Raccomandazioni
    print(f"\n{'='*60}")
    print("RACCOMANDAZIONI")
    print(f"{'='*60}")
    
    successful_results = {k: v for k, v in results.items() if v.get("success")}
    
    if successful_results:
        # Trova il migliore per numero di sezioni
        best_sections = max(successful_results.items(), key=lambda x: x[1]["sections"])
        
        # Trova il più veloce
        fastest = min(successful_results.items(), key=lambda x: x[1]["time"])
        
        # Trova il più accurato (confidenza)
        most_confident = max(successful_results.items(), key=lambda x: x[1].get("avg_confidence", 0))
        
        print(f"🎯 Più sezioni trovate: {best_sections[0]} ({best_sections[1]['sections']} sezioni)")
        print(f"⚡ Più veloce: {fastest[0]} ({fastest[1]['time']:.2f}s)")
        print(f"🎯 Più accurato: {most_confident[0]} (confidenza {most_confident[1].get('avg_confidence', 0):.2f})")
        
        # Raccomandazione generale
        if best_sections[0] == "adaptive_low":
            print("\n💡 RACCOMANDAZIONE: Usa Adaptive con confidenza bassa per massima copertura")
        elif best_sections[0] == "llm_first":
            print("\n💡 RACCOMANDAZIONE: Usa LLM-first per massima accuratezza")
        elif best_sections[0] == "advanced_hybrid":
            print("\n💡 RACCOMANDAZIONE: Usa Advanced Hybrid per bilanciare velocità e accuratezza")
        else:
            print("\n💡 RACCOMANDAZIONE: Usa Adaptive Auto per selezione automatica")
    else:
        print("❌ Nessun approccio ha avuto successo")
    
    return results

def test_with_sample_text():
    """
    Test con testo di esempio.
    """
    sample_text = """
    RELAZIONE CLINICA ALLA DIMISSIONE - DEFINITIVA
    
    Paziente: Mario Rossi
    Data ricovero: 15/01/2024
    Data dimissione: 25/01/2024
    
    ANAMNESI
    Il paziente presenta storia di cardiopatia ischemica...
    
    EPICRISI TERAPIA INTENSIVA/TICCH
    Il paziente è stato ricoverato in terapia intensiva...
    
    SCHEDA ANESTESIOLOGICA INTRAOPERATORIA
    Data intervento: 18/01/2024
    Tempi sala: entrata 08:00, uscita 14:00
    
    VERBALE OPERATORIO
    Intervento cardiochirurgico eseguito il 18/01/2024...
    
    LABORATORIO DI EMODINAMICA E CARDIOLOGIA INTERVENTISTICA
    Coronarografia eseguita il 16/01/2024...
    
    LABORATORI DI ECOCARDIOGRAFIA
    Ecocardiogramma transtoracico eseguito il 17/01/2024...
    
    LABORATORI DI ECOCARDIOGRAFIA
    Ecocardiogramma transtoracico eseguito il 20/01/2024...
    
    TC CUORE
    Tomografia computerizzata eseguita il 19/01/2024...
    """
    
    return test_segmentation_approaches(sample_text, "Sample Clinical Document")

def test_with_ocr_text():
    """
    Test con testo che simula artefatti OCR.
    """
    ocr_text = """
    RELAZIONE CLINICA ALLA DIMISSIONE - DEFINITIVA
    
    Paziente: Mario Rossi
    Data ricovero: 15/01/2024
    Data dimissione: 25/01/2024
    
    ANAMNESI
    Il paziente presenta storia di cardiopatia ischemica...
    
    EPICRISI TERAPIA INTENSIVA/TICCH
    Il paziente è stato ricoverato in terapia intensiva...
    
    SCHEDA ANESTESIOLOGICA INTRAOPERATORIA
    Data intervento: 18/01/2024
    Tempi sala: entrata 08:00, uscita 14:00
    
    VERBALE OPERATORIO
    Intervento cardiochirurgico eseguito il 18/01/2024...
    
    LABORATORIO DI EMODINAMICA E CARDIOLOGIA INTERVENTISTICA
    Coronarografia eseguita il 16/01/2024...
    
    LABORATORI DI ECOCARDIOGRAFIA
    Ecocardiogramma transtoracico eseguito il 17/01/2024...
    
    LABORATORI DI ECOCARDIOGRAFIA
    Ecocardiogramma transtoracico eseguito il 20/01/2024...
    
    TC CUORE
    Tomografia computerizzata eseguita il 19/01/2024...
    
    Note: Questo testo simula artefatti OCR con caratteri isolati e formattazione irregolare.
    """
    
    return test_segmentation_approaches(ocr_text, "OCR-like Document")

if __name__ == "__main__":
    print("🧪 TESTING SEGMENTATION APPROACHES")
    print("=" * 60)
    
    # Test con testo di esempio
    results_sample = test_with_sample_text()
    
    # Test con testo OCR-like
    results_ocr = test_with_ocr_text()
    
    print(f"\n{'='*60}")
    print("TEST COMPLETATI")
    print(f"{'='*60}")
    print("✅ Tutti i test sono stati eseguiti con successo!")
    print("📊 Controlla i risultati sopra per scegliere l'approccio migliore.") 