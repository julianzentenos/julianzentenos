"""
Julián Zenteno S.

Aqui hare el Live Trade

Voy a hacer la inclusión de dos ventanas temporales
"""

from datetime import datetime
from ta.momentum import RSIIndicator
import pandas as pd
import time
import requests
import json


#Parametros
position = 0 # Posicion inicial
trades = []
r_cum = 0

#API's
SLACK_API ='LINK'

#MSG NEW SESION
requests.post(SLACK_API, data = json.dumps({"text":"Nueva Sesión"}))

### Live Trade
while True:
    try:
        
        ### Actualizo datos
        
        response = requests.get("https://api.kraken.com/0/public/OHLC?pair=SOLBTC&interval=1&since=now")
        
        df = response.json()

        df = pd.DataFrame(df['result']["SOLXBT"],
                          columns=['Timestamp', 'Open', 'High', 'Low', 'Close', "vwap", 'Volume', 'Count'])

        df['Close'] = df['Close'].astype(float)

        # Convertir la columna de tiempo a formato datetime
        df['Date'] = pd.to_datetime(df['Timestamp'], unit='s')
        
        df = df[['Date', 'Close']]
        
        ### Calculo de variables
        
        # Moving Average
        df['MA_S'] = df['Close'].rolling(window=20).mean()
        df['MA_L'] = df['Close'].rolling(window=60).mean()

        
        # RSI Short y Long
        df['RSI_S'] = RSIIndicator(df['Close'], window=15).rsi()
        df['RSI_L'] = RSIIndicator(df['Close'], window=60).rsi()
        
        # RSI MA
        df['RSI_S_MA'] = df['RSI_S'].rolling(window=20).mean()
        df['RSI_L_MA'] = df['RSI_L'].rolling(window=20).mean()
        
        # Precio
        close_price = df['Close'].tail(1).iloc[0] 
        
        # Valores actuales
        MA_S = df['MA_S'].tail(1).iloc[0] 
        MA_L = df['MA_L'].tail(1).iloc[0] 
        RSI_S = df['RSI_S'].tail(1).iloc[0] 
        RSI_L = df['RSI_L'].tail(1).iloc[0] 
        RSI_S_MA = df['RSI_S_MA'].tail(1).iloc[0] 
        RSI_L_MA = df['RSI_L_MA'].tail(1).iloc[0] 
        
        del df
        
        if position == 0:  # No hay posición abierta
            if RSI_S < 40 and RSI_L < 40 and RSI_S_MA < 45 and RSI_L_MA < 45 and MA_S > MA_L:  # Orden de compra - Abre
                trades.append(('Buy', close_price, datetime.now(), " - Open"))
                position = 1
                stop_loss_price = close_price * 0.99 
                take_profit_price = close_price * 1.03 
                #Orden:
                precio = close_price  
                #Notificación:
                print("ORDER: ", 'Buy', close_price, datetime.now(), " - OPEN")
                time.sleep(1)
        
        elif position == 1:  # Posición larga abierta - Cierre
            if (RSI_S_MA > RSI_S and RSI_S_MA < 50) or close_price <= stop_loss_price:  # Señal de venta, stop loss o take profit alcanzado
                trades.append(('Sell', close_price, datetime.now(), " - Close"))
                position = 0
                stop_loss_price = None
                take_profit_price = None
                #Orden:
                r = (close_price - precio)/precio
                r_cum = (1+r_cum)*(1+r)-1
                #Notificación:
                MSG = f'ORDER: Sell {close_price} // {datetime.now()} - CLOSE // R : {round(r*100,3)} % // RCUM : {round(r_cum*100,3)} %'
                requests.post(SLACK_API, data = json.dumps({"text":MSG}))    
                print("ORDER: ", 'Sell', close_price, datetime.now(), " - CLOSE")
                time.sleep(1)
            elif close_price >= take_profit_price:
                take_profit_price = take_profit_price + 0.02
                stop_loss_price = stop_loss_price + 0.02
      
        
        # Esperar un tiempo antes de la próxima actualización (por ejemplo, 5 segundos)
        time.sleep(5)
        print("WORK: ", close_price, datetime.now(), " // MA_S: ", round(MA_S,3), " // MA_L: ", round(MA_L,3), " // RSI_S: ", round(RSI_S,3), " // RSI_L: ", round(RSI_L,3), " // RSI_S_MA: ", round(RSI_S_MA,3), " // RSI_L_MA: ", round(RSI_L_MA,3), " // R: ", round(r_cum*100,3))

    except Exception as e:
        print("Ocurrió un error:", e)

