from typing import Dict
from features.online_features import IncrementalStats

class ZScoreStrategy:
    """
    Mean-Reversion strategija bazirana na Z-scoreu.
    Ne koristi nikakve povijesne podatke unaprijed (No-Knowledge princip).
    """
    def __init__(self, window_size: int = 150, z_threshold: float = 2.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        # Rječnik instanci IncrementalStats za svaki simbol zasebno
        self.stats_trackers: Dict[str, IncrementalStats] = {}

    def generate_signals(self, tick_data: Dict[str, Dict[str, float]]) -> Dict[str, int]:
        """
        Prima trenutne cijene, ažurira značajke i vraća signale.
        Signal: 1 (Kupi), -1 (Prodaj), 0 (Čekaj)
        """
        signals = {}
        
        for simbol, data in tick_data.items():
            cijena = data['price']
            
            # Inicijaliziraj tracker ako simbol dođe prvi put
            if simbol not in self.stats_trackers:
                self.stats_trackers[simbol] = IncrementalStats(window_size=self.window_size)
                
            # Ažuriraj statistiku
            stats = self.stats_trackers[simbol].update(cijena)
            
            # Ako se prozor tek puni, nema signala
            if stats is None:
                signals[simbol] = 0
                continue
            
            # Računanje Z-scorea
            std = stats['std'] if stats['std'] > 0 else 1e-9 # Zaštita od dijeljenja s nulom
            z_score = (cijena - stats['mean']) / std
            
            # Logika odlučivanja
            if z_score < -self.z_threshold:
                signals[simbol] = 1   # Preprodano -> Kupi
            elif z_score > self.z_threshold:
                signals[simbol] = -1  # Prekupljeno -> Prodaj
            else:
                signals[simbol] = 0   # Normalno ponašanje -> Čekaj
                
        return signals