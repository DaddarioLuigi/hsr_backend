# config/segmentation_config.py
# -*- coding: utf-8 -*-
"""
Configurazione per il sistema di segmentazione avanzato.
"""

from typing import Dict, Any

# Configurazione del segmenter avanzato
ADVANCED_SEGMENTER_CONFIG = {
    # Soglie di confidenza
    "confidence_thresholds": {
        "low": 0.5,      # Accetta quasi tutto
        "medium": 0.7,   # Bilanciato (default)
        "high": 0.8      # Solo sezioni molto sicure
    },
    
    # Parametri per la validazione LLM
    "llm_validation": {
        "enable": True,           # Abilita validazione LLM
        "threshold": 0.8,         # Valida sezioni con confidenza < 0.8
        "boost_amount": 0.2,      # Incremento confidenza se validato
        "max_validation_length": 1000  # Lunghezza massima per validazione
    },
    
    # Parametri per l'analisi temporale
    "temporal_analysis": {
        "enable": True,           # Abilita analisi temporale
        "boost_amount": 0.1,      # Incremento confidenza per eco pre/post
        "penalty_amount": 0.1     # Decremento confidenza se non determinabile
    },
    
    # Parametri per pattern flessibili
    "flexible_patterns": {
        "enable": True,           # Abilita pattern flessibili per OCR
        "min_section_length": 30, # Lunghezza minima sezione
        "merge_gap_chars": 20     # Gap massimo per unire sezioni
    },
    
    # Parametri per sezioni multiple
    "multiple_sections": {
        "allow_same_type": True,  # Permette sezioni multiple dello stesso tipo
        "remove_exact_duplicates": True,  # Rimuove duplicati esatti
        "keep_highest_confidence": True   # Mantiene quella con confidenza maggiore
    },
    
    # Logging e debug
    "logging": {
        "enable_detailed_logs": True,     # Log dettagliati
        "log_confidence_scores": True,    # Log dei punteggi di confidenza
        "log_temporal_analysis": True,    # Log dell'analisi temporale
        "log_llm_validation": True        # Log della validazione LLM
    }
}

# Configurazione per diversi ambienti
ENVIRONMENT_CONFIGS = {
    "development": {
        "confidence_thresholds": {
            "low": 0.3,      # Più permissivo in development
            "medium": 0.5,
            "high": 0.7
        },
        "llm_validation": {
            "enable": True,
            "threshold": 0.6,  # Valida più sezioni in development
        },
        "logging": {
            "enable_detailed_logs": True,
            "log_confidence_scores": True,
            "log_temporal_analysis": True,
            "log_llm_validation": True
        }
    },
    
    "production": {
        "confidence_thresholds": {
            "low": 0.5,
            "medium": 0.7,
            "high": 0.8
        },
        "llm_validation": {
            "enable": True,
            "threshold": 0.8,
        },
        "logging": {
            "enable_detailed_logs": False,  # Meno verbose in production
            "log_confidence_scores": True,
            "log_temporal_analysis": False,
            "log_llm_validation": False
        }
    },
    
    "testing": {
        "confidence_thresholds": {
            "low": 0.2,      # Molto permissivo per testing
            "medium": 0.4,
            "high": 0.6
        },
        "llm_validation": {
            "enable": False,  # Disabilita LLM per testing veloce
        },
        "logging": {
            "enable_detailed_logs": True,
            "log_confidence_scores": True,
            "log_temporal_analysis": True,
            "log_llm_validation": True
        }
    }
}

def get_config(environment: str = "production") -> Dict[str, Any]:
    """
    Restituisce la configurazione per l'ambiente specificato.
    
    Args:
        environment: "development", "production", "testing"
        
    Returns:
        Configurazione completa per l'ambiente
    """
    base_config = ADVANCED_SEGMENTER_CONFIG.copy()
    env_config = ENVIRONMENT_CONFIGS.get(environment, ENVIRONMENT_CONFIGS["production"])
    
    # Merge delle configurazioni
    for key, value in env_config.items():
        if key in base_config:
            if isinstance(value, dict) and isinstance(base_config[key], dict):
                base_config[key].update(value)
            else:
                base_config[key] = value
        else:
            base_config[key] = value
    
    return base_config

def get_confidence_threshold(level: str, environment: str = "production") -> float:
    """
    Restituisce la soglia di confidenza per il livello e ambiente specificati.
    
    Args:
        level: "low", "medium", "high"
        environment: "development", "production", "testing"
        
    Returns:
        Soglia di confidenza
    """
    config = get_config(environment)
    return config["confidence_thresholds"].get(level, 0.7)

def is_llm_validation_enabled(environment: str = "production") -> bool:
    """
    Verifica se la validazione LLM è abilitata per l'ambiente.
    
    Args:
        environment: "development", "production", "testing"
        
    Returns:
        True se abilitata, False altrimenti
    """
    config = get_config(environment)
    return config["llm_validation"]["enable"]

def get_llm_validation_threshold(environment: str = "production") -> float:
    """
    Restituisce la soglia per la validazione LLM.
    
    Args:
        environment: "development", "production", "testing"
        
    Returns:
        Soglia di validazione LLM
    """
    config = get_config(environment)
    return config["llm_validation"]["threshold"] 