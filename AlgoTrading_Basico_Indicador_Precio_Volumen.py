# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 07:43:06 2022

@author: Ariel
"""

#1)_Importar librerias
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt

#2)_Seleccion de activo
ticker='GGAL'

#===========INICIALIZACION DEL BOT=============#

#3.1)_Funciones creadas
#3.1.1)Datos de mercado
def market_data (ticker, desde, hasta, intervalo):
    datos=yf.download(ticker,start=desde, end=hasta, interval=intervalo)
    return datos

#3.1.2)_Funciones de precios
#3.1.2.1)_Media movil
def media_movil_simple (precios, cantidad_rondas, metodo='manual'):
    if (metodo=='manual'):
        
        media_SMA=precios.rolling(window=cantidad_rondas,
                                           min_periods=cantidad_rondas).mean()
        return media_SMA
    
    if (metodo=='manual_2'):
        
        rondas=cantidad_rondas*-1
        
        cierres=precios.iloc[rondas:,:]['Close']
        
        promedio_manual=0
        
        for suma_cierres in cierres:
            promedio_manual=promedio_manual+suma_cierres
            
        promedio_manual=promedio_manual/cantidad_rondas
        
        return promedio_manual
      
    if (metodo=='automatico'):
        sma_ta=ta.sma(close=precios,length=cantidad_rondas)
        return sma_ta
    
#3.1.2.2)_Media exponencial
def media_movil_exponencial (precios, cantidad_rondas, metodo='manual'):
    if(metodo=='manual'):
        media_ema=precios.ewm(alpha=2/(cantidad_rondas+1), adjust=False,
                                       min_periods=cantidad_rondas).mean()
        return media_ema
    
    if (metodo=='automatico'):
        ema_ta=ta.ema(close=precios,length=cantidad_rondas)
                
        return ema_ta
            
#3.1.3)_Funciones de momentum
#3.1.3.1)_Indicador de momentum RSI
def rsi (precios, periodos=14, metodo='manual'):
    
    if (metodo=='manual'):
    
        diff_cierres=precios['Close'].diff()
        
        cierres_positivos=diff_cierres.clip(lower=0)
        cierres_negativos=-1 * diff_cierres.clip(upper=0)
        
        cierres_positivos_suavizados=cierres_positivos.ewm(alpha=1 / (periodos), adjust=False, min_periods=periodos).mean()
        cierres_negativos_suavizados=cierres_negativos.ewm(alpha=1 / (periodos), adjust=False, min_periods=periodos).mean()
        
        rsi= 100 - (100 / (1+(cierres_positivos_suavizados/cierres_negativos_suavizados)))
        
        return rsi
    
    if (metodo=='automatico'):
        
        rsi_ta=ta.rsi(precios['Close'], length=14)
        
        return rsi_ta
    
#3.1.3.1.1)_Status RSI
def status_rsi(x):
    if (x>=70):
        return 'Sobrecompra'
    
    if (x<=30):
        return 'Sobreventa'
    
##3.1.3.2)_Indicador de momentum MACD
def macd (precios, metodo='manual'):
    if (metodo=='manual'):
        ema_12=media_movil_exponencial(precios,12,metodo='manual')
        ema_26=media_movil_exponencial(precios,25,metodo='manual')
        dif_ema=ema_12-ema_26
        
        media_ema=media_movil_exponencial(dif_ema, 9, metodo='manual')
        
        histograma=dif_ema-media_ema
        
        macd_df=pd.DataFrame(
            {
            'Dif_EMA':dif_ema,
            'Media_EMA':media_ema,
            'Histograma':histograma
            }
            )
        return macd_df    
    
    if(metodo=='automatico'):
        ema_ta=ta.macd(precios)
        return ema_ta

#3.1.4)_Funciones de status
#3.1.4.1)_Buy & Sell
def buysell (x):
    if (x>0):
        return 'Buy'
    
    if (x<0):
        return 'Sell'
    
#3.1.4.2)_Golden Cross
def golden_death_cross (x):
    if (x>0):
        return 'Golden Cross'
    if (x<0):
        return 'Death Cross'
    
#===========COMIENZO DE PROGRAMA PRINCIPAL=============#
precios_historicos=market_data(ticker,
                               desde='2019-1-1',
                               hasta='2022-1-13',
                               intervalo='1d')

#4.1)_Analisis de precio
#Variacion % de precios
precios_historicos['Var%_P']=precios_historicos['Close'].pct_change()*100

##Medias moviles
#Medias moviles semanal vs mensual
precios_historicos['SMA5']=media_movil_simple(precios_historicos['Close'],5,metodo='manual')
precios_historicos['SMA20']=media_movil_simple(precios_historicos['Close'],20,metodo='manual')

#Funcion de status
precios_historicos['Calculos_buysell']=(precios_historicos['SMA5']-precios_historicos['SMA20'])
precios_historicos['Buy&Sell']=precios_historicos['Calculos_buysell'].apply(buysell)

#Medias moviles mediano y largo plazo
precios_historicos['SMA200']=media_movil_simple(precios_historicos['Close'],200,metodo='automatico')
precios_historicos['SMA50']=media_movil_simple(precios_historicos['Close'],50,metodo='automatico')

##Funcion de status
precios_historicos['Calculos_cross']=(precios_historicos['SMA50']-precios_historicos['SMA200'])
precios_historicos['Cross_Status']=precios_historicos['Calculos_cross'].apply(golden_death_cross)

#Filtro_1
precios_historicos['Cross_Status_Filtro']=(precios_historicos['SMA50']-precios_historicos['SMA200']>1)\
    &\
        (precios_historicos['SMA50']-precios_historicos['SMA200']<2)
        
##Indicadores de momentum
#MACD
macd=macd(precios_historicos['Close'],metodo='manual')
precios_historicos=pd.concat([precios_historicos,macd],axis=1)

#Filtro_de_MACD_Alcista
precios_historicos['Bullish']=(
    precios_historicos['Dif_EMA']>0
    )&(
       precios_historicos['Media_EMA']>0
       )&(precios_historicos['Histograma']>0)

#RSI
precios_historicos['RSI_Calculo']=rsi(precios_historicos,metodo='manual')
precios_historicos['RSI']=precios_historicos['RSI_Calculo'].apply(status_rsi)

#Filtro_MACD/RSI
precios_historicos['MACD/RSI_Compra']=(precios_historicos['Bullish']>0)\
    &\
        (precios_historicos['RSI']=='Sobreventa')

#4.2)_Analisis del volumen
#Variacion % de Volumen
precios_historicos['Var_V%']=precios_historicos['Volume'].pct_change()*100

#Promedio mensual 
precios_historicos['Prom_Volume_(m)']=media_movil_simple(precios_historicos['Volume'],20,metodo='manual')

#Radio de Volumen
precios_historicos['Radio_10/100']=media_movil_simple(precios_historicos['Volume'],10,metodo='manual')/media_movil_simple(precios_historicos['Volume'],100,metodo='manual')

##Divergencia o Confirmacion semanal precio/volumen 
#Tendencia de precios
precios_historicos['Tendencia_Alcista_Precio']=(precios_historicos['Close']>precios_historicos['Close'].shift(1))\
    &\
        (precios_historicos['Close']>precios_historicos['Close'].shift(2))\
            &\
                (precios_historicos['Close']>precios_historicos['Close'].shift(3))\
                    &\
                        (precios_historicos['Close']>precios_historicos['Close'].shift(4))\
                            &\
                                (precios_historicos['Close']>precios_historicos['Close'].shift(5))

#Tendencia de volumen                                
precios_historicos['Tendencia_Alcista_Volumen']=(precios_historicos['Volume']>precios_historicos['Volume'].shift(1))\
    &\
        (precios_historicos['Volume']>precios_historicos['Volume'].shift(2))\
            &\
                (precios_historicos['Volume']>precios_historicos['Volume'].shift(3))\
                    &\
                        (precios_historicos['Volume']>precios_historicos['Volume'].shift(4))\
                            &\
                                (precios_historicos['Volume']>precios_historicos['Volume'].shift(5))

#Volumen como validador de tendencia                                    
precios_historicos['Volumen_c/validador_de_Tendencia']=(precios_historicos['Tendencia_Alcista_Precio']==True)\
    &\
        (precios_historicos['Tendencia_Alcista_Volumen']==True)

#4.3)_Creacion_DataFrame
#df calculos
calculos_df=precios_historicos

#df precios
precios_df=calculos_df[['Open','High','Low','Close','Volume','Var%_P','Var_V%','SMA5','SMA20',
                                'Buy&Sell','SMA200','SMA50','Cross_Status','Cross_Status_Filtro','Bullish','RSI','MACD/RSI_Compra']]

#df volumen
volumen_df=calculos_df[['Close','Var%_P','Var_V%','Prom_Volume_(m)','Radio_10/100','Tendencia_Alcista_Precio',
                               'Tendencia_Alcista_Volumen','Volumen_c/validador_de_Tendencia']]
#4.4)_Reportes
#Ejemplo Reportes
#Tendencia alcista corto plazo, cruce Golden Cross, MACD Bullish y 
#radio de volumen superior o igual al 100%
reporte_de_compra=calculos_df[\
                            (calculos_df['Buy&Sell']=='Buy')\
                                &\
                            (calculos_df['Cross_Status']=='Golden Cross')\
                                &\
                            (calculos_df['Bullish']==True)\
                                &\
                                    (calculos_df['Radio_10/100']>=1)]
    
reporte_confirmacion_divergencia=calculos_df[calculos_df['Volumen_c/validador_de_Tendencia']==True][['Close','Var%_P','Var_V%','Volumen_c/validador_de_Tendencia']]
print('Confirmacion semanal')
print(reporte_confirmacion_divergencia)

#4.5)_Exportar los DataFrame creados
#Exportar df a formato 'csv'
calculos_df.to_csv('C:/python/proyectos/algo_trading/calculos_df.csv')
# precios_df.to_csv('C:/python/proyectos/algo_trading/precios_df.csv')                                    
# volumen_df.to_csv('C:/python/proyectos/algo_trading/volumen_df.csv')                                        

#4.6)_Visualizacion
fig, axes = plt.subplots(4,1)

calculos_df[['Close','SMA5','SMA20','SMA50','SMA200']].plot(figsize=(48,29),ax=axes[0])

calculos_df['Volume'].plot(kind='bar',ax=axes[1])


calculos_df[['Dif_EMA','Media_EMA']].plot(ax=axes[2])

histograma=calculos_df.reset_index()
histograma['Histograma'].plot(kind="bar",ax=axes[3])
