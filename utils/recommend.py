import pandas as pd
import numpy as np
from collections import Counter
from sklearn.preprocessing import MinMaxScaler


def get_recommendations(favorite_books_list, works_df, top_n=10):

    print(f"Libro fav: {favorite_books_list} -")
    
    # Extraer solo los work_ids y convertir a enteros
    favorite_ids = [int(book_id) for _, book_id in favorite_books_list]
    print(f"Libro fav ID: {favorite_ids} -")
    print(f"analizando {len(favorite_ids)} libros favoritos...")
    works_df['work_id'] = works_df['work_id'].astype(int)
    # Obtener información de libros favoritos
    fav_books = works_df[works_df['work_id'].isin(favorite_ids)].copy()
    
    if fav_books.empty:
        print("❌ No se encontraron libros favoritos")
        return works_df.head(top_n)
    
    # 1. ANÁLISIS DE PREFERENCIAS DEL USUARIO
    genre_counter = Counter()
    author_preferences = Counter()
    year_preferences = []
    rating_preferences = []
    
    for _, book in fav_books.iterrows():
        # Géneros preferidos
        if pd.notna(book['genres']):
            genres = [g.strip().lower() for g in book['genres'].split(',')]
            genre_counter.update(genres)
        
        # Autores preferidos
        if pd.notna(book['author']):
            author_preferences[book['author']] += 1
        
        # Años de publicación preferidos
        if pd.notna(book['original_publication_year']):
            year_preferences.append(book['original_publication_year'])
        
        # Ratings preferidos
        if pd.notna(book['avg_rating']):
            rating_preferences.append(book['avg_rating'])
    
    # Obtener preferencias principales
    top_genres = [g for g, _ in genre_counter.most_common(5)]  # Top 5 géneros
    top_authors = set([a for a, _ in author_preferences.most_common(3)])
    
    avg_year_pref = np.mean(year_preferences) if year_preferences else 2000
    avg_rating_pref = np.mean(rating_preferences) if rating_preferences else 4.0
    
    print(f"Géneros preferidos: {top_genres[:3]}")
    print(f"Autores preferidos: {list(top_authors)[:2]}")
    
    # 2. OBTENER LIBROS SIMILARES
    similar_ids = set()
    for similar_books_str in fav_books['similar_books'].dropna():
        try:
            similar_list = [int(x.strip()) for x in similar_books_str.split(',') if x.strip().isdigit()]
            similar_ids.update(similar_list)
        except:
            continue
    
    # 3. PREPARAR CANDIDATOS
    candidates = works_df[~works_df['work_id'].isin(favorite_ids)].copy()
    candidates = candidates.dropna(subset=['avg_rating', 'ratings_count'])
    
    # Filtrar libros con muy pocas reseñas (ruido)
    candidates = candidates[candidates['ratings_count'] >= 50]
    
    # 4. CALCULAR SCORES DE SIMILARIDAD
    
    # Score por libros similares (máximo peso)
    candidates['similarity_score'] = candidates['work_id'].isin(similar_ids).astype(int) * 3
    
    # Score por géneros (personalizado por usuario)
    candidates['genres'] = candidates['genres'].fillna('')
    candidates['genre_score'] = candidates['genres'].apply(
        lambda g: calculate_genre_similarity(g, top_genres, genre_counter)
    )
    
    # Score por autor (bonus moderado)
    candidates['author_score'] = candidates['author'].isin(top_authors).astype(int) * 1.5
    
    # Score por rating (preferencia de calidad)
    candidates['rating_score'] = candidates['avg_rating'].apply(
        lambda x: max(0, 2 - abs(x - avg_rating_pref))  # Penaliza diferencias grandes
    )
    
    # Score por época (preferencia temporal)
    candidates['year_score'] = candidates['original_publication_year'].apply(
        lambda x: max(0, 1 - abs(x - avg_year_pref) / 20) if pd.notna(x) else 0
    )
    
    # 5. DIVERSIDAD Y ANTI-MAINSTREAM
    
    # Penalizar libros demasiado populares (diversidad)
    scaler = MinMaxScaler()
    candidates['popularity_norm'] = scaler.fit_transform(candidates[['ratings_count']])
    candidates['diversity_bonus'] = (1 - candidates['popularity_norm']) * 0.5
    
    # Bonus por diversidad de géneros
    user_genre_set = set(top_genres)
    candidates['diversity_genre_bonus'] = candidates['genres'].apply(
        lambda g: calculate_genre_diversity_bonus(g, user_genre_set)
    )
    
    # 6. SCORE FINAL PONDERADO
    candidates['final_score'] = (
        candidates['similarity_score'] * 0.35 +      # 35% - Libros similares
        candidates['genre_score'] * 0.25 +           # 25% - Géneros preferidos  
        candidates['rating_score'] * 0.20 +          # 20% - Calidad del libro
        candidates['author_score'] * 0.10 +          # 10% - Autores conocidos
        candidates['year_score'] * 0.05 +            # 5% - Época preferida
        candidates['diversity_bonus'] * 0.03 +       # 3% - Anti-mainstream
        candidates['diversity_genre_bonus'] * 0.02   # 2% - Diversidad de géneros
    )
    
    # 7. RANDOMIZACIÓN CONTROLADA PARA DIVERSIDAD
    # Tomar top 30 y randomizar un poco el orden
    top_candidates = candidates.nlargest(min(top_n * 3, 30), 'final_score')
    
    # Aplicar un pequeño factor aleatorio para diversificar
    np.random.seed(hash(str(favorite_ids)) % 1000)  # Seed basado en favoritos
    top_candidates['random_factor'] = np.random.normal(0, 0.1, len(top_candidates))
    top_candidates['final_score'] += top_candidates['random_factor']
    
    # 8. SELECCIÓN FINAL CON DIVERSIDAD
    recommendations = select_diverse_recommendations(top_candidates, top_n, top_genres)
    
    print(f"Generadas {len(recommendations)} recomendaciones únicas")
    print(f"Work IDs recomendados: {recommendations['work_id'].tolist()}")
    
    return recommendations

