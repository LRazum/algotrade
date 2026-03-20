from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import os

API_KEY = "key"
SECRET_KEY = "key"

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def procesiraj_jedan_simbol(simbol, start_dt, end_dt, save_dir):
    """
    Ova funkcija odrađuje cijeli posao za samo jedan simbol.
    Dizajnirana je tako da može raditi paralelno s ostalima u zasebnom threadu.
    """
    try:
        request_params = StockTradesRequest(
            symbol_or_symbols=simbol,
            start=start_dt,
            end=end_dt
        )

        trades_data = client.get_stock_trades(request_params)
        trades = trades_data.df
        
        if trades is None or trades.empty:
            return f"⚠️ Nema podataka za {simbol}."
            
        if isinstance(trades.index, pd.MultiIndex):
            trades = trades.xs(simbol)
            
        df_12s = trades['price'].resample('12s').ohlc()
        df_12s['volume'] = trades['size'].resample('12s').sum()
        
        df_12s['close'] = df_12s['close'].ffill()
        for col in ['open', 'high', 'low']:
            df_12s[col] = df_12s[col].fillna(df_12s['close'])
            
        df_12s['volume'] = df_12s['volume'].fillna(0)

        df_12s = df_12s.between_time('14:30', '21:00')

        file_path = os.path.join(save_dir, f"{simbol}_12s_data.csv")
        df_12s.to_csv(file_path)
        
        return f"Uspješno: {simbol:4} | Spremljeno {len(df_12s)} redaka."
        
    except Exception as e:
        return f"Greška za {simbol}: {e}"


def skini_12s_podatke_brzo(simboli, start_d, end_d, save_dir="data/raw/12s/11_11"):
    os.makedirs(save_dir, exist_ok=True)
    
    start_dt = datetime.strptime(start_d, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = datetime.strptime(end_d, "%Y-%m-%dT%H:%M:%SZ")

    print(f"Preuzimanje za {len(simboli)} simbola...\n")

    with ThreadPoolExecutor(max_workers=len(simboli)) as executor:
        futures = [executor.submit(procesiraj_jedan_simbol, sym, start_dt, end_dt, save_dir) for sym in simboli]
        
        for future in as_completed(futures):
            print(future.result())
            
    print("\nPreuzimanja završena!")


if __name__ == "__main__":
    etf_simboli = ["SPY", "GLD", "QQQ", "IWM", "DIA", "USO"]
    
    START = "2025-11-11T14:29:00Z"
    END = "2025-11-11T21:01:00Z"

    skini_12s_podatke_brzo(etf_simboli, START, END)