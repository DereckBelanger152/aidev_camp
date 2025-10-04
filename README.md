# aider_camp

Repo pour le AI Dev Camp Mirego - Application de recommandation musicale par analyse audio

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
  - Hugging Face Transformers (audio embeddings)
  - Modèle suggéré: `facebook/wav2vec2-base` ou `MIT/ast-finetuned-audioset`
- **Similarity Search**:
  - scikit-learn (cosine similarity)
  - FAISS (pour optimisation si nécessaire)

---

## Structure du projet

```
aider_camp/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── TrackCard.tsx
│   │   │   ├── AudioPlayer.tsx
│   │   │   └── RecommendationGrid.tsx
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
│   │   │   ├── audio_analysis_service.py
│   │   │   └── embedding_service.py
│   │   └── models/
│   │       └── schemas.py
│   └── requirements.txt
└── README.md
```

---

## Flux de données

1. **Recherche**: User entre titre → Frontend → Backend → Deezer API → Résultats
2. **Sélection**: User clique sur track → Backend télécharge preview (30s)
3. **Analyse**: Audio → Preprocessing → Embedding Model → Feature vector
4. **Recherche similaire**:
   - Backend récupère catalogue Deezer (ou DB pré-calculée)
   - Calcule embeddings pour tracks candidats
   - Cosine similarity entre vecteurs
   - Retourne top-N similaires
5. **Affichage**: Cards avec preview, play button, métadonnées

---

## Composants clés

### Backend - Endpoints

#### `POST /api/search`
```json
Request: { "query": "Bohemian Rhapsody" }
Response: [
  {
    "id": "3135556",
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "preview_url": "https://...",
    "cover": "https://..."
  }
]
```

#### `POST /api/recommend`
```json
Request: { "track_id": "3135556" }
Response: [
  {
    "id": "...",
    "title": "...",
    "artist": "...",
    "similarity_score": 0.92,
    "preview_url": "...",
    "cover": "..."
  }
]
```

### Backend - Services

#### `DeezerService`
- `search_tracks(query)` - Recherche par titre
- `get_track_preview(track_id)` - Download audio 30s
- `get_track_metadata(track_id)` - Infos track

#### `AudioAnalysisService`
- `extract_features(audio_file)` - Librosa features:
  - Spectral centroid
  - Chroma features
  - MFCC
  - Tempo/beat
  - Zero crossing rate

#### `EmbeddingService`
- `load_model()` - Charge modèle HF
- `generate_embedding(audio_features)` - Vecteur embedding
- `calculate_similarity(embedding1, embedding2)` - Cosine similarity

### Frontend - Composants

#### `SearchBar`
- Input + debounce
- Affiche suggestions temps réel
- Gère sélection

#### `TrackCard`
- Affiche cover, titre, artiste
- Button "Find Similar"
- Mini player intégré

#### `RecommendationGrid`
- Grid responsive de cards
- Score de similarité visible
- Auto-play optionnel

---

## Pipeline d'analyse audio

1. **Download**: MP3 30s depuis Deezer
2. **Load**: librosa.load() → waveform + sample rate
3. **Preprocess**:
   - Resample si nécessaire (16kHz pour modèles)
   - Normalisation amplitude
4. **Feature extraction**:
   - Low-level: MFCC, spectral features
   - High-level: Embedding model HF
5. **Combine features**: Concat ou weighted average
6. **Normalize**: L2 normalization pour cosine similarity

---

## Optimisations Hackathon

### Phase 1 (MVP - 4h)
- Backend: Deezer API + librosa features uniquement (skip HF)
- Frontend: Search + 1 player + grid simple
- Similarity: Cosine sur MFCC seulement

### Phase 2 (Enhancement - 2h)
- Intégrer modèle HF pour embeddings
- Améliorer UI/UX
- Cache embeddings calculés

### Phase 3 (Polish - 2h)
- Animations
- Gestion erreurs
- Loading states
- Deploy

---

## Stack technique détaillée

### Python dependencies
```
fastapi
uvicorn
librosa
torch
transformers
numpy
scipy
scikit-learn
requests
python-multipart
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

1. **Rate limiting Deezer**: Max 50 req/5sec
2. **Latence embeddings**: Pré-calculer si possible
3. **Storage audio**: Nettoyer files temporaires
4. **CORS**: Configurer backend pour frontend
5. **Modèle HF**: Choisir léger (< 500MB) pour rapidité

---

## Démo flow

1. User tape "Stairway to Heaven"
2. Sélectionne track Led Zeppelin
3. Backend analyse → 512-dim embedding
4. Compare avec 100 tracks populaires (pré-indexées)
5. Retourne 12 tracks similaires (prog rock, guitare acoustique/électrique, structure similaire)
6. User écoute previews dans grid
