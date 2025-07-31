import streamlit as st
import pandas as pd
import sys
import traceback
import requests
from io import StringIO


# Configuración básica
st.set_page_config(
    page_title="Summer Reading List",
    page_icon="📚",
    layout="wide"
)

def main():
    st.title("📚 Summer Reading List - Debug Version")
    
    try:
        st.info("✅ App started successfully!")
        st.write(f"Python version: {sys.version}")
        st.write("Streamlit version:", st.__version__)
        
        # Test básico de pandas
        df_test = pd.DataFrame({'test': [1, 2, 3]})
        st.write("✅ Pandas working:", df_test)
        
        # Test de importación
        try:
            from utils.recommend import get_recommendations
            st.success("✅ recommend.py imported successfully")
        except ImportError as e:
            st.error(f"❌ Error importing recommend.py: {e}")
        except Exception as e:
            st.error(f"❌ Error in recommend.py: {e}")
        
        # Test carga de datos (comentado por ahora)
        st.info("Data loading test for debugging")
        try: 
            review_url = 'https://huggingface.co/datasets/Pauleera/Goodreads-Book-Reviews/resolve/main/goodreads_reviews.csv'
            with st.spinner("📥 Loading review database..."):
                review_response = requests.get(review_url)
                review = pd.read_csv(StringIO(review_response.text))
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()
        
        # Test session state
        if "test" not in st.session_state:
            st.session_state.test = "working"
        
        st.success(f"✅ Session state: {st.session_state.test}")
        
    except Exception as e:
        st.error("❌ Critical error in main()")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()