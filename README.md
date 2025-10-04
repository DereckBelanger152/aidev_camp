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
│   │   │   ├── audio_analysis_service.py
│   │   │   └── embedding_service.py
│   │   └── models/
│   │       └── schemas.py
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
   - Backend télécharge preview MP3 (30s)
   - Preprocessing audio (librosa)
   - Génération embedding via modèle HF
   - Feature vector extrait

4. **Recherche similaire**:
   - Pré-filtrage: Embedding model HF sur catalogue Deezer
   - Filtrage fin: Bibliothèque Python (librosa features + cosine similarity)
   - Sélection top-3 tracks mélodiquement similaires

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

#### `POST /api/analyze`
```json
Request: { "track_id": "3135556" }
Response: {
  "status": "processing",
  "message": "Analyse en cours..."
}
```

#### `GET /api/recommendations/{track_id}`
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

1. User tape "Stairway to Heaven" (recherche exacte)
2. Backend retourne premier match Deezer
3. Confirmation: "C'est bien ce morceau que vous voulez rechercher?" avec preview audio
4. User play l'extrait et clique "Oui, continuer"
5. Backend: analyse → embedding HF → filtrage librosa
6. Retourne 3 tracks mélodiquement similaires (guitare acoustique/électrique, structure/tempo similaire)
7. User voit 3 cards, peut play previews et (optionnel) save to Spotify
