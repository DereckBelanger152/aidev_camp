# Backend - Music Recommendation API

API FastAPI pour la recommandation de chansons basée sur l'analyse audio et la recherche vectorielle.

## Prérequis

- **Python**: 3.10 ou 3.11
- **Espace disque**: ~15 GB
  - Modèle CLAP: ~600 MB
  - ChromaDB: ~2-3 GB
  - Audio temporaires: ~3-5 GB durant l'init
- **RAM**: 8 GB minimum

## Installation

### 1. Créer l'environnement virtuel

```bash
cd backend
python3 -m venv venv
```

### 2. Activer l'environnement

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: L'installation peut prendre 5-10 minutes (torch est volumineux).

## Configuration

### Initialiser la base de données vectorielle

**Important**: Cette étape doit être effectuée avant le premier lancement.

```bash
python scripts/init_vector_db.py
```

**Durée estimée**: 30-60 minutes pour 1000 chansons.

**Options disponibles**:
```bash
# Initialiser avec moins de chansons (pour tests)
python scripts/init_vector_db.py --count 100

# Reprendre après interruption
python scripts/init_vector_db.py --resume

# Reset complet de la base
python scripts/init_vector_db.py --reset
```

### Vérifier l'installation

```bash
python scripts/verify_db.py
```

Devrait afficher:
```
✓ Database contains 1000 tracks
✓ Embedding dimension correct: 512
✓ All required metadata fields present
✓ Similarity search working
```

## Lancer le serveur

### Mode développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ou directement:

```bash
python -m app.main
```

### Mode production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Le serveur sera disponible sur: `http://localhost:8000`

## Documentation API

Une fois le serveur lancé, accédez à la documentation interactive:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints disponibles

### `GET /`
Page d'accueil avec infos API.

### `GET /health`
Health check - vérifie la connexion à la base de données.

**Response**:
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "track_count": 1000
  }
}
```

### `POST /api/search`
Recherche une chanson par nom.

**Request**:
```json
{
  "query": "Bohemian Rhapsody"
}
```

**Response**:
```json
{
  "id": "3135556",
  "title": "Bohemian Rhapsody",
  "artist": "Queen",
  "preview_url": "https://...",
  "cover": "https://...",
  "message": "C'est bien ce morceau que vous voulez rechercher?"
}
```

### `POST /api/recommendations/{track_id}`
Obtient les 3 chansons les plus similaires.

**Response**:
```json
{
  "tracks": [
    {
      "id": "123",
      "title": "We Are The Champions",
      "artist": "Queen",
      "similarity_score": 0.89,
      "popularity": 950000,
      "preview_url": "https://...",
      "cover": "https://..."
    },
    // ... 2 autres tracks
  ],
  "source_track_id": "3135556"
}
```

### `POST /api/admin/add-tracks`
Ajoute des chansons à la base de données.

**Request**:
```json
{
  "track_ids": ["123456", "789012"]
}
```

**Response**:
```json
{
  "status": "success",
  "added_count": 2,
  "message": "2 tracks added to database"
}
```

## Architecture

```
backend/
├── app/
│   ├── main.py              # Application FastAPI principale
│   ├── routers/
│   │   ├── search.py        # Endpoint de recherche
│   │   └── recommendations.py  # Endpoints de recommandation
│   ├── services/
│   │   ├── deezer_service.py    # Intégration Deezer API
│   │   ├── embedding_service.py # Génération embeddings CLAP
│   │   └── vector_db_service.py # Gestion ChromaDB
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── db/
│       └── vector_store/    # Base ChromaDB (généré)
├── scripts/
│   ├── init_vector_db.py    # Initialisation base de données
│   └── verify_db.py         # Vérification intégrité
└── requirements.txt
```

## Workflow de développement

### 1. Développement avec base limitée (rapide)

```bash
# Init avec seulement 100 chansons (5-10 min)
python scripts/init_vector_db.py --count 100

# Lancer le serveur
uvicorn app.main:app --reload
```

### 2. Test manuel via curl

```bash
# Rechercher une chanson
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Stairway to Heaven"}'

