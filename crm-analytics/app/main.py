from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.analytics import get_rfm_data

# Inicializimi i aplikacionit FastAPI
app = FastAPI(
    title="CRM Data Analytics API",
    description="API e prototipit të diplomës për segmentimin e klientëve SME shqiptare",
    version="1.0.0"
)

# Konfigurimi i CORS (Lejon frontend-in tonë të komunikojë me backend-in pa u bllokuar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Në prodhim vendoset URL specifike, por për prototip lejohet çdo gjë
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Faqja e thjeshtë e mirëseardhjes në API"""
    return {
        "status": "online",
        "mesazhi": "Mirëseerdhët në API-në e Sistemit CRM Analytics!",
        "universiteti": "Tirana Business University"
    }

@app.get("/api/rfm-data")
def get_rfm_results():
    """
    Ky endpoint thërret motorrin analitik, ekzekuton modelin K-Means
    mbi të dhënat e freskëta dhe i kthen ato në format JSON për Dashboard-in.
    """
    try:
        # Thërrasim funksionin që krijuam në Hapun 3
        df_rezultati = get_rfm_data()
        
        # Konvertojmë DataFrame e Pandas në format standard JSON (Listë me fjalorë)
        te_dhenat_json = df_rezultati.to_dict(orient='records')
        
        return {
            "status": "sukses",
            "total_kliente": len(df_rezultati),
            "data": te_dhenat_json
        }
    except Exception as e:
        return {
            "status": "gabim",
            "mesazhi": f"Ndodhi një gabim gjatë procesimit: {str(e)}"
        }