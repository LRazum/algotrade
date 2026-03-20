import pandas as pd
import time
from pathlib import Path
from typing import List, Callable, Dict, Any

class LiveSimulator:
    def __init__(self, simboli: List[str], brzina_sekunde: float = 0.1, on_tick_callback: Callable = None, date: str = ""):
        """
        Glavni simulator koji glumi WebSocket stream.
        """
        self.simboli = simboli
        self.brzina = brzina_sekunde
        self.on_tick_callback = on_tick_callback
        
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.raw_dir = self.base_dir / "data" / "raw" / "12s" / date
        self.master_df = None

    def _ucitaj_i_pripremi(self) -> bool:
        """Učitava, čisti i sinkronizira CSV datoteke u jedan veliki DataFrame."""
        all_dfs = []
        
        if not self.raw_dir.exists():
            print(f"❌ Direktorij ne postoji: {self.raw_dir}")
            return False

        print(f"--- Učitavanje podataka iz: {self.raw_dir.name} ---")

        for simbol in self.simboli:
            putanja = self.raw_dir / f"{simbol}_12s_data.csv"
            
            if not putanja.exists():
                print(f"⚠️ Preskačem {simbol}: Datoteka nije pronađena.")
                continue
            
            try:
                df = pd.read_csv(putanja)
                # Sređivanje imena stupca za vrijeme
                col_name = 'timestamp' if 'timestamp' in df.columns else df.columns[0]
                
                df[col_name] = pd.to_datetime(df[col_name])
                df.set_index(col_name, inplace=True)
                
                # Zadržavamo samo cijenu i volumen, optimiziramo memoriju
                df = df[['close', 'volume']].astype('float32')
                df.columns = [f"{simbol}_close", f"{simbol}_volume"]
                all_dfs.append(df)
            except Exception as e:
                print(f"❌ Greška pri učitavanju {simbol}: {e}")

        if not all_dfs:
            print("❌ Niti jedan simbol nije uspješno učitan.")
            return False

        # Outer join po vremenu i forward-fill za praznine u trgovanju
        self.master_df = pd.concat(all_dfs, axis=1).sort_index().ffill()
        print(f"✅ Učitavanje završeno. Ukupno tickova (koraka): {len(self.master_df)}")
        return True

    def pokreni(self):
        """Pokreće simulaciju prolazeći kroz podatke redak po redak."""
        if self.master_df is None and not self._ucitaj_i_pripremi():
            return

        print("\n🚀 START SIMULACIJE\n" + "="*40)
        
        try:
            for row in self.master_df.itertuples():
                vrijeme = row.Index
                
                tick_data: Dict[str, Dict[str, float]] = {}
                for simbol in self.simboli:
                    try:
                        cijena = getattr(row, f"{simbol}_close")
                        volumen = getattr(row, f"{simbol}_volume")
                        if pd.notna(cijena):
                            tick_data[simbol] = {'price': cijena, 'volume': volumen}
                    except AttributeError:
                        continue

                if self.on_tick_callback and tick_data:
                    self.on_tick_callback(vrijeme, tick_data)
                
                if self.brzina > 0:
                    time.sleep(self.brzina)

        except KeyboardInterrupt:
            print("\n🛑 Simulacija ručno prekinuta.")
        
        print("="*40 + "\n🏁 Simulacija završena.")