def calculate_genre_similarity(book_genres_str, user_top_genres, genre_counter):
    """Calcula similaridad de géneros ponderada por preferencias del usuario"""
    if not book_genres_str:
        return 0
    
    book_genres = [g.strip().lower() for g in book_genres_str.split(',')]
    score = 0
    
    for genre in book_genres:
        if genre in user_top_genres:
            # Peso basado en qué tan frecuente es este género en los favoritos
            genre_weight = genre_counter.get(genre, 0) / max(genre_counter.values())
            score += 1 + genre_weight  # Base + peso por frecuencia
    
    return min(score, 3)  # Cap máximo

def calculate_genre_diversity_bonus(book_genres_str, user_genre_set):
    """Bonus por introducir géneros nuevos pero relacionados"""
    if not book_genres_str:
        return 0
    
    book_genres = set([g.strip().lower() for g in book_genres_str.split(',')])
    
    # Géneros relacionados que podrían interesar
    genre_expansion = {
        'fantasy': ['science fiction', 'mythology', 'adventure'],
        'romance': ['contemporary', 'historical fiction', 'drama'],
        'mystery': ['thriller', 'crime', 'suspense'],
        'science fiction': ['fantasy', 'dystopian', 'adventure'],
        'historical fiction': ['biography', 'war', 'drama'],
        'young adult': ['coming of age', 'contemporary', 'fantasy']
    }
    
    expanded_interests = set(user_genre_set)
    for user_genre in user_genre_set:
        if user_genre in genre_expansion:
            expanded_interests.update(genre_expansion[user_genre])
    
    # Bonus si tiene géneros relacionados pero no exactos
    new_related_genres = book_genres.intersection(expanded_interests) - user_genre_set
    return len(new_related_genres) * 0.3

def select_diverse_recommendations(candidates, top_n, user_genres):
    """Selecciona recomendaciones diversas evitando demasiada repetición"""
    
    selected = []
    used_authors = set()
    genre_count = Counter()
    
    # Ordenar por score final
    sorted_candidates = candidates.sort_values('final_score', ascending=False)
    
    for _, book in sorted_candidates.iterrows():
        if len(selected) >= top_n:
            break
        
        # Evitar demasiados libros del mismo autor
        if book['author'] in used_authors and len([s for s in selected if s['author'] == book['author']]) >= 2:
            continue
        
        # Evitar saturación de un solo género
        book_genres = [g.strip().lower() for g in book['genres'].split(',') if g.strip()]
        main_genre = book_genres[0] if book_genres else 'unknown'
        
        if genre_count[main_genre] >= max(2, top_n // 3):  # Máximo 2 o 1/3 del total
            continue
        
        # Agregar a seleccionados
        selected.append(book)
        used_authors.add(book['author'])
        genre_count[main_genre] += 1
    
    # Si no tenemos suficientes, completar con los mejores restantes
    if len(selected) < top_n:
        #remaining = top_n - len(selected)
        for _, book in sorted_candidates.iterrows():
            if len(selected) >= top_n:
                break
            if not any(s['work_id'] == book['work_id'] for s in selected):
                selected.append(book)
    
    return pd.DataFrame(selected)