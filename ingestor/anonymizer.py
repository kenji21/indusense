import hashlib
import os
import sys

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def _hash(value: str) -> str:
    salt = os.environ.get("ANON_SALT")
    if not salt:
        print("Variable ANON_SALT manquante dans .env")
        sys.exit(1)
    return hashlib.sha256(f"{salt}{value}".encode()).hexdigest()[:10]


def anonymize_operators(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["operator_name"] = data["operator_name"].dropna().apply(
        lambda v: f"OP-{_hash(v)}"
    )
    data["operator_badge"] = data["operator_badge"].dropna().apply(
        lambda v: f"BADGE-{_hash(v)}"
    )
    return data
