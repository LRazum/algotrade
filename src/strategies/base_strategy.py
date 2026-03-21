import numpy as np
from typing import Dict
from collections import deque
from src.features.online_features import IncrementalStats

class ZScoreStrategy:
    def __init__(self, window_size=150):
        self.window_size = window_size
        self.prices = []

    def generate_signal(self, current_price):
        self.prices.append(current_price)
        
        if len(self.prices) > self.window_size:
            self.prices.pop(0)
            
        if len(self.prices) < self.window_size:
            return 0
            
        mean = np.mean(self.prices)
        std = np.std(self.prices)
        z_score = (current_price - mean) / (std + 1e-9)
        
        if z_score < -2.0: return 1
        if z_score > 2.0: return -1
        return 0
    
class EmaCrossStrategy:
    """
    Kaufman Adaptive Moving Average (KAMA) Crossover.
    Koristi standardnu devijaciju zadnjih 100 tickova 
    """
    def __init__(self, er_period: int = 10, vol_period: int = 100, std_multiplier: float = 0.5):
        self.er_period = er_period
        self.vol_period = vol_period
        self.std_multiplier = std_multiplier

        self.fast_fastest_alpha = 2 / (2 + 1)
        self.fast_slowest_alpha = 2 / (30 + 1)
        self.slow_fastest_alpha = 2 / (30 + 1)
        self.slow_slowest_alpha = 2 / (150 + 1)

        self.fast_ema: Dict[str, float] = {}
        self.slow_ema: Dict[str, float] = {}
        self.tick_counts: Dict[str, int] = {}
        self.previous_state: Dict[str, int] = {}
        self.history: Dict[str, list] = {}
        
        self.volatility_history: Dict[str, deque] = {}

    def generate_signals(self, tick_data: Dict[str, Dict[str, float]]) -> Dict[str, int]: 
        signals = {}

        for simbol, data in tick_data.items():
            cijena = data['price']

            if simbol not in self.history:
                self.history[simbol] = []
                self.volatility_history[simbol] = deque(maxlen=self.vol_period)

            self.history[simbol].append(cijena)
            self.volatility_history[simbol].append(cijena)

            if len(self.history[simbol]) > self.er_period + 1:
                self.history[simbol].pop(0)

            if simbol not in self.fast_ema:
                self.fast_ema[simbol] = cijena
                self.slow_ema[simbol] = cijena
                self.tick_counts[simbol] = 1
                self.previous_state[simbol] = 0
                signals[simbol] = 0
                continue

            if len(self.history[simbol]) < self.er_period + 1:
                self.tick_counts[simbol] += 1
                signals[simbol] = 0
                continue

            # Kaufman Adaptive Math
            signal_smjera = abs(cijena - self.history[simbol][0])
            buka = sum(abs(self.history[simbol][i] - self.history[simbol][i-1]) for i in range(1, len(self.history[simbol])))
            er = signal_smjera / buka if buka != 0 else 0

            smooth_fast = (er * (self.fast_fastest_alpha - self.fast_slowest_alpha) + self.fast_slowest_alpha) ** 2
            smooth_slow = (er * (self.slow_fastest_alpha - self.slow_slowest_alpha) + self.slow_slowest_alpha) ** 2
                
            self.fast_ema[simbol] = (cijena * smooth_fast) + (self.fast_ema[simbol] * (1 - smooth_fast))
            self.slow_ema[simbol] = (cijena * smooth_slow) + (self.slow_ema[simbol] * (1 - smooth_slow))
            self.tick_counts[simbol] += 1

            if self.tick_counts[simbol] < self.vol_period:
                signals[simbol] = 0
                continue

            # Stdev na dugom prozoru
            std_dev = np.std(self.volatility_history[simbol])
            prag = std_dev * self.std_multiplier

            if self.fast_ema[simbol] > self.slow_ema[simbol] + prag:
                trenutno_stanje = 1  
            elif self.fast_ema[simbol] < self.slow_ema[simbol] - prag:
                trenutno_stanje = -1 
            else:
                trenutno_stanje = 0  

            if trenutno_stanje != self.previous_state[simbol] and trenutno_stanje != 0:
                signals[simbol] = trenutno_stanje
                self.previous_state[simbol] = trenutno_stanje
            else:
                signals[simbol] = 0

        return signals