# Obtenir des recommandations
curl -X POST "http://localhost:8000/api/recommendations/3135556"
```

### 3. Test via Swagger UI

Ouvrir http://localhost:8000/docs et tester interactivement.

## Troubleshooting

### Erreur: "Unable to import 'app.services.xxx'"

**Cause**: Environnement virtuel non activé.

**Solution**:
```bash
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows
```

### Erreur: "Database is empty"

**Cause**: Base de données non initialisée.

**Solution**:
```bash
python scripts/init_vector_db.py
```

### Erreur: "CLAP model download failed"

**Cause**: Problème de connexion ou firewall.

**Solution**: Download manuel du modèle:
```bash
mkdir -p ~/.cache/laion_clap
cd ~/.cache/laion_clap
wget https://huggingface.co/lukewys/laion_clap/resolve/main/music_audioset_epoch_15_esc_90.14.pt
```

### Erreur: "429 Too Many Requests" (Deezer)

**Cause**: Rate limiting Deezer API.

**Solution**: Le script gère automatiquement les délais. Si persistant, augmenter le sleep dans `init_vector_db.py`.

### Port 8000 déjà utilisé

**Solution**: Changer le port:
```bash
uvicorn app.main:app --port 8001
```

### "Out of memory" durant l'init

**Solutions**:
1. Fermer autres applications
2. Initialiser par petits lots:
```bash
python scripts/init_vector_db.py --count 100
# Puis étendre progressivement
```

## Scripts utilitaires

### Statistiques de la base

```bash
python scripts/db_stats.py
```

### Backup de la base

```bash
cp -r app/db/vector_store/ app/db/backup_$(date +%Y%m%d)/
```

### Reset de la base

```bash
python scripts/init_vector_db.py --reset
```

## Variables d'environnement (optionnel)

Créer un fichier `.env` dans `backend/`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database
VECTOR_DB_PATH=app/db/vector_store
COLLECTION_NAME=music_embeddings

# Logging
LOG_LEVEL=INFO
```

## Performance

### Temps de réponse typiques

- `/api/search`: 200-500ms (appel Deezer)
- `/api/recommendations/{id}`: 3-5s
  - Download audio: ~500ms
  - Génération embedding: 2-3s
  - Query vector DB: ~100ms
  - Filtrage: <10ms

### Optimisations possibles

1. **Cache embeddings**: Stocker embeddings des chansons recherchées fréquemment
2. **GPU**: Utiliser CUDA pour accélérer CLAP (2-3x plus rapide)
3. **Pré-téléchargement**: Garder previews en cache temporaire
4. **Workers**: Augmenter nombre de workers Uvicorn en production

## Tests

### Test unitaire d'un service

```python
from app.services.deezer_service import get_deezer_service

deezer = get_deezer_service()
result = deezer.search_tracks("Bohemian Rhapsody")
print(result)
```

### Test complet du workflow

```bash
# 1. Rechercher
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Bohemian Rhapsody"}' \
  | jq '.id'

# 2. Obtenir recommandations (remplacer TRACK_ID)
curl -X POST http://localhost:8000/api/recommendations/TRACK_ID \
  | jq '.tracks[].title'
```

## Logs

Les logs sont affichés dans la console. Format:
```
2025-01-15 10:30:45 - INFO - Starting up application...
2025-01-15 10:30:47 - INFO - Loading embedding service...
2025-01-15 10:30:50 - INFO - Vector database ready with 1000 tracks
```

Pour sauvegarder les logs:
```bash
uvicorn app.main:app --reload 2>&1 | tee backend.log
```

## Production

### Checklist avant déploiement

- [ ] Base de données initialisée avec 1000+ tracks
- [ ] Tests de vérification passés
- [ ] Backup de la base créé
- [ ] CORS configuré pour le domaine frontend
- [ ] Variables d'environnement configurées
- [ ] Logs configurés (fichier + monitoring)
- [ ] Rate limiting activé (si nécessaire)
- [ ] Health check fonctionnel

### Exemple Docker (optionnel)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Support

Pour les problèmes persistants:
1. Vérifier les logs: `tail -f backend.log`
2. Tester le health check: `curl http://localhost:8000/health`
3. Vérifier la base: `python scripts/verify_db.py`
4. Consulter la documentation Swagger: http://localhost:8000/docs

## License

MIT
