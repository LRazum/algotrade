from typing import Dict
import pandas as pd

class PortfolioManager:
    """
    Prati stanje računa, drži otvorene pozicije i izračunava profit (P&L).
    """
    def __init__(self, initial_cash: float = 10000.0, risk_per_trade_pct: float = 0.20):
        self.cash = initial_cash
        self.pocetni_cash = initial_cash
        self.risk_pct = risk_per_trade_pct # Postotak slobodnog casha (npr. 0.20 = 20%)
        
        # Praćenje inventara: simbol -> količina (broj dionica)
        self.pozicije: Dict[str, float] = {}
        self.prosjecna_cijena_ulaza: Dict[str, float] = {}
        
        self.ukupni_realizirani_pnl = 0.0
        self.broj_tradeova = 0

    def process_signals(self, signals: Dict[str, int], tick_data: Dict[str, Dict[str, float]], timestamp):
        """Izvršava signale koje je poslala strategija."""
        for simbol, signal in signals.items():
            if signal == 0:
                continue
                
            cijena = tick_data[simbol]['price']
            trenutna_pozicija = self.pozicije.get(simbol, 0.0)
            
            # BUY SIGNAL
            if signal == 1 and trenutna_pozicija == 0.0:
                # Dinamički ulog baziran na trenutno dostupnom novcu
                trenutni_ulog = self.cash * self.risk_pct
                
                if trenutni_ulog > 10.0 and self.cash >= trenutni_ulog:
                    kolicina = trenutni_ulog / cijena
                    self.pozicije[simbol] = kolicina
                    self.prosjecna_cijena_ulaza[simbol] = cijena
                    self.cash -= trenutni_ulog
                    self.broj_tradeova += 1
                    print(f"[{timestamp.strftime('%H:%M:%S')}] 🟢 KUPI  {simbol:4} | Cijena: {cijena:.2f} | Ulog: ${trenutni_ulog:.2f} ({(self.risk_pct*100):.0f}% casha)")

            # SELL SIGNAL (Zatvaranje long pozicije)
            elif signal == -1 and trenutna_pozicija > 0.0:
                vrijednost_prodaje = trenutna_pozicija * cijena
                ulog = trenutna_pozicija * self.prosjecna_cijena_ulaza[simbol]
                profit = vrijednost_prodaje - ulog
                
                self.cash += vrijednost_prodaje
                self.ukupni_realizirani_pnl += profit
                self.pozicije[simbol] = 0.0 # Očisti poziciju
                self.prosjecna_cijena_ulaza[simbol] = 0.0
                
                ikonica = "💰" if profit > 0 else "🩸"
                print(f"[{timestamp.strftime('%H:%M:%S')}] 🔴 PRODAJ {simbol:4} | Cijena: {cijena:.2f} | Profit: {ikonica} ${profit:.2f}")

    def liquidate_all(self, tick_data: Dict[str, Dict[str, float]], timestamp):
        """
        Hitno zatvara sve otvorene pozicije po trenutnim tržišnim cijenama.
        Koristi se na kraju dana kako bi se izbjegao rizik držanja preko noći.
        """
        for simbol, kolicina in list(self.pozicije.items()):
            if kolicina > 0.0 and simbol in tick_data:
                cijena = tick_data[simbol]['price']
                vrijednost_prodaje = kolicina * cijena
                ulog = kolicina * self.prosjecna_cijena_ulaza[simbol]
                profit = vrijednost_prodaje - ulog
                
                # Ažuriranje balansa
                self.cash += vrijednost_prodaje
                self.ukupni_realizirani_pnl += profit
                self.pozicije[simbol] = 0.0
                self.prosjecna_cijena_ulaza[simbol] = 0.0
                
                ikonica = "💰" if profit > 0 else "🩸"
                print(f"[{timestamp.strftime('%H:%M:%S')}] 🚨 LIKVIDACIJA {simbol:4} | Cijena: {cijena:.2f} | Profit: {ikonica} ${profit:.2f}")

    def get_portfolio_value(self, tick_data: Dict[str, Dict[str, float]]) -> float:
        """Računa trenutnu ukupnu vrijednost portfelja (Mark-to-Market)."""
        vrijednost_pozicija = 0.0
        for simbol, kolicina in self.pozicije.items():
            if kolicina > 0 and simbol in tick_data:
                vrijednost_pozicija += kolicina * tick_data[simbol]['price']
        return self.cash + vrijednost_pozicija
        
    def ispis_rezultata(self):
        print("\n" + "="*40)
        print("📊 IZVJEŠTAJ O TRGOVANJU (Dinamički ulozi)")
        print("="*40)
        print(f"Broj odrađenih tradeova: {self.broj_tradeova}")
        print(f"Realizirani Profit/Gubitak (P&L): ${self.ukupni_realizirani_pnl:.2f}")
        print(f"Završni Cash na računu: ${self.cash:.2f}")
        roi = ((self.cash - self.pocetni_cash) / self.pocetni_cash) * 100
        print(f"Ukupni prinos (ROI): {roi:.2f}%")
        print("="*40)