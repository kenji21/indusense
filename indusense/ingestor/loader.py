import pandas as pd


def load_incidents(path: str) -> pd.DataFrame:
    return pd.read_csv(path)
