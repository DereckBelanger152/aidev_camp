# aidev_camp

Repo pour le AI Dev Camp Mirego - Application de recommandation musicale par analyse audio

## Prérequis

- **Python**: 3.10 ou 3.11 (requis pour torch, pydantic, laion-clap)
- **Node.js**: 18+ (pour le frontend)

## Architecture générale

### Frontend

- **Framework**: React avec TypeScript
- **UI Library**: Tailwind CSS + shadcn/ui pour les composants
- **Lecteur audio**: HTML5 Audio API ou Howler.js
- **État**: React Context ou Zustand

### Backend

- **Framework**: FastAPI (Python)
- **API Integration**: Deezer API
- **Audio Processing**:
  - librosa (analyse audio)
  - numpy/scipy (traitement signal)
- **ML Model**:
  - LAION CLAP (Contrastive Language-Audio Pretraining)
  - Modèle: `music_audioset_epoch_15_esc_90.14.pt`
- **Vector Database**:
  - ChromaDB (base de données vectorielle pour recherche de similarité)
  - Cosine similarity pour trouver les chansons similaires
  - Base pré-calculée de 1000 chansons top Deezer

---

## Structure du projet

```
aider_camp/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ConfirmationCard.tsx
│   │   │   ├── ResultCard.tsx
│   │   │   ├── ResultsGrid.tsx
│   │   │   └── AudioPlayer.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── search.py
│   │   │   └── recommendations.py
│   │   ├── services/
│   │   │   ├── deezer_service.py
│   │   │   ├── embedding_service.py
│   │   │   └── vector_db_service.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   └── db/
│   │       └── vector_store/  (ChromaDB data)
│   ├── scripts/
│   │   └── init_vector_db.py
│   └── requirements.txt
└── README.md
```

---

## Flux de données

1. **Recherche initiale**:

   - User entre titre exact (recherche stricte, aucune faute permise)
   - Frontend envoie query tel quel → Backend → Deezer API
   - Backend retourne premier résultat exact

2. **Confirmation**:

   - Backend répond: "C'est bien ce morceau que vous voulez rechercher?"
   - Affiche: titre, artiste, cover, preview audio (30s)
   - User peut play l'extrait pour confirmer
   - Boutons: "Oui, continuer" / "Non, annuler"

3. **Analyse audio** (si confirmé):

   - Backend télécharge preview MP3 (30s) de la chanson recherchée
   - Preprocessing audio (librosa → 48kHz)
   - Génération embedding via modèle CLAP (512-dim)
   - Feature vector normalisé

4. **Recherche similaire** (via base vectorielle):

   - Query de la base ChromaDB (1000 chansons pré-calculées)
   - Recherche par cosine similarity → top 10 plus similaires
   - Filtrage final par popularité (rank Deezer)
   - Sélection des top 3 résultats finaux

5. **Affichage résultats**:
   - 3 cards avec: cover, titre, artiste
   - Play button pour preview (30s)
   - Button "Save to Spotify" (placeholder, optionnel si temps)

---

## Composants clés

### Backend - Endpoints

#### `POST /api/search`

```json
Request: { "query": "Bohemian Rhapsody" }
Response: {
  "id": "3135556",
  "title": "Bohemian Rhapsody",
  "artist": "Queen",
  "preview_url": "https://...",
  "cover": "https://...",
  "message": "C'est bien ce morceau que vous voulez rechercher?"
}
```

#### `POST /api/recommendations/{track_id}`

```json
Response: [
  {
    "id": "...",
    "title": "...",
    "artist": "...",
    "similarity_score": 0.89,
    "preview_url": "...",
    "cover": "..."
  }
  // Top 3 résultats
]
```

### Backend - Services

#### `DeezerService`

- `search_tracks(query)` - Recherche par titre
- `download_preview(preview_url)` - Download audio 30s
- `get_track_metadata(track_id)` - Infos track
- `get_top_tracks(total_count)` - Récupère top N chansons des charts

#### `EmbeddingService`

- `load_audio(audio_path)` - Charge et préprocesse audio (48kHz)
- `generate_embedding(audio_path)` - Génère vecteur embedding CLAP (512-dim)
- `calculate_similarity(embedding1, embedding2)` - Cosine similarity

#### `VectorDBService`

- `add_track(track_id, embedding, metadata)` - Ajoute une chanson
- `bulk_add_tracks(track_ids, embeddings, metadatas)` - Ajout en batch
- `query_similar(embedding, n_results)` - Trouve les N plus similaires
- `track_exists(track_id)` - Vérifie si chanson existe
- `count_tracks()` - Compte total de chansons

### Frontend - Composants

#### `SearchBar`

- Input simple (pas de debounce)
- Submit direct au backend
- Pas de suggestions

#### `ConfirmationCard`

- Affiche track trouvé: cover, titre, artiste
- Message: "C'est bien ce morceau que vous voulez rechercher?"
- Audio player intégré (preview 30s)
- Boutons: "Oui, continuer" / "Non, annuler"

