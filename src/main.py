import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.execution.simulator import LiveSimulator
from src.strategies.base_strategy import ZScoreStrategy
from src.portfolio.manager import PortfolioManager

strategija = ZScoreStrategy(window_size=150, z_threshold=2.5) 
portfolio = PortfolioManager(initial_cash=10000.0, risk_per_trade_pct=0.20)

trgovanje_aktivno = True

def master_tick_handler(timestamp, tick_data):
    global trgovanje_aktivno

    if timestamp.hour == 20 and timestamp.minute >= 55:
        if trgovanje_aktivno:
            print(f"\n[{timestamp.strftime('%H:%M:%S')}] KRAJ DANA BLIZU - POKREĆEM LIKVIDACIJU SVIH POZICIJA!")
            portfolio.liquidate_all(tick_data, timestamp)
            trgovanje_aktivno = False
        
        return 

    if trgovanje_aktivno:
        signali = strategija.generate_signals(tick_data)
        
        portfolio.process_signals(signali, tick_data, timestamp)


if __name__ == "__main__":
    SIMBOLI = ["SPY", "QQQ", "GLD", "USO", "DIA", "IWM"]
    
    simulator = LiveSimulator(
        simboli=SIMBOLI, 
        brzina_sekunde=0.001, 
        on_tick_callback=master_tick_handler,
        date="08_13"
    )
    
    simulator.pokreni()
    
    portfolio.ispis_rezultata()