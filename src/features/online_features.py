import numpy as np
from collections import deque
from typing import Optional, Dict

class IncrementalStats:
    """
    Memorijski efikasna klasa za računanje statistike u letu (Online Learning).
    Koristi 'deque' iz collections modula jer je brži od obične liste za pop/append operacije.
    """
    def __init__(self, window_size: int = 150):
        # maxlen automatski izbacuje najstariji element kad se napuni!
        self.window_size = window_size
        self.values = deque(maxlen=window_size) 

    def update(self, new_value: float) -> Optional[Dict[str, float]]:
        """Dodaje novu vrijednost i vraća trenutne statistike ako je prozor pun."""
        self.values.append(new_value)
        
        # Ne vraćamo statistiku dok se bot ne "zagrije"
        if len(self.values) < self.window_size:
            return None
            
        # Računanje statistike samo na trenutnom prozoru
        mean_val = np.mean(self.values)
        std_val = np.std(self.values)
        
        return {
            'mean': mean_val,
            'std': std_val,
            'last': self.values[-1]
        }