import streamlit as st
import pandas as pd
from utils.recommend import get_recommendations
import time


@st.cache_data
def load_data_works():
    works = pd.read_csv('https://huggingface.co/datasets/Pauleera/Goodreads-Book-Reviews/resolve/main/goodreads_works.csv')
    works['original_title'] = works['original_title'].fillna('').astype(str)
    works['author'] = works['author'].fillna('').astype(str)
    works['description'] = works['description'].fillna('').astype(str)
    works['genres'] = works['genres'].fillna('').astype(str)
    works['work_id'] = works['work_id'].fillna(0).astype(int).astype(str)

    # Crear una columna combinada para búsqueda
    works['searchable_text'] = (
        works['original_title'] + ' ' +
        works['author'] + ' ' +
        works['description'] + ' ' +
        works['genres'] + ' ' +
        works['work_id']
    ).str.lower()

    return works

@st.cache_data
def load_data_reviews():
    reviews = pd.read_csv('https://huggingface.co/datasets/Pauleera/Goodreads-Book-Reviews/resolve/main/goodreads_reviews.csv')
    reviews['date_added'] = pd.to_datetime(reviews['date_added']).dt.date
    reviews['work_id'] = reviews['work_id'].astype(str)  # Convertir una sola vez
    return reviews

@st.cache_data(show_spinner=False)
def search_books(query, works_data):
    if len(query) < 3:
        return pd.DataFrame()
    
    query_lower = query.lower()
    mask = works_data['searchable_text'].str.contains(query_lower, na=False, regex=False)
    filtered_results = works_data[mask]
    
    if filtered_results.empty:
        return pd.DataFrame()
    
    cols_to_show = ['original_title', 'author', 'reviews_count', 'work_id']
    if 'image_url' in filtered_results.columns:
        cols_to_show.append('image_url')
    if 'avg_rating' in filtered_results.columns:
        cols_to_show.append('avg_rating')
    
    suggestions = filtered_results[cols_to_show].drop_duplicates()
    suggestions = suggestions.sort_values(by='reviews_count', ascending=False).head(15)  # Reducido a 10
    return suggestions

# Configuración de la página
st.set_page_config(layout="wide", page_title="Summer Reading List")

# Cargar datos solo una vez
@st.cache_resource
def initialize_data():
    works = load_data_works()
    reviews = load_data_reviews()
    return works, reviews

works, reviews = initialize_data()

if works.empty:
    st.stop()

# Inicializar estados de sesión de forma más eficiente
def init_session_state():
    defaults = {
        "favorites": [],
        "readinglist": [],
        "recommendations": None,
        "show_recommendations": False,
        "search_query": "",
        "last_search_time": 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

st.title("Your Perfect Summer Reading List! 📚", anchor='top')

# Usar tabs para mejor organización y rendimiento
tab1, tab2, tab3 = st.tabs(["🔍 Search Books", "🎯 Get Recommendations", "📚 My Lists"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Búsqueda con debounce
        book_input = st.text_input(
            "Search by title, author or genre:",
            value="",
            placeholder="Example: Harry Potter, Stephen King, romance...",
            key="book_search_input"
        )
        
        # Solo buscar si la query cambió y pasó suficiente tiempo (debounce)
        current_time = time.time()
        should_search = (
            len(book_input) >= 3 and 
            book_input != st.session_state.get("last_query", "") and
            current_time - st.session_state.last_search_time > 0.5  # 500ms debounce
        )
        
        if should_search:
            st.session_state.last_query = book_input
            st.session_state.last_search_time = current_time
            
            with st.spinner("🔍 Searching..."):
                suggestions = search_books(book_input, works)
            
            # Guardar resultados en session state para evitar recálculos
            st.session_state.search_results = suggestions
        
        # Mostrar resultados guardados
        if hasattr(st.session_state, 'search_results') and not st.session_state.search_results.empty and len(book_input) >= 3:
            suggestions = st.session_state.search_results
            st.write(f"📚 **{len(suggestions)} results for '{book_input}':**")
            
            # Mostrar resultados en formato más compacto
            for idx, (_, row) in enumerate(suggestions.iterrows()):
                with st.container():
                    # Layout más compacto
                    img_col, info_col, btn_col = st.columns([1, 4, 2])
                    
                    with img_col:
                        if 'image_url' in row and pd.notna(row['image_url']) and row['image_url']:
                            try:
                                st.image(row['image_url'], width=60)
                            except:
                                st.write("📖")
                        else:
                            st.write("📖")
                    
                    with info_col:
                        st.write(f"**{row['original_title']}**")
                        st.write(f"*{row['author']}*")
                        if 'avg_rating' in row and pd.notna(row['avg_rating']):
                            rating = float(row['avg_rating'])
                            st.write(f"⭐ {rating:.1f}")
                    
                    with btn_col:
                        # Botones más compactos
                        book_title = row['original_title']
                        book_id = row['work_id']
                        
                        # Check si ya está en favoritos/lista
                        in_favorites = any(fav[0] == book_title for fav in st.session_state.favorites)
                        in_reading_list = book_title in st.session_state.readinglist
                        
                        if not in_favorites:
                            if st.button("❤️ I Like it!", key=f"fav_{idx}_{book_id}", help="Add to favorites"):
                                st.session_state.favorites.append((book_title, book_id))
                                st.success("Added to favorites!")
                                time.sleep(0.5)  # Breve pausa para mostrar feedback
                                st.rerun()
                        else:
                            st.write("❤️ Added")
                        
                        if not in_reading_list:
                            if st.button("📚 Reading list", key=f"read_{idx}_{book_id}", help="Add to reading list"):
                                st.session_state.readinglist.append(book_title)
                                st.success("Added to reading list!")
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.write("📚 Added")
                
                if idx < len(suggestions) - 1:
                    st.divider()
            #Botón para ir anchor #top
            st.markdown("[⬆️ Go to top](#top)", unsafe_allow_html=True)
        
        elif len(book_input) >= 3 and hasattr(st.session_state, 'search_results') and st.session_state.search_results.empty:
            st.info("No books found 😔")
        elif book_input and len(book_input) < 3:
            st.info("Please type at least 3 characters")
    
    with col2:
        st.markdown("### Quick Stats")
        st.metric("Favorites", len(st.session_state.favorites), delta=None)
        st.metric("Reading List", len(st.session_state.readinglist), delta=None)

with tab2:
    st.markdown("""
    ### 🎯 Get Personalized Recommendations
    
    **How it works:**
    1. Add favorite books from the search tab, click the ❤️.
    2. Click the button below to get recommendations ✨.
    3. Add recommended books to your reading list, click the 📚.
    """)
    
    fav_count = len(st.session_state.favorites)
    
    if fav_count > 0:
        st.success(f"Great! You have {fav_count} favorite books.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✨ Generate Recommendations", use_container_width=True, type="primary"):
                with st.spinner("🤖 Creating your personalized recommendations..."):
                    st.session_state.recommendations = get_recommendations(st.session_state.favorites, works)
                    st.session_state.show_recommendations = True
                st.success("Recommendations generated!")
                st.rerun()
        
        with col2:
            if st.button("🔄 New Recommendations", use_container_width=True):
                st.session_state.show_recommendations = False
                st.session_state.recommendations = None
    else:
        st.warning("Add some favorite books first from the Search tab!")
    
    # Mostrar recomendaciones
    if st.session_state.show_recommendations and st.session_state.recommendations is not None:
        st.markdown("### 🎯 Your Recommendations")
        
        if not st.session_state.recommendations.empty:

            for idx, (_, row) in enumerate(st.session_state.recommendations.head(8).iterrows()):
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if pd.notna(row["image_url"]):
                            st.image(row["image_url"], width=120)
                        else:
                            st.write("📖")
                    
                    with col2:
                        # Información básica del libro
                        year = int(row['original_publication_year']) if pd.notna(row['original_publication_year']) else 'N/A'
                        st.markdown(f"### {row['original_title']} ({year})")
                        st.markdown(f"**Author:** {row['author']}")
                        st.markdown(f"**Genres:** {row['genres']}")
                        
                        if pd.notna(row['avg_rating']):
                            rating = int(float(row['avg_rating']))
                            stars = '★' * rating + '☆' * (5 - rating)
                            st.markdown(f"**Rating:** {stars} ({row['avg_rating']}/5)")
                        
                        # Botón para añadir a lista de lectura
                        book_title = row['original_title']
                        if book_title not in st.session_state.readinglist:
                            if st.button(f"📚 Add to Reading List", key=f"rec_{idx}_{row['work_id']}"):
                                st.session_state.readinglist.append(book_title)
                                st.success("Added to reading list!")
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.success("✅ Already in reading list")
                        
                        # Popover con descripción completa y comentarios
                        with st.popover("More info", icon="➕", use_container_width=True):
                            # Descripción completa
                            full_desc = row['description'] if pd.notna(row['description']) else 'No description available'
                            st.markdown(f"**Full Description:**")
                            st.write(full_desc)
                            
                            st.divider()
                            
                            # Comentarios/Reviews
                            st.markdown("**User Reviews:**")
                            
                            # Filtrar reviews para este libro específico
                            book_reviews = reviews[reviews['work_id'] == str(row['work_id'])].head(10)
                            
                            if not book_reviews.empty:
                                # Ordenar por rating descendente
                                sorted_reviews = book_reviews.sort_values(by='rating', ascending=False)
                                
                                for review_idx, (_, review) in enumerate(sorted_reviews.iterrows()):
                                    rating_stars = "⭐" * int(review['rating']) if pd.notna(review['rating']) else "No rating"
                                    review_date = review['date_added'] if pd.notna(review['date_added']) else 'No date'
                                    
                                    with st.expander(f"{rating_stars} - {review_date}", expanded=False):
                                        review_text = review['review_text'] if pd.notna(review['review_text']) else 'No review text available'
                                        st.write(review_text)
                            else:
                                st.info("No reviews available for this book.")
                    
                    if idx < len(st.session_state.recommendations) - 1:
                        st.markdown("---")
            st.markdown("[⬆️ Go to top](#top)", unsafe_allow_html=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⭐ My Favorites")
        if st.session_state.favorites:
            for i, (book_title, book_id) in enumerate(st.session_state.favorites[:10]):  
                col_book, col_remove = st.columns([4, 1])
                with col_book:
                    st.write(f"{i+1}. {book_title}")
                with col_remove:
                    if st.button("❌", key=f"rm_fav_{i}", help="Remove"):
                        st.session_state.favorites.remove((book_title, book_id))
                        st.session_state.show_recommendations = False
                        st.rerun()
            
            if len(st.session_state.favorites) > 10:
                st.info(f"...and {len(st.session_state.favorites) - 10} more books")
            
            if st.button("🗑️ Clear All Favorites", type="secondary"):
                st.session_state.favorites = []
                st.session_state.show_recommendations = False
                st.rerun()
        else:
            st.info("No favorites yet!")
    
    with col2:
        st.markdown("### 📚 My Reading List")
        if st.session_state.readinglist:
            for i, book in enumerate(st.session_state.readinglist[:15]):  # Límite de 15
                col_book, col_remove = st.columns([4, 1])
                with col_book:
                    st.write(f"{i+1}. {book}")
                with col_remove:
                    if st.button("❌", key=f"rm_read_{i}", help="Remove"):
                        st.session_state.readinglist.remove(book)
                        st.rerun()
            
            if len(st.session_state.readinglist) > 15:
                st.info(f"...and {len(st.session_state.readinglist) - 15} more books")
            
            st.markdown("### 📸 Capture your list to save:")
            st.code("\n".join([f"{i+1}. {book}" for i, book in enumerate(st.session_state.readinglist)]), language="markdown")

            
            if st.button("🗑️ Clear Reading List", type="secondary"):
                st.session_state.readinglist = []
                st.rerun()
        else:
            st.info("No books in reading list yet!")

# Footer con estadísticas
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Books in Database", f"{len(works):,}")
with col2:
    st.metric("❤️ My Favorites", len(st.session_state.favorites))
with col3:
    st.metric("📚 Reading List", len(st.session_state.readinglist))
with col4:
    if st.button("🔄 Refresh App"):
        st.rerun()