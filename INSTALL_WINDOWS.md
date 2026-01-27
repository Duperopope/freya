# Installation Freya sur Windows

## Le problème
Votre `.venv` pointe vers un autre projet. Le script `freya.exe` cherche dans `H:\Code\Local LLM\.venv`.

## Solution 1 : Réinstaller dans le bon venv

```powershell
# Depuis H:\Code\Freya2 (PAS dans web/)
cd H:\Code\Freya2

# Désactiver l'ancien venv si actif
deactivate

# Créer un nouveau venv dédié à Freya
python -m venv .venv

# Activer le nouveau venv
.\.venv\Scripts\Activate.ps1

# Installer Freya en mode éditable
pip install -e .

# Vérifier
freya serve
```

## Solution 2 : Utiliser directement Python

```powershell
cd H:\Code\Freya2
python -m freya.cli serve
```

## Solution 3 : Réinstaller dans le venv actuel

```powershell
# Depuis H:\Code\Freya2 (racine du projet, PAS web/)
cd H:\Code\Freya2
pip install -e .
```

## Commande rapide pour démarrer

```powershell
cd H:\Code\Freya2
python -m uvicorn freya.api.main:create_debug_app --factory --host 127.0.0.1 --port 8765 --reload
```

Puis ouvrir : http://127.0.0.1:8765