#### `ResultCard`

- Affiche: cover, titre, artiste
- Play button pour preview (30s)
- Button "Save to Spotify" (placeholder)

#### `ResultsGrid`

- Grid de 3 cards
- Layout responsive

---

## Pipeline d'analyse audio

### Initialisation (une seule fois au démarrage)

1. **Récupération top 1000**: Deezer API charts
2. **Download batch**: 1000 previews MP3 (30s)
3. **Génération embeddings**: CLAP sur chaque preview
4. **Stockage**: ChromaDB avec métadonnées (title, artist, rank, preview_url, cover)

### Recherche en temps réel (par requête utilisateur)

1. **Download**: MP3 30s de la chanson recherchée
2. **Load**: librosa.load() → waveform @ 48kHz
3. **Preprocess**:
   - Resample à 48kHz (requis par CLAP)
   - Pad/trim à 10 secondes
   - Normalisation amplitude
4. **Embedding**: Modèle CLAP → vecteur 512-dim
5. **Query vector DB**: ChromaDB cosine similarity → top 10
6. **Filter**: Tri par popularité → top 3

---

## Initialisation de la base de données

### Script: `scripts/init_vector_db.py`

**Objectif**: Créer et peupler la base vectorielle avec les top 1000 chansons Deezer

**Étapes**:

1. Récupérer les top 1000 chansons via `DeezerService.get_top_tracks(1000)`
2. Pour chaque chanson:
   - Télécharger le preview audio (30s)
   - Générer l'embedding avec `EmbeddingService.generate_embedding()`
   - Stocker dans ChromaDB via `VectorDBService.add_track()`
3. Gérer les erreurs (preview manquant, timeout, etc.)
4. Logger la progression (ex: "Processed 250/1000 tracks")

**Usage**:

```bash
python scripts/init_vector_db.py
```

**Note**: Ce script doit être exécuté une fois avant le premier lancement de l'application. La base peut ensuite être étendue via l'endpoint `/api/admin/add-tracks`.

---

## Extension de la base de données

### Endpoint: `POST /api/admin/add-tracks`

Permet d'ajouter de nouvelles chansons à la base vectorielle.

```json
Request: { "track_ids": ["123456", "789012"] }
Response: {
  "status": "success",
  "added_count": 2,
  "message": "2 tracks added to database"
}
```

**Workflow**:

1. Pour chaque `track_id`:
   - Vérifier si déjà dans la DB
   - Télécharger metadata + preview
   - Générer embedding
   - Ajouter à ChromaDB
2. Retourner le nombre de chansons ajoutées

---

## Optimisations Hackathon

### Phase 1 (MVP - 4h)

- Backend: Deezer API + librosa features uniquement (skip HF initialement)
- Frontend: SearchBar → ConfirmationCard → ResultsGrid (3 cards)
- Similarity: Cosine sur MFCC + spectral features
- Flow complet: recherche → confirmation → analyse → 3 résultats

### Phase 2 (Enhancement - 2h)

- Intégrer modèle HF pour embeddings (amélioration similarité)
- Améliorer UI/UX (animations, transitions)
- Cache embeddings calculés
- Gestion erreurs robuste

### Phase 3 (Polish - 1-2h)

- Loading states élégants
- Placeholder "Save to Spotify" (si temps)
- Polish visuel final
- Tests end-to-end

---

## Stack technique détaillée

### Python dependencies

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2

# Audio processing
librosa==0.10.2
soundfile==0.12.1

# ML & Embeddings
torch==2.5.1
transformers==4.46.2
laion-clap==1.1.4

# Vector database
chromadb==0.5.20

# HTTP & API
requests==2.32.3
httpx==0.27.2

# Utilities
numpy==1.26.4
scipy==1.14.1
python-multipart==0.0.12
```

### React dependencies

```
react
typescript
vite
tailwindcss
axios
react-query
```

---

## Points d'attention

1. **Rate limiting Deezer**: Max 50 req/5sec → Batch downloads avec délai
2. **Initialisation DB**: Première exécution peut prendre 30-60 min (1000 tracks)
3. **Storage audio**: Nettoyer files temporaires après génération embeddings
4. **CORS**: Configurer backend pour frontend
5. **Modèle CLAP**: ~600MB → téléchargement automatique au premier lancement
6. **ChromaDB**: Base persistante dans `backend/app/db/vector_store/`

---

## Démo flow

1. User tape "Stairway to Heaven" (recherche exacte)
2. Backend retourne premier match Deezer
3. Confirmation: "C'est bien ce morceau que vous voulez rechercher?" avec preview audio
4. User play l'extrait et clique "Oui, continuer"
5. Backend:
   - Génère embedding CLAP du preview
   - Query ChromaDB → top 10 similaires
   - Filtre par popularité → top 3
6. Retourne 3 tracks mélodiquement similaires
7. User voit 3 cards avec preview audio jouable
