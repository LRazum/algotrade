from alpaca_trade_api.rest import REST, TimeFrame
import pandas as pd
import os
from datetime import datetime

API_KEY = "key"
SECRET_KEY = "key"
BASE_URL = "https://paper-api.alpaca.markets"

api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

def skini_alpaca_podatke_pojedinacno(simboli, start_datum, end_datum, save_dir="data/raw/1m"):
    os.makedirs(save_dir, exist_ok=True)
    
    for simbol in simboli:
        print(f"Dohvaćam podatke za: {simbol}...")
        try:
            bars = api.get_bars(
                simbol, 
                TimeFrame.Minute, 
                start=start_datum, 
                end=end_datum,
                adjustment='all'
            ).df

            if not bars.empty:
                bars.index = pd.to_datetime(bars.index)

                bars = bars.between_time('14:30', '21:00')

                file_path = os.path.join(save_dir, f"{simbol}_1m_data.csv")
                bars.to_csv(file_path)
                print(f"Spremljeno: {file_path} (Redaka: {len(bars)})")
                
        except Exception as e:
            print(f"Greška za {simbol}: {e}\n")

if __name__ == "__main__":
    etf_simboli = ["SPY", "GLD", "QQQ", "IWM", "DIA", "USO"]
    
    START = "2026-03-02T00:00:00Z" 
    END = "2026-03-06T23:59:59Z"

    skini_alpaca_podatke_pojedinacno(etf_simboli, start_datum=START, end_datum=END)