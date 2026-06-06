import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def get_rfm_data():
    """
    Ky funksion lexon të dhënat nga CSV, llogarit metrikat RFM,
    ekzekuton K-Means Clustering dhe emërton segmentet e klientëve shqiptarë.
    """
    # 1. Përcaktimi i rrugës (path) relative të skedarëve CSV
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    customers_path = os.path.join(base_dir, 'data', 'customers.csv')
    transactions_path = os.path.join(base_dir, 'data', 'transactions.csv')

    # Leximi i skedarëve
    df_cust = pd.read_csv(customers_path, encoding='cp1252')
    df_trans = pd.read_csv(transactions_path, encoding='cp1252')

    # Kthimi i shtyllës së datës në formatin e duhur Datetime
    df_trans['transaction_date'] = pd.to_datetime(df_trans['transaction_date'])

    # 2. LLOGARITJA E METRIKAVE RFM
    # Përcaktojmë një datë si pikë reference (1 ditë pas transaksionit më të fundit në dataset)
    snapshot_date = df_trans['transaction_date'].max() + pd.Timedelta(days=1)

    # Agregimi i të dhënave për çdo klient
    rfm = df_trans.groupby('customer_id').agg({
        # Recency: Sa ditë kanë kaluar nga blerja e fundit
        'transaction_date': lambda x: (snapshot_date - x.max()).days,
        # Frequency: Numri total i blerjeve (transaksioneve)
        'transaction_id': 'count',
        # Monetary: Shuma totale e shpenzuar
        'amount': 'sum'
    }).reset_index()

    # Emërtimi i ri i kolonave të llogaritura
    rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']

    # 3. STANDARDIZIMI (NORMALIZIMI) I TË DHËNAVE
    # K-Means është i ndjeshëm ndaj diferencave të shkallëve (p.sh. ditët vs vlerat në Lekë).
    # StandardScaler bën që çdo variabël të ketë mesatare 0 dhe devijim standard 1.
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm[['recency', 'frequency', 'monetary']])

    # 4. EKZEKUTIMI I ALGORITMIT K-MEANS
    # Përcaktojmë 4 grupe (n_clusters=4).
    # random_state=42 siguron që algoritmi të japë ekzaktesisht të njëjtat grupe në çdo ekzekutim para komisionit.
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm['cluster'] = kmeans.fit_predict(rfm_scaled)

    # 5. EMËRTIMI LOGJIK I GRUPEVE BAZUAR NË KARAKTERISTIKAT E TYRE
    # Llogarisim mesataret e çdo grupi për të kuptuar se kush është kush
    cluster_means = rfm.groupby('cluster').agg({
        'recency': 'mean',
        'frequency': 'mean',
        'monetary': 'mean'
    }).reset_index()

    cluster_mapping = {}
    for idx, row in cluster_means.iterrows():
        c_id = int(row['cluster'])
        
        # Rregullat logjike të segmentimit për prezantimin tënd:
        if row['monetary'] > rfm['monetary'].mean() and row['recency'] < rfm['recency'].mean():
            cluster_mapping[c_id] = "Klientë VIP"
        elif row['recency'] > rfm['recency'].mean() * 1.3:
            cluster_mapping[c_id] = "Në Rrezik Largimi (Churn Risk)"
        elif row['frequency'] <= 1.5:
            cluster_mapping[c_id] = "Klientë të Rinj"
        else:
            cluster_mapping[c_id] = "Klientë Aktivë / Standard"

    # Mapimi i emrave në DataFrame
    rfm['segment_name'] = rfm['cluster'].map(cluster_mapping)

    # 6. BASHKIMI ME TË DHËNAT DEMOGRAFIKE TË CRM-së
    # Bashkojmë tabelën analitike RFM me Emrat e Kompanive, Qytetet dhe Industrinë
    final_df = pd.merge(rfm, df_cust, on='customer_id', how='left')
    
    return final_df

if __name__ == "__main__":
    # Kjo pjesë ekzekutohet vetëm kur e nisim këtë skedar direkt për testim
    print("="*60)
    print("Duke testuar Motorrin Analitik RFM & K-Means...")
    print("="*60)
    
    try:
        rezultati = get_rfm_data()
        print("\n✅ Sukses! Algoritmi u ekzekutua pa asnjë gabim.")
        print(f"Total klientë të procesuar: {len(rezultati)}")
        print("\nPamje e 5 rreshtave të parë të analizës:")
        print(rezultati[['customer_id', 'company_name', 'recency', 'frequency', 'monetary', 'segment_name']].head())
        
        print("\nShpërndarja e kompanive sipas Segmenteve:")
        print(rezultati['segment_name'].value_counts())
    except Exception as e:
        print(f"\n❌ Gabim gjatë ekzekutimit: {str(e)}")
    print("="*60)