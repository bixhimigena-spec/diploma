import os
import datetime as dt
import hashlib
import random

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def load_retail_files():
    """Try to load the two retail files (CSV or Excel) from ./data/."""
    paths = {
        "csv1": "data/online_retail_09_10.csv",
        "csv2": "data/online_retail_10_11.csv",
        "xlsx1": "data/online_retail_09_10.xlsx",
        "xlsx2": "data/online_retail_10_11.xlsx",
    }

    try:
        if os.path.exists(paths["csv1"]) and os.path.exists(paths["csv2"]):
            a = pd.read_csv(paths["csv1"], encoding="ISO-8859-1")
            b = pd.read_csv(paths["csv2"], encoding="ISO-8859-1")
        elif os.path.exists(paths["xlsx1"]) and os.path.exists(paths["xlsx2"]):
            a = pd.read_excel(paths["xlsx1"])
            b = pd.read_excel(paths["xlsx2"])
        else:
            raise FileNotFoundError("Files not found in data/ directory.")
    except Exception:
        raise

    return a, b


def normalize_column_names(df):
    """Map common column name variants to a small set of expected names."""
    cols = list(df.columns)
    cleaned = {c: c for c in cols}

    for c in cols:
        key = str(c).lower().replace(" ", "").replace("_", "")
        if "customer" in key or "cust" in key:
            cleaned[c] = "customer_id"
        elif "invoice" in key and "date" not in key:
            cleaned[c] = "invoice_no"
        elif "date" in key or "time" in key:
            cleaned[c] = "invoice_date"
        elif "quant" in key or "qty" in key:
            cleaned[c] = "quantity"
        elif "price" in key or "rate" in key or "amount" in key or "munt" in key:
            cleaned[c] = "unit_price"

    return df.rename(columns=cleaned)


def safe_to_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def generate_local_company_info(customer_ids):
    """Create plausible Albanian SME names, cities and industries deterministically."""
    base_names = [
        "Alba", "Arbëria", "Koha", "Eagle", "Iliria", "Dyrrah", "Rozafa",
        "Teuta", "Skënderbeu", "Besa", "Jon", "Adriatik", "Apex", "Matrix"
    ]
    suffixes = ["Ndërtim", "Shpërndarje", "Retail", "Tech", "Trading", "Logistics", "Foods", "Pharma", "Solutions"]
    cities = ["Tiranë", "Durrës", "Vlorë", "Elbasan", "Shkodër", "Fier", "Korçë", "Berat"]
    industries = ["Ndërtim", "Retail & Tregti", "Shërbime", "Teknologji & IT", "Agro-biznes", "Transport & Logjistikë", "Prodhim", "Turizëm & Hoteleri"]

    names, city_list, inds = [], [], []

    for cid in customer_ids:
        # deterministic but not obviously "AI": use a short hash of the id
        h = hashlib.md5(str(cid).encode("utf-8")).hexdigest()
        seed = int(h[:8], 16)
        rnd = random.Random(seed)

        name = f"{rnd.choice(base_names)} {rnd.choice(suffixes)} sh.p.k."
        # skew city distribution toward Tirana
        city = rnd.choices(cities, weights=[40, 20, 10, 5, 5, 10, 5, 5], k=1)[0]
        ind = rnd.choice(industries)

        names.append(name)
        city_list.append(city)
        inds.append(ind)

    return names, city_list, inds


def compute_rfm(df):
    """Compute Recency, Frequency, Monetary for each customer."""
    # remove rows without customer id
    df = df[df["customer_id"].notna()].copy()

    df["quantity"] = safe_to_numeric(df["quantity"])
    df["unit_price"] = safe_to_numeric(df["unit_price"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)].copy()

    df["total_revenue"] = df["quantity"] * df["unit_price"]
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df = df[df["invoice_date"].notna()].copy()

    snapshot = df["invoice_date"].max() + dt.timedelta(days=1)

    agg = df.groupby("customer_id").agg(
        recency=("invoice_date", lambda x: (snapshot - x.max()).days),
        frequency=("invoice_no", "nunique"),
        monetary=("total_revenue", "sum"),
    ).reset_index()

    # normalize customer id formatting (drop .0 if numeric)
    def fmt_id(x):
        s = str(x)
        try:
            if s.endswith(".0"):
                return str(int(float(s)))
        except Exception:
            pass
        return s

    agg["customer_id"] = agg["customer_id"].apply(fmt_id)
    return agg


def assign_segments(rfm_df, n_clusters=4):
    """Cluster customers and assign human-friendly segment labels."""
    scaler = StandardScaler()
    X = scaler.fit_transform(rfm_df[["recency", "frequency", "monetary"]])

    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    rfm_df["cluster"] = labels

    # rank clusters by average monetary value
    cluster_order = (
        rfm_df.groupby("cluster")["monetary"]
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    # map to readable Albanian segment names
    mapping = {}
    names = [
        "Klientë VIP (Vlerë e Lartë)",
        "Klientë të Rregullt (Vlerë Mesatare)",
        "Klientë të Rinj / Me Volum të Ulët",
        "Klientë në Rrezik Largimi"
    ]
    for i, cl in enumerate(cluster_order):
        mapping[cl] = names[i] if i < len(names) else f"Segment {i+1}"

    rfm_df["segment_name"] = rfm_df["cluster"].map(mapping)
    return rfm_df


def get_rfm_data():
    """Main entry point: load data, compute RFM, add local metadata and segments."""
    try:
        a, b = load_retail_files()
    except Exception as e:
        print("Gabim: nuk mund të ngarkohen skedarët. Kontrolloni data/ dhe emrat e skedarëve.")
        raise

    df = pd.concat([a, b], ignore_index=True)

    # normalize column names and check required fields
    df = normalize_column_names(df)
    required = {"customer_id", "invoice_no", "invoice_date", "quantity", "unit_price"}
    if not required.issubset(set(df.columns)):
        missing = required.difference(set(df.columns))
        raise RuntimeError(f"Skedari mungon kolonat e nevojshme: {missing}")

    rfm = compute_rfm(df)

    # add local company info
    names, cities, industries = generate_local_company_info(rfm["customer_id"].tolist())
    rfm["company_name"] = names
    rfm["city"] = cities
    rfm["industry"] = industries

    # clustering and segment labels
    rfm = assign_segments(rfm, n_clusters=4)

    # final column order
    cols = ["customer_id", "company_name", "city", "industry", "recency", "frequency", "monetary", "segment_name"]
    return rfm[cols]


if __name__ == "__main__":
    # Example usage: call the function and show a small sample
    try:
        df_out = get_rfm_data()
        print("RFM sample:")
        print(df_out.head(10).to_string(index=False))
    except Exception as err:
        print(f"Procesi dështoi: {err}")
