import streamlit as st
import pandas as pd
import requests
from io import StringIO
import sys
import traceback
import time

# Configuración básica
st.set_page_config(
    page_title="Summer Reading List",
    page_icon="📚",
    layout="wide"
)

@st.cache_data(ttl=3600, show_spinner=False)
def load_dataset_safe(url, dataset_name, max_retries=3):
    """Cargar dataset con manejo robusto de errores"""
    
    for attempt in range(max_retries):
        try:
            st.info(f"🔄 Loading {dataset_name}... (Attempt {attempt + 1}/{max_retries})")
            
            # Configurar timeout y headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Request con timeout
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            
            st.success(f"✅ Downloaded {dataset_name} ({len(response.content)} bytes)")
            
            # Convertir a DataFrame
            df = pd.read_csv(StringIO(response.text))
            st.success(f"✅ Parsed {dataset_name}: {len(df)} rows, {len(df.columns)} columns")
            
            return df
            
        except requests.exceptions.Timeout:
            st.warning(f"⏰ Timeout loading {dataset_name} (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial
            continue
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network error loading {dataset_name}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue
            
        except pd.errors.EmptyDataError:
            st.error(f"❌ {dataset_name} is empty or corrupted")
            break
            
        except Exception as e:
            st.error(f"❌ Unexpected error loading {dataset_name}: {str(e)}")
            st.code(traceback.format_exc())
            break
    
    st.error(f"❌ Failed to load {dataset_name} after {max_retries} attempts")
    return pd.DataFrame()

def process_works_data_safe(works):
    """Procesar datos de works con manejo de errores"""
    try:
        st.info("🔄 Processing books data...")
        
        original_size = len(works)
        st.write(f"📊 Original size: {original_size} books")
        
        # Verificar columnas esenciales
        required_cols = ['work_id', 'original_title', 'author']
        missing_cols = [col for col in required_cols if col not in works.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {missing_cols}")
            st.write("Available columns:", works.columns.tolist())
            return pd.DataFrame()
        
        # Procesamiento paso a paso
        works = works.copy()
        
        # Limpieza básica
        works['original_title'] = works['original_title'].fillna('Unknown').astype(str)
        works['author'] = works['author'].fillna('Unknown').astype(str)
        works['description'] = works['description'].fillna('').astype(str)
        works['genres'] = works['genres'].fillna('').astype(str)
        
        # work_id processing
        if works['work_id'].dtype != 'int64':
            works['work_id'] = pd.to_numeric(works['work_id'], errors='coerce').fillna(0).astype(int)
        
        works['work_id'] = works['work_id'].astype(str)
        
        # Crear texto buscable (sin esta parte primero)
        st.info("🔄 Creating searchable text...")
        works['searchable_text'] = (
            works['original_title'] + ' ' +
            works['author'] + ' ' +
            works['genres']
        ).str.lower()
        
        # Filtrar libros válidos
        valid_books = works[
            (works['original_title'] != 'Unknown') & 
            (works['author'] != 'Unknown') &
            (works['work_id'] != '0')
        ]
        
        st.success(f"✅ Processed books: {len(valid_books)} valid books from {original_size}")
        
        return valid_books
        
    except Exception as e:
        st.error(f"❌ Error processing books data: {str(e)}")
        st.code(traceback.format_exc())
        return pd.DataFrame()

def process_reviews_data_safe(reviews):
    """Procesar datos de reviews con manejo de errores"""
    try:
        st.info("🔄 Processing reviews data...")
        
        original_size = len(reviews)
        st.write(f"📊 Original reviews: {original_size}")
        
        # Verificar columnas esenciales
        required_cols = ['work_id', 'rating']
        missing_cols = [col for col in required_cols if col not in reviews.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns in reviews: {missing_cols}")
            return pd.DataFrame()
        
        reviews = reviews.copy()
        
        # Procesar fechas con manejo de errores
        if 'date_added' in reviews.columns:
            reviews['date_added'] = pd.to_datetime(reviews['date_added'], errors='coerce').dt.date
        
        # work_id consistency
        reviews['work_id'] = reviews['work_id'].astype(str)
        
        # Filtrar reviews válidas
        valid_reviews = reviews.dropna(subset=['work_id'])
        
        st.success(f"✅ Processed reviews: {len(valid_reviews)} valid reviews from {original_size}")
        
        return valid_reviews
        
    except Exception as e:
        st.error(f"❌ Error processing reviews data: {str(e)}")
        st.code(traceback.format_exc())
        return pd.DataFrame()

def main():
    st.title("📚 Summer Reading List - Data Loading Test")
    
    try:
        st.info("🚀 Starting data loading process...")
        
        # URLs de tus datasets (REEMPLAZA CON TUS URLs REALES)
        WORKS_URL = 'https://huggingface.co/datasets/Pauleera/Goodreads-Book-Reviews/resolve/main/goodreads_works.csv'
        REVIEWS_URL = 'https://huggingface.co/datasets/Pauleera/Goodreads-Book-Reviews/resolve/main/goodreads_reviews.csv'
        # Test con URLs de ejemplo (comenta esto cuando tengas las URLs reales)
        st.warning("⚠️ Using test URLs - Replace with your actual Hugging Face URLs")
        
        # Para testing, usa datasets más pequeños primero
        st.info("📝 **PASO 1: Configura tus URLs de Hugging Face**")
        st.code("""
# Reemplaza estas URLs con las tuyas:
WORKS_URL = "https://huggingface.co/datasets/TU-USUARIO/TU-DATASET/resolve/main/goodreads_works.csv"
REVIEWS_URL = "https://huggingface.co/datasets/TU-USUARIO/TU-DATASET/resolve/main/goodreads_reviews.csv"
        """)
        
        # Opción manual para testing
        st.info("📝 **PASO 2: Test manual**")
        
        url_works = st.text_input("URL del dataset de libros:", value="")
        url_reviews = st.text_input("URL del dataset de reviews:", value="")
        
        if st.button("🚀 Test Data Loading") and url_works:
            
            with st.spinner("Loading data..."):
                # Cargar works
                works = load_dataset_safe(url_works, "Books Dataset")
                
                if not works.empty:
                    # Procesar works
                    works = process_works_data_safe(works)
                    
                    if not works.empty:
                        st.balloons()
                        st.success("🎉 Books data loaded successfully!")
                        
                        # Mostrar preview
                        st.subheader("📋 Books Preview")
                        st.dataframe(works.head())
                        
                        # Stats
                        st.subheader("📊 Books Statistics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Books", len(works))
                        with col2:
                            st.metric("Unique Authors", works['author'].nunique())
                        with col3:
                            st.metric("With Descriptions", works['description'].str.len().gt(10).sum())
                        
                        # Test reviews si se proporciona URL
                        if url_reviews:
                            st.info("🔄 Loading reviews...")
                            reviews = load_dataset_safe(url_reviews, "Reviews Dataset")
                            
                            if not reviews.empty:
                                reviews = process_reviews_data_safe(reviews)
                                
                                if not reviews.empty:
                                    st.success("🎉 Reviews data loaded successfully!")
                                    
                                    st.subheader("📊 Reviews Statistics") 
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Total Reviews", len(reviews))
                                    with col2:
                                        if 'rating' in reviews.columns:
                                            avg_rating = reviews['rating'].mean()
                                            st.metric("Average Rating", f"{avg_rating:.2f}")
                                    
                                    # Test de join entre datasets
                                    st.info("🔗 Testing data join...")
                                    common_works = set(works['work_id']) & set(reviews['work_id'])
                                    st.success(f"✅ {len(common_works)} books have reviews")
                                    
                                    if len(common_works) > 0:
                                        st.success("🎉 ALL DATA LOADED SUCCESSFULLY!")
                                        st.info("✅ Ready to deploy full application")
                    
        # Información adicional
        st.subheader("🔧 Troubleshooting")
        st.info("""
        **Si el loading falla:**
        1. Verifica que las URLs de Hugging Face sean públicas
        2. Comprueba que los archivos CSV no estén corruptos
        3. Asegúrate de que los datasets no sean demasiado grandes (>100MB puede ser problemático)
        4. Considera usar una muestra más pequeña para testing
        """)
        
        # System info
        with st.expander("🔍 System Information"):
            st.write(f"Python version: {sys.version}")
            st.write(f"Streamlit version: {st.__version__}")
            st.write(f"Pandas version: {pd.__version__}")
            st.write(f"Requests version: {requests.__version__}")
        
    except Exception as e:
        st.error("❌ Critical error in main()")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()