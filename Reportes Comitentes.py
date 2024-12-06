#Este programa genera los reportes de las cuentas comitentes. Trae del archivo "TVAFECHA" las tenencias de las comitentes
#También utiliza uno llamado "Administración de Títulos Valores", que lo trae de Gara, con las categorías de las especies, esto nos va a servir para poder sectorizar y separar las especies por grupos.
#Utiliza por último el archivo "exterior_y_cedears", que contiene la información de las especies que sean ACCIONES (CEDEARS, ADRs y Exterior que no operen como CEDEARS acá)
import pandas as pd
import os
from datetime import datetime
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
#Creamos las carpetas donde guardamos las cosas. Dentro de Inputs, guardo las fotos que hace el programa, y en Reportes, que está antes, guardo los PDFs
from datetime import date 
from datetime import timedelta
import time
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import PIL.Image
import matplotlib.gridspec as gridspec
import plotly.graph_objs as go
import eikon as ek
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os.path
import math
import eikon as ek
ek.set_app_key('46e757135590444b817e89a2b5d8af0ae013bd3b')
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pandas.core.dtypes.cast")
path=r"C:\Users\ldt\Documents\Agustin Ehrman\Reportes Comitentes (definitivo)"
os.chdir(path)

reporte= os.path.join(path,"Reportes\\")
if not os.path.exists(reporte):
    os.mkdir(reporte)

path= r"C:\Users\ldt\Documents\Agustin Ehrman\Reportes Comitentes (definitivo)\Inputs"
os.chdir(path)
graficos= os.path.join(path,"Graficos\\")
if not os.path.exists(graficos):
    os.mkdir(graficos)
    
import shutil
Date = str(date.today())
dir = os.path.join(reporte, Date)
dirG = os.path.join(graficos, Date)
if os.path.exists(dir):
    pass
else:
    os.mkdir(dir)
if os.path.exists(dirG):
    pass
else:
    os.mkdir(dirG)
today = datetime.today().strftime('%Y-%m-%d') #Fecha de hoy
#Descargamos el CCL para poder dividir los precios de las especies que están en pesos.
dolar= input('Inserte qué dolar quiere utilizar: 1 para MEP, 2 para CCL, o 3 si quiere ingresarlo a mano: ')
if dolar== '1':
    CCL= ek.get_data('ARSMEP=','CF_LAST')[0]['CF_LAST'].astype(float).iloc[0]
elif dolar== '2':
    ggal= ek.get_data('AAPL.O','CF_LAST')[0]['CF_LAST'].astype(float)
    ggalba= ek.get_data('AAPLm.BA','CF_LAST')[0]['CF_LAST'].astype(float)
    CCL= (ggalba/ggal).iloc[0]*20
elif dolar== '3':
    CCL = float(input('Ingrese el tipo de cambio que quiere utilizar: '))
gara_raw= pd.read_excel("Administración de Títulos Valores.xls", header=1) #De acá voy a sacar la CATEGORÍA DE LAS ESPECIES, si son CEDEARS, ADRS, BONOS, Etc.
gara_raw= gara_raw.rename(columns={"Cód.":"Codigo",
                           "Categoría":"Categoria",
                           "Un.Precio":"Unidad_precio",
                           "Denominación Abrev.":"Nombre"})
gara= gara_raw.reindex(columns=["Codigo", "Categoria", "Unidad_precio"]) #Me quedo solamente con estas columnas, son las que me interesan
gara.loc[gara['Categoria'] == 'Fondos de Inversion', 'Unidad_precio'] = 1000
moneda= pd.DataFrame({"Codigo":[7000,8000,8700,9000,9002,10000,6000],
                      "Categoria":["Moneda","Moneda","Moneda","Moneda","Moneda","Moneda","Moneda"],
                      "Unidad_precio":[1,1,1,1,1,1,1]}) #Agrego las especies de moneda al de Gara para tenerlas clasificadas.
categorias= pd.concat([gara,moneda], ignore_index=True) #Agrego las especies del tipo moneda ya categorizadas.

exterior= pd.read_excel("exterior_y_cedears_ACTUALIZADO.xlsx", header=1) #Importo el excel que contiene información sobre las especies que son acciones del exterior, ya sea su sector, el RIC, etc. 
del(exterior["Sector_ingles"])
exterior= exterior.rename(columns={'Nombre_Especie':'Nombre'})
columns_to_replace = ['PE fwd', 'PBV', 'Dividend Yield', 'Close', 'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk', '52Wk High', '52Wk Low','ROE','ROA','PS','PE','GEO','FundType']
for column in columns_to_replace:
    exterior[column] = exterior[column].apply(lambda x: 0 if str(x).startswith('Unable') or str(x).startswith('Access') else x)
exterior[columns_to_replace] = exterior[columns_to_replace].replace([np.nan], 0)
exterior.dropna(inplace=True)
exterior = exterior.reindex(columns=['Codigo','RIC','Nombre','Sector','Pais','PE','PE fwd','PBV','PS', 'Dividend Yield','ROE','ROA', 'Close', 'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk', '52Wk High', '52Wk Low', 'GEO','FundType'])
exterior['ROE'] = exterior['ROE'].astype(float)
exterior['ROA'] = exterior['ROA'].astype(float)

cedears= pd.read_excel("exterior_y_cedears_ACTUALIZADO.xlsx",sheet_name="CEDEARS", header=1) #Hacemos lo mismo con esta sheet que contiene info. sobre CEDEARS, su RIC, sector, etc.
cedears = cedears.reindex(columns=['Codigo','RIC EXTRANJERO','Nombre_Especie','Sector','Pais','PE','PE fwd','PBV','PS', 'Dividend Yield','ROE','ROA', 'Close', 'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk', '52Wk High', '52Wk Low', 'GEO','FundType'])
cedears= cedears.rename(columns={"Nombre_Especie":'Nombre', 'RIC EXTRANJERO':'RIC'})
for column in columns_to_replace:
    cedears[column]= cedears[column].apply(lambda x: 0 if str(x).startswith('Unable') or str(x).startswith('Access') else x)
cedears[columns_to_replace] = cedears[columns_to_replace].replace([np.nan], 0)
cedears_nan = cedears[cedears[['Sector']].isna().any(axis=1)]
cedears= cedears.dropna(subset=["RIC"])
cedears['ROE'] = cedears['ROE'].astype(float)
cedears['ROA'] = cedears['ROA'].astype(float)

columns_to_replace = ['PE fwd', 'PBV', 'Dividend Yield', 'Close', 'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk', '52Wk High', '52Wk Low','ROE','ROA','PS','PE']
byma= pd.read_excel("exterior_y_cedears_ACTUALIZADO.xlsx",sheet_name="ACCIONES ARGENTINAS", header=0) 
byma= byma.reindex(columns=['Codigo','RIC','Nombre','Sector','Pais','PE','PE fwd','PBV','PS', 'Dividend Yield','ROE','ROA', 'Close', 'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk', '52Wk High', '52Wk Low'])
for column in columns_to_replace:
    byma[column]= byma[column].apply(lambda x: 0 if str(x).startswith('Unable') or str(x).startswith('Access') else x)
byma[columns_to_replace] = byma[columns_to_replace].replace([np.nan], 0)
byma['ROE'] = byma['ROE'].astype(float)
byma['ROA'] = byma['ROA'].astype(float)
byma.dropna(inplace=True)

general= pd.read_excel("exterior_y_cedears_ACTUALIZADO.xlsx", sheet_name= "GENERAL", header= 0)
general= general[['Codigo','RIC','Nombre_eikon','Sector','Pais','PE','PE fwd','PBV','PS', 'Dividend Yield','ROE','ROA', 'Close', 'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk', '52Wk High', '52Wk Low']]
for column in columns_to_replace:
    general[column]= general[column].apply(lambda x: 0 if str(x).startswith('Unable') or str(x).startswith('Access') else x)
general[columns_to_replace] = general[columns_to_replace].replace([np.nan], 0)
general= general.rename(columns={'Nombre_eikon':'Nombre'})
general['ROE'] = general['ROE'].astype(float)
general['ROA'] = general['ROA'].astype(float)
general.dropna(inplace=True)

info_especies= pd.concat([exterior, cedears, byma, general], ignore_index=True) #Recopilamos la informacion de las especies que son acciones aqui.
info_especies.drop_duplicates(subset=['Codigo'], inplace=True)
info_especies.fillna(0, inplace=True)

codigos_ext= exterior["Codigo"].tolist() #Vamos a agregar las especies de exterior al dataframe que contiene a las categorías y la unidad de precio.
codigos_exterior= pd.DataFrame({"Codigo":codigos_ext,
                                "Categoria":["Exterior"]*len(codigos_ext),  
                                "Unidad_precio":[1]*len(codigos_ext)}) 

categorias= pd.concat([categorias, codigos_exterior],ignore_index=True) #Ahora tenemos todas las especies que operan en LDT clasificadas.
categorias.drop_duplicates(['Codigo'], inplace=True) #Hay especies que están dos veces cuándo cargo las de exterior, que el archivo de Gara ya tenía como ADR


bonos_afuera= pd.read_excel('LISTA_BONOS_EXT.xlsx')
bonos_ext= bonos_afuera.Codigo.to_list()

categorias= pd.concat([categorias,bonos_afuera], ignore_index=True)

#Agregamos ahora la columna que va a distinguir si es acción de acá, de afuera, o si es un bono de acá, o de afuera. Las categorías anteriores van a servir para poder diferenciar las especies dentro de estas 4 grandes categorías.
condiciones = [categorias["Categoria"].isin(["Acciones Privadas", "A.D.R. S (Acciones)","Acciones PYMES","Cupones Privados","Fondos de Inversion"]),
               categorias["Categoria"].isin(["CEDEARS", "Exterior","Cupones Externos"]),
               categorias["Categoria"].isin(["Titulos Publicos","Titulos de Deuda","Letras","Letras del Tesoro Nacional","Bonos Consolidacion","Bonos Externos","Obligaciones Negociables","Obligaciones Negociables PYME","Cupones Publicos", "Certificados de Participacion"]),
               categorias["Categoria"] == "Moneda",
               categorias["Categoria"] == "ONs del exterior"
               ]
valores = ["Renta Variable Local", "Renta Variable Extranjera", "Renta Fija Local", "Moneda", "Renta Fija Extranjera"]
categorias["Clasificacion"]= np.select(condiciones, valores, default=np.nan)
#Completamos algunas categorías, que son los fondos de inversión y redefinimos algunos valores, ya que en la categoría "Exterior" habían bonos u ONs de afuera, o los treasuries que estaban como titulos publicos en gara. 
categorias.loc[(categorias["Clasificacion"]=="Acciones Exterior")&(categorias["Unidad_precio"]==100),'Clasificacion']= "Bonos Exterior"
etfs= [5824, 7483, 7747, 8549, 8550, 8551, 8552, 8553, 8554, 8555, 8556, 8557, 41118, 41159, 41160, 41422, 41462, 41534, 41721, 41994, 47532, 47543, 47667, 47793, 47812, 47961, 48369, 48469, 48775, 49075, 49093, 49276, 49292, 49804, 49815, 49870, 49900, 90331, 90462, 90563, 90581, 90651, 90662, 90664, 90671, 90791, 90802, 90875, 90939,
       93072, 93073, 93074, 93223, 93322, 93363, 93438, 93589, 93593, 93596, 93600, 93601, 93682, 93729, 93770, 93807, 93975, 94020, 94157, 94473, 94527, 94620, 95160, 95232, 95523, 95558, 95646, 96167, 96254, 96299]
codigos_treasury = gara_raw[gara_raw['Nombre'].str.contains("TREA")]['Codigo'].tolist()
categorias.loc[categorias['Codigo'].isin(etfs), 'Clasificacion'] = 'ETFs'
categorias.loc[categorias['Codigo'].isin(codigos_treasury), 'Clasificacion'] = 'Renta Fija Extranjera'
categorias.loc[categorias['Codigo'].isin(bonos_ext), 'Clasificacion'] = 'Renta Fija Extranjera'
#corregimos un par de especies que estaban categorizadas como locales pero que son de exterior
corregir= [7024,90060,90240,96328]
categorias.loc[categorias['Codigo'].isin(corregir), 'Clasificacion'] = 'Renta Variable Extranjera'
categorias.loc[(categorias['Categoria'] == 'Fondos de Inversion')&(categorias['Clasificacion'] == 'ETFs'), 'Unidad_precio'] = 1
#Cargamos las tenencias de los clientes
categorias.drop_duplicates(['Codigo'], inplace=True)
tenencia_raw= pd.read_excel("TVAFECHA.xls")
tenencia_raw=tenencia_raw.rename(columns={"'Numero'":'Comitente',
                                  "'Tenencia'":'Tenencia',
                                  "'Nombre de la Especie'":'Especie',
                                  "'Importe'":'Importe',
                                  "'Precios'":'P_gallo'})

tenencia_raw['Comitente']=tenencia_raw['Comitente'].fillna(method='pad')
#Guardamos la tenencia en pesos aparte (es negativa a veces, dependiendo si es tomador de caución o debe) 
pesos=tenencia_raw[(tenencia_raw.Especie=='PESOS')]
pesos=pesos.reindex(columns=['Comitente','Importe'])
pesos= pesos.rename(columns={"'Importe'":'Valorizada'})
pesos.reset_index(drop=True, inplace=True)
                    

aux= tenencia_raw['Especie'].str.split(" ", n = 1, expand = True) #De esta forma desagregamos el nombre de las especies y el código
tenencia_raw["Codigo"]=aux[0]
tenencia_raw["Nombre_Especie"]=aux[1]

tenencia_reportes = tenencia_raw.reindex(columns=['Comitente','Codigo','Nombre_Especie','Tenencia','P_gallo'])
tenencia_reportes=tenencia_reportes[(tenencia_reportes.Tenencia!=0)] #Remuevo las que tienen tenencia 0.

tenencias_opciones= tenencia_reportes[tenencia_reportes["Codigo"].str.endswith('B')].copy() #Las opciones tienen una B al final del código, las guardo aparte por ahora.
tenencias_opciones.loc[:, "Codigo"] = tenencias_opciones["Codigo"].astype(str).str.replace("B", "000") #Modifico el codigo de las especies que son opciones para que terminen con tres ceros en vez de que terminen con una B
tenencias_opciones["Codigo"]=tenencias_opciones["Codigo"].astype(int)
codigos_opciones_nuevos= tenencias_opciones["Codigo"].unique().tolist()
opciones_categorizadas= pd.DataFrame({"Codigo":codigos_opciones_nuevos,
                                "Categoria":["Opciones"]*len(codigos_opciones_nuevos),  
                                "Unidad_precio":[0.01]*len(codigos_opciones_nuevos),#Yo divido el precio por la unidad, como las opciones es $x100 divido por 0.01
                                "Clasificacion":["Opciones"]*len(codigos_opciones_nuevos)}
                               ) 
categorias= pd.concat([categorias, opciones_categorizadas],ignore_index=True) #Unimos las opciones a las categorías

tenencia_reportes.loc[:, "Codigo"] = tenencia_reportes["Codigo"].astype(str).str.replace("B", "000")
tenencia_reportes["Codigo"]=tenencia_reportes["Codigo"].astype(int)
#Estaban como string, por las opciones que contienen la B, ahora los paso a números para poder mergear con las categorías
cuentas_afuera= pd.read_excel('cta fenix.xlsx')
cuentas_afuera= cuentas_afuera[['Account','Product','Description','Symbol / ID','ISIN','Quantity','Value ($)']]
cuentas_afuera.columns= ['Comitente','Clasificacion','Nombre_Especie','RIC','ISIN','Tenencia','Valorizada']
cuentas_afuera['Clasificacion'] = cuentas_afuera['Clasificacion'].replace('Cash & Equivalents', 'Moneda')
cuentas_afuera['Clasificacion'] = cuentas_afuera['Clasificacion'].replace('Equities', 'Renta Variable Extranjera')
cuentas_afuera['Clasificacion'] = cuentas_afuera['Clasificacion'].replace('Mutual Funds', 'ETFs')
cuentas_afuera['Clasificacion'] = cuentas_afuera['Clasificacion'].replace('Fixed Income', 'Renta Fija Extranjera')
cuentas_afuera['Tenencia']= np.where(cuentas_afuera['Clasificacion']=='Moneda',cuentas_afuera['Valorizada'],cuentas_afuera['Tenencia'])

'''#cuentas_afuera['Valorizada'] = cuentas_afuera['Valorizada'].str.replace(',', '').astype(float)
cash_equivalents = cuentas_afuera[cuentas_afuera['Clasificación'] == 'Cash & Equivalents']
cash_equivalents= cash_equivalents[['Comitente','Valorizada']]
cash_equivalents.columns= ['Comitente','Importe']
pesos= pd.concat([pesos, cash_equivalents])
pesos.reset_index(inplace=True, drop=True)
cuentas_afuera= cuentas_afuera[cuentas_afuera['Clasificación'] != 'Cash & Equivalents']
'''

categorias= pd.merge(categorias, info_especies, on='Codigo', how='left')
categorias.loc[categorias['Sector'] == 'Indice', 'Clasificacion'] = 'ETFs'
categorias.loc[(categorias['Categoria']=="A.D.R. S (Acciones)")&(categorias['Pais']!="Argentina"),'Clasificacion']='Renta Variable Extranjera'
cate= categorias.copy()
cate= cate[['Codigo','RIC']]
cate.columns= ['Codigo','RIC']
cate = cate.drop_duplicates(subset='Codigo')
cuentas_afuera= pd.merge(cuentas_afuera, cate, on='RIC',how='left')
cuentas_afuera = cuentas_afuera.drop_duplicates(subset='RIC')
cuentas_afuera= cuentas_afuera[['Comitente','Codigo','Nombre_Especie','Clasificacion','RIC','Tenencia','Valorizada']]
cuentas_afuera= pd.merge(cuentas_afuera, categorias, on='Codigo', how='left')
cuentas_afuera.pop('RIC_x')
cuentas_afuera.rename(columns={'RIC_y': 'RIC'}, inplace=True)
cuentas_afuera.pop('Clasificacion_y')
cuentas_afuera.rename(columns={'Clasificacion_x': 'Clasificacion'}, inplace=True)

tenencia_reportes= pd.merge(tenencia_reportes, categorias, on="Codigo", how="left")
#Ahora nos guardamos las especies que faltan saber sus precios, puede que sea porque sean viejas o porque falle gallo la carga de precio
df_p_gallo = tenencia_reportes[tenencia_reportes["P_gallo"]== 0]
df_p_gallo.to_excel("df_faltantes_precio_TVA.xlsx")
tenencia_reportes= tenencia_reportes[((tenencia_reportes["P_gallo"] != 0) | (tenencia_reportes["Clasificacion"] == "Moneda"))] #Quito las especies con precio distinto de 0, salvo para las que son moneda
df_nan = tenencia_reportes[tenencia_reportes[["Clasificacion", "Unidad_precio"]].isna().any(axis=1)]
df_nan.to_excel("df_faltantes_de_categorias.xlsx")  #Acá voy a guardar las especies que me faltan agregarle la categoría y la unidad de precio, por si faltan en el de Gara, se agregan a mano más arriba.
tenencia_reportes.dropna(subset=["Clasificacion"], inplace=True)
tenencia_reportes.reset_index(drop=True, inplace=True)
df_cat= tenencia_reportes[tenencia_reportes[["Categoria"]].isna().any(axis=1)]
#Ahora dolarizamos las especies, el archivo TVA de Gallo trae el precio en dólares de las especies que son ADRS, y especies del exterior (Bonos y Acciones)
tenencia_reportes["Valorizada"]= (tenencia_reportes["Tenencia"]*tenencia_reportes["P_gallo"]/tenencia_reportes["Unidad_precio"])*(tenencia_reportes["Categoria"]!="Moneda") + tenencia_reportes["Tenencia"]*(tenencia_reportes["Categoria"]=="Moneda")
#Lo que hize en la línea de arriba fue hacer P*Q/divisor de precio para las especies que no son moneda, y luego defino Valorizada como la tenencia solamente para las categorías de moneda.
categorias_excluidas= ["Renta Variable Extranjera","Moneda","Renta Fija Extranjera","ETFs"] #Estas son las que NO voy a dividir por CCL porque ya están en dólares, o porque la especie es Pesos o Euros
tenencia_reportes["Valorizada"]= tenencia_reportes["Valorizada"]/CCL*(~tenencia_reportes["Clasificacion"].isin(categorias_excluidas)) + tenencia_reportes["Valorizada"]*(tenencia_reportes["Clasificacion"].isin(categorias_excluidas))
tenencia_reportes.loc[tenencia_reportes['Categoria'] == 'CEDEARS', 'Valorizada'] /= CCL #Corregimos este valor ya que el precio en gallo es en pesos.
tenencia_reportes.loc[(tenencia_reportes['Categoria'] == 'A.D.R. S (Acciones)')&(tenencia_reportes['Pais'] == 'Argentina'), 'Valorizada'] *= CCL #Este valor también ya que es en dólares, lo habíamos dividido por el CCL dos líneas arriba
tenencia_reportes= pd.concat([tenencia_reportes, cuentas_afuera])
tenencia_reportes.loc[tenencia_reportes['Sector'] == 'Indice', 'Clasificacion'] = 'ETFs'

#Importamos el excel que realiza los ratios financieros para las acciones argentinas
ratios_arg= pd.read_excel("Ratios_rawdata.xlsx")
ratios_arg= ratios_arg.rename(columns={"ticker":"RIC"})
ratios_arg['RIC'] = ratios_arg['RIC'].str.replace('.BA', 'm.BA')
for index, row in ratios_arg.iterrows():
    ric = row['RIC']
    pbv = row['PBV']
    ps= row['PS']
    roe= row['ROE']
    roa= row['ROA']
    pe= row['PE']
    tenencia_reportes.loc[tenencia_reportes['RIC']==ric, 'PBV'] = pbv
    tenencia_reportes.loc[tenencia_reportes['RIC']==ric, 'PS'] = ps
    tenencia_reportes.loc[tenencia_reportes['RIC']==ric, 'ROE'] = roe
    tenencia_reportes.loc[tenencia_reportes['RIC']==ric, 'ROA'] = roa
    tenencia_reportes.loc[tenencia_reportes['RIC']==ric, 'PE'] = pe
    
negativas= tenencia_reportes[tenencia_reportes["Tenencia"]<=0] #Me guardo las que tienen tenencia negativa
tenencia_reportes= tenencia_reportes[tenencia_reportes["Tenencia"]>0] #Quito las tenencias negativas
#%%
alexbrown= pd.read_csv(f'3454_AlexBrown.csv')
alexbrown['Valorizada'] = alexbrown['Current Value'].str.replace('$', '').str.replace(',', '').astype(float)
mapping = {
    'Cash & Cash Alternatives': 'Moneda',
    'Alternatives': 'ETFs',
    'Funds': 'ETFs',
    'Stock': 'Renta Variable Extranjera'
}

# Crear la nueva columna 'Clasificación'
alexbrown['Clasificacion'] = alexbrown['Product Type'].map(mapping)

alexbrown['Categoria']= 'Exterior'
alexbrown['Comitente']= 3454
alexbrown['Tenencia'] = alexbrown['Quantity'].str.replace(',', '').astype(float)
alexbrown['RIC']= alexbrown['SYMBOL/CUSIP'].copy()
alexbrown['Nombre_Especie']= alexbrown['Description'].copy()
alexbrown['Nombre']= ['Raymond James Bank Deposit Program','I-Select Absolute Alpha Pf A USD','BFG Fixed Income Global Opp A5 USD','Invesco QQQ Trust Series 1','iShares MSCI India ETF','JH Global Technology and Innovation A2 USD',
                      'Loomis Sayles Multisector Income Fund R/A USD','Loomis Sayles U.S. Core Plus Bond Fund R/A (USD)','MFS Meridian Funds-Global High Yield A2 USD','Pampa Energia SA','Toyota Motors Corporation','VALE SA Sponsored ADS'
                      ,'VanEck Semiconductor ETF','Vontobel Fd TwentyFour Strat Inc Fd H1 hgd USD','YPF Sociedad Anónima ADR']
alexbrown['Sector']= [np.nan,'Indice','Indice','Indice','Indice','Indice','Indice','Indice','Indice','Servicios públicos','Consumo discrecional','Materiales básicos','Indice','Indice','Energía']
alexbrown['Pais']= [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,'Argentina','Japan','Brazil',np.nan ,np.nan,'Argentina']
alexbrown['GEO']= [np.nan,'United States of America','Global','United States of America','India','Global','United States of America','United States of America','Global',np.nan,np.nan,np.nan,'United States of America','Global',np.nan]
alexbrown['FundType']= [np.nan,'Alternatives','Bond','Equity','Equity','Equity','Bond','Bond','Bond',np.nan,np.nan,np.nan,'Equity','Bond',np.nan]
alexbrown= alexbrown[['Comitente','Nombre_Especie','RIC','Categoria','Clasificacion','Tenencia','Valorizada','Nombre','Sector','Pais','GEO','FundType']]
alexbrown['Nombre_Especie'] = alexbrown['Nombre_Especie'].apply(lambda x: ' '.join(x.split()[:5]))
alexbrown['Nombre'] = alexbrown['Nombre'].apply(lambda x: ' '.join(x.split()[:5]))
tenencia_reportes= pd.concat([tenencia_reportes,alexbrown])
#%%
#Ya tenemos todo el dataframe categorizado, falta unir las acciones con sus características (dataframes "cedears" y "exterior")
#Vamos a comenzar el armado de las imágenes para el reporte. 
#Importamos la informacion de los bonos del exterior y los bonos de argentina
bonos_exterior= pd.read_excel("exterior_y_cedears_ACTUALIZADO.xlsx",sheet_name='BONOS EXTRANJEROS', header=0)
bonos_locales= pd.read_excel("exterior_y_cedears_ACTUALIZADO.xlsx",sheet_name='BONOS LOCALES', header=0)
comitentes = set(tenencia_reportes['Comitente'])
comitentes = sorted(comitentes)

while True:
    muchas = input("Ingrese 1 si desea hacer un informe por cuenta. 2 si quiere consolidar más de una por reporte: ")
    
    if muchas in ('1', '2'):
        cuentas = []
        while True:
            cuenta = input("Ingrese la cuenta comitente que quiera realizar el reporte. Ingrese 'x' para terminar: ")
            if cuenta == 'x' or cuenta=='X':
                break
            cuenta = int(cuenta)
            if cuenta not in comitentes:
                print("El número de cuenta ingresado no está en la lista de comitentes. Por favor, intente de nuevo.")
            else:
                cuentas.append(cuenta)
        
        # If the input was valid and the inner loop completed, break the outer loop
        break
    else:
        print("Opción no válida. Por favor, ingrese 1 o 2.")
while True:
    pprom= input("Desea computar el rendimiento promedio de sus tenencias? Presione 1 si desea evitarlo, 2 si quiere computarlo: ")
    if pprom in ('1', '2'):
        break
    else:
        print("Opción no válida. Por favor, ingrese 1 o 2.")
    
while True:
    calcular_g= input("Desea calcular las tasas de crecimiento de las empresas? Presione 1 si desea evitarlo, 2 si quiere computarlo: ")
    if calcular_g in ('1', '2'):
        break
    else:
        print("Opción no válida. Por favor, ingrese 1 o 2.")
    
#%%
if muchas=='2':
    cuenta= cuentas
    tenencia_cuenta= tenencia_reportes[tenencia_reportes["Comitente"].isin(cuenta)]
    tenencia_cuenta= tenencia_cuenta.sort_values('Clasificacion')   
    tenencia_cuenta.reset_index(drop=True, inplace=True)
    
    def contadoconliqui(method='YF'): #Descarga y crea serie historica para CCL
        if method == 'YF':
            tickers = ["GGAL","GGAL.BA"]
            GGAL = yf.download(tickers, interval='1d', ignore_tz=True)['Adj Close']
            ccl =GGAL["GGAL.BA"]/GGAL["GGAL"]*10
            ccl= ccl.fillna(method='ffill')
            ccl= ccl.dropna()
            ccl= ccl.reset_index(drop=False)
            ccl.columns= ['FechaOp','CCL']
        else:
            ccl= ek.get_timeseries('ARSMEP=', start_date='2015-01-01')['CLOSE'].astype(float)
            ccl= ccl.fillna(method='ffill')
            ccl.dropna(inplace=True)
            ccl=ccl.reset_index(drop=False)
            ccl.columns= ['FechaOp','CCL']
        return ccl
    
    def corregir_precios(ht, method='YF'):
        rics = ht.loc[ht['Categoria'] == 'Exterior', 'RIC'].unique().tolist()
        if method == 'YF':
            precios = yf.download(rics, period="max")['Adj Close']
        else:
            precios = ek.get_timeseries(rics, start_date = datetime.now() + timedelta(-365*4))
            precios = precios.swaplevel(i='Security', j='Field', axis=1)
            precios= precios['CLOSE'].fillna(method='ffill')
        # Función para obtener el precio ajustado al cierre para una fila dada
        def obtener_precio_ajustado(row):
            if row['Categoria'] != 'Exterior':
                return row['Precio']  # Si no es de la categoría 'Exterior', retornar el precio original
            fecha = row['FechaOp']
            ric = row['RIC']
            # Intentar obtener el precio ajustado para la fecha y el RIC; si falla, usar el precio original
            try:
                return precios.loc[fecha, ric]
            except KeyError:
                return row['Precio']
        
        # Aplicar la función a cada fila del DataFrame original para actualizar los precios
        ht['Precio'] = ht.apply(obtener_precio_ajustado, axis=1)
    
    def rendimientos(tenencia_cuenta, cuenta, categorias):
        ccl= contadoconliqui(method='YF')
        tenencias= tenencia_cuenta[tenencia_cuenta["Clasificacion"] != "Moneda"]
        tenencias= tenencias[tenencias["Clasificacion"] != "Opciones"]
        cuenta_str = [str(num).zfill(6) for num in cuenta]
        cuenta_str= '-'.join(map(str, cuenta_str))
        cuenta_s= '-'.join(map(str, cuenta))
        
        ht= pd.read_excel(f'HT{cuenta_str}.xls')
        ht.columns=['Comitente','Codigo','Especie','Concepto','FechaLiq','FechaOp','Comprobante','Referencia','Cantidad','Precio','Saldo']
        ht= ht[['Comitente','Codigo','Especie','Concepto','FechaOp','Cantidad','Precio']]
        ht= pd.merge(ht,categorias, on="Codigo", how="left")
        ht= pd.merge(ht, ccl, on='FechaOp', how='left')
        ht['RIC'] = ht['RIC'].fillna('')
        cols= ['Comitente', 'Codigo', 'Especie', 'Concepto', 'FechaOp', 'Cantidad',
               'Precio', 'Categoria', 'Unidad_precio', 'Clasificacion', 'RIC',
               'Nombre', 'Sector', 
               'CCL']
        ht= ht[cols]
        ht.loc[ht['Concepto'] == 'CANJ', 'Precio'] = 0
        try:
            corregir_precios(ht, method='EK')
        except:
            try:
                corregir_precios(ht, method='EK')
            except:
                pass
        ht['Monto_Pesos'] = np.where(ht['Categoria'] != 'Exterior',
                                     ht['Cantidad'] * ht['Precio'] / ht['Unidad_precio'],
                                     ht['Cantidad'] * (ht['Precio'] / ht['Unidad_precio']) * ht['CCL'])

        ht['Monto_Usd']= ht['Monto_Pesos']/ht['CCL']
        codigos = tenencias['Codigo'].unique().tolist() #Me quedo solo con los papeles que están en el TVAFECHA
        mask= ht.Codigo.isin(codigos)
        ht= ht[mask]
        
        conceptos = ['DETS','RTTS']
        mask= ht.Concepto.isin(conceptos)
        ht= ht[~mask]
        
        to_drop = []
        # Iterar a través del DataFrame utilizando índices
        for i in range(len(ht)):
            # Elimino la compra de dólar MEP para las especies que compraron y vendieron por la misma cantidad.
            if ht.iloc[i]['Concepto'] == 'VTU$' and ht.iloc[i-1]['Concepto'] == 'CPRA' and ht.iloc[i]['Cantidad'] == -ht.iloc[i-1]['Cantidad'] and ht.iloc[i]['Codigo'] == ht.iloc[i-1]['Codigo']:
                # Agregar índices de las filas a la lista
                to_drop.append(i)
                to_drop.append(i-1)
            if ht.iloc[i]['Concepto'] == 'CPRA' and ht.iloc[i-1]['Concepto'] == 'VTU$' and ht.iloc[i]['Cantidad'] == -ht.iloc[i-1]['Cantidad'] and ht.iloc[i]['Codigo'] == ht.iloc[i-1]['Codigo']:
                # Agregar índices de las filas a la lista
                to_drop.append(i)
                to_drop.append(i-1)
        # Eliminar las filas marcadas
        ht = ht.drop(ht.index[to_drop])
        ht = ht.reset_index(drop=True)
        
        clases= ht.Clasificacion.unique().tolist()
        for clase in clases:
            ht_clase= ht[ht['Clasificacion']==clase].copy()
            if clase in ['Renta Variable Extranjera','ETFs']:
                ht_porespecie = dict(tuple(ht_clase.groupby('RIC')))
            else:
                ht_porespecie = dict(tuple(ht_clase.groupby('Codigo')))
            ht_porespecie_filtrado = ht_porespecie.copy()
            
            for codigo, df in ht_porespecie_filtrado.items():
                print(codigo)
                juntos= pd.DataFrame()
                for comitente in cuenta:
                    ht_cuenta= df[df['Comitente']==comitente]
                    ht_cuenta= ht_cuenta.sort_values(by=['FechaOp'])
                    ht_cuenta = ht_cuenta.reset_index(drop=True)
                    ht_cuenta['Saldo_Usd'] = ht_cuenta['Monto_Usd'].cumsum()
                    ht_cuenta['Cantidad_Acum'] = ht_cuenta['Cantidad'].cumsum()
                    
                    # Identificamos los índices donde el saldo es menor o igual a cero, indicando que vendió todo
                    reset_indices = ht_cuenta[(ht_cuenta['Saldo_Usd'] <= 0) & (ht_cuenta['Cantidad_Acum'] <= 0)].index

                    if not reset_indices.empty:
                        # Tomamos el último índice donde el saldo fue menor o igual a cero
                        last_reset_index = reset_indices[-1]
                        # Filtramos el DataFrame para considerar solo operaciones después de ese punto
                        df_filtered = ht_cuenta.loc[last_reset_index + 1:]
                        df_filtered= df_filtered.reset_index(drop=True)
                        df_filtered['Saldo_Usd']= df_filtered['Monto_Usd'].cumsum()
                        df_filtered['Cantidad_Acum']= df_filtered['Cantidad'].cumsum()
                        fila= df_filtered.tail(1)
                        ##ht_porespecie_filtrado[codigo] = df_filtered  # Actualizamos el diccionario con el DF filtrado
                        juntos= pd.concat([juntos, fila], ignore_index=True)
                    else:
                        juntos= pd.concat([juntos, ht_cuenta.tail(1)], ignore_index=True)
                        ##ht_porespecie_filtrado[codigo] = df  # Aseguramos que el DF se mantenga en el diccionario si no hay reset
                if clase in ['Renta Variable Extranjera','ETFs']:
                    juntos=  juntos.groupby('Nombre').agg({'Especie':'first','RIC': 'first','Clasificacion':'first','Saldo_Usd':'sum','Cantidad_Acum':'sum'}).reset_index()
                else:
                    juntos=  juntos.groupby('Codigo').agg({'Especie': 'first','RIC':'first','Nombre':'first','Clasificacion':'first','Saldo_Usd':'sum','Cantidad_Acum':'sum'}).reset_index()
                ht_porespecie_filtrado[codigo] = juntos
            pprom = {}
            for codigo, df in ht_porespecie_filtrado.items():
                print(codigo)
                try:
                    df_pprom= pd.DataFrame()
                    df_pprom['Especie']= df.Especie.unique().tolist()
                    if clase in ['Renta Variable Extranjera','ETFs','Renta Variable Local']:
                        df_pprom['Nombre']= df.Nombre.unique().tolist()
                        df_pprom['RIC']= df.RIC.unique().tolist()
                    df_pprom['Clasificacion']= df.Clasificacion.unique().tolist()
                    
                    df_pprom['Monto Invertido Usd']= [df['Saldo_Usd'].iloc[-1]]
                    if clase in ['Renta Variable Extranjera','ETFs']:
                        df_pprom['Monto Actual Usd']= [tenencias[tenencias['RIC']==codigo]['Valorizada'].sum()] 
                    else:
                        
                        df_pprom['Monto Actual Usd']= [tenencias[tenencias['Codigo']==codigo]['Valorizada'].sum()] 
                    df_pprom['Rendimiento Usd']= (df_pprom['Monto Actual Usd'] / df_pprom['Monto Invertido Usd'] -1)*100
                    
                    pprom[codigo]= df_pprom
                except:
                    pass
    
            preciospromedios = pd.DataFrame()
            # Concatenar los DataFrames de cada clave en el diccionario
            for codigo, df_pprom in pprom.items():
                preciospromedios = pd.concat([preciospromedios, df_pprom], ignore_index=True)
            
            preciospromedios['Participacion']= preciospromedios['Monto Actual Usd'] / preciospromedios['Monto Actual Usd'].sum()*100
            preciospromedios['Participacion']= preciospromedios['Participacion'].map('{:.2f}%'.format)
            preciospromedios['Monto Invertido Usd']= preciospromedios['Monto Invertido Usd'].map('{:,.2f}'.format)
            preciospromedios['Monto Actual Usd']= preciospromedios['Monto Actual Usd'].map('{:,.2f}'.format)
            preciospromedios['Rendimiento Usd']= preciospromedios['Rendimiento Usd'].map('{:.2f}%'.format)
       
            tabla= preciospromedios.copy()
            if clase in ['Renta Fija Local', 'Renta Fija Extranjera']:
                fig = go.Figure(data=[go.Table(
                    columnwidth=[3.5, 1.5, 1.5, 1.5, 1.5],
                    header=dict(height = 30,
                                values=['<b>ESPECIE</b>','<b>USD INVERTIDOS</b>','<b>USD ACTUALES</b>','<b>REND. %</b>','<b>% S/ACTIVOS</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Especie, tabla['Monto Invertido Usd'], tabla['Monto Actual Usd'],tabla['Rendimiento Usd'],tabla['Participacion']],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+4.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                
                fig.write_image(f'{dirG}\\tabla rendimientos {clase} - {cuenta_s}.png',scale=1)
            
            else:
                fig = go.Figure(data=[go.Table(
                    columnwidth=[3, 1.5, 1.5, 1.5, 1.5],
                    header=dict(height = 30,
                                values=['<b>ESPECIE</b>','<b>USD INVERTIDOS</b>','<b>USD ACTUALES</b>','<b>REND. %</b>','<b>% S/ACTIVOS</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Nombre, tabla['Monto Invertido Usd'], tabla['Monto Actual Usd'],tabla['Rendimiento Usd'],tabla['Participacion']],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align= 'center',
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+4.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                
                fig.write_image(f'{dirG}\\tabla rendimientos {clase} - {cuenta_s}.png',scale=1)
    if pprom=='2':
        rendimientos(tenencia_cuenta, cuenta, categorias)    
    #Comenzamos a generar los gráficos. El primero es el de torta general.
    def torta_general(tenencia_cuenta, cuenta):
        tenencia_activos= tenencia_cuenta[tenencia_cuenta['Clasificacion']!= 'Moneda']
        assets = tenencia_activos.groupby("Clasificacion")["Valorizada"].sum()
        '''
        tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"]
        #Agregamos las tenencias negativas
        tenencia_negativos= negativas[negativas["Comitente"].isin(cuenta)&(negativas['Clasificacion']=='Moneda')]
        tenencia_moneda = pd.concat([tenencia_moneda, tenencia_negativos], ignore_index=True)
        
        
        cuenta_corriente= pesos[pesos["Comitente"].isin(cuenta)].copy()
        cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos en Cta. Corriente en USD al CCL"
        cuenta_corriente= cuenta_corriente[["Nombre_Especie", "Importe"]]
        cuenta_corriente= cuenta_corriente.rename(columns={"Importe":"Valorizada"})
        tenencia_moneda= pd.concat([tenencia_moneda, cuenta_corriente], ignore_index= True)
        
        tenencia_moneda.loc[tenencia_moneda['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
        total_row = pd.DataFrame({'Nombre_Especie': ['TOTAL USD'], 'Valorizada': [tenencia_moneda.Valorizada.sum()]})
        tenencia_moneda = pd.concat([tenencia_moneda, total_row], ignore_index=True)
        if tenencia_moneda.empty:
            pass
            
        else:
            monedas = tenencia_moneda.groupby("Nombre_Especie")["Valorizada"].sum()
            if monedas.sum()<=0:
                pass
            else:
                assets.loc["Moneda"]= monedas.sum()
        '''
        
        parameters = {'axes.labelsize': 20,
                      'axes.titlesize': 20,
                      'font.family': 'Arial'}
        plt.rcParams.update(parameters)
        
        # Crear la figura y los subplots utilizando plt.GridSpec
        fig = plt.figure(figsize=(30, 10))
        grid = plt.GridSpec(2, 3, width_ratios=[2, 1, 1])
        
        ax1 = plt.subplot(grid[:, 0])  # Este subplot ocupa ambas filas de la primera columna
        ax1.pie(assets.values, labels=assets.index, labeldistance=1.1, autopct='%1.1f%%',pctdistance=0.8,textprops={'fontsize': 16}, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
        circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
        ax1.add_artist(circle)
        ax1.set_title('Distribución General de la Cartera')
        
        #Montos en activos locales
        tenencia_categorias= tenencia_activos.groupby("Clasificacion").sum()
        tenencia_categorias= tenencia_categorias.reset_index()
        
        tenencia_locales= tenencia_categorias.loc[tenencia_categorias['Clasificacion'].str.contains('Local', case=False)]
        tenencia_locales= tenencia_locales[["Clasificacion","Valorizada"]]
        tenencia_locales["Participacion"]= tenencia_locales["Valorizada"]/tenencia_locales.Valorizada.sum()*100
        ax2 = plt.subplot(grid[0, 1])  # Este subplot está en la fila 1 y columna 2
        ax2.pie(tenencia_locales.Participacion, labels=tenencia_locales.Clasificacion, labeldistance=1.1, autopct='%1.1f%%',pctdistance=0.8,textprops={'fontsize': 16}, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
        circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
        ax2.add_artist(circle)
        ax2.set_title('Distribucion en Activos Locales')
        
        tenencia_extranjeras= tenencia_categorias.loc[tenencia_categorias['Clasificacion'].str.contains('Extranjera', case=False)]
        tenencia_extranjeras= tenencia_extranjeras[["Clasificacion","Valorizada"]]
        tenencia_extranjeras["Participacion"]= tenencia_extranjeras["Valorizada"]/tenencia_extranjeras.Valorizada.sum()*100
        ax3 = plt.subplot(grid[1, 1])  # Este subplot está en la fila 1 y columna 2
        ax3.pie(tenencia_extranjeras.Participacion, labels=tenencia_extranjeras.Clasificacion, labeldistance=1.1, autopct='%1.1f%%',pctdistance=0.8,textprops={'fontsize': 16}, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
        circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
        ax3.add_artist(circle)
        ax3.set_title('Distribucion en Activos Extranjeros')
        cuenta= '-'.join(map(str, cuenta))
        plt.savefig(f'{dirG}\\torta General {cuenta}.png',bbox_inches='tight',edgecolor='w')
    torta_general(tenencia_cuenta,cuenta)
    
       
    #Correr en la consola este comando: conda install -c plotly plotly-orca
    #Ahora hacemos las tablas de tenencia de cada uno.
    def tabla_moneda(tenencia_cuenta, cuenta, dirG):
        tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"].groupby("Nombre_Especie").sum()
        tenencia_moneda.reset_index(inplace=True)
        #Agregamos las tenencias negativas
        tenencia_negativos= negativas[negativas["Comitente"].isin(cuenta)&(negativas['Clasificacion']=='Moneda')].groupby("Nombre_Especie").sum()
        tenencia_negativos.reset_index(inplace=True)
        tenencia_moneda = pd.concat([tenencia_moneda, tenencia_negativos], ignore_index=True)
        tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"].groupby("Nombre_Especie").sum()
        tenencia_moneda.reset_index(inplace=True)
        
        cuenta_corriente= pesos[pesos["Comitente"].isin(cuenta)].copy()
        cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos en Cta. Corriente en USD al CCL"
        cuenta_corriente= cuenta_corriente[["Nombre_Especie", "Importe"]]
        cuenta_corriente= cuenta_corriente.rename(columns={"Importe":"Valorizada"})
        cuenta_corriente= cuenta_corriente.groupby('Nombre_Especie').sum()
        cuenta_corriente.reset_index(inplace=True)
        tenencia_moneda= pd.concat([tenencia_moneda, cuenta_corriente], ignore_index= True)
        
        tenencia_moneda.loc[tenencia_moneda['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
        total_row = pd.DataFrame({'Nombre_Especie': ['TOTAL USD'], 'Valorizada': [tenencia_moneda.Valorizada.sum()]})
        tenencia_moneda = pd.concat([tenencia_moneda, total_row], ignore_index=True)
        
        
        
        tenencia_moneda['Valorizada'] = tenencia_moneda['Valorizada'].map('{:,.2f}'.format)
        tabla= tenencia_moneda[['Nombre_Especie','Valorizada']].copy()
        tabla.loc[tabla['Nombre_Especie'] == 'TOTAL USD', :] = tabla.loc[tabla['Nombre_Especie'] == 'TOTAL USD', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
        
        
        
        if tabla.empty:
            print("No hay tenencia de moneda")
            no_moneda= True
            return no_moneda
        
        fig = go.Figure(data=[go.Table(
            columnwidth=[0.8,0.8,0.8],
            header=dict(height = 30,
                        values=['<b>TIPO DE MONEDA </b>','<b>TENENCIA</b>'],
                        fill_color='#d7d8d6',
                        line_color='darkslategray',
                        align='center',
                        font=dict(family='Arial', color='black', size=20)),
            cells=dict(values=[tabla.Nombre_Especie, tabla.Valorizada],
                        fill_color=['#ffffff'],
                        height=30,
                        line_color='darkslategray',
                        align=['left','center','center'],
                        font=dict(family='Arial', color='black', size=18)))
        ])
        h=(len(tabla.index)+2.5)*cm
        fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
        cuenta= '-'.join(map(str, cuenta))
        fig.write_image(f'{dirG}\\tabla moneda - {cuenta}.png',scale=1)
        
    tabla_moneda(tenencia_cuenta, cuenta, dirG)
    
    def tabla_tenencia_activos(tenencia_cuenta, cuenta, dirG):
        tenencias_totales = tenencia_cuenta[tenencia_cuenta["Clasificacion"] != "Moneda"]
        tabla= tenencias_totales[['Clasificacion','Valorizada']]
        aux= tabla.groupby('Clasificacion').sum()
        aux.reset_index(inplace=True)
        total_valorizada = aux['Valorizada'].sum()
        total_row = pd.DataFrame({'Clasificacion': ['Total'], 'Valorizada': [total_valorizada]})
        tabla = pd.concat([aux, total_row], ignore_index=True)
        tabla['Participacion']= tabla['Valorizada']/total_valorizada*100
        tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
        tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
        tabla.loc[tabla['Clasificacion'] == 'Total', :] = tabla.loc[tabla['Clasificacion'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
    
        fig = go.Figure(data=[go.Table(
            columnwidth=[0.8,0.8,0.8],
            header=dict(height = 30,
                        values=['<b>CLASIFICACION</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                        fill_color='#d7d8d6',
                        line_color='darkslategray',
                        align='center',
                        font=dict(family='Arial', color='black', size=20)),
            cells=dict(values=[tabla.Clasificacion, tabla.Valorizada, tabla.Participacion],
                        fill_color=['#ffffff'],
                        height=30,
                        line_color='darkslategray',
                        align=['left','center','center'],
                        font=dict(family='Arial', color='black', size=18)))
        ])
        h=(len(tabla.index)+2.5)*cm
        fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
        cuenta= '-'.join(map(str, cuenta))
        fig.write_image(f'{dirG}\\tabla activos - {cuenta}.png',  scale=1)
                                    
    tabla_tenencia_activos(tenencia_cuenta, cuenta, dirG)
    
    
    
    
    def tablas_negativas(negativas, cuenta, dirG):
        tenencia_negativos= negativas[negativas["Comitente"].isin(cuenta)]
        tenencia_negativos= tenencia_negativos[['Nombre_Especie', 'Clasificacion', 'Valorizada']]
        tenencia_negativos.loc[tenencia_negativos['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
        total_row= pd.DataFrame({"Nombre_Especie": ["TOTAL"], "Clasificacion": "", "Valorizada": tenencia_negativos.Valorizada.sum()})
        tenencia_negativos= pd.concat([tenencia_negativos, total_row], ignore_index= True)
        tenencia_negativos['Valorizada'] = tenencia_negativos['Valorizada'].map('{:,.2f}'.format)
        
        tabla= tenencia_negativos.copy()
        tabla.loc[tabla['Nombre_Especie'] == 'TOTAL', :] = tabla.loc[tabla['Nombre_Especie'] == 'TOTAL', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
        if tabla.empty:
            print("No hay tenencia negativas")
            no_negativos= True
            return no_negativos
        if (tabla.Clasificacion == "Opciones").any()==True:
            columnwidth= [1.2,0.8,0.8]
        else:
            columnwidth=[0.8,0.8,0.8]
        
        fig = go.Figure(data=[go.Table(
            columnwidth=columnwidth,
            header=dict(height = 30,
                        values=['<b>NOMBRE DE LA ESPECIE</b>','<b>CLASIFICACION</b>','<b>MONTO (USD)</b>'],
                        fill_color='#d7d8d6',
                        line_color='darkslategray',
                        align='center',
                        font=dict(family='Arial', color='black', size=20)),
            cells=dict(values=[tabla.Nombre_Especie, tabla.Clasificacion, tabla.Valorizada],
                        fill_color=['#ffffff'],
                        height=30,
                        line_color='darkslategray',
                        align=['left','center','center'],
                        font=dict(family='Arial', color='black', size=18)))
        ])
        h=(len(tabla.index)+4.5)*cm
        fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
        cuenta= '-'.join(map(str, cuenta))
        fig.write_image(f'{dirG}\\tabla tenencias negativas - {cuenta}.png', scale=1)
        
    tablas_negativas(negativas, cuenta, dirG)
    
    def tabla_tenencia_total(tenencia_cuenta, cuenta, negativas, pesos, dirG):
        tenencia_activos= tenencia_cuenta[tenencia_cuenta['Clasificacion']!= 'Moneda']
        assets = tenencia_activos.groupby("Clasificacion")["Valorizada"].sum()
        
        tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"]
        #Agregamos las tenencias negativas
        tenencia_negativos= negativas[negativas["Comitente"].isin(cuenta)&(negativas['Clasificacion']=='Moneda')]
        tenencia_moneda = pd.concat([tenencia_moneda, tenencia_negativos], ignore_index=True)
        
        
        cuenta_corriente= pesos[pesos["Comitente"].isin(cuenta)].copy()
        cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos en Cta. Corriente en USD al CCL"
        cuenta_corriente= cuenta_corriente[["Nombre_Especie", "Importe"]]
        cuenta_corriente= cuenta_corriente.rename(columns={"Importe":"Valorizada"})
        tenencia_moneda= pd.concat([tenencia_moneda, cuenta_corriente], ignore_index= True)
        
        tenencia_moneda.loc[tenencia_moneda['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
       
        
        if tenencia_moneda.empty:
            monedas= 0
            
        else:
            
            tenencia_moneda = tenencia_moneda.groupby("Nombre_Especie")["Valorizada"].sum()
            monedas= tenencia_moneda.sum()
            
       
        
        tenenciatotal= assets.sum() + monedas #Esto está dolarizado (los euros se suman como están)
        tabla= pd.DataFrame({"Clasificacion": ["Activos", "Moneda", "Tenencia TOTAL"], "Valorizada":[assets.sum(), monedas, tenenciatotal]})
        tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
        tabla.loc[tabla['Clasificacion'] == 'Tenencia TOTAL', :] = tabla.loc[tabla['Clasificacion'] == 'Tenencia TOTAL', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
        
        fig = go.Figure(data=[go.Table(
            columnwidth=[0.8,0.8,0.8],
            header=dict(height = 30,
                        values=['<b>CLASIFICACION</b>','<b>TENENCIA (U$S)</b>'],
                        fill_color='#d7d8d6',
                        line_color='darkslategray',
                        align='center',
                        font=dict(family='Arial', color='black', size=20)),
            cells=dict(values=[tabla.Clasificacion, tabla.Valorizada],
                        fill_color=['#ffffff'],
                        height=30,
                        line_color='darkslategray',
                        align=['left','center','center'],
                        font=dict(family='Arial', color='black', size=18)))
        ])
        h=(len(tabla.index)+2.5)*cm
        fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
        cuenta= '-'.join(map(str, cuenta))
        fig.write_image(f'{dirG}\\tabla total - {cuenta}.png',  scale=1)
        
    tabla_tenencia_total(tenencia_cuenta, cuenta, negativas, pesos, dirG)
    
    tenencia_clase= tenencia_cuenta[tenencia_cuenta['Clasificacion']!='Moneda'].copy()
        
    
    clases= list(tenencia_clase.Clasificacion.unique())
    for clase in clases:
        print(clase)
    #PONER SANGRIA A PARTIR DE ACA DENUEVO
    #clase= "Renta Variable Extranjera"
        if clase in ['Renta Variable Local', 'Renta Variable Extranjera']:
            def tabla_info_financiera(tenencia_clase, cuenta, dirG):
                tenencia_info= tenencia_clase[tenencia_clase['Clasificacion']==clase]
                tenencia_info= tenencia_info.reindex(columns=['Codigo','Valorizada','Clasificacion','RIC','Nombre','Sector', 'PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA', 'Close',
                                                              'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk','52Wk High', '52Wk Low'])
                tenencia_info_ratios= tenencia_info.groupby('Nombre').agg({'Sector': 'first','Close':'first','PE':'first','PE fwd':'first','PBV':'first','PS':'first','Dividend Yield':'first','ROE':'first','ROA':'first', 'Valorizada': 'sum'}).reset_index()
                tenencia_info_ratios['Dividend Yield']= tenencia_info_ratios['Dividend Yield'].astype(float)
                numeric_columns = tenencia_info_ratios.select_dtypes(include=[float, int]).columns.tolist() #Selecciono las columnas que contienen valores numéricos para reemplazar los valores negativos por 0
                tenencia_info_ratios[numeric_columns] = tenencia_info_ratios[numeric_columns].applymap(lambda x: 0 if x < 0 else x) #Corregimos los valores negativos por 0
                total = tenencia_info_ratios['Valorizada'].sum()
                
                df_sectores= tenencia_info_ratios.groupby('Sector').sum()
                df_sectores.reset_index(inplace=True)
                df_sectores= df_sectores.reindex(columns=['Sector','Valorizada'])
                df_sectores=df_sectores.rename(columns={"Valorizada":"Total_Sector"})
                df_new_weights= pd.merge(tenencia_info_ratios,df_sectores, on='Sector')
                df_new_weights['Nueva_Participacion']= df_new_weights['Valorizada']/df_new_weights['Total_Sector']*100 #Estos son los weigths re-calculados por sector, armando como si fuese una cartera por sector.
                df_totales= df_new_weights.copy()
                columns_to_multiply = ['PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA']
                df_totales[columns_to_multiply] = df_totales[columns_to_multiply].multiply(df_totales['Nueva_Participacion']/100, axis=0)
                df_totales= df_totales.groupby('Sector').sum()
                del(df_totales['Total_Sector'])
                df_totales.reset_index(inplace=True)
                df_totales['Participacion']= df_totales['Valorizada']/df_totales['Valorizada'].sum()*100
                
                tenencia_info_ratios['Participacion']= tenencia_info_ratios['Valorizada']/total*100
                df_ratios_ponderados= tenencia_info_ratios.copy() #Realizamos la ponderación de los ratios de cada acción en tenencia, por su participación en cartera.
                columns_to_multiply = ['PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA'] #Multiplicaremos a estos ratios
                df_ratios_ponderados[columns_to_multiply] = df_ratios_ponderados[columns_to_multiply].multiply(df_ratios_ponderados['Participacion']/100, axis=0)
                cartera_total= pd.DataFrame({'Nombre':['Total Cartera'],'Sector':['Total Cartera'],'PE': [df_ratios_ponderados['PE'].sum()],'PE fwd':[df_ratios_ponderados['PE fwd'].sum()],'PBV':[df_ratios_ponderados['PBV'].sum()],
                                             'PS':[df_ratios_ponderados['PS'].sum()],'Dividend Yield': [df_ratios_ponderados['Dividend Yield'].sum()],'ROE':[df_ratios_ponderados['ROE'].sum()],'ROA':[df_ratios_ponderados['ROA'].sum()], 'Valorizada':[df_ratios_ponderados['Valorizada'].sum()], 'Participacion': [df_ratios_ponderados['Participacion'].sum()] })
                
                #df_totales_sector= df_ratios_ponderados.groupby('Sector').sum()
                #df_totales_sector.reset_index(inplace=True)
                #tabla= pd.concat([tenencia_info_ratios,df_totales_sector], ignore_index=True)
                #tabla['Nombre'] = tabla['Nombre'].fillna('Total')
                #mask = tabla['Nombre'] == 'Total'
                #df_totals = tabla.loc[mask].copy()
                # Realizar la multiplicación solo en las filas seleccionadas (Se habían sumado los subtotales para los ratios, necesito saber su promedio ponderado)
                #tabla.loc[mask] = df_totals #Actualizamos los valores corregidos.
                tabla= tenencia_info_ratios.copy()
                columns_format= ['Close','PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA', 'Valorizada']
                tabla[columns_format] = tabla[columns_format].applymap(lambda x: '-' if x == 0 else '{:,.2f}'.format(x))
                tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                tabla= tabla.sort_values(['Sector'])
                #tabla.reset_index(inplace=True)
                #tabla= tabla.sort_values(['Sector','index'])
                #del(tabla['index'])
                tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                
                #Creamos la tabla de las tenencias de cada clase
                fig = go.Figure(data=[go.Table(
                    columnwidth=[4.5, 5, 1.5, 2, 1.5, 2.5, 2],
                    header=dict(height = 30,
                                values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>PE</b>','<b>PE F.</b>','<b>PBV</b>','<b>DIV. YLD</b>','<b>ROE</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Sector, tabla.Nombre, tabla.PE, tabla['PE fwd'], tabla.PBV, tabla['Dividend Yield'], tabla.ROE],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+5.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                cuenta= '-'.join(map(str, cuenta))    
                fig.write_image(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png',  scale=1)
                
                #Hacemos la tabla de los totales
                df_totales= pd.concat([df_totales,cartera_total],join='inner', ignore_index=True)
                columns_format= ['PE','PE fwd', 'PBV', 'Dividend Yield','ROE','Valorizada']
                df_totales[columns_format] = df_totales[columns_format].applymap(lambda x: '-' if x == 0 else '{:,.2f}'.format(x))
                df_totales['Participacion']= df_totales['Participacion'].map('{:.2f}%'.format)
                df_totales.loc[df_totales['Sector'] == 'Total Cartera', :] = df_totales.loc[df_totales['Sector'] == 'Total Cartera', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                
                fig = go.Figure(data=[go.Table(
                    columnwidth=[3.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
                    header=dict(height = 30,
                                values=['<b>SECTOR</b>','<b>PE</b>','<b>PE F.</b>','<b>PBV</b>','<b>DIV. YLD</b>','<b>ROE</b>','<b>PART.</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[df_totales.Sector, df_totales.PE,df_totales['PE fwd'], df_totales.PBV, df_totales['Dividend Yield'],df_totales.ROE, df_totales.Participacion],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=len(df_totales.index)+1.5
                fig.update_layout(width=1000,height=h*1200/34,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                    
                fig.write_image(f'{dirG}\\total info financiera {clase} - {cuenta}.png', scale=1)
            tabla_info_financiera(tenencia_clase, cuenta, dirG)
            
        tenencia_clase_tabla= tenencia_clase[tenencia_clase['Clasificacion']==clase]
        
        def tabla_bonos(tenencia_clase_tabla, tabla_bonos, clase, cuenta, dirG):
            tenencias= tenencia_clase_tabla[['Codigo','Categoria','Nombre_Especie','RIC','Valorizada']]
            tenencias['Nombre_Especie'] = tenencias['Nombre_Especie'].apply(lambda x: ' '.join(x.split()[:4]))
            del(tenencias['RIC'])
            tenencias= tenencias.groupby('Nombre_Especie').agg({'Codigo':'first','Categoria': 'first','Valorizada':'sum'}).reset_index(drop=False)

            tabla= pd.merge(tenencias, tabla_bonos, on='Codigo', how='left')
            tabla= tabla.drop_duplicates(subset=['Codigo'], keep='first')
            tabla['Maturity']= pd.to_datetime(tabla['Maturity']) +timedelta(days=1) #Le agrego un día ya que Reuters trae el vencimiento un día antes de lo que figura en todos lados
            tabla['Maturity']= tabla['Maturity'].dt.strftime('%d %b %Y')
            
            fig = go.Figure(data=[go.Table(
                columnwidth=[6, 6, 3, 1.5, 2.5],
                header=dict(height = 30,
                            values=['<b>NOMBRE</b>','<b>EMISOR</b>','<b>VENCIMIENTO</b>','<b>CUPÓN</b>','<b>MONEDA</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Nombre_Especie, tabla.Issuer, tabla.Maturity, tabla.Coupon, tabla['Principal Currency']],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['center','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+15)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            cuenta= '-'.join(map(str, cuenta))
            fig.write_image(f'{dirG}\\info bonos {clase} - {cuenta}.png', scale=1)
            
        if clase== 'Renta Fija Extranjera':
            tabla_bonos(tenencia_clase_tabla, bonos_exterior, clase, cuenta, dirG)
        elif clase== 'Renta Fija Local':
            tabla_bonos(tenencia_clase_tabla, bonos_locales, clase, cuenta, dirG)
            
        def tabla_performance(tenencia_clase_tabla, clase, cuenta, dirG):
            tabla= tenencia_clase_tabla[['Sector','Nombre','Close','Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk','52Wk High', '52Wk Low']]
            tabla= tabla.groupby('Nombre').agg({'Sector': 'first','Close':'first','Total Return 1Mo':'first','Total Return 3Mo':'first','Total Return 52Wk':'first','Close':'first','52Wk High':'first','52Wk Low':'first'}).reset_index()
            tabla= tabla.sort_values(['Sector'])
            numeric_columns = tabla.select_dtypes(include=[float, int]).columns.tolist()
            tabla[numeric_columns[-2:]] = tabla[numeric_columns[-2:]].applymap(lambda x: '-' if x == 0 else '{:,.2f}'.format(x))
            tabla[numeric_columns[1:-2]] = tabla[numeric_columns[1:-2]].applymap(lambda x: '-' if x == 0 else '{:.2f}%'.format(x))
            tabla['Close'] = tabla['Close'].map('{:,.2f}'.format)
            
            fig = go.Figure(data=[go.Table(
                columnwidth=[7, 7, 3, 2.5, 2.5, 2.5, 2.5, 2.5],
                header=dict(height = 30,
                            values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>CLOSE</b>','<b>RET. 1M</b>','<b>RET. 3M</b>','<b>RET. 52S</b>','<b>MAX 52S</b>','<b>MIN 52S</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Sector, tabla.Nombre, tabla.Close, tabla['Total Return 1Mo'], tabla['Total Return 3Mo'], tabla['Total Return 52Wk'], tabla['52Wk High'], tabla['52Wk Low']],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['center','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+6.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            cuenta= '-'.join(map(str, cuenta))
            fig.write_image(f'{dirG}\\performance {clase} - {cuenta}.png', scale=1)    
            
        def eps_sales_growth(ticker):
            eps,err= ek.get_data(ticker,fields= ['TR.EPSActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY).date','TR.EPSActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY)'])
            sales,err= ek.get_data(ticker, fields=['TR.RevenueActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY).date','TR.RevenueActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY)'])
            eps = eps.drop(columns=['Instrument'])
            eps['Date'] = pd.to_datetime(eps['Date'])
            eps.set_index('Date', inplace=True)
            eps.index = eps.index.tz_convert(None)
            eps.sort_index(ascending=True, inplace=True)
            eps=eps.astype(float)
            eps['EPS Growth']= ((eps - eps.shift(1)) / abs(eps.shift(1)))
            eps= eps.dropna()
            eps_periods= len(eps)
            eps_geom_growth =  np.power(np.prod(1 + eps['EPS Growth']), 1 / len(eps)) - 1
            if np.isnan(eps_geom_growth):
                eps_geom_growth = eps['EPS Growth'].mean()
            sales = sales.drop(columns=['Instrument'])
            sales['Date'] = pd.to_datetime(sales['Date'])
            sales.set_index('Date', inplace=True)
            sales.index = sales.index.tz_convert(None)
            sales.sort_index(ascending=True, inplace=True)
            sales=sales.astype(float)
            sales['Sales Growth']= ((sales - sales.shift(1)) / abs(sales.shift(1))) 
            sales= sales.dropna()
            sales_periods= len(sales)
            sales_geom_growth = np.power(np.prod(1 + sales['Sales Growth']), 1 / len(sales)) - 1
            if np.isnan(sales_geom_growth):
                sales_geom_growth = sales['Sales Growth'].mean()
            return eps_geom_growth, eps_periods, sales_geom_growth, sales_periods
        
        def tabla_growth(tenencia_clase_tabla, clase, cuenta, dirG):
            tabla= tenencia_clase_tabla[['Sector','Nombre','RIC']]
            tabla= tabla.groupby('Nombre').agg({'Sector': 'first','RIC':'first'}).reset_index()
            tabla= tabla.sort_values(['Sector'])
            tickers= tabla.RIC.to_list()
            columns = ['RIC', 'EPS Growth','EPS Periods', 'Sales Growth','Sales Periods']
            growth_df = pd.DataFrame(columns=columns)

            # Recorrer la lista de tickers
            for ticker in tickers:
                # Llamar a la función para obtener los resultados
                eps_growth, eps_periods, sales_growth, sales_periods = eps_sales_growth(ticker)
                
                # Crear un DataFrame temporal con los resultados
                temp_df = pd.DataFrame([[ticker,eps_growth, eps_periods, sales_growth, sales_periods]], columns=columns)
                
                # Concatenar el DataFrame temporal al DataFrame principal
                growth_df = pd.concat([growth_df, temp_df], ignore_index=True)
            
            tabla= pd.merge(tabla,growth_df, on='RIC',how='left')    
            numeric_columns = tabla.select_dtypes(include=[float, int]).columns.tolist()
            tabla[numeric_columns]*=100
            tabla[numeric_columns] = tabla[numeric_columns].applymap(lambda x: '-' if x == 0 else '{:,.2f}%'.format(x))
            
            
            fig = go.Figure(data=[go.Table(
                columnwidth=[4, 4, 2, 2, 2, 2],
                header=dict(height = 30,
                            values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>EPS GROWTH</b>','<b>EPS PERIODS</b>','<b>SALES GROWTH</b>','<b>SALES PERIODS</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Sector, tabla.Nombre, tabla['EPS Growth'],tabla['EPS Periods'],tabla['Sales Growth'],tabla['Sales Periods']],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['center','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+5.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5}) 
            fig.update_layout(width=1000,height=h*cm,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            fig.write_image(f'{dirG}\\growth {clase} - {cuenta}.png', scale=1)
                
        if clase =='Renta Variable Extranjera': #VER COMO HACER CON LOS FONDOS
            tabla_performance(tenencia_clase_tabla, clase, cuenta, dirG)
            if calcular_g == '2':
                tabla_growth(tenencia_clase_tabla, clase, cuenta, dirG)
            df_paises= tenencia_clase_tabla[['Pais','Valorizada']]
            df_paises= df_paises.groupby('Pais').sum()
            df_paises.reset_index(inplace=True)
            df_paises['Participacion']= df_paises['Valorizada']/df_paises['Valorizada'].sum()
            tenencia_clase_tabla= tenencia_clase_tabla[['Sector','Pais','Nombre','Valorizada']] #Estas son las especies que contienen sector, ric, etc (INFO DE REUTERS)
            tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre').agg({'Sector': 'first','Pais':'first', 'Valorizada': 'sum'}).reset_index()
            total = tenencia_clase_tabla['Valorizada'].sum()
            tenencia_clase_tabla['Participacion']= tenencia_clase_tabla['Valorizada']/total*100
            df_sectores= tenencia_clase_tabla.groupby('Sector').sum()
            df_sectores.reset_index(inplace=True)
            tabla= pd.concat([tenencia_clase_tabla,df_sectores], ignore_index=True)
            tabla['Nombre'] = tabla['Nombre'].fillna('Total')
            tabla['Pais']=tabla['Pais'].fillna('')
            
            tabla= tabla.sort_values(['Sector'])
            tabla.reset_index(inplace=True)
            tabla= tabla.sort_values(['Sector','Participacion'])
            del(tabla['index'])
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
            tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            
            #Creamos la tabla de las tenencias de cada clase
            def tabla_tenencias_clase(tabla, cuenta, dirG):
                fig = go.Figure(data=[go.Table(
                    columnwidth=[3.5, 3, 3.5, 1.5, 1.5],
                    header=dict(height = 30,
                                values=['<b>SECTOR</b>','<b>PAIS</b>','<b>NOMBRE</b>','<b>TENENCIA</b>','<b>PART. %</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Sector, tabla.Pais, tabla.Nombre, tabla.Valorizada,tabla.Participacion],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+7.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                cuenta= '-'.join(map(str, cuenta))
                fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',  scale=1)
                     
            tabla_tenencias_clase(tabla, cuenta, dirG)
            #Ahora creamos el grafico de torta doble, uno que separa por sector, y el otro por empresa individual, que es mas detallado
            def grafico_clase(df_sectores, df_paises, tenencia_clase_tabla, cuenta, dirG):
                #Primero voy a agrupar los sectores que tienen tenencia menor a 1.5% en la categoria 'Otro'
                suma_sectores_chicos= df_sectores[df_sectores['Participacion'] < 1.5]['Valorizada'].sum()
                if suma_sectores_chicos !=0:
                    df_sin_sectores_chicos= df_sectores[df_sectores['Participacion'] > 1.5]
                    df_otros= pd.DataFrame({'Sector':['Otro'],'Valorizada': [suma_sectores_chicos], 'Participacion': [suma_sectores_chicos / df_sectores['Valorizada'].sum() * 100]})
                    df_sectores= pd.concat([df_sin_sectores_chicos, df_otros])
                
                parameters = {'axes.labelsize': 20,
                        'axes.titlesize': 20}
                plt.rcParams.update(parameters)
                df_sectores= df_sectores.sort_values('Participacion')
                slices= df_sectores['Participacion']
                small = slices[:len(slices) // 2].to_list()
                large = slices[len(slices) // 2:].to_list()
                            
                reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                r=pd.DataFrame(reordered,columns=['Participacion'])
                df_torta1=pd.merge(r,df_sectores,on='Participacion')
                #fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=[20, 20])
                #ax4.axis('off')  # Desactivar ejes en ax4
                fig = plt.figure(figsize=[20, 20])
                gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1], wspace=0.5)
                
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[1, :])
                
                angle = 180 + float(sum(small[::2])) / sum(df_torta1.Participacion) * 360
                pie_wedge_collection = ax1.pie(df_torta1.Participacion,  labels=df_torta1.Sector, 
                                        labeldistance=1.1, 
                                        startangle=angle,  
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
                for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                    if len(label.get_text()) > 12:
                        label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))
                        
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax1.set_title('Distribución Sectorial', fontweight='bold')
                ax1.add_artist(centre_circle)
                
                #Ahora armamos la torta por empresa individual. Hacemos lo mismo que antes, agrupamos las empresas con poca tenencia en 'Otras empresas'.
                suma_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] < 2]['Valorizada'].sum()
                if suma_empresas_chicas !=0:
                    df_sin_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] > 2]
                    df_otras_empresas= pd.DataFrame({'Nombre':['Otras empresas'],'Sector':['Otro'],'Valorizada': [suma_empresas_chicas], 'Participacion': [suma_empresas_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                    tenencia_clase_tabla= pd.concat([df_sin_empresas_chicas, df_otras_empresas])
                tenencia_clase_tabla= tenencia_clase_tabla.sort_values('Participacion')
                slices= tenencia_clase_tabla['Participacion']
                small = slices[:len(slices) // 2].to_list()
                large = slices[len(slices) // 2:].to_list()
                            
                reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                r=pd.DataFrame(reordered,columns=['Participacion'])
                df_torta2=pd.merge(r,tenencia_clase_tabla,on='Participacion')
                
                angle = 180 + float(sum(small[::2])) / sum(df_torta2.Participacion) * 360
                pie_wedge_collection = ax2.pie(df_torta2.Participacion,  labels=df_torta2.Nombre, 
                                        labeldistance=1.1, 
                                        startangle=angle,  
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
                '''for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                    if len(label.get_text()) > 12:
                        label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))'''
                        
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax2.set_title('Distribución por Empresa', fontweight='bold')
                ax2.add_artist(centre_circle)
                
                
                df_paises= df_paises.sort_values('Participacion')
                slices= df_paises['Participacion']
                small = slices[:len(slices) // 2].to_list()
                large = slices[len(slices) // 2:].to_list()
                            
                reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                r=pd.DataFrame(reordered,columns=['Participacion'])
                df_torta3=pd.merge(r,df_paises,on='Participacion')
                
                angle = 180 + float(sum(small[::2])) / sum(df_torta2.Participacion) * 360
                pie_wedge_collection = ax3.pie(df_torta3.Participacion,  labels=df_torta3.Pais, 
                                        labeldistance=1.1, 
                                        startangle=angle,  
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
                
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax3.set_title('Distribución por Países', fontweight='bold')
                ax3 = plt.gcf()
                fig.gca().add_artist(centre_circle)
                cuenta= '-'.join(map(str, cuenta))
                plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
            grafico_clase(df_sectores,df_paises, tenencia_clase_tabla, cuenta, dirG)
        elif clase== 'Renta Variable Local':
            tabla_performance(tenencia_clase_tabla, clase, cuenta, dirG)
            tenencia_clase_tabla= tenencia_clase_tabla[['Sector','Nombre','Valorizada']] #Estas son las especies que contienen sector, ric, etc (INFO DE REUTERS)
            tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre').agg({'Sector': 'first', 'Valorizada': 'sum'}).reset_index()
            total = tenencia_clase_tabla['Valorizada'].sum()
            tenencia_clase_tabla['Participacion']= tenencia_clase_tabla['Valorizada']/total*100
            df_sectores= tenencia_clase_tabla.groupby('Sector').sum()
            df_sectores.reset_index(inplace=True)
            tabla= pd.concat([tenencia_clase_tabla,df_sectores], ignore_index=True)
            tabla['Nombre'] = tabla['Nombre'].fillna('Total')
            
            tabla= tabla.sort_values(['Sector'])
            tabla.reset_index(inplace=True)
            tabla= tabla.sort_values(['Sector','Participacion'])
            del(tabla['index'])
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
            tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            
            #Creamos la tabla de las tenencias de cada clase
            def tabla_tenencias_clase(tabla, cuenta, dirG):
                fig = go.Figure(data=[go.Table(
                    columnwidth=[2, 2.5, 1.5, 1.5],
                    header=dict(height = 30,
                                values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Sector, tabla.Nombre, tabla.Valorizada,tabla.Participacion],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+7.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                cuenta= '-'.join(map(str, cuenta))
                fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',  scale=1)
                     
            tabla_tenencias_clase(tabla, cuenta, dirG)
            #Ahora creamos el grafico de torta doble, uno que separa por sector, y el otro por empresa individual, que es mas detallado
            def grafico_clase(df_sectores, tenencia_clase_tabla, cuenta, dirG):
                #Primero voy a agrupar los sectores que tienen tenencia menor a 1.5% en la categoria 'Otro'
                suma_sectores_chicos= df_sectores[df_sectores['Participacion'] < 1.5]['Valorizada'].sum()
                if suma_sectores_chicos !=0:
                    df_sin_sectores_chicos= df_sectores[df_sectores['Participacion'] > 1.5]
                    df_otros= pd.DataFrame({'Sector':['Otro'],'Valorizada': [suma_sectores_chicos], 'Participacion': [suma_sectores_chicos / df_sectores['Valorizada'].sum() * 100]})
                    df_sectores= pd.concat([df_sin_sectores_chicos, df_otros])
                
                parameters = {'axes.labelsize': 20,
                        'axes.titlesize': 20}
                plt.rcParams.update(parameters)
                df_sectores= df_sectores.sort_values('Participacion')
                slices= df_sectores['Participacion']
                small = slices[:len(slices) // 2].to_list()
                large = slices[len(slices) // 2:].to_list()
                            
                reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                r=pd.DataFrame(reordered,columns=['Participacion'])
                df_torta1=pd.merge(r,df_sectores,on='Participacion')
                #fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=[20, 20])
                #ax4.axis('off')  # Desactivar ejes en ax4
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[20, 10])
                plt.subplots_adjust(wspace=0.5)
                angle = 180 + float(sum(small[::2])) / sum(df_torta1.Participacion) * 360
                pie_wedge_collection = ax1.pie(df_torta1.Participacion,  labels=df_torta1.Sector, 
                                        labeldistance=1.1, 
                                        startangle=angle,  
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
                for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                    if len(label.get_text()) > 12:
                        label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))
                        
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax1.set_title('Distribución Sectorial', fontweight='bold')
                ax1.add_artist(centre_circle)
                
                #Ahora armamos la torta por empresa individual. Hacemos lo mismo que antes, agrupamos las empresas con poca tenencia en 'Otras empresas'.
                suma_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] < 2]['Valorizada'].sum()
                if suma_empresas_chicas !=0:
                    df_sin_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] > 2]
                    df_otras_empresas= pd.DataFrame({'Nombre':['Otras empresas'],'Sector':['Otro'],'Valorizada': [suma_empresas_chicas], 'Participacion': [suma_empresas_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                    tenencia_clase_tabla= pd.concat([df_sin_empresas_chicas, df_otras_empresas])
                tenencia_clase_tabla= tenencia_clase_tabla.sort_values('Participacion')
                slices= tenencia_clase_tabla['Participacion']
                small = slices[:len(slices) // 2].to_list()
                large = slices[len(slices) // 2:].to_list()
                            
                reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                r=pd.DataFrame(reordered,columns=['Participacion'])
                df_torta2=pd.merge(r,tenencia_clase_tabla,on='Participacion')
                
                angle = 180 + float(sum(small[::2])) / sum(df_torta2.Participacion) * 360
                pie_wedge_collection = ax2.pie(df_torta2.Participacion,  labels=df_torta2.Nombre, 
                                        labeldistance=1.1, 
                                        startangle=angle,  
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
                '''for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                    if len(label.get_text()) > 12:
                        label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))'''
                        
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax2.set_title('Distribución por Empresa', fontweight='bold')
                ax2.add_artist(centre_circle)
                cuenta= '-'.join(map(str, cuenta))
                plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
            grafico_clase(df_sectores, tenencia_clase_tabla, cuenta, dirG)
        
        elif clase== 'ETFs':
            tenencia_clase_tabla= tenencia_clase_tabla[['Nombre','GEO','FundType','Valorizada']]
            tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre').agg({'GEO':'first','FundType': 'first','Valorizada':'sum'}).reset_index(drop=False)
            total = tenencia_clase_tabla['Valorizada'].sum()
            '''                
            tenencia_clase_tabla['Nombre'] = tenencia_clase_tabla['Nombre'].apply(lambda x: ' '.join(x.split()[:5]))

            tabla['Participacion']= tabla['Valorizada']/total*100
            tabla= tabla.sort_values(['FundType','Participacion'])
            tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            '''
            df_sectores= tenencia_clase_tabla.groupby('FundType').sum()
            df_sectores.reset_index(inplace=True)
            tabla= pd.concat([tenencia_clase_tabla,df_sectores], ignore_index=True)
            tabla['Nombre'] = tabla['Nombre'].fillna('Total')
            tabla['GEO']=tabla['GEO'].fillna('')
            tabla['FundType']=tabla['FundType'].fillna('')
            
            tabla= tabla.sort_values(['FundType'])
            tabla.reset_index(inplace=True)
            tabla['Participacion']= tabla['Valorizada']/total*100
            tabla= tabla.sort_values(['FundType','Participacion'])
            del(tabla['index'])
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
            tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            
            def tabla_tenencias_clase(tabla, cuenta, dirG):
                fig = go.Figure(data=[go.Table(
                    columnwidth=[5,3.5,1.5,3,1.5],
                    header=dict(height = 30,
                                values=['<b>NOMBRE</b>','<b>SECTOR GEO.</b>','<b>TIPO</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Nombre,tabla.GEO, tabla.FundType, tabla.Valorizada, tabla.Participacion],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+7.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                cuenta= '-'.join(map(str, cuenta))    
                fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',scale=1)
                     
            tabla_tenencias_clase(tabla, cuenta, dirG)
            
            def grafico_clase(tenencia_clase_tabla, cuenta, dirG):
                df_sectores= tenencia_clase_tabla.groupby('GEO').sum()
                df_sectores.reset_index(inplace=True)
                df_sectores['Participacion']= df_sectores['Valorizada']/df_sectores['Valorizada'].sum() *100
                
                df_fundtype= tenencia_clase_tabla.groupby('FundType').sum()
                df_fundtype.reset_index(inplace=True)
                df_fundtype['Participacion']= df_fundtype['Valorizada']/df_fundtype['Valorizada'].sum() *100
                
                df_torta= tenencia_clase_tabla[['Nombre', 'Valorizada']].copy()
                df_torta['Participacion']= df_torta['Valorizada']/df_torta['Valorizada'].sum() *100
                suma_especies_chicas= df_torta[df_torta['Participacion'] < 1.5]['Valorizada'].sum()
                if suma_especies_chicas !=0:
                    df_sin_especies_chicas= df_torta[df_torta['Participacion'] > 1.5]
                    df_otras_especies= pd.DataFrame({'Nombre':['Otras especies'],'Valorizada': [suma_especies_chicas], 'Participacion': [suma_especies_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                    df_torta= pd.concat([df_sin_especies_chicas, df_otras_especies])
                df_torta= df_torta.sort_values('Participacion')
                parameters = {'axes.labelsize': 20,
                        'axes.titlesize': 20}
                plt.rcParams.update(parameters)
                
                fig = plt.figure(figsize=[20, 20])
                gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1], wspace=0.5)
                
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[1, :])
                
                pie_wedge_collection1 = ax1.pie(df_torta.Participacion,
                                        labels=df_torta.Nombre, 
                                        labeldistance=1.1,   
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection1[0]:
                    pie_wedge.set_edgecolor('white')
                for label in pie_wedge_collection1[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                    if len(label.get_text()) >20:
                        label.set_text('\n'.join(textwrap.wrap(label.get_text(), 20)))
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax1.add_artist(centre_circle)
                ax1.set_title(f'Distribución de la Cartera de {clase}', fontweight='bold')
                
                pie_wedge_collection = ax2.pie(df_sectores.Participacion,  labels=df_sectores.GEO, 
                                        labeldistance=1.1, 
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
                for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                    if len(label.get_text()) > 12:
                        label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax2.add_artist(centre_circle)
                ax2.set_title('Distribución por Sector Geográfico', fontweight='bold')
                
                pie_wedge_collection2 = ax3.pie(df_fundtype.Participacion,  labels=df_fundtype.FundType, 
                                        labeldistance=1.1, 
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection2[0]:
                    pie_wedge.set_edgecolor('white')
                
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax3.add_artist(centre_circle)
                ax3.set_title('Distribución por Tipo de Fondo', fontweight='bold')
                
                cuenta= '-'.join(map(str, cuenta))
                plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
                plt.clf()
            grafico_clase(tenencia_clase_tabla, cuenta, dirG)
        else: #Categorias que no son acciones, ya sea bonos, fondos, opciones, etc.
            tenencia_clase_tabla= tenencia_clase_tabla[['Nombre_Especie','Valorizada']]
            tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre_Especie').agg({'Valorizada': 'sum'}).reset_index()
            total = tenencia_clase_tabla['Valorizada'].sum()
            total_row = pd.DataFrame({'Nombre_Especie': ['Total'], 'Valorizada': [total]})
            tabla = pd.concat([tenencia_clase_tabla, total_row], ignore_index=True)
            tabla['Participacion']= tabla['Valorizada']/total*100
            tabla= tabla.sort_values(['Participacion'])
            tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla.loc[tabla['Nombre_Especie'] == 'Total', :] = tabla.loc[tabla['Nombre_Especie'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            
            def tabla_tenencias_clase(tabla, cuenta, dirG):
                fig = go.Figure(data=[go.Table(
                    columnwidth=[2.5, 1.2, 1],
                    header=dict(height = 30,
                                values=['<b>NOMBRE</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Nombre_Especie, tabla.Valorizada, tabla.Participacion],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+7.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                cuenta= '-'.join(map(str, cuenta))    
                fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',scale=1)
                     
            tabla_tenencias_clase(tabla, cuenta, dirG)
            
            def grafico_clase(tenencia_clase_tabla, cuenta, dirG):
                df_torta= tenencia_clase_tabla
                df_torta['Participacion']= df_torta['Valorizada']/df_torta['Valorizada'].sum() *100
                suma_especies_chicas= df_torta[df_torta['Participacion'] < 1.5]['Valorizada'].sum()
                if suma_especies_chicas !=0:
                    df_sin_especies_chicas= df_torta[df_torta['Participacion'] > 1.5]
                    df_otras_especies= pd.DataFrame({'Nombre_Especie':['Otras especies'],'Valorizada': [suma_especies_chicas], 'Participacion': [suma_especies_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                    df_torta= pd.concat([df_sin_especies_chicas, df_otras_especies])
                df_torta= df_torta.sort_values('Participacion')
                parameters = {'axes.labelsize': 20,
                        'axes.titlesize': 20}
                plt.rcParams.update(parameters)
                fig = plt.figure(figsize=[10, 10])
                ax = fig.add_subplot(111)
                
                pie_wedge_collection = ax.pie(df_torta.Participacion,
                                        labels=df_torta.Nombre_Especie, 
                                        labeldistance=1.1,   
                                        autopct='%1.1f%%',
                                        pctdistance=0.8,
                                        textprops={'fontsize': 16})
                for pie_wedge in pie_wedge_collection[0]:
                    pie_wedge.set_edgecolor('white')
        
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                fig = plt.gcf()
                fig.gca().add_artist(centre_circle)
                ax.set_title(f'Distribución de la Cartera de {clase}', fontweight='bold')
                cuenta= '-'.join(map(str, cuenta))
                plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
                plt.clf()
            grafico_clase(tenencia_clase_tabla, cuenta, dirG)
    #Comenzamos a hacer el PDF
    while True:
        reporte_largo_corto= int(input("Presione 1 si quiere el reporte resumido, 2 si quiere el informe detallado: "))
        if reporte_largo_corto==1:
            short= True
            break
        if reporte_largo_corto==2:
            short=False
            break
        else:
            print("No ha ingresado un número correcto, intente denuevo. ")
        
    def hacer_pdf(cuenta, clases, short, dir, dirG):
        #for file in os.listdir(): #Esto borrará los archivos viejos, para que cada vez que se ejecute el programa aparezcan en carpeta los gráficos que se quieren descargar
            #if file.endswith('.pdf'):
                #try:
                    #os.remove(file)
                #except Exception as e:
                   # print(f'Error deleting {file}: {e}')
        cuenta= '-'.join(map(str, cuenta))    
        pdf=canvas.Canvas(f'{dir}\\Reporte - {cuenta}.pdf',pagesize=A4)
        w, h = A4
        
        
        '''#Imagen
        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
        #Titulo
        pdf.setTitle('Reporte comitente')
        pdf.setFillColor('Black')
        pdf.setFont('Helvetica-Bold',24)
        pdf.drawString(1*cm,27.4*cm,f'Resumen de Tenencia {cuenta}')
        #Linea horizontal
        pdf.line(1*cm,27*cm,A4[0] -1*cm,27*cm)
        #Fecha abajo
        today = time.strftime("%d/%m/%Y")
        pdf.setFont('Helvetica',14)
        pdf.setFillColor("Gray")
        pdf.drawString(1*cm,26.4*cm,f'{today}')
        
        
        
        filepath= f'{dirG}\\tabla cuenta corriente - {cuenta}.png'
        corriente= PIL.Image.open(filepath)
        corrienteh= corriente.height/(1*cm)
        corrientew= corriente.width/(1*cm)
        corrienteasp= corrientew/corrienteh
        corrienteh= 19/corrienteasp
        
        filepath= f'{dirG}\\tabla tenencias negativas - {cuenta}.png'
        negativa= PIL.Image.open(filepath)
        negativah= negativa.height/(1*cm)
        negativaw= negativa.width/(1*cm)
        negativaasp= negativaw/negativah
        negativah= 19/negativaasp
        
        
        pdf.setFillColor("Darkgreen")
        pdf.setFont('Helvetica',18)
        pdf.drawString(1*cm,18*cm,'Tenencia Cta. Corriente')
        pdf.drawInlineImage(f'{dirG}\\tabla cuenta corriente - {cuenta}.png', 1*cm, 17.5*cm-corrienteh*cm, width=19*cm, height=corrienteh*cm, preserveAspectRatio=True)
        
        pdf.setFillColor("Darkgreen")
        pdf.setFont('Helvetica',18)
        pdf.drawString(1*cm,12*cm,'Tenencias Negativas')
        pdf.drawInlineImage(f'{dirG}\\tabla tenencias negativas - {cuenta}.png', 1*cm, 11.5*cm-negativah*cm, width=19*cm, height=negativah*cm, preserveAspectRatio=True)
        
        pdf.showPage()
        '''
        pdf.setTitle('Reporte comitente')
        pdf.setFillColor('Black')
        pdf.setFont('Helvetica-Bold',20)
        pdf.drawString(1*cm,27.2*cm,f'Tenencia Total {cuenta}')
        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
        today = time.strftime("%d/%m/%Y")
        pdf.setFont('Helvetica',14)
        pdf.setFillColor("Gray")
        pdf.drawString(14*cm,27.2*cm,f'TC: {CCL:.2f}       {today}')
        
        filepath = f'{dirG}\\tabla activos - {cuenta}.png'
        primera = PIL.Image.open(filepath)
        primerah= primera.height/(1*cm)
        primeraw= primera.width/(1*cm)
        primeraasp= primeraw/primerah
        primerah= 19/primeraasp
        
        filepath = f'{dirG}\\tabla moneda - {cuenta}.png'
        segunda = PIL.Image.open(filepath)
        segundah=segunda.height/(1*cm)
        segundaw= segunda.width/(1*cm)
        segundaasp= segundaw/segundah
        segundah= 19/segundaasp
        
        filepath = f'{dirG}\\torta General {cuenta}.png'
        tercera= PIL.Image.open(filepath)
        tercerah= tercera.height/(1*cm)
        terceraw= tercera.width/(1*cm)
        terceraasp= terceraw/tercerah
        tercerah= 19/terceraasp
        
        filepath= f'{dirG}\\tabla total - {cuenta}.png'
        totales= PIL.Image.open(filepath)
        totalesh= totales.height/(1*cm)
        totalesw= totales.width/(1*cm)
        totalesasp= totalesw/totalesh
        totalesh= 19/totalesasp
        '''filepath= f'{dirG}\\barra moneda - {cuenta}.png'
        cuarta= PIL.Image.open(filepath)
        cuartah= cuarta.height/(1*cm)
        cuartaw= cuarta.width/(1*cm)
        cuartaasp= cuartaw/cuartah
        cuartah= 19/cuartaasp'''
        pdf.setFillColor("Darkgreen")
        pdf.setFont('Helvetica',18)
        pdf.drawString(1*cm,26*cm,'Tenencia Total')
        pdf.drawInlineImage(f'{dirG}\\tabla total - {cuenta}.png', 1*cm, 25.5*cm-totalesh*cm, width=19*cm, height=totalesh*cm, preserveAspectRatio=True)
        
        #Escribimos titulos e insertamos graficos
        pdf.setFillColor("Darkgreen")
        pdf.setFont('Helvetica',18)
        pdf.drawString(1*cm,24*cm-totalesh*cm,'Resumen de ACTIVOS')
        pdf.drawInlineImage(f'{dirG}\\tabla activos - {cuenta}.png', 1*cm, 23.5*cm-totalesh*cm-primerah*cm, width=19*cm, height=primerah*cm, preserveAspectRatio=True)
        pdf.drawInlineImage(f'{dirG}\\torta General {cuenta}.png', 1*cm, 23*cm-totalesh*cm-primerah*cm-tercerah*cm, width=19*cm, height= tercerah*cm, preserveAspectRatio=True)
        pdf.drawString(1*cm,22.5*cm-totalesh*cm-primerah*cm-tercerah*cm,'Resumen de MONEDA')
        pdf.drawInlineImage(f'{dirG}\\tabla moneda - {cuenta}.png', 1*cm, 22*cm-totalesh*cm-primerah*cm-tercerah*cm-segundah*cm, width=19*cm, height= segundah*cm, preserveAspectRatio=True)
        
        #pdf.drawInlineImage(f'{dirG}\\barra moneda - {cuenta}.png', (10.5-9/2)*cm, (-3.5*cm), width=9*cm, height= cuartah*cm,preserveAspectRatio=True)
        pdf.showPage()
        
        #A partir de aqui comenzamos con el detalle de cada especie.
        for clase in clases:
            pdf.setTitle('Reporte comitente')
            pdf.setFillColor('Black')
            pdf.setFont('Helvetica-Bold',20)
            pdf.drawString(1*cm,27.2*cm,f'Tenencia Total - {clase}')
            pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
            pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
            
            filepath = f'{dirG}\\tabla tenencia {clase} - {cuenta}.png'
            compo = PIL.Image.open(filepath)
            compoh= compo.height/(1*cm)
            compow= compo.width/(1*cm)
            compoasp= compow/compoh
            compoh= 19/compoasp #Vamos a fijar el ancho en 19 cm, asi ocupa el ancho total de la pagina dejando un poco de margen.
            #print(f'height compo {cuenta}-{clase}= {compoh}')
            #print(f'width compo {cuenta}-{clase}= {compow}')
            
            filepath = f'{dirG}\\torta {clase}-{cuenta}.png'
            torta = PIL.Image.open(filepath)
            tortah= torta.height/(1*cm)
            tortaw= torta.width/(1*cm)
            tortaasp= tortaw/tortah
            tortah= 19/tortaasp
            #print(f'height torta {cuenta}-{clase}= {tortah}')
            #print(f'width torta {cuenta}-{clase}= {tortaw}')
            
            total_height = compoh + tortah + 3.7 #esto es todo lo que entra en la hoja A4, seria la tabla mas los graficos mas el espacio hasta arriba
            w, h = A4
            #print(f'total height {cuenta}-{clase}= {total_height}')
            #print(f'height A4= {h/(1*cm)}')
            if total_height > h/(1*cm): #Aca tengo dos casos, uno es que entre bien la tabla en la hoja, y otro donde sea tan grande que tenga que ajustar la altura para que entre en la hoja (PROVISORIO)
                if compoh> 25.5:
                    compow= compoasp*(25.5)
                    pdf.drawImage(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png', (10.5-compow/2)*cm, 26*cm-25.5*cm, height=25.5*cm, width=compow*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                else:
                    pdf.drawImage(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png', 1*cm, 26*cm-1*compoh*cm, height=1*compoh*cm, preserveAspectRatio=True, mask='auto',anchor='nw')
                
                #Si es muy grande la tabla tal que ocupa toda la pagina, pego los graficos de torta en hoja nueva (PROVISORIO HASTA HACER QUE SE CORTE EN DOS LA FOTO, EN LA FUNCION QUE CREA LA IMAGEN DE LA TABLA)
                pdf.showPage()
                
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm, f'Tenencia Total - {clase}')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                pdf.drawInlineImage(f'{dirG}\\torta {clase}-{cuenta}.png',1*cm, 25*cm-tortah*cm, width=19*cm,height= tortah*cm,preserveAspectRatio=True)
                
                pdf.showPage()
            else:
                tortah= 19/tortaasp
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm, f'Tenencia Total - {clase}')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                pdf.drawInlineImage(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png', 1*cm, 26*cm-compoh*cm, width=19*cm, height=compoh*cm, preserveAspectRatio=True)
                pdf.drawImage(f'{dirG}\\torta {clase}-{cuenta}.png',(10.5-19/2)*cm, 24*cm-compoh*cm-1*tortah*cm, width=19*cm, height=tortah*cm, preserveAspectRatio=True)
                
                pdf.showPage()
            if short== True:
                pass
            
            else:
                if clase in ['Renta Variable Local', 'Renta Variable Extranjera']: #Insertamos en una nueva página la información financiera de las especies de renta variable
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, f'Información Financiera - {clase}')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    filepath = f'{dirG}\\tabla info financiera {clase}- {cuenta}.png'
                    compo = PIL.Image.open(filepath)
                    compoh= compo.height/(1*cm)
                    compow= compo.width/(1*cm)
                    compoasp= compow/compoh
                    compoh= 19/compoasp
                    
                    filepath = f'{dirG}\\total info financiera {clase} - {cuenta}.png'
                    general = PIL.Image.open(filepath)
                    generalh= general.height/(1*cm)
                    generalw= general.width/(1*cm)
                    generalasp= generalw/generalh
                    generalh= 19/generalasp
                    
                    totalh= compoh + generalh
                    if totalh > 25.5: #Aca tengo dos casos, uno es que entre bien la tabla en la hoja, y otro donde sea tan grande que tenga que ajustar la altura para que entre en la hoja (PROVISORIO)
                        if compoh> 25.5:
                            compow= compoasp*(25.5)
                            pdf.drawImage(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png', (10.5-compow/2)*cm, 26*cm-25.5*cm, height=25.5*cm, width=compow*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        else:
                            pdf.drawImage(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png', 1*cm, 26*cm-1*compoh*cm, height=1*compoh*cm, preserveAspectRatio=True, mask='auto',anchor='nw')
                        pdf.showPage()
                        #Insertamos en una nueva página la tabla de información financiera total si es que no entran ambas en una misma pág.
                        pdf.setTitle('Reporte comitente')
                        pdf.setFillColor('Black')
                        pdf.setFont('Helvetica-Bold',20)
                        pdf.drawString(1*cm,27.2*cm, f'Información Financiera - {clase}')
                        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                        pdf.drawImage(f'{dirG}\\total info financiera {clase} - {cuenta}.png', 1*cm, 26*cm-1*generalh*cm, height=generalh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        pdf.showPage()
                    else:
                        pdf.drawImage(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png', 1*cm, 26*cm-1*compoh*cm, height=compoh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        pdf.drawImage(f'{dirG}\\total info financiera {clase} - {cuenta}.png', 1*cm, 25.5*cm-1*compoh*cm-1*generalh*cm, height=generalh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')                
                        pdf.showPage()
                        
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, f'Performance - {clase}')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    filepath= f'{dirG}\\performance {clase} - {cuenta}.png'
                    performance= PIL.Image.open(filepath)
                    performanceh= performance.height/(1*cm)
                    #print(f'la altura de la tabla performance {clase} es {performanceh}')
                    performancew= performance.width/(1*cm)
                    performanceasp= performancew/performanceh
                    if performanceh > 53:
                        performancew= performanceasp*26
                        pdf.drawImage(f'{dirG}\\performance {clase} - {cuenta}.png', (10.5-performancew/2)*cm, 0*cm, height=26*cm, width=performancew*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                    else:
                        performanceh= 19/performanceasp
                        pdf.drawImage(f'{dirG}\\performance {clase} - {cuenta}.png', 1*cm, 26*cm-1*performanceh*cm, height=performanceh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                    if pprom=='2': 
                        #Rendimientos, cómo venimos con nuestras inversiones? Arriba abajo? En qué %?
                        pdf.setTitle('Reporte comitente')
                        pdf.setFillColor('Black')
                        pdf.setFont('Helvetica-Bold',20)
                        pdf.drawString(1*cm,27.2*cm, f'Rendimientos - {clase}')
                        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                        
                        filepath= f'{dirG}\\tabla rendimientos {clase} - {cuenta}.png'
                        rendimientos= PIL.Image.open(filepath)
                        rendimientosh= rendimientos.height/(1*cm)
                        #print(f'la altura de la tabla performance {clase} es {performanceh}')
                        rendimientosw= rendimientos.width/(1*cm)
                        rendimientosasp= rendimientosw/rendimientosh
                        if rendimientosh > 53:
                            rendimientosw= rendimientosasp*26
                            pdf.drawImage(f'{dirG}\\tabla rendimientos {clase} - {cuenta}.png', (10.5-rendimientosw/2)*cm, 0*cm, height=26*cm, width=rendimientosw*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                        else:
                            rendimientosh= 19/rendimientosasp
                            pdf.drawImage(f'{dirG}\\tabla rendimientos {clase} - {cuenta}.png', 1*cm, 26*cm-1*rendimientosh*cm, height=rendimientosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        pdf.showPage()
                    if clase == 'Renta Variable Extranjera' and calcular_g=='2':    
                        pdf.setTitle('Reporte comitente')
                        pdf.setFillColor('Black')
                        pdf.setFont('Helvetica-Bold',20)
                        pdf.drawString(1*cm,27.2*cm, f'Crecimiento - {clase}')
                        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                        
                        filepath= (f'{dirG}\\growth {clase} - {cuenta}.png')
                        crecimiento= PIL.Image.open(filepath)
                        crecimientoh= crecimiento.height/(1*cm)
                        crecimientow= crecimiento.width/(1*cm)
                        crecimientoasp= crecimientow/crecimientoh
                        pdf.drawImage(f'{dirG}\\growth {clase} - {cuenta}.png', 1*cm, 26*cm-1*crecimientoh*cm, height=crecimientoh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        pdf.showPage()
        #Insertamos la información de los bonos que tiene cada cliente, si es que tiene bonos en cuenta.
        if short== True:
            pdf.save()
        
        else:     
            if all(cls in clases for cls in ['Renta Fija Local', 'Renta Fija Extranjera']):
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                
                pdf.setFillColor("Darkgreen")
                pdf.setFont('Helvetica',18)
                pdf.drawString(1*cm,26*cm,'Resumen de Renta Fija Local')
                filepath= f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png'
                locales= PIL.Image.open(filepath)
                localesh= locales.height/(1*cm)
                localesw= locales.width/(1*cm)
                localesasp= localesw/localesh
                localesh= 19/localesasp
                pdf.drawImage(f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png', 1*cm, 25.5*cm-1*localesh*cm, height=localesh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                pdf.showPage()
                
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                
                pdf.setFillColor("Darkgreen")
                pdf.setFont('Helvetica',18)
                pdf.drawString(1*cm,26*cm,'Resumen de Renta Fija Extranjera')
                filepath= f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png'
                extranjeros= PIL.Image.open(filepath)
                extranjerosh= extranjeros.height/(1*cm)
                extranjerosw= extranjeros.width/(1*cm)
                extranjerosasp= extranjerosw/extranjerosh
                extranjerosh= 19/extranjerosasp
                pdf.drawImage(f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png', 1*cm, 25.5*cm-1*extranjerosh*cm, height=extranjerosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                pdf.showPage()
                
                
            elif 'Renta Fija Local' in clases:
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                
                pdf.setFillColor("Darkgreen")
                pdf.setFont('Helvetica',18)
                pdf.drawString(1*cm,26*cm,'Resumen de Renta Fija Local')
                filepath= f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png'
                locales= PIL.Image.open(filepath)
                localesh= locales.height/(1*cm)
                localesw= locales.width/(1*cm)
                localesasp= localesw/localesh
                localesh= 19/localesasp
                pdf.drawImage(f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png', 1*cm, 25.5*cm-1*localesh*cm, height=localesh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                pdf.showPage()
                if pprom=='2': 
                    #Rendimientos, cómo venimos con nuestras inversiones? Arriba abajo? En qué %?
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, f'Rendimientos - Renta Fija Local')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    filepath= f'{dirG}\\tabla rendimientos Renta Fija Local - {cuenta}.png'
                    rendimientos= PIL.Image.open(filepath)
                    rendimientosh= rendimientos.height/(1*cm)
                    #print(f'la altura de la tabla performance {clase} es {performanceh}')
                    rendimientosw= rendimientos.width/(1*cm)
                    rendimientosasp= rendimientosw/rendimientosh
                    if rendimientosh > 53:
                        rendimientosw= rendimientosasp*26
                        pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Local - {cuenta}.png', (10.5-rendimientosw/2)*cm, 0*cm, height=26*cm, width=rendimientosw*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                    else:
                        rendimientosh= 19/rendimientosasp
                        pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Local - {cuenta}.png', 1*cm, 26*cm-1*rendimientosh*cm, height=rendimientosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                
            elif 'Renta Fija Extranjera' in clases:
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                
                pdf.drawString(1*cm,25.5*cm,'Resumen de Renta Fija Extranjera')
                filepath= f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png'
                extranjeros= PIL.Image.open(filepath)
                extranjerosh= extranjeros.height/(1*cm)
                extranjerosw= extranjeros.width/(1*cm)
                extranjerosasp= extranjerosw/extranjerosh
                extranjerosh= 19/extranjerosasp
                pdf.drawImage(f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png', 1*cm, 25*cm-1*extranjerosh*cm, height=extranjerosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                pdf.showPage()
                if pprom=='2': 
                    #Rendimientos, cómo venimos con nuestras inversiones? Arriba abajo? En qué %?
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, f'Rendimientos - Renta Fija Extranjera')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    filepath= f'{dirG}\\tabla rendimientos Renta Fija Extranjera - {cuenta}.png'
                    rendimientos= PIL.Image.open(filepath)
                    rendimientosh= rendimientos.height/(1*cm)
                    #print(f'la altura de la tabla performance {clase} es {performanceh}')
                    rendimientosw= rendimientos.width/(1*cm)
                    rendimientosasp= rendimientosw/rendimientosh
                    if rendimientosh > 53:
                        rendimientosw= rendimientosasp*26
                        pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Extranjera - {cuenta}.png', (10.5-rendimientosw/2)*cm, 0*cm, height=26*cm, width=rendimientosw*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                    else:
                        rendimientosh= 19/rendimientosasp
                        pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Extranjera - {cuenta}.png', 1*cm, 26*cm-1*rendimientosh*cm, height=rendimientosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                
            pdf.save()
    hacer_pdf(cuenta,clases, short ,dir, dirG)
    
    def mandar_mails(cuenta, dir, mail):
        cuenta= '-'.join(map(str, cuenta))
        email = 'ldtbrokers@gmail.com'
        password = 'bzcd zmdw bgib nixm'
        send_to_email = mail
        subject = f'Reporte Tenencia del Comitente {cuenta}'
        message = 'Estimado cliente, en el archivo adjunto encontrará el reporte de sus tenencias valorizadas al día de la fecha'
        file_location = f'{dir}\\Reporte - {cuenta}.pdf'
        
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = send_to_email
        msg['Subject'] = subject
    
        msg.attach(MIMEText(message, 'plain'))
    
        # Setup the attachment
        filename = os.path.basename(file_location)
        attachment = open(file_location, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
        # Attach the attachment to the MIMEMultipart object
        msg.attach(part)
    
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        text = msg.as_string()
        server.sendmail(email, send_to_email, text)
        server.quit()
    #mandar_mails(cuenta, dir, mail)
    cuenta= '-'.join(map(str, cuenta))
    os.startfile(f'{dir}\\Reporte - {cuenta}.pdf')
else:       
    for cuenta in cuentas:#(PONER SANGRIA A PARTIR DE ACA)
        tenencia_cuenta= tenencia_reportes[tenencia_reportes["Comitente"]==cuenta]
        tenencia_cuenta= tenencia_cuenta.sort_values('Clasificacion')   
        tenencia_cuenta.reset_index(drop=True, inplace=True)
        tenencia_cuenta=tenencia_cuenta.replace('Stale', 0)
        
        
                    
        if pprom=='2':
            def contadoconliqui(method='YF'): #Descarga y crea serie historica para CCL
                if method == 'YF':
                    tickers = ["GGAL","GGAL.BA"]
                    GGAL = yf.download(tickers, interval='1d', ignore_tz=True)['Adj Close']
                    ccl =GGAL["GGAL.BA"]/GGAL["GGAL"]*10
                    ccl= ccl.fillna(method='ffill')
                    ccl= ccl.dropna()
                    ccl= ccl.reset_index(drop=False)
                    ccl.columns= ['FechaOp','CCL']
                else:
                    ccl= ek.get_timeseries('ARSMEP=', start_date='2012-01-01')['CLOSE'].astype(float)
                    ccl= ccl.fillna(method='ffill')
                    ccl.dropna(inplace=True)
                    ccl=ccl.reset_index(drop=False)
                    ccl.columns= ['FechaOp','CCL']
                return ccl
    
            def corregir_precios(ht, method='YF'):
                rics = ht.loc[ht['Categoria'] == 'Exterior', 'RIC'].unique().tolist()
                if method == 'YF':
                    precios = yf.download(rics, period="max")['Adj Close']
                else:
                    precios = ek.get_timeseries(rics, start_date = datetime.now() + timedelta(-365*4))
                    precios = precios.swaplevel(i='Security', j='Field', axis=1)
                    precios= precios['CLOSE'].fillna(method='ffill')
                # Función para obtener el precio ajustado al cierre para una fila dada
                def obtener_precio_ajustado(row):
                    if row['Categoria'] != 'Exterior':
                        return row['Precio']  # Si no es de la categoría 'Exterior', retornar el precio original
                    fecha = row['FechaOp']
                    ric = row['RIC']
                    # Intentar obtener el precio ajustado para la fecha y el RIC; si falla, usar el precio original
                    try:
                        return precios.loc[fecha, ric]
                    except KeyError:
                        return row['Precio']
                
                # Aplicar la función a cada fila del DataFrame original para actualizar los precios
                ht['Precio'] = ht.apply(obtener_precio_ajustado, axis=1)
    
            def rendimientos(tenencia_cuenta, cuenta, categorias):
                ccl= contadoconliqui(method='EK')
                tenencias= tenencia_cuenta[tenencia_cuenta["Clasificacion"] != "Moneda"]
                tenencias= tenencias[tenencias["Clasificacion"] != "Opciones"]
                cuenta= [cuenta]
                cuenta_str = [str(num).zfill(6) for num in cuenta]
                cuenta_str= '-'.join(map(str, cuenta_str))
                dirpprom=r"C:\Users\ldt\Documents\Agustin Ehrman\Precio Promedio"
                ht= pd.read_excel(f'{dirpprom}\HT{cuenta_str}.xls')
                cuenta_s= '-'.join(map(str, cuenta))
                ht.columns=['Comitente','Codigo','Especie','Concepto','FechaLiq','FechaOp','Comprobante','Referencia','Cantidad','Precio','Saldo']
                ht['Referencia']= ht['Referencia'].fillna('')
                ht = ht[~ht['Referencia'].str.contains('ANUL', case=False)]
                ht.loc[ht['Referencia'].str.contains('SPL', case=False), 'Concepto'] = 'CANJ'
                ht.loc[ht['Referencia'].str.contains('SPIN', case=False), 'Concepto'] = 'CANJ'
                ht= ht[['Comitente','Codigo','Especie','Concepto','FechaOp','Cantidad','Precio']]
                ht= pd.merge(ht,categorias, on="Codigo", how="left")
                ht= pd.merge(ht, ccl, on='FechaOp', how='left')
                
                fechaop= ht['FechaOp'].copy()
                fechaop= fechaop.sort_values()
                start = (fechaop.iloc[0] - timedelta(days=1)).strftime('%Y-%m-%d')
                usdoficial= ek.get_timeseries('ARS=', start_date= start)['CLOSE'].astype(float)
                usdoficial= usdoficial.reset_index(drop=False)
                usdoficial.columns= ['FechaOp','dolaroficial']
                usdoficial= usdoficial.shift(1).dropna()
                ht= pd.merge(ht, usdoficial, how='left', on='FechaOp')
                ht['CCL']= np.where(ht['CCL'].isna(),ht['dolaroficial'],ht['CCL'])
                ht['RIC'] = ht['RIC'].fillna('')
                cols= ['Comitente', 'Codigo', 'Especie', 'Concepto', 'FechaOp', 'Cantidad',
                       'Precio', 'Categoria', 'Unidad_precio', 'Clasificacion', 'RIC',
                       'Nombre', 'Sector', 
                       'CCL','dolaroficial']
                ht= ht[cols]
                ht.loc[ht['Concepto'] == 'CANJ', 'Precio'] = 0
                
                ht.loc[ht['Concepto'] == 'CPU$', 'Precio'] = ht['Precio'] / ht['dolaroficial'] * ht['CCL']
                ht.loc[ht['Concepto'] == 'VTU$', 'Precio'] = ht['Precio'] / ht['dolaroficial'] * ht['CCL']
                ht.loc[ht['Concepto'] == 'CTRP', 'Precio'] = ht['Precio'] / ht['dolaroficial'] * ht['CCL']
                ht.loc[ht['Concepto'] == 'VTRP', 'Precio'] = ht['Precio'] / ht['dolaroficial'] * ht['CCL']
                try:
                    corregir_precios(ht, method='EK')
                except:
                    try:
                        corregir_precios(ht, method='EK')
                    except:
                        pass
                ht['Monto_Pesos'] = np.where(ht['Categoria'] != 'Exterior',
                                             ht['Cantidad'] * ht['Precio'] / ht['Unidad_precio'],
                                             ht['Cantidad'] * (ht['Precio'] / ht['Unidad_precio']) * ht['CCL'])
    
                ht['Monto_Usd']= ht['Monto_Pesos']/ht['CCL']
                codigos = tenencias['Codigo'].unique().tolist() #Me quedo solo con los papeles que están en el TVAFECHA
                mask= ht.Codigo.isin(codigos)
                ht= ht[mask]
                
                conceptos = ['EGOF','DGOF']
                mask= ht.Concepto.isin(conceptos)
                ht= ht[~mask]
                
                to_drop = []
                # Iterar a través del DataFrame utilizando índices
                '''for i in range(len(ht)):
                    # Elimino la compra de dólar MEP para las especies que compraron y vendieron por la misma cantidad.
                    if ht.iloc[i]['Concepto'] == 'VTU$' and ht.iloc[i-1]['Concepto'] == 'CPRA' and ht.iloc[i]['Cantidad'] == -ht.iloc[i-1]['Cantidad'] and ht.iloc[i]['Codigo'] == ht.iloc[i-1]['Codigo']:
                        # Agregar índices de las filas a la lista
                        to_drop.append(i)
                        to_drop.append(i-1)
                    if ht.iloc[i]['Concepto'] == 'CPRA' and ht.iloc[i-1]['Concepto'] == 'VTU$' and ht.iloc[i]['Cantidad'] == -ht.iloc[i-1]['Cantidad'] and ht.iloc[i]['Codigo'] == ht.iloc[i-1]['Codigo']:
                        # Agregar índices de las filas a la lista
                        to_drop.append(i)
                        to_drop.append(i-1)
                # Eliminar las filas marcadas
                ht = ht.drop(ht.index[to_drop])'''
                ht = ht.reset_index(drop=True)
                todos= pd.DataFrame()
                clases= ht.Clasificacion.unique().tolist()
                for clase in clases:
                    ht_clase= ht[ht['Clasificacion']==clase].copy()
                    
                    ht_porespecie = dict(tuple(ht_clase.groupby('Codigo')))
                    ht_porespecie_filtrado = ht_porespecie.copy()
                    
                    for codigo, df in ht_porespecie_filtrado.items():
                        print(codigo)
                        juntos= pd.DataFrame()
                        if df['Cantidad'].sum()<=0:
                            pass
                        else:
                            for comitente in cuenta:
                                ht_cuenta= df[df['Comitente']==comitente]
                                ht_cuenta= ht_cuenta.sort_values(by=['FechaOp'])
                                ht_cuenta = ht_cuenta.reset_index(drop=True)
                                ht_cuenta['Saldo_Usd'] = ht_cuenta['Monto_Usd'].cumsum()
                                ht_cuenta['Cantidad_Acum'] = ht_cuenta['Cantidad'].cumsum()
                                
                                # Identificamos los índices donde el saldo es menor o igual a cero, indicando que vendió todo
                                reset_indices = ht_cuenta[(ht_cuenta['Saldo_Usd'] <= 0) & (ht_cuenta['Cantidad_Acum'] <= 0)].index
    
                                if not reset_indices.empty:
                                    # Tomamos el último índice donde el saldo fue menor o igual a cero
                                    last_reset_index = reset_indices[-1]
                                    # Filtramos el DataFrame para considerar solo operaciones después de ese punto
                                    df_filtered = ht_cuenta.loc[last_reset_index + 1:]
                                    df_filtered= df_filtered.reset_index(drop=True)
                                    df_filtered['Saldo_Usd']= df_filtered['Monto_Usd'].cumsum()
                                    df_filtered['Cantidad_Acum']= df_filtered['Cantidad'].cumsum()
                                    fila= df_filtered.tail(1)
                                    ##ht_porespecie_filtrado[codigo] = df_filtered  # Actualizamos el diccionario con el DF filtrado
                                    juntos= pd.concat([juntos, fila], ignore_index=True)
                                else:
                                    juntos= pd.concat([juntos, ht_cuenta.tail(1)], ignore_index=True)
                                    ##ht_porespecie_filtrado[codigo] = df  # Aseguramos que el DF se mantenga en el diccionario si no hay reset
                            
                                juntos=  juntos.groupby('Codigo').agg({'Especie': 'first','RIC':'first','Nombre':'first','Clasificacion':'first','Saldo_Usd':'sum','Cantidad_Acum':'sum'}).reset_index()
                            ht_porespecie_filtrado[codigo] = juntos
                    pprom = {}
                    for codigo, df in ht_porespecie_filtrado.items():
                        print(codigo)
                        try:
                            df_pprom= pd.DataFrame()
                            df_pprom['Codigo']= [codigo]
                            df_pprom['Especie']= df.Especie.unique().tolist()
                            if clase in ['Renta Variable Extranjera','ETFs','Renta Variable Local']:
                                df_pprom['Nombre']= df.Nombre.unique().tolist()
                                df_pprom['RIC']= df.RIC.unique().tolist()
                            df_pprom['Clasificacion']= df.Clasificacion.unique().tolist()
                            
                            df_pprom['Monto Invertido Usd']= [df['Saldo_Usd'].iloc[-1]]
                            if clase in ['Renta Variable Extranjera','ETFs']:
                                df_pprom['Monto Actual Usd']= [tenencias[tenencias['Codigo']==codigo]['Valorizada'].sum()] 
                            else:
                                
                                df_pprom['Monto Actual Usd']= [tenencias[tenencias['Codigo']==codigo]['Valorizada'].sum()] 
                            df_pprom['Rendimiento Usd']= (df_pprom['Monto Actual Usd'] / df_pprom['Monto Invertido Usd'] -1)
                            
                            pprom[codigo]= df_pprom    
                        except:
                            pass
                    preciospromedios = pd.DataFrame()
                    # Concatenar los DataFrames de cada clave en el diccionario
                    for codigo, df_pprom in pprom.items():
                        preciospromedios = pd.concat([preciospromedios, df_pprom], ignore_index=True)
                    
                    todos= pd.concat([todos, preciospromedios], ignore_index=True)
                todos['Participacion']= todos['Monto Actual Usd'] / todos['Monto Actual Usd'].sum()
                #todos.to_excel(f'PPROM_{comitente}.xlsx')
                return todos
    
            
            ppromedios= rendimientos(tenencia_cuenta, cuenta, categorias)
            #AHORA VA EL FIFO
            cuenta_str = str(cuenta).zfill(6)
            dirpprom=r"C:\Users\ldt\Documents\Agustin Ehrman\Precio Promedio"
            filename= f'{dirpprom}\HT{cuenta_str}.xls' 
    
            def process_fifo_operations(filename):  
                codigos_exterior= pd.read_excel('exterior_y_cedears_ACTUALIZADO.xlsx', header=1).Codigo.tolist()
                df = pd.read_excel(filename)
                columns= ['Comitente','Codigo','Especie','Concepto','FechaLiq','FechaOp','Cpbte','Referencia','Cantidad','Precio','SaldoCajaValores']
                df.columns= columns
                df['Referencia']= df['Referencia'].fillna('')
                df = df[~df['Referencia'].str.contains('ANUL', case=False)]
                df.loc[(df['Referencia'].str.contains('SPL', case=False)) & (df['Precio'] == 0), 'Concepto'] = 'ESPECIAL'
                df.loc[(df['Referencia'].str.contains('SPIN', case=False)) & (df['Precio'] == 0), 'Concepto'] = 'ESPECIAL'
                
                df= df[['Comitente','Codigo','Especie','Concepto','FechaOp','Cantidad','Precio']]
                fechaop= df['FechaOp'].copy()
                fechaop= fechaop.sort_values()
                start = (fechaop.iloc[0] - timedelta(days=1)).strftime('%Y-%m-%d')
                usdoficial= ek.get_timeseries('ARS=', start_date= start)['CLOSE'].astype(float)
                usdoficial= usdoficial.reset_index(drop=False)
                usdoficial.columns= ['FechaOp','dolaroficial']
                usdoficial= usdoficial.shift(1).dropna()
                
                df= pd.merge(df, usdoficial, how='left', on='FechaOp')
                
                ccl= ek.get_timeseries('ARSMEP=',start_date=start)['CLOSE'].astype(float)
                ccl= ccl.fillna(method='ffill')
                ccl= ccl.reset_index(drop=False)
                ccl.columns= ['FechaOp','dolarccl']
                df= pd.merge(df, ccl, how='left',on='FechaOp')
                df['dolarccl']= np.where(df['dolarccl'].isna(),df['dolaroficial'],df['dolarccl'])
                df= df[~df['Concepto'].isin(['EGOF','DGOF', 'DEGO','ENGO','PVCC','PVCT'])]
                df= df[~df['Codigo'].isin([6000,7000,8000,8700,9000,9002,10000])]
                df.loc[df['Concepto'] == 'CPU$', 'Precio'] = df['Precio'] / df['dolaroficial'] * df['dolarccl']
                df.loc[df['Concepto'] == 'VTU$', 'Precio'] = df['Precio'] / df['dolaroficial'] * df['dolarccl']
                df.loc[df['Concepto'] == 'CTRP', 'Precio'] = df['Precio'] / df['dolaroficial'] * df['dolarccl']
                df.loc[df['Concepto'] == 'VTRP', 'Precio'] = df['Precio'] / df['dolaroficial'] * df['dolarccl']
                
                df['Monto']= df.Cantidad*df.Precio
                #df.loc[df['Concepto'] == 'CPMX', 'Monto'] = df['Monto'] * df['dolarccl']
                #df.loc[df['Concepto'] == 'VTMX', 'Monto'] = df['Monto'] * df['dolarccl']
                df.loc[df['Codigo'].isin(codigos_exterior), 'Monto'] = df['Monto'] * df['dolarccl']
                
                df['Monto']= df['Monto']/df['dolarccl']
                #conceptos=['CPRA','VTAS','CANJ','SUSC','COTR','VTTR','EJPV','EJPC','DIV','LICI','CPMX','VTMX','CPU$','VTU$','CTRP','VTRP','RESC','LIPA','LSFI','LRFI','DETS','DETR','DIVT','RTTR']
                resultados= {}
                for codigo, group in df.groupby('Codigo'):
                    print(codigo)
                    #group= group[group.Concepto.isin(conceptos)].copy()
                    group= group[~((group.Concepto=='CANJ')&(group.Cantidad < 0))].copy()
                           
                    if group.empty:
                        pass
                    if group.Cantidad.sum() <= 0:
                        pass
                    else:
                        df_filtered= group.copy()
                        df_filtered['Cantidad_Remanente']= df_filtered.Cantidad.copy()    
                        #group['MontoAcum']= group['Monto'].cumsum() 
                        #compras= df_filtered[df_filtered.Concepto=='CPRA']
                        #ventas= df_filtered[df_filtered.Concepto=='VTAS']
                        FIFO = pd.DataFrame()
                        for index, row in df_filtered.iterrows():
                            if row['Concepto'] in ['CPRA','CPU$','LIPA','LICI','DIV','CPMX','INAJ','COCU','SUSC','LSFI','IEEC','DETS','DETR','CTRP','COTR','EJPC','DETC','ICEE','INTE']:
                                # Agrega una nueva fila a FIFO cuando es una compra
                                FIFO = pd.concat([FIFO, pd.DataFrame([row])], ignore_index=True)
                            elif row['Concepto'] in ['VTAS','VTMX','VTTR','EJPV','VTU$', 'VTRP','RESC','LRFI','DIVT','RTTR','RTTS','ENAJ','PDE','BSU','ECIE','EGAJ','VCAB','EGCA','EEIC','ENPR','REDC','RETC']:
                                if not FIFO.empty:
                                    cantidad_venta = abs(row['Cantidad'])
                                    fifo_iloc = 0
                        
                                    while cantidad_venta != 0 and fifo_iloc < len(FIFO):
                                        cantidad_remanente = FIFO.iloc[fifo_iloc]['Cantidad_Remanente']
                        
                                        if cantidad_venta >= cantidad_remanente:
                                            # Si la cantidad de la venta es mayor o igual que la remanente,
                                            # se establece la cantidad remanente en 0 y se ajusta la cantidad de venta
                                            cantidad_venta -= cantidad_remanente
                                            FIFO.at[fifo_iloc, 'Cantidad_Remanente'] = 0
                                            FIFO.at[fifo_iloc, 'Monto'] = 0
                                        else:
                                            # Si la cantidad de la venta es menor, ajusta la cantidad remanente
                                            # y reduce el monto proporcionalmente
                                            FIFO.at[fifo_iloc, 'Cantidad_Remanente'] -= cantidad_venta
                                            original_cantidad = FIFO.iloc[fifo_iloc]['Cantidad']
                                            FIFO.at[fifo_iloc, 'Monto'] = (FIFO.iloc[fifo_iloc]['Monto'] / original_cantidad) * FIFO.iloc[fifo_iloc]['Cantidad_Remanente']
                                            cantidad_venta = 0  # La venta ha sido completamente asignada
                                        fifo_iloc += 1
                            elif row['Concepto']=='ESPECIAL': #Caso de DIV que dice SPLIT por ejemplo con precio 0
                                if FIFO.empty:
                                    FIFO = pd.concat([FIFO, pd.DataFrame([row])], ignore_index=True)
                                else:    
                                    ppc= FIFO['Monto'].sum()/FIFO['Cantidad_Remanente'].sum()
                                    row['Cantidad']+= FIFO['Cantidad'].sum()
                                    row['Cantidad_Remanente']= row['Cantidad'].copy()
                                    FIFO = pd.DataFrame()
                                    row['Precio']= ppc
                                    row['Monto']= row['Precio']*row['Cantidad']
                                    FIFO = pd.concat([FIFO, pd.DataFrame([row])], ignore_index=True)
                            else: #Concepto == CANJ
                                if FIFO.empty:
                                    FIFO = pd.concat([FIFO, pd.DataFrame([row])], ignore_index=True)
                                else:    
                                    ppc= FIFO['Monto'].sum()/row['Cantidad']
                                    FIFO = pd.DataFrame()
                                    row['Precio']= ppc
                                    row['Monto']= row['Precio']*row['Cantidad']
                                    FIFO = pd.concat([FIFO, pd.DataFrame([row])], ignore_index=True)
                                    
                        if FIFO['Cantidad_Remanente'].sum() != 0:
                            PPC_FIFO = FIFO['Monto'].sum() / FIFO['Cantidad_Remanente'].sum()
                        else:
                            PPC_FIFO = 0
                        Cantidad_Rem_FIFO = FIFO['Cantidad_Remanente'].sum()
                        resultados[codigo]= (PPC_FIFO,Cantidad_Rem_FIFO, FIFO)
                return resultados
    
            results = process_fifo_operations(filename)
    
            results_filtered = {clave: valor for clave, valor in results.items() if valor[0] != 0}
    
            promedios_fifo=pd.DataFrame()
            for codigo, tupla in results_filtered.items():
                row= pd.DataFrame({'Codigo':[codigo], 'PrecioFIFO':[tupla[0]]})
                promedios_fifo= pd.concat([promedios_fifo, row], ignore_index=True)
            
            tabla_fifo= pd.merge(tenencia_cuenta, promedios_fifo, how='left',on='Codigo')
            tabla_fifo['PrecioActualUSD']= tabla_fifo['P_gallo']/CCL
            tabla_fifo['Monto Actual Usd']= tabla_fifo['Valorizada'].copy()
            tabla_fifo.loc[tabla_fifo['Nombre_Especie'].str.contains('_U-', case=False), 'PrecioActualUSD']*= CCL
            tabla_fifo.loc[tabla_fifo['Nombre_Especie'].str.contains('_U-', case=False), 'Monto Actual Usd']*= CCL
            tabla_fifo.pop('Monto Actual Usd')
    
            tabla_fifo['Rendimiento FIFO %']= (tabla_fifo['PrecioActualUSD']/ tabla_fifo['PrecioFIFO']-1)*100
    
            ppromedios= ppromedios[['Codigo','Monto Invertido Usd']]
            tabla_fifo= pd.merge(tabla_fifo, ppromedios, how='left',on='Codigo')
            tabla_fifo['Monto Actual Usd']= tabla_fifo['Valorizada'].copy()
            tabla_fifo['PPC']= tabla_fifo['Monto Invertido Usd']/tabla_fifo['Tenencia']*tabla_fifo['Unidad_precio']
            tabla_fifo['Rendimiento PPC %']= (tabla_fifo['Monto Actual Usd']/ tabla_fifo['Monto Invertido Usd']-1)*100
            tabla_fifo= tabla_fifo.sort_values(by='Clasificacion')
            tabla_fifo= tabla_fifo[['Nombre_Especie', 'Clasificacion', 'Monto Invertido Usd','Monto Actual Usd',
                                    'PPC', 'PrecioFIFO', 'PrecioActualUSD', 'Rendimiento FIFO %',  'Rendimiento PPC %']]
            tabla_fifo= tabla_fifo[tabla_fifo['Clasificacion']!='Moneda']
            tabla_fifo['Monto Invertido Usd']= tabla_fifo['Monto Invertido Usd'].map('{:,.2f}'.format)
            tabla_fifo['Monto Actual Usd']= tabla_fifo['Monto Actual Usd'].map('{:,.2f}'.format)
            tabla_fifo['PPC']= tabla_fifo['PPC'].map('{:,.2f}'.format)
            tabla_fifo['PrecioFIFO']= tabla_fifo['PrecioFIFO'].map('{:,.2f}'.format)
            tabla_fifo['PrecioActualUSD']= tabla_fifo['PrecioActualUSD'].map('{:,.2f}'.format)
            tabla_fifo['Rendimiento FIFO %']= tabla_fifo['Rendimiento FIFO %'].map('{:.2f}%'.format)
            tabla_fifo['Rendimiento PPC %']= tabla_fifo['Rendimiento PPC %'].map('{:.2f}%'.format)
            tabla_fifo['Nombre_Especie']= tabla_fifo['Nombre_Especie'].str.split('-').str[0]
            for clasification in tabla_fifo['Clasificacion'].unique().tolist():
                tabla= tabla_fifo[tabla_fifo['Clasificacion']==clasification].copy()
                fig = go.Figure(data=[go.Table(
                    columnwidth=[8, 3, 3, 3, 3, 3, 3, 3],
                    header=dict(height = 30,
                                values=['<b>ESPECIE</b>','<b>USD INV.</b>','<b>USD ACT.</b>','<b>PPC</b>','<b>PPC FIFO</b>','<b>PUSD ACT.</b>','<b>REND% PPC</b>','<b>REND% FIFO</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla['Nombre_Especie'],tabla['Monto Invertido Usd'],tabla['Monto Actual Usd'],tabla['PPC'],tabla['PrecioFIFO'],tabla['PrecioActualUSD'],tabla['Rendimiento PPC %'],tabla['Rendimiento FIFO %']],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+10)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                
                fig.write_image(f'{dirG}\\tabla rendimientos {clasification} - {cuenta}.png',scale=1)
        #Comenzamos a generar los gráficos. El primero es el de torta general.
        def torta_general(tenencia_cuenta):
            tenencia_activos= tenencia_cuenta[tenencia_cuenta['Clasificacion']!= 'Moneda']
            assets = tenencia_activos.groupby("Clasificacion")["Valorizada"].sum()
            '''
            tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"]
            #Agregamos las tenencias negativas
            tenencia_negativos= negativas[((negativas["Comitente"] == cuenta)&(negativas['Clasificacion']=='Moneda'))]
            tenencia_moneda = pd.concat([tenencia_moneda, tenencia_negativos], ignore_index=True)
            
            
            cuenta_corriente= pesos[pesos["Comitente"]==cuenta].copy()
            cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos en Cta. Corriente en USD al CCL"
            cuenta_corriente= cuenta_corriente[["Nombre_Especie", "Importe"]]
            cuenta_corriente= cuenta_corriente.rename(columns={"Importe":"Valorizada"})
            tenencia_moneda= pd.concat([tenencia_moneda, cuenta_corriente], ignore_index= True)
            
            tenencia_moneda.loc[tenencia_moneda['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
            total_row = pd.DataFrame({'Nombre_Especie': ['TOTAL USD'], 'Valorizada': [tenencia_moneda.Valorizada.sum()]})
            tenencia_moneda = pd.concat([tenencia_moneda, total_row], ignore_index=True)
            if tenencia_moneda.empty:
                pass
                
            else:
                monedas = tenencia_moneda.groupby("Nombre_Especie")["Valorizada"].sum()
                if monedas.sum()<=0:
                    pass
                else:
                    assets.loc["Moneda"]= monedas.sum()
            '''
            
            parameters = {'axes.labelsize': 20,
                          'axes.titlesize': 20,
                          'font.family': 'Arial'}
            plt.rcParams.update(parameters)
            
            # Crear la figura y los subplots utilizando plt.GridSpec
            fig = plt.figure(figsize=(30, 10))
            grid = plt.GridSpec(2, 3, width_ratios=[2, 1, 1])
            
            ax1 = plt.subplot(grid[:, 0])  # Este subplot ocupa ambas filas de la primera columna
            ax1.pie(assets.values, labels=assets.index, labeldistance=1.1, autopct='%1.1f%%',pctdistance=0.8,textprops={'fontsize': 16}, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
            circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
            ax1.add_artist(circle)
            ax1.set_title('Distribución General de la Cartera')
            
            #Montos en activos locales
            tenencia_categorias= tenencia_activos.groupby("Clasificacion").sum()
            tenencia_categorias= tenencia_categorias.reset_index()
            
            tenencia_locales= tenencia_categorias.loc[tenencia_categorias['Clasificacion'].str.contains('Local', case=False)]
            tenencia_locales= tenencia_locales[["Clasificacion","Valorizada"]]
            tenencia_locales["Participacion"]= tenencia_locales["Valorizada"]/tenencia_locales.Valorizada.sum()*100
            ax2 = plt.subplot(grid[0, 1])  # Este subplot está en la fila 1 y columna 2
            ax2.pie(tenencia_locales.Participacion, labels=tenencia_locales.Clasificacion, labeldistance=1.1, autopct='%1.1f%%',pctdistance=0.8,textprops={'fontsize': 16}, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
            circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
            ax2.add_artist(circle)
            ax2.set_title('Distribucion en Activos Locales')
            
            tenencia_extranjeras= tenencia_categorias.loc[tenencia_categorias['Clasificacion'].str.contains('Extranjera', case=False)]
            tenencia_extranjeras= tenencia_extranjeras[["Clasificacion","Valorizada"]]
            tenencia_extranjeras["Participacion"]= tenencia_extranjeras["Valorizada"]/tenencia_extranjeras.Valorizada.sum()*100
            ax3 = plt.subplot(grid[1, 1])  # Este subplot está en la fila 1 y columna 2
            ax3.pie(tenencia_extranjeras.Participacion, labels=tenencia_extranjeras.Clasificacion, labeldistance=1.1, autopct='%1.1f%%',pctdistance=0.8,textprops={'fontsize': 16}, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
            circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
            ax3.add_artist(circle)
            ax3.set_title('Distribucion en Activos Extranjeros')
            
            plt.savefig(f'{dirG}\\torta General {cuenta}.png',bbox_inches='tight',edgecolor='w')
        torta_general(tenencia_cuenta)
        
       
        #Correr en la consola este comando: conda install -c plotly plotly-orca
        #Ahora hacemos las tablas de tenencia de cada uno.
        def tabla_moneda(tenencia_cuenta, cuenta, dirG):
            tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"]
            #Agregamos las tenencias negativas
            tenencia_negativos= negativas[((negativas["Comitente"] == cuenta)&(negativas['Clasificacion']=='Moneda'))]
            tenencia_moneda = pd.concat([tenencia_moneda, tenencia_negativos], ignore_index=True)
            
            tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"].groupby("Nombre_Especie").sum()
            tenencia_moneda.reset_index(inplace=True)
            
            cuenta_corriente= pesos[pesos["Comitente"]==cuenta].copy()
            cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos en Cta. Corriente en USD al CCL"
            cuenta_corriente= cuenta_corriente[["Nombre_Especie", "Importe"]]
            cuenta_corriente= cuenta_corriente.rename(columns={"Importe":"Valorizada"})
            tenencia_moneda= pd.concat([tenencia_moneda, cuenta_corriente], ignore_index= True)
            
            tenencia_moneda.loc[tenencia_moneda['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
            total_row = pd.DataFrame({'Nombre_Especie': ['TOTAL USD'], 'Valorizada': [tenencia_moneda.Valorizada.sum()]})
            tenencia_moneda = pd.concat([tenencia_moneda, total_row], ignore_index=True)
            
            
            
            tenencia_moneda['Valorizada'] = tenencia_moneda['Valorizada'].map('{:,.2f}'.format)
            tabla= tenencia_moneda[['Nombre_Especie','Valorizada']].copy()
            tabla.loc[tabla['Nombre_Especie'] == 'TOTAL USD', :] = tabla.loc[tabla['Nombre_Especie'] == 'TOTAL USD', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            
            
            
            if tabla.empty:
                print("No hay tenencia de moneda")
                no_moneda= True
                return no_moneda
            
            fig = go.Figure(data=[go.Table(
                columnwidth=[0.8,0.8,0.8],
                header=dict(height = 30,
                            values=['<b>TIPO DE MONEDA </b>','<b>TENENCIA</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Nombre_Especie, tabla.Valorizada],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['left','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+2.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            
            fig.write_image(f'{dirG}\\tabla moneda - {cuenta}.png',scale=1)
            
        tabla_moneda(tenencia_cuenta, cuenta, dirG)
        
        def tabla_tenencia_activos(tenencia_cuenta, cuenta, dirG):
            tenencias_totales = tenencia_cuenta[tenencia_cuenta["Clasificacion"] != "Moneda"]
            tabla= tenencias_totales[['Clasificacion','Valorizada']]
            aux= tabla.groupby('Clasificacion').sum()
            aux.reset_index(inplace=True)
            total_valorizada = aux['Valorizada'].sum()
            total_row = pd.DataFrame({'Clasificacion': ['Total'], 'Valorizada': [total_valorizada]})
            tabla = pd.concat([aux, total_row], ignore_index=True)
            tabla['Participacion']= tabla['Valorizada']/total_valorizada*100
            tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla.loc[tabla['Clasificacion'] == 'Total', :] = tabla.loc[tabla['Clasificacion'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
        
            fig = go.Figure(data=[go.Table(
                columnwidth=[0.8,0.8,0.8],
                header=dict(height = 30,
                            values=['<b>CLASIFICACION</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Clasificacion, tabla.Valorizada, tabla.Participacion],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['left','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+2.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            
            fig.write_image(f'{dirG}\\tabla activos - {cuenta}.png',  scale=1)
                                        
        tabla_tenencia_activos(tenencia_cuenta, cuenta, dirG)
        
        def tabla_cuenta_corriente(pesos, cuenta, dirG):
            cuenta_corriente= pesos[pesos["Comitente"]==cuenta].copy()
            cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos"
            tabla= cuenta_corriente[["Nombre_Especie", "Importe"]].copy()
            tabla['Importe'] = tabla['Importe'].map('{:,.2f}'.format)
            
            if tabla.empty:
                no_ctacorr= True
                return no_ctacorr
            fig = go.Figure(data=[go.Table(
                columnwidth=[0.8,0.8,0.8],
                header=dict(height = 30,
                            values=['<b>TIPO DE MONEDA</b>','<b>TENENCIA</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Nombre_Especie, tabla.Importe],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['left','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+2.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            
            fig.write_image(f'{dirG}\\tabla cuenta corriente - {cuenta}.png',  scale=1)
            
        tabla_cuenta_corriente(pesos, cuenta, dirG)
        
        
        def tablas_negativas(negativas, cuenta, dirG):
            tenencia_negativos= negativas[negativas["Comitente"] == cuenta]
            tenencia_negativos= tenencia_negativos[['Nombre_Especie', 'Clasificacion', 'Valorizada']]
            tenencia_negativos.loc[tenencia_negativos['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
            total_row= pd.DataFrame({"Nombre_Especie": ["TOTAL"], "Clasificacion": "", "Valorizada": tenencia_negativos.Valorizada.sum()})
            tenencia_negativos= pd.concat([tenencia_negativos, total_row], ignore_index= True)
            tenencia_negativos['Valorizada'] = tenencia_negativos['Valorizada'].map('{:,.2f}'.format)
            
            tabla= tenencia_negativos.copy()
            tabla.loc[tabla['Nombre_Especie'] == 'TOTAL', :] = tabla.loc[tabla['Nombre_Especie'] == 'TOTAL', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            if tabla.empty:
                print("No hay tenencia negativas")
                no_negativos= True
                return no_negativos
            if (tabla.Clasificacion == "Opciones").any()==True:
                columnwidth= [1.2,0.8,0.8]
            else:
                columnwidth=[0.8,0.8,0.8]
            
            fig = go.Figure(data=[go.Table(
                columnwidth=columnwidth,
                header=dict(height = 30,
                            values=['<b>NOMBRE DE LA ESPECIE</b>','<b>CLASIFICACION</b>','<b>MONTO (USD)</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Nombre_Especie, tabla.Clasificacion, tabla.Valorizada],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['left','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+2.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            
            fig.write_image(f'{dirG}\\tabla tenencias negativas - {cuenta}.png', scale=1)
            
        tablas_negativas(negativas, cuenta, dirG)
        
        def tabla_tenencia_total(tenencia_cuenta, cuenta, negativas, pesos, dirG):
            tenencia_activos= tenencia_cuenta[tenencia_cuenta['Clasificacion']!= 'Moneda']
            assets = tenencia_activos.groupby("Clasificacion")["Valorizada"].sum()
            
            tenencia_moneda = tenencia_cuenta[tenencia_cuenta["Clasificacion"] == "Moneda"]
            #Agregamos las tenencias negativas
            tenencia_negativos= negativas[((negativas["Comitente"] == cuenta)&(negativas['Clasificacion']=='Moneda'))]
            tenencia_moneda = pd.concat([tenencia_moneda, tenencia_negativos], ignore_index=True)
            
            
            cuenta_corriente= pesos[pesos["Comitente"]==cuenta].copy()
            cuenta_corriente.loc[:, "Nombre_Especie"] = "Pesos en Cta. Corriente en USD al CCL"
            cuenta_corriente= cuenta_corriente[["Nombre_Especie", "Importe"]]
            cuenta_corriente= cuenta_corriente.rename(columns={"Importe":"Valorizada"})
            tenencia_moneda= pd.concat([tenencia_moneda, cuenta_corriente], ignore_index= True)
            
            tenencia_moneda.loc[tenencia_moneda['Nombre_Especie'].str.contains('PESOS', case=False), 'Valorizada'] /= CCL #Dolarizamos los pesos a CCL
           
            
            if tenencia_moneda.empty:
                monedas= 0
                
            else:
                
                tenencia_moneda = tenencia_moneda.groupby("Nombre_Especie")["Valorizada"].sum()
                monedas= tenencia_moneda.sum()
                
           
            
            tenenciatotal= assets.sum() + monedas #Esto está dolarizado (los euros se suman como están)
            tabla= pd.DataFrame({"Clasificacion": ["Activos", "Moneda", "Tenencia TOTAL"], "Valorizada":[assets.sum(), monedas, tenenciatotal]})
            tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
            tabla.loc[tabla['Clasificacion'] == 'Tenencia TOTAL', :] = tabla.loc[tabla['Clasificacion'] == 'Tenencia TOTAL', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
            
            fig = go.Figure(data=[go.Table(
                columnwidth=[0.8,0.8,0.8],
                header=dict(height = 30,
                            values=['<b>CLASIFICACION</b>','<b>TENENCIA (U$S)</b>'],
                            fill_color='#d7d8d6',
                            line_color='darkslategray',
                            align='center',
                            font=dict(family='Arial', color='black', size=20)),
                cells=dict(values=[tabla.Clasificacion, tabla.Valorizada],
                            fill_color=['#ffffff'],
                            height=30,
                            line_color='darkslategray',
                            align=['left','center','center'],
                            font=dict(family='Arial', color='black', size=18)))
            ])
            h=(len(tabla.index)+2.5)*cm
            fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
            
            fig.write_image(f'{dirG}\\tabla total - {cuenta}.png',  scale=1)
            
        tabla_tenencia_total(tenencia_cuenta, cuenta, negativas, pesos, dirG)
        
        tenencia_clase= tenencia_cuenta[tenencia_cuenta['Clasificacion']!='Moneda'].copy()
            
        
        clases= list(tenencia_clase.Clasificacion.unique())
        for clase in clases:
            print(clase)
        #PONER SANGRIA A PARTIR DE ACA DENUEVO
        #clase= "Renta Variable Extranjera"
            if clase in ['Renta Variable Local', 'Renta Variable Extranjera']:
                def tabla_info_financiera(tenencia_clase, cuenta, dirG):
                    tenencia_info= tenencia_clase[tenencia_clase['Clasificacion']==clase]
                    tenencia_info= tenencia_info.reindex(columns=['Codigo','Valorizada','Clasificacion','RIC','Nombre','Sector', 'PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA', 'Close',
                                                                  'Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk','52Wk High', '52Wk Low'])
                    tenencia_info_ratios= tenencia_info.groupby('Nombre').agg({'Sector': 'first','Close':'first','PE':'first','PE fwd':'first','PBV':'first','PS':'first','Dividend Yield':'first','ROE':'first','ROA':'first', 'Valorizada': 'sum'}).reset_index()
                    tenencia_info_ratios['Dividend Yield']= tenencia_info_ratios['Dividend Yield'].astype(float)
                    numeric_columns = tenencia_info_ratios.select_dtypes(include=[float, int]).columns.tolist() #Selecciono las columnas que contienen valores numéricos para reemplazar los valores negativos por 0
                    tenencia_info_ratios[numeric_columns] = tenencia_info_ratios[numeric_columns].applymap(lambda x: 0 if x < 0 else x) #Corregimos los valores negativos por 0
                    total = tenencia_info_ratios['Valorizada'].sum()
                    
                    df_sectores= tenencia_info_ratios.groupby('Sector').sum()
                    df_sectores.reset_index(inplace=True)
                    df_sectores= df_sectores.reindex(columns=['Sector','Valorizada'])
                    df_sectores=df_sectores.rename(columns={"Valorizada":"Total_Sector"})
                    df_new_weights= pd.merge(tenencia_info_ratios,df_sectores, on='Sector')
                    df_new_weights['Nueva_Participacion']= df_new_weights['Valorizada']/df_new_weights['Total_Sector']*100 #Estos son los weigths re-calculados por sector, armando como si fuese una cartera por sector.
                    df_totales= df_new_weights.copy()
                    columns_to_multiply = ['PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA']
                    df_totales[columns_to_multiply] = df_totales[columns_to_multiply].multiply(df_totales['Nueva_Participacion']/100, axis=0)
                    df_totales= df_totales.groupby('Sector').sum()
                    del(df_totales['Total_Sector'])
                    df_totales.reset_index(inplace=True)
                    df_totales['Participacion']= df_totales['Valorizada']/df_totales['Valorizada'].sum()*100
                    
                    tenencia_info_ratios['Participacion']= tenencia_info_ratios['Valorizada']/total*100
                    df_ratios_ponderados= tenencia_info_ratios.copy() #Realizamos la ponderación de los ratios de cada acción en tenencia, por su participación en cartera.
                    columns_to_multiply = ['PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA'] #Multiplicaremos a estos ratios
                    df_ratios_ponderados[columns_to_multiply] = df_ratios_ponderados[columns_to_multiply].multiply(df_ratios_ponderados['Participacion']/100, axis=0)
                    cartera_total= pd.DataFrame({'Nombre':['Total Cartera'],'Sector':['Total Cartera'],'PE': [df_ratios_ponderados['PE'].sum()],'PE fwd':[df_ratios_ponderados['PE fwd'].sum()],'PBV':[df_ratios_ponderados['PBV'].sum()],
                                                 'PS':[df_ratios_ponderados['PS'].sum()],'Dividend Yield': [df_ratios_ponderados['Dividend Yield'].sum()],'ROE':[df_ratios_ponderados['ROE'].sum()],'ROA':[df_ratios_ponderados['ROA'].sum()], 'Valorizada':[df_ratios_ponderados['Valorizada'].sum()], 'Participacion': [df_ratios_ponderados['Participacion'].sum()] })
                    
                    #df_totales_sector= df_ratios_ponderados.groupby('Sector').sum()
                    #df_totales_sector.reset_index(inplace=True)
                    #tabla= pd.concat([tenencia_info_ratios,df_totales_sector], ignore_index=True)
                    #tabla['Nombre'] = tabla['Nombre'].fillna('Total')
                    #mask = tabla['Nombre'] == 'Total'
                    #df_totals = tabla.loc[mask].copy()
                    # Realizar la multiplicación solo en las filas seleccionadas (Se habían sumado los subtotales para los ratios, necesito saber su promedio ponderado)
                    #tabla.loc[mask] = df_totals #Actualizamos los valores corregidos.
                    tabla= tenencia_info_ratios.copy()
                    columns_format= ['Close','PE','PE fwd', 'PBV','PS', 'Dividend Yield','ROE','ROA', 'Valorizada']
                    tabla[columns_format] = tabla[columns_format].applymap(lambda x: '-' if x == 0 else '{:,.2f}'.format(x))
                    tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                    tabla= tabla.sort_values(['Sector'])
                    #tabla.reset_index(inplace=True)
                    #tabla= tabla.sort_values(['Sector','index'])
                    #del(tabla['index'])
                    tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                    
                    #Creamos la tabla de las tenencias de cada clase
                    fig = go.Figure(data=[go.Table(
                        columnwidth=[4.5, 5, 1.5, 2, 1.5, 2.5, 2],
                        header=dict(height = 30,
                                    values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>PE</b>','<b>PE F.</b>','<b>PBV</b>','<b>DIV. YLD</b>','<b>ROE</b>'],
                                    fill_color='#d7d8d6',
                                    line_color='darkslategray',
                                    align='center',
                                    font=dict(family='Arial', color='black', size=20)),
                        cells=dict(values=[tabla.Sector, tabla.Nombre, tabla.PE, tabla['PE fwd'], tabla.PBV, tabla['Dividend Yield'], tabla.ROE],
                                    fill_color=['#ffffff'],
                                    height=30,
                                    line_color='darkslategray',
                                    align=['center','center','center'],
                                    font=dict(family='Arial', color='black', size=18)))
                    ])
                    h=(len(tabla.index)+5.5)*cm
                    fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                        
                    fig.write_image(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png',  scale=1)
                    
                    #Hacemos la tabla de los totales
                    df_totales= pd.concat([df_totales,cartera_total],join='inner', ignore_index=True)
                    columns_format= ['PE','PE fwd', 'PBV', 'Dividend Yield','ROE','Valorizada']
                    df_totales[columns_format] = df_totales[columns_format].applymap(lambda x: '-' if x == 0 else '{:,.2f}'.format(x))
                    df_totales['Participacion']= df_totales['Participacion'].map('{:.2f}%'.format)
                    df_totales.loc[df_totales['Sector'] == 'Total Cartera', :] = df_totales.loc[df_totales['Sector'] == 'Total Cartera', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                    
                    fig = go.Figure(data=[go.Table(
                        columnwidth=[3.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
                        header=dict(height = 30,
                                    values=['<b>SECTOR</b>','<b>PE</b>','<b>PE F.</b>','<b>PBV</b>','<b>DIV. YLD</b>','<b>ROE</b>','<b>PART.</b>'],
                                    fill_color='#d7d8d6',
                                    line_color='darkslategray',
                                    align='center',
                                    font=dict(family='Arial', color='black', size=20)),
                        cells=dict(values=[df_totales.Sector, df_totales.PE,df_totales['PE fwd'], df_totales.PBV, df_totales['Dividend Yield'],df_totales.ROE, df_totales.Participacion],
                                    fill_color=['#ffffff'],
                                    height=30,
                                    line_color='darkslategray',
                                    align=['center','center','center'],
                                    font=dict(family='Arial', color='black', size=18)))
                    ])
                    h=len(df_totales.index)+1.5
                    fig.update_layout(width=1000,height=h*1200/34,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                        
                    fig.write_image(f'{dirG}\\total info financiera {clase} - {cuenta}.png', scale=1)
                tabla_info_financiera(tenencia_clase, cuenta, dirG)
                
            tenencia_clase_tabla= tenencia_clase[tenencia_clase['Clasificacion']==clase]
            
            def tabla_bonos(tenencia_clase_tabla, tabla_bonos, clase, cuenta, dirG):
                tenencias= tenencia_clase_tabla[['Codigo','Categoria','Nombre_Especie','RIC','Valorizada']]
                del(tenencias['RIC'])
                tenencias['Nombre_Especie'] = tenencias['Nombre_Especie'].apply(lambda x: ' '.join(x.split()[:4]))
                tenencias= tenencias.groupby('Nombre_Especie').agg({'Codigo':'first','Categoria': 'first','Valorizada':'sum'}).reset_index(drop=False)
                tabla= pd.merge(tenencias, tabla_bonos, on='Codigo', how='left')
                tabla= tabla.drop_duplicates(subset=['Codigo'], keep='first')
                tabla['Maturity']= pd.to_datetime(tabla['Maturity']) +timedelta(days=1) #Le agrego un día ya que Reuters trae el vencimiento un día antes de lo que figura en todos lados
                tabla['Maturity']= tabla['Maturity'].dt.strftime('%d %b %Y')
                
                fig = go.Figure(data=[go.Table(
                    columnwidth=[6, 6, 3, 1.5, 2.5],
                    header=dict(height = 30,
                                values=['<b>NOMBRE</b>','<b>EMISOR</b>','<b>VENCIMIENTO</b>','<b>CUPÓN</b>','<b>MONEDA</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Nombre_Especie, tabla.Issuer, tabla.Maturity, tabla.Coupon, tabla['Principal Currency']],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+15)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                    
                fig.write_image(f'{dirG}\\info bonos {clase} - {cuenta}.png', scale=1)
                
            if clase== 'Renta Fija Extranjera':
                tabla_bonos(tenencia_clase_tabla, bonos_exterior, clase, cuenta, dirG)
            elif clase== 'Renta Fija Local':
                tabla_bonos(tenencia_clase_tabla, bonos_locales, clase, cuenta, dirG)
                
            def tabla_performance(tenencia_clase_tabla, clase, cuenta, dirG):
                tabla= tenencia_clase_tabla[['Sector','Nombre','Close','Total Return 1Mo', 'Total Return 3Mo', 'Total Return 52Wk','52Wk High', '52Wk Low']]
                tabla= tabla.groupby('Nombre').agg({'Sector': 'first','Close':'first','Total Return 1Mo':'first','Total Return 3Mo':'first','Total Return 52Wk':'first','Close':'first','52Wk High':'first','52Wk Low':'first'}).reset_index()
                tabla= tabla.sort_values(['Sector'])
                numeric_columns = tabla.select_dtypes(include=[float, int]).columns.tolist()
                tabla[numeric_columns[-2:]] = tabla[numeric_columns[-2:]].applymap(lambda x: '-' if x == 0 else '{:,.2f}'.format(x))
                tabla[numeric_columns[1:-2]] = tabla[numeric_columns[1:-2]].applymap(lambda x: '-' if x == 0 else '{:.2f}%'.format(x))
                tabla['Close'] = tabla['Close'].map('{:,.2f}'.format)
                
                fig = go.Figure(data=[go.Table(
                    columnwidth=[7, 7, 3, 2.5, 2.5, 2.5, 2.5, 2.5],
                    header=dict(height = 30,
                                values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>CLOSE</b>','<b>RET. 1M</b>','<b>RET. 3M</b>','<b>RET. 52S</b>','<b>MAX 52S</b>','<b>MIN 52S</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Sector, tabla.Nombre, tabla.Close, tabla['Total Return 1Mo'], tabla['Total Return 3Mo'], tabla['Total Return 52Wk'], tabla['52Wk High'], tabla['52Wk Low']],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+6.5)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                fig.write_image(f'{dirG}\\performance {clase} - {cuenta}.png', scale=1)    
            
            def eps_sales_growth(ticker):
                eps,err= ek.get_data(ticker,fields= ['TR.EPSActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY).date','TR.EPSActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY)'])
                sales,err= ek.get_data(ticker, fields=['TR.RevenueActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY).date','TR.RevenueActValue(SDate=0,EDate=-10,Period=FY0,Frq=FY)'])
                eps = eps.drop(columns=['Instrument'])
                eps['Date'] = pd.to_datetime(eps['Date'])
                eps.set_index('Date', inplace=True)
                eps.index = eps.index.tz_convert(None)
                eps.sort_index(ascending=True, inplace=True)
                eps=eps.astype(float)
                eps['EPS Growth']= ((eps - eps.shift(1)) / abs(eps.shift(1)))
                eps= eps.dropna()
                eps_periods= len(eps)
                eps_geom_growth =  np.power(np.prod(1 + eps['EPS Growth']), 1 / len(eps)) - 1
                if np.isnan(eps_geom_growth):
                    eps_geom_growth = eps['EPS Growth'].mean()
                sales = sales.drop(columns=['Instrument'])
                sales['Date'] = pd.to_datetime(sales['Date'])
                sales.set_index('Date', inplace=True)
                sales.index = sales.index.tz_convert(None)
                sales.sort_index(ascending=True, inplace=True)
                sales=sales.astype(float)
                sales['Sales Growth']= ((sales - sales.shift(1)) / abs(sales.shift(1))) 
                sales= sales.dropna()
                sales_periods= len(sales)
                sales_geom_growth = np.power(np.prod(1 + sales['Sales Growth']), 1 / len(sales)) - 1
                if np.isnan(sales_geom_growth):
                    sales_geom_growth = sales['Sales Growth'].mean()
                return eps_geom_growth, eps_periods, sales_geom_growth, sales_periods
            
            def tabla_growth(tenencia_clase_tabla, clase, cuenta, dirG):
                tabla= tenencia_clase_tabla[['Sector','Nombre','RIC']]
                tabla= tabla.groupby('Nombre').agg({'Sector': 'first','RIC':'first'}).reset_index()
                tabla= tabla.sort_values(['Sector'])
                tickers= tabla.RIC.to_list()
                columns = ['RIC', 'EPS Growth','EPS Periods', 'Sales Growth','Sales Periods']
                growth_df = pd.DataFrame(columns=columns)

                # Recorrer la lista de tickers
                for ticker in tickers:
                    # Llamar a la función para obtener los resultados
                    eps_growth, eps_periods, sales_growth, sales_periods = eps_sales_growth(ticker)
                    
                    # Crear un DataFrame temporal con los resultados
                    temp_df = pd.DataFrame([[ticker,eps_growth, eps_periods, sales_growth, sales_periods]], columns=columns)
                    
                    # Concatenar el DataFrame temporal al DataFrame principal
                    growth_df = pd.concat([growth_df, temp_df], ignore_index=True)
                
                tabla= pd.merge(tabla,growth_df, on='RIC',how='left')    
                numeric_columns = tabla.select_dtypes(include=[float, int]).columns.tolist()
                tabla[numeric_columns]*=100
                tabla[numeric_columns] = tabla[numeric_columns].applymap(lambda x: '-' if x == 0 else '{:,.2f}%'.format(x))
                
                
                fig = go.Figure(data=[go.Table(
                    columnwidth=[4, 4, 2, 2, 2, 2],
                    header=dict(height = 30,
                                values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>EPS GROWTH</b>','<b>EPS PERIODS</b>','<b>SALES GROWTH</b>','<b>SALES PERIODS</b>'],
                                fill_color='#d7d8d6',
                                line_color='darkslategray',
                                align='center',
                                font=dict(family='Arial', color='black', size=20)),
                    cells=dict(values=[tabla.Sector, tabla.Nombre, tabla['EPS Growth'],tabla['EPS Periods'],tabla['Sales Growth'],tabla['Sales Periods']],
                                fill_color=['#ffffff'],
                                height=30,
                                line_color='darkslategray',
                                align=['center','center','center'],
                                font=dict(family='Arial', color='black', size=18)))
                ])
                h=(len(tabla.index)+6)*cm
                fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                fig.write_image(f'{dirG}\\growth {clase} - {cuenta}.png', scale=1)
                
            if clase =='Renta Variable Extranjera': #VER COMO HACER CON LOS FONDOS
                tabla_performance(tenencia_clase_tabla, clase, cuenta, dirG)
                if calcular_g == '2':
                    tabla_growth(tenencia_clase_tabla, clase, cuenta, dirG)
                df_paises= tenencia_clase_tabla[['Pais','Valorizada']]
                df_paises= df_paises.groupby('Pais').sum()
                df_paises.reset_index(inplace=True)
                df_paises['Participacion']= df_paises['Valorizada']/df_paises['Valorizada'].sum()
                tenencia_clase_tabla= tenencia_clase_tabla[['Sector','Pais','Nombre','Valorizada']] #Estas son las especies que contienen sector, ric, etc (INFO DE REUTERS)
                tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre').agg({'Sector': 'first','Pais':'first', 'Valorizada': 'sum'}).reset_index()
                total = tenencia_clase_tabla['Valorizada'].sum()
                tenencia_clase_tabla['Participacion']= tenencia_clase_tabla['Valorizada']/total*100
                df_sectores= tenencia_clase_tabla.groupby('Sector').sum()
                df_sectores.reset_index(inplace=True)
                tabla= pd.concat([tenencia_clase_tabla,df_sectores], ignore_index=True)
                tabla['Nombre'] = tabla['Nombre'].fillna('Total')
                tabla['Pais']=tabla['Pais'].fillna('')
                
                tabla= tabla.sort_values(['Sector'])
                tabla.reset_index(inplace=True)
                tabla= tabla.sort_values(['Sector','Participacion'])
                del(tabla['index'])
                tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
                tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                
                #Creamos la tabla de las tenencias de cada clase
                def tabla_tenencias_clase(tabla, cuenta, dirG):
                    fig = go.Figure(data=[go.Table(
                        columnwidth=[3.5, 3, 3.5, 1.5, 1.5],
                        header=dict(height = 30,
                                    values=['<b>SECTOR</b>','<b>PAIS</b>','<b>NOMBRE</b>','<b>TENENCIA</b>','<b>PART. %</b>'],
                                    fill_color='#d7d8d6',
                                    line_color='darkslategray',
                                    align='center',
                                    font=dict(family='Arial', color='black', size=20)),
                        cells=dict(values=[tabla.Sector, tabla.Pais, tabla.Nombre, tabla.Valorizada,tabla.Participacion],
                                    fill_color=['#ffffff'],
                                    height=30,
                                    line_color='darkslategray',
                                    align=['center','center','center'],
                                    font=dict(family='Arial', color='black', size=18)))
                    ])
                    h=(len(tabla.index)+7.5)*cm
                    fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                        
                    fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',  scale=1)
                         
                tabla_tenencias_clase(tabla, cuenta, dirG)
                #Ahora creamos el grafico de torta doble, uno que separa por sector, y el otro por empresa individual, que es mas detallado
                def grafico_clase(df_sectores, df_paises, tenencia_clase_tabla, cuenta, dirG):
                    #Primero voy a agrupar los sectores que tienen tenencia menor a 1.5% en la categoria 'Otro'
                    suma_sectores_chicos= df_sectores[df_sectores['Participacion'] < 1.5]['Valorizada'].sum()
                    if suma_sectores_chicos !=0:
                        df_sin_sectores_chicos= df_sectores[df_sectores['Participacion'] > 1.5]
                        df_otros= pd.DataFrame({'Sector':['Otro'],'Valorizada': [suma_sectores_chicos], 'Participacion': [suma_sectores_chicos / df_sectores['Valorizada'].sum() * 100]})
                        df_sectores= pd.concat([df_sin_sectores_chicos, df_otros])
                    
                    parameters = {'axes.labelsize': 20,
                            'axes.titlesize': 20}
                    plt.rcParams.update(parameters)
                    df_sectores= df_sectores.sort_values('Participacion')
                    slices= df_sectores['Participacion']
                    small = slices[:len(slices) // 2].to_list()
                    large = slices[len(slices) // 2:].to_list()
                                
                    reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                    r=pd.DataFrame(reordered,columns=['Participacion'])
                    df_torta1=pd.merge(r,df_sectores,on='Participacion')
                    #fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=[20, 20])
                    #ax4.axis('off')  # Desactivar ejes en ax4
                    fig = plt.figure(figsize=[20, 20])
                    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1], wspace=0.5)
                    
                    ax1 = fig.add_subplot(gs[0, 0])
                    ax2 = fig.add_subplot(gs[0, 1])
                    ax3 = fig.add_subplot(gs[1, :])
                    
                    angle = 180 + float(sum(small[::2])) / sum(df_torta1.Participacion) * 360
                    pie_wedge_collection = ax1.pie(df_torta1.Participacion,  labels=df_torta1.Sector, 
                                            labeldistance=1.1, 
                                            startangle=angle,  
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
                    for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                        if len(label.get_text()) > 12:
                            label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))
                            
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax1.set_title('Distribución Sectorial', fontweight='bold')
                    ax1.add_artist(centre_circle)
                    
                    #Ahora armamos la torta por empresa individual. Hacemos lo mismo que antes, agrupamos las empresas con poca tenencia en 'Otras empresas'.
                    suma_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] < 2]['Valorizada'].sum()
                    if suma_empresas_chicas !=0:
                        df_sin_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] > 2]
                        df_otras_empresas= pd.DataFrame({'Nombre':['Otras empresas'],'Sector':['Otro'],'Valorizada': [suma_empresas_chicas], 'Participacion': [suma_empresas_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                        tenencia_clase_tabla= pd.concat([df_sin_empresas_chicas, df_otras_empresas])
                    tenencia_clase_tabla= tenencia_clase_tabla.sort_values('Participacion')
                    slices= tenencia_clase_tabla['Participacion']
                    small = slices[:len(slices) // 2].to_list()
                    large = slices[len(slices) // 2:].to_list()
                                
                    reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                    r=pd.DataFrame(reordered,columns=['Participacion'])
                    df_torta2=pd.merge(r,tenencia_clase_tabla,on='Participacion')
                    
                    angle = 180 + float(sum(small[::2])) / sum(df_torta2.Participacion) * 360
                    pie_wedge_collection = ax2.pie(df_torta2.Participacion,  labels=df_torta2.Nombre, 
                                            labeldistance=1.1, 
                                            startangle=angle,  
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
                    '''for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                        if len(label.get_text()) > 12:
                            label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))'''
                            
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax2.set_title('Distribución por Empresa', fontweight='bold')
                    ax2.add_artist(centre_circle)
                    
                    
                    df_paises= df_paises.sort_values('Participacion')
                    slices= df_paises['Participacion']
                    small = slices[:len(slices) // 2].to_list()
                    large = slices[len(slices) // 2:].to_list()
                                
                    reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                    r=pd.DataFrame(reordered,columns=['Participacion'])
                    df_torta3=pd.merge(r,df_paises,on='Participacion')
                    
                    angle = 180 + float(sum(small[::2])) / sum(df_torta2.Participacion) * 360
                    pie_wedge_collection = ax3.pie(df_torta3.Participacion,  labels=df_torta3.Pais, 
                                            labeldistance=1.1, 
                                            startangle=angle,  
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
                    
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax3.set_title('Distribución por Países', fontweight='bold')
                    ax3 = plt.gcf()
                    fig.gca().add_artist(centre_circle)
                    
                    plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
                grafico_clase(df_sectores,df_paises, tenencia_clase_tabla, cuenta, dirG)
            elif clase== 'Renta Variable Local':
                tabla_performance(tenencia_clase_tabla, clase, cuenta, dirG)
                tenencia_clase_tabla= tenencia_clase_tabla[['Sector','Nombre','Valorizada']] #Estas son las especies que contienen sector, ric, etc (INFO DE REUTERS)
                tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre').agg({'Sector': 'first', 'Valorizada': 'sum'}).reset_index()
                total = tenencia_clase_tabla['Valorizada'].sum()
                tenencia_clase_tabla['Participacion']= tenencia_clase_tabla['Valorizada']/total*100
                df_sectores= tenencia_clase_tabla.groupby('Sector').sum()
                df_sectores.reset_index(inplace=True)
                tabla= pd.concat([tenencia_clase_tabla,df_sectores], ignore_index=True)
                tabla['Nombre'] = tabla['Nombre'].fillna('Total')
                tabla= tabla.sort_values(['Sector'])
                tabla.reset_index(inplace=True)
                tabla= tabla.sort_values(['Sector','Participacion'])
                del(tabla['index'])
                tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
                tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                
                #Creamos la tabla de las tenencias de cada clase
                def tabla_tenencias_clase(tabla, cuenta, dirG):
                    fig = go.Figure(data=[go.Table(
                        columnwidth=[2, 2.5, 1.5, 1.5],
                        header=dict(height = 30,
                                    values=['<b>SECTOR</b>','<b>NOMBRE</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                                    fill_color='#d7d8d6',
                                    line_color='darkslategray',
                                    align='center',
                                    font=dict(family='Arial', color='black', size=20)),
                        cells=dict(values=[tabla.Sector, tabla.Nombre, tabla.Valorizada,tabla.Participacion],
                                    fill_color=['#ffffff'],
                                    height=30,
                                    line_color='darkslategray',
                                    align=['center','center','center'],
                                    font=dict(family='Arial', color='black', size=18)))
                    ])
                    h=(len(tabla.index)+7.5)*cm
                    fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                        
                    fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',  scale=1)
                         
                tabla_tenencias_clase(tabla, cuenta, dirG)
                #Ahora creamos el grafico de torta doble, uno que separa por sector, y el otro por empresa individual, que es mas detallado
                def grafico_clase(df_sectores, tenencia_clase_tabla, cuenta, dirG):
                    #Primero voy a agrupar los sectores que tienen tenencia menor a 1.5% en la categoria 'Otro'
                    suma_sectores_chicos= df_sectores[df_sectores['Participacion'] < 1.5]['Valorizada'].sum()
                    if suma_sectores_chicos !=0:
                        df_sin_sectores_chicos= df_sectores[df_sectores['Participacion'] > 1.5]
                        df_otros= pd.DataFrame({'Sector':['Otro'],'Valorizada': [suma_sectores_chicos], 'Participacion': [suma_sectores_chicos / df_sectores['Valorizada'].sum() * 100]})
                        df_sectores= pd.concat([df_sin_sectores_chicos, df_otros])
                    
                    parameters = {'axes.labelsize': 20,
                            'axes.titlesize': 20}
                    plt.rcParams.update(parameters)
                    df_sectores= df_sectores.sort_values('Participacion')
                    slices= df_sectores['Participacion']
                    small = slices[:len(slices) // 2].to_list()
                    large = slices[len(slices) // 2:].to_list()
                                
                    reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                    r=pd.DataFrame(reordered,columns=['Participacion'])
                    df_torta1=pd.merge(r,df_sectores,on='Participacion')
                    #fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=[20, 20])
                    #ax4.axis('off')  # Desactivar ejes en ax4
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[20, 10])
                    plt.subplots_adjust(wspace=0.5)
                    angle = 180 + float(sum(small[::2])) / sum(df_torta1.Participacion) * 360
                    pie_wedge_collection = ax1.pie(df_torta1.Participacion,  labels=df_torta1.Sector, 
                                            labeldistance=1.1, 
                                            startangle=angle,  
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
                    for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                        if len(label.get_text()) > 12:
                            label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))
                            
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax1.set_title('Distribución Sectorial', fontweight='bold')
                    ax1.add_artist(centre_circle)
                    
                    #Ahora armamos la torta por empresa individual. Hacemos lo mismo que antes, agrupamos las empresas con poca tenencia en 'Otras empresas'.
                    suma_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] < 2]['Valorizada'].sum()
                    if suma_empresas_chicas !=0:
                        df_sin_empresas_chicas= tenencia_clase_tabla[tenencia_clase_tabla['Participacion'] > 2]
                        df_otras_empresas= pd.DataFrame({'Nombre':['Otras empresas'],'Sector':['Otro'],'Valorizada': [suma_empresas_chicas], 'Participacion': [suma_empresas_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                        tenencia_clase_tabla= pd.concat([df_sin_empresas_chicas, df_otras_empresas])
                    tenencia_clase_tabla= tenencia_clase_tabla.sort_values('Participacion')
                    slices= tenencia_clase_tabla['Participacion']
                    small = slices[:len(slices) // 2].to_list()
                    large = slices[len(slices) // 2:].to_list()
                                
                    reordered = large[1::2] + small[::2] + large[::2] + small[1::2]
                    r=pd.DataFrame(reordered,columns=['Participacion'])
                    df_torta2=pd.merge(r,tenencia_clase_tabla,on='Participacion')
                    
                    angle = 180 + float(sum(small[::2])) / sum(df_torta2.Participacion) * 360
                    pie_wedge_collection = ax2.pie(df_torta2.Participacion,  labels=df_torta2.Nombre, 
                                            labeldistance=1.1, 
                                            startangle=angle,  
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
                    '''for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                        if len(label.get_text()) > 12:
                            label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))'''
                            
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax2.set_title('Distribución por Empresa', fontweight='bold')
                    ax2.add_artist(centre_circle)
                    plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
                grafico_clase(df_sectores, tenencia_clase_tabla, cuenta, dirG)
            
            elif clase== 'ETFs':
                tenencia_clase_tabla= tenencia_clase_tabla[['Nombre','GEO','FundType','Valorizada']]
                tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre').agg({'GEO':'first','FundType': 'first','Valorizada':'sum'}).reset_index(drop=False)
                total = tenencia_clase_tabla['Valorizada'].sum()
                '''                
                tenencia_clase_tabla['Nombre'] = tenencia_clase_tabla['Nombre'].apply(lambda x: ' '.join(x.split()[:5]))

                tabla['Participacion']= tabla['Valorizada']/total*100
                tabla= tabla.sort_values(['FundType','Participacion'])
                tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
                tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                '''
                df_sectores= tenencia_clase_tabla.groupby('FundType').sum()
                df_sectores.reset_index(inplace=True)
                tabla= pd.concat([tenencia_clase_tabla,df_sectores], ignore_index=True)
                tabla['Nombre'] = tabla['Nombre'].fillna('Total')
                tabla['GEO']=tabla['GEO'].fillna('')
                tabla['FundType']=tabla['FundType'].fillna('')
                
                tabla= tabla.sort_values(['FundType'])
                tabla.reset_index(inplace=True)
                tabla['Participacion']= tabla['Valorizada']/total*100
                tabla= tabla.sort_values(['FundType','Participacion'])
                del(tabla['index'])
                tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
                tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                tabla.loc[tabla['Nombre'] == 'Total', :] = tabla.loc[tabla['Nombre'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                
                def tabla_tenencias_clase(tabla, cuenta, dirG):
                    fig = go.Figure(data=[go.Table(
                        columnwidth=[5,3.5,1.5,3,1.5],
                        header=dict(height = 30,
                                    values=['<b>NOMBRE</b>','<b>SECTOR GEO.</b>', '<b>TIPO</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                                    fill_color='#d7d8d6',
                                    line_color='darkslategray',
                                    align='center',
                                    font=dict(family='Arial', color='black', size=20)),
                        cells=dict(values=[tabla.Nombre,tabla.GEO, tabla.FundType, tabla.Valorizada, tabla.Participacion],
                                    fill_color=['#ffffff'],
                                    height=30,
                                    line_color='darkslategray',
                                    align=['center','center','center'],
                                    font=dict(family='Arial', color='black', size=18)))
                    ])
                    h=(len(tabla.index)+7.5)*cm
                    fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                        
                    fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',scale=1)
                         
                tabla_tenencias_clase(tabla, cuenta, dirG)
                
                def grafico_clase(tenencia_clase_tabla, cuenta, dirG):
                    df_sectores= tenencia_clase_tabla.groupby('GEO').sum()
                    df_sectores.reset_index(inplace=True)
                    df_sectores['Participacion']= df_sectores['Valorizada']/df_sectores['Valorizada'].sum() *100
                    
                    df_fundtype= tenencia_clase_tabla.groupby('FundType').sum()
                    df_fundtype.reset_index(inplace=True)
                    df_fundtype['Participacion']= df_fundtype['Valorizada']/df_fundtype['Valorizada'].sum() *100
                    
                    df_torta= tenencia_clase_tabla[['Nombre', 'Valorizada']].copy()
                    df_torta['Participacion']= df_torta['Valorizada']/df_torta['Valorizada'].sum() *100
                    suma_especies_chicas= df_torta[df_torta['Participacion'] < 1.5]['Valorizada'].sum()
                    if suma_especies_chicas !=0:
                        df_sin_especies_chicas= df_torta[df_torta['Participacion'] > 1.5]
                        df_otras_especies= pd.DataFrame({'Nombre':['Otras especies'],'Valorizada': [suma_especies_chicas], 'Participacion': [suma_especies_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                        df_torta= pd.concat([df_sin_especies_chicas, df_otras_especies])
                    df_torta= df_torta.sort_values('Participacion')
                    parameters = {'axes.labelsize': 20,
                            'axes.titlesize': 20}
                    plt.rcParams.update(parameters)
                    
                    fig = plt.figure(figsize=[20, 20])
                    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1], wspace=0.5)
                    
                    ax1 = fig.add_subplot(gs[0, 0])
                    ax2 = fig.add_subplot(gs[0, 1])
                    ax3 = fig.add_subplot(gs[1, :])
                    
                    pie_wedge_collection1 = ax1.pie(df_torta.Participacion,
                                            labels=df_torta.Nombre, 
                                            labeldistance=1.1,   
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection1[0]:
                        pie_wedge.set_edgecolor('white')
                    for label in pie_wedge_collection1[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                        if len(label.get_text()) >20:
                            label.set_text('\n'.join(textwrap.wrap(label.get_text(), 20)))
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax1.add_artist(centre_circle)
                    ax1.set_title(f'Distribución de la Cartera de {clase}', fontweight='bold')
                    
                    pie_wedge_collection = ax2.pie(df_sectores.Participacion,  labels=df_sectores.GEO, 
                                            labeldistance=1.1, 
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
                    for label in pie_wedge_collection[1]: # Dividir el texto en varias líneas si tiene más de 12 caracteres                            
                        if len(label.get_text()) > 12:
                            label.set_text('\n'.join(textwrap.wrap(label.get_text(), 12)))
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax2.add_artist(centre_circle)
                    ax2.set_title('Distribución por Sector Geográfico', fontweight='bold')
                    
                    pie_wedge_collection2 = ax3.pie(df_fundtype.Participacion,  labels=df_fundtype.FundType, 
                                            labeldistance=1.1, 
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection2[0]:
                        pie_wedge.set_edgecolor('white')
                    
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    ax3.add_artist(centre_circle)
                    ax3.set_title('Distribución por Tipo de Fondo', fontweight='bold')
                    
                    plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
                    plt.clf()
                grafico_clase(tenencia_clase_tabla, cuenta, dirG)
            else: #Categorias que no son acciones, ya sea bonos, fondos, opciones, etc.
                tenencia_clase_tabla= tenencia_clase_tabla[['Nombre_Especie','Valorizada']]
                tenencia_clase_tabla= tenencia_clase_tabla.groupby('Nombre_Especie').sum().reset_index(drop=False)

                total = tenencia_clase_tabla['Valorizada'].sum()
                total_row = pd.DataFrame({'Nombre_Especie': ['Total'], 'Valorizada': [total]})
                tabla = pd.concat([tenencia_clase_tabla, total_row], ignore_index=True)
                tabla['Participacion']= tabla['Valorizada']/total*100
                tabla= tabla.sort_values(['Participacion'])
                tabla['Participacion']= tabla['Participacion'].map('{:.2f}%'.format)
                tabla['Valorizada'] = tabla['Valorizada'].map('{:,.2f}'.format)
                tabla.loc[tabla['Nombre_Especie'] == 'Total', :] = tabla.loc[tabla['Nombre_Especie'] == 'Total', :].apply(lambda x: x.apply(lambda y: f"<b>{y}</b>"), axis=1)
                
                def tabla_tenencias_clase(tabla, cuenta, dirG):
                    fig = go.Figure(data=[go.Table(
                        columnwidth=[2.5, 1.2, 1],
                        header=dict(height = 30,
                                    values=['<b>NOMBRE</b>','<b>TENENCIA (U$S)</b>','<b>PART. %</b>'],
                                    fill_color='#d7d8d6',
                                    line_color='darkslategray',
                                    align='center',
                                    font=dict(family='Arial', color='black', size=20)),
                        cells=dict(values=[tabla.Nombre_Especie, tabla.Valorizada, tabla.Participacion],
                                    fill_color=['#ffffff'],
                                    height=30,
                                    line_color='darkslategray',
                                    align=['center','center','center'],
                                    font=dict(family='Arial', color='black', size=18)))
                    ])
                    h=(len(tabla.index)+7.5)*cm
                    fig.update_layout(width=1000,height=h,margin={'l': 5, 'r': 5, 't': 5, 'b': 5})
                        
                    fig.write_image(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png',scale=1)
                         
                tabla_tenencias_clase(tabla, cuenta, dirG)
                
                def grafico_clase(tenencia_clase_tabla, cuenta, dirG):
                    df_torta= tenencia_clase_tabla
                    df_torta['Participacion']= df_torta['Valorizada']/df_torta['Valorizada'].sum() *100
                    suma_especies_chicas= df_torta[df_torta['Participacion'] < 1.5]['Valorizada'].sum()
                    if suma_especies_chicas !=0:
                        df_sin_especies_chicas= df_torta[df_torta['Participacion'] > 1.5]
                        df_otras_especies= pd.DataFrame({'Nombre_Especie':['Otras especies'],'Valorizada': [suma_especies_chicas], 'Participacion': [suma_especies_chicas / tenencia_clase_tabla['Valorizada'].sum() * 100]})
                        df_torta= pd.concat([df_sin_especies_chicas, df_otras_especies])
                    df_torta= df_torta.sort_values('Participacion')
                    parameters = {'axes.labelsize': 20,
                            'axes.titlesize': 20}
                    plt.rcParams.update(parameters)
                    fig = plt.figure(figsize=[10, 10])
                    ax = fig.add_subplot(111)
                    
                    pie_wedge_collection = ax.pie(df_torta.Participacion,
                                            labels=df_torta.Nombre_Especie, 
                                            labeldistance=1.1,   
                                            autopct='%1.1f%%',
                                            pctdistance=0.8,
                                            textprops={'fontsize': 16})
                    for pie_wedge in pie_wedge_collection[0]:
                        pie_wedge.set_edgecolor('white')
            
                    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                    fig = plt.gcf()
                    fig.gca().add_artist(centre_circle)
                    ax.set_title(f'Distribución de la Cartera de {clase}', fontweight='bold')
                    plt.savefig(f'{dirG}\\torta {clase}-{cuenta}.png',bbox_inches='tight',edgecolor='w')
                    plt.clf()
                grafico_clase(tenencia_clase_tabla, cuenta, dirG)
        #Comenzamos a hacer el PDF
        while True:
            reporte_largo_corto= int(input("Presione 1 si quiere el reporte resumido, 2 si quiere el informe detallado: "))
            if reporte_largo_corto==1:
                short= True
                break
            if reporte_largo_corto==2:
                short=False
                break
            else:
                print("No ha ingresado un número correcto, intente denuevo. ")
            
        def hacer_pdf(cuenta, clases, short, dir, dirG):
            for file in os.listdir(): #Esto borrará los archivos viejos, para que cada vez que se ejecute el programa aparezcan en carpeta los gráficos que se quieren descargar
                if file.endswith('.pdf'):
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f'Error deleting {file}: {e}')
                
            pdf=canvas.Canvas(f'{dir}\\Reporte - {cuenta}.pdf',pagesize=A4)
            w, h = A4
            
            
            '''#Imagen
            pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
            #Titulo
            pdf.setTitle('Reporte comitente')
            pdf.setFillColor('Black')
            pdf.setFont('Helvetica-Bold',24)
            pdf.drawString(1*cm,27.4*cm,f'Resumen de Tenencia {cuenta}')
            #Linea horizontal
            pdf.line(1*cm,27*cm,A4[0] -1*cm,27*cm)
            #Fecha abajo
            today = time.strftime("%d/%m/%Y")
            pdf.setFont('Helvetica',14)
            pdf.setFillColor("Gray")
            pdf.drawString(1*cm,26.4*cm,f'{today}')
            
            
            
            filepath= f'{dirG}\\tabla cuenta corriente - {cuenta}.png'
            corriente= PIL.Image.open(filepath)
            corrienteh= corriente.height/(1*cm)
            corrientew= corriente.width/(1*cm)
            corrienteasp= corrientew/corrienteh
            corrienteh= 19/corrienteasp
            
            filepath= f'{dirG}\\tabla tenencias negativas - {cuenta}.png'
            negativa= PIL.Image.open(filepath)
            negativah= negativa.height/(1*cm)
            negativaw= negativa.width/(1*cm)
            negativaasp= negativaw/negativah
            negativah= 19/negativaasp
            
            
            pdf.setFillColor("Darkgreen")
            pdf.setFont('Helvetica',18)
            pdf.drawString(1*cm,18*cm,'Tenencia Cta. Corriente')
            pdf.drawInlineImage(f'{dirG}\\tabla cuenta corriente - {cuenta}.png', 1*cm, 17.5*cm-corrienteh*cm, width=19*cm, height=corrienteh*cm, preserveAspectRatio=True)
            
            pdf.setFillColor("Darkgreen")
            pdf.setFont('Helvetica',18)
            pdf.drawString(1*cm,12*cm,'Tenencias Negativas')
            pdf.drawInlineImage(f'{dirG}\\tabla tenencias negativas - {cuenta}.png', 1*cm, 11.5*cm-negativah*cm, width=19*cm, height=negativah*cm, preserveAspectRatio=True)
            
            pdf.showPage()
            '''
            pdf.setTitle('Reporte comitente')
            pdf.setFillColor('Black')
            pdf.setFont('Helvetica-Bold',20)
            pdf.drawString(1*cm,27.2*cm,f'Resumen de Tenencia {cuenta}')
            pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
            pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
            today = time.strftime("%d/%m/%Y")
            pdf.setFont('Helvetica',14)
            pdf.setFillColor("Gray")
            pdf.drawString(14*cm,27.2*cm,f'TC: {CCL:.2f}       {today}')
            
            filepath = f'{dirG}\\tabla activos - {cuenta}.png'
            primera = PIL.Image.open(filepath)
            primerah= primera.height/(1*cm)
            primeraw= primera.width/(1*cm)
            primeraasp= primeraw/primerah
            primerah= 19/primeraasp
            
            filepath = f'{dirG}\\tabla moneda - {cuenta}.png'
            segunda = PIL.Image.open(filepath)
            segundah=segunda.height/(1*cm)
            segundaw= segunda.width/(1*cm)
            segundaasp= segundaw/segundah
            segundah= 19/segundaasp
            
            filepath = f'{dirG}\\torta General {cuenta}.png'
            tercera= PIL.Image.open(filepath)
            tercerah= tercera.height/(1*cm)
            terceraw= tercera.width/(1*cm)
            terceraasp= terceraw/tercerah
            tercerah= 19/terceraasp
            
            filepath= f'{dirG}\\tabla total - {cuenta}.png'
            totales= PIL.Image.open(filepath)
            totalesh= totales.height/(1*cm)
            totalesw= totales.width/(1*cm)
            totalesasp= totalesw/totalesh
            totalesh= 19/totalesasp
            '''filepath= f'{dirG}\\barra moneda - {cuenta}.png'
            cuarta= PIL.Image.open(filepath)
            cuartah= cuarta.height/(1*cm)
            cuartaw= cuarta.width/(1*cm)
            cuartaasp= cuartaw/cuartah
            cuartah= 19/cuartaasp'''
            pdf.setFillColor("Darkgreen")
            pdf.setFont('Helvetica',18)
            pdf.drawString(1*cm,26*cm,'Tenencia Total')
            pdf.drawInlineImage(f'{dirG}\\tabla total - {cuenta}.png', 1*cm, 25.5*cm-totalesh*cm, width=19*cm, height=totalesh*cm, preserveAspectRatio=True)
            
            #Escribimos titulos e insertamos graficos
            pdf.setFillColor("Darkgreen")
            pdf.setFont('Helvetica',18)
            pdf.drawString(1*cm,24*cm-totalesh*cm,'Resumen de ACTIVOS')
            pdf.drawInlineImage(f'{dirG}\\tabla activos - {cuenta}.png', 1*cm, 23.5*cm-totalesh*cm-primerah*cm, width=19*cm, height=primerah*cm, preserveAspectRatio=True)
            pdf.drawInlineImage(f'{dirG}\\torta General {cuenta}.png', 1*cm, 23*cm-totalesh*cm-primerah*cm-tercerah*cm, width=19*cm, height= tercerah*cm, preserveAspectRatio=True)
            pdf.drawString(1*cm,22.5*cm-totalesh*cm-primerah*cm-tercerah*cm,'Resumen de MONEDA')
            pdf.drawInlineImage(f'{dirG}\\tabla moneda - {cuenta}.png', 1*cm, 22*cm-totalesh*cm-primerah*cm-tercerah*cm-segundah*cm, width=19*cm, height= segundah*cm, preserveAspectRatio=True)
            
            #pdf.drawInlineImage(f'{dirG}\\barra moneda - {cuenta}.png', (10.5-9/2)*cm, (-3.5*cm), width=9*cm, height= cuartah*cm,preserveAspectRatio=True)
            pdf.showPage()
            
            #A partir de aqui comenzamos con el detalle de cada especie.
            for clase in clases:
                pdf.setTitle('Reporte comitente')
                pdf.setFillColor('Black')
                pdf.setFont('Helvetica-Bold',20)
                pdf.drawString(1*cm,27.2*cm,f'Resumen de Tenencia {cuenta} - {clase}')
                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                
                filepath = f'{dirG}\\tabla tenencia {clase} - {cuenta}.png'
                compo = PIL.Image.open(filepath)
                compoh= compo.height/(1*cm)
                compow= compo.width/(1*cm)
                compoasp= compow/compoh
                compoh= 19/compoasp #Vamos a fijar el ancho en 19 cm, asi ocupa el ancho total de la pagina dejando un poco de margen.
                #print(f'height compo {cuenta}-{clase}= {compoh}')
                #print(f'width compo {cuenta}-{clase}= {compow}')
                
                filepath = f'{dirG}\\torta {clase}-{cuenta}.png'
                torta = PIL.Image.open(filepath)
                tortah= torta.height/(1*cm)
                tortaw= torta.width/(1*cm)
                tortaasp= tortaw/tortah
                tortah= 19/tortaasp
                #print(f'height torta {cuenta}-{clase}= {tortah}')
                #print(f'width torta {cuenta}-{clase}= {tortaw}')
                
                total_height = compoh + tortah + 3.7 #esto es todo lo que entra en la hoja A4, seria la tabla mas los graficos mas el espacio hasta arriba
                w, h = A4
                #print(f'total height {cuenta}-{clase}= {total_height}')
                #print(f'height A4= {h/(1*cm)}')
                if total_height > h/(1*cm): #Aca tengo dos casos, uno es que entre bien la tabla en la hoja, y otro donde sea tan grande que tenga que ajustar la altura para que entre en la hoja (PROVISORIO)
                    if compoh> 25.5:
                        compow= compoasp*(25.5)
                        pdf.drawImage(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png', (10.5-compow/2)*cm, 26*cm-25.5*cm, height=25.5*cm, width=compow*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    else:
                        pdf.drawImage(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png', 1*cm, 26*cm-1*compoh*cm, height=1*compoh*cm, preserveAspectRatio=True, mask='auto',anchor='nw')
                    
                    #Si es muy grande la tabla tal que ocupa toda la pagina, pego los graficos de torta en hoja nueva (PROVISORIO HASTA HACER QUE SE CORTE EN DOS LA FOTO, EN LA FUNCION QUE CREA LA IMAGEN DE LA TABLA)
                    pdf.showPage()
                    
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, f'Resumen de Tenencia {cuenta} - {clase}')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    pdf.drawInlineImage(f'{dirG}\\torta {clase}-{cuenta}.png',1*cm, 25*cm-tortah*cm, width=19*cm,height= tortah*cm,preserveAspectRatio=True)
                    
                    pdf.showPage()
                else:
                    tortah= 19/tortaasp
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, f'Resumen de Tenencia {cuenta} - {clase}')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    pdf.drawInlineImage(f'{dirG}\\tabla tenencia {clase} - {cuenta}.png', 1*cm, 26*cm-compoh*cm, width=19*cm, height=compoh*cm, preserveAspectRatio=True)
                    pdf.drawImage(f'{dirG}\\torta {clase}-{cuenta}.png',(10.5-19/2)*cm, 25*cm-compoh*cm-1*tortah*cm, width=19*cm, height=tortah*cm, preserveAspectRatio=True)
                    
                    pdf.showPage()
                if short== True:
                    pass
                
                else:
                    if clase in ['Renta Variable Local', 'Renta Variable Extranjera']: #Insertamos en una nueva página la información financiera de las especies de renta variable
                        pdf.setTitle('Reporte comitente')
                        pdf.setFillColor('Black')
                        pdf.setFont('Helvetica-Bold',20)
                        pdf.drawString(1*cm,27.2*cm, f'Información Financiera - {clase}')
                        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                        
                        filepath = f'{dirG}\\tabla info financiera {clase}- {cuenta}.png'
                        compo = PIL.Image.open(filepath)
                        compoh= compo.height/(1*cm)
                        compow= compo.width/(1*cm)
                        compoasp= compow/compoh
                        compoh= 19/compoasp
                        
                        filepath = f'{dirG}\\total info financiera {clase} - {cuenta}.png'
                        general = PIL.Image.open(filepath)
                        generalh= general.height/(1*cm)
                        generalw= general.width/(1*cm)
                        generalasp= generalw/generalh
                        generalh= 19/generalasp
                        
                        totalh= compoh + generalh
                        if totalh > 25.5: #Aca tengo dos casos, uno es que entre bien la tabla en la hoja, y otro donde sea tan grande que tenga que ajustar la altura para que entre en la hoja (PROVISORIO)
                            if compoh> 25.5:
                                compow= compoasp*(25.5)
                                pdf.drawImage(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png', (10.5-compow/2)*cm, 26*cm-25.5*cm, height=25.5*cm, width=compow*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                            else:
                                pdf.drawImage(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png', 1*cm, 26*cm-1*compoh*cm, height=1*compoh*cm, preserveAspectRatio=True, mask='auto',anchor='nw')
                            pdf.showPage()
                            #Insertamos en una nueva página la tabla de información financiera total si es que no entran ambas en una misma pág.
                            pdf.setTitle('Reporte comitente')
                            pdf.setFillColor('Black')
                            pdf.setFont('Helvetica-Bold',20)
                            pdf.drawString(1*cm,27.2*cm, f'Información Financiera - {clase}')
                            pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                            pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                            pdf.drawImage(f'{dirG}\\total info financiera {clase} - {cuenta}.png', 1*cm, 26*cm-1*generalh*cm, height=generalh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                            pdf.showPage()
                        else:
                            pdf.drawImage(f'{dirG}\\tabla info financiera {clase}- {cuenta}.png', 1*cm, 26*cm-1*compoh*cm, height=compoh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                            pdf.drawImage(f'{dirG}\\total info financiera {clase} - {cuenta}.png', 1*cm, 25.5*cm-1*compoh*cm-1*generalh*cm, height=generalh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')                
                            pdf.showPage()
                           
                        pdf.setTitle('Reporte comitente')
                        pdf.setFillColor('Black')
                        pdf.setFont('Helvetica-Bold',20)
                        pdf.drawString(1*cm,27.2*cm, f'Performance - {clase}')
                        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                        
                        filepath= f'{dirG}\\performance {clase} - {cuenta}.png'
                        performance= PIL.Image.open(filepath)
                        performanceh= performance.height/(1*cm)
                        #print(f'la altura de la tabla performance {clase} es {performanceh}')
                        performancew= performance.width/(1*cm)
                        performanceasp= performancew/performanceh
                        if performanceh > 53:
                            performancew= performanceasp*26
                            pdf.drawImage(f'{dirG}\\performance {clase} - {cuenta}.png', (10.5-performancew/2)*cm, 0*cm, height=26*cm, width=performancew*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                        else:
                            performanceh= 19/performanceasp
                            pdf.drawImage(f'{dirG}\\performance {clase} - {cuenta}.png', 1*cm, 26*cm-1*performanceh*cm, height=performanceh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        pdf.showPage()
                        if pprom=='2':
                            try:
                                #Rendimientos, cómo venimos con nuestras inversiones? Arriba abajo? En qué %?
                                pdf.setTitle('Reporte comitente')
                                pdf.setFillColor('Black')
                                pdf.setFont('Helvetica-Bold',20)
                                pdf.drawString(1*cm,27.2*cm, f'Rendimientos - {clase}')
                                pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                                pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                                
                                filepath= f'{dirG}\\tabla rendimientos {clase} - {cuenta}.png'
                                rendimientos= PIL.Image.open(filepath)
                                rendimientosh= rendimientos.height/(1*cm)
                                #print(f'la altura de la tabla performance {clase} es {performanceh}')
                                rendimientosw= rendimientos.width/(1*cm)
                                rendimientosasp= rendimientosw/rendimientosh
                                if rendimientosh > 53:
                                    rendimientosw= rendimientosasp*26
                                    pdf.drawImage(f'{dirG}\\tabla rendimientos {clase} - {cuenta}.png', (10.5-rendimientosw/2)*cm, 0*cm, height=26*cm, width=rendimientosw*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                                else:
                                    rendimientosh= 19/rendimientosasp
                                    pdf.drawImage(f'{dirG}\\tabla rendimientos {clase} - {cuenta}.png', 1*cm, 26*cm-1*rendimientosh*cm, height=rendimientosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                                pdf.showPage()
                            except:
                                pass
                        if clase == 'Renta Variable Extranjera' and calcular_g=='2':
                            pdf.setTitle('Reporte comitente')
                            pdf.setFillColor('Black')
                            pdf.setFont('Helvetica-Bold',20)
                            pdf.drawString(1*cm,27.2*cm, f'Crecimiento - {clase}')
                            pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                            pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                            
                            filepath= (f'{dirG}\\growth {clase} - {cuenta}.png')
                            crecimiento= PIL.Image.open(filepath)
                            crecimientoh= crecimiento.height/(1*cm)
                            crecimientow= crecimiento.width/(1*cm)
                            crecimientoasp= crecimientow/crecimientoh
                            pdf.drawImage(f'{dirG}\\growth {clase} - {cuenta}.png', 1*cm, 26*cm-1*crecimientoh*cm, height=crecimientoh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                            pdf.showPage()
            #Insertamos la información de los bonos que tiene cada cliente, si es que tiene bonos en cuenta.
            if short== True:
                pdf.save()
            
            else:     
                if all(cls in clases for cls in ['Renta Fija Local', 'Renta Fija Extranjera']):
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    pdf.setFillColor("Darkgreen")
                    pdf.setFont('Helvetica',18)
                    pdf.drawString(1*cm,26*cm,'Resumen de Renta Fija Local')
                    filepath= f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png'
                    locales= PIL.Image.open(filepath)
                    localesh= locales.height/(1*cm)
                    localesw= locales.width/(1*cm)
                    localesasp= localesw/localesh
                    localesh= 19/localesasp
                    pdf.drawImage(f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png', 1*cm, 25.5*cm-1*localesh*cm, height=localesh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                    
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    pdf.setFillColor("Darkgreen")
                    pdf.setFont('Helvetica',18)
                    pdf.drawString(1*cm,26*cm,'Resumen de Renta Fija Extranjera')
                    filepath= f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png'
                    extranjeros= PIL.Image.open(filepath)
                    extranjerosh= extranjeros.height/(1*cm)
                    extranjerosw= extranjeros.width/(1*cm)
                    extranjerosasp= extranjerosw/extranjerosh
                    extranjerosh= 19/extranjerosasp
                    pdf.drawImage(f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png', 1*cm, 25.5*cm-1*extranjerosh*cm, height=extranjerosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                    
                elif 'Renta Fija Local' in clases:
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    pdf.setFillColor("Darkgreen")
                    pdf.setFont('Helvetica',18)
                    pdf.drawString(1*cm,26*cm,'Resumen de Renta Fija Local')
                    filepath= f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png'
                    locales= PIL.Image.open(filepath)
                    localesh= locales.height/(1*cm)
                    localesw= locales.width/(1*cm)
                    localesasp= localesw/localesh
                    localesh= 19/localesasp
                    pdf.drawImage(f'{dirG}\\info bonos Renta Fija Local - {cuenta}.png', 1*cm, 25.5*cm-1*localesh*cm, height=localesh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                    if pprom=='2':
                        try:
                            #Rendimientos, cómo venimos con nuestras inversiones? Arriba abajo? En qué %?
                            pdf.setTitle('Reporte comitente')
                            pdf.setFillColor('Black')
                            pdf.setFont('Helvetica-Bold',20)
                            pdf.drawString(1*cm,27.2*cm, f'Rendimientos - Renta Fija Local')
                            pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                            pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                            
                            filepath= f'{dirG}\\tabla rendimientos Renta Fija Local - {cuenta}.png'
                            rendimientos= PIL.Image.open(filepath)
                            rendimientosh= rendimientos.height/(1*cm)
                            #print(f'la altura de la tabla performance {clase} es {performanceh}')
                            rendimientosw= rendimientos.width/(1*cm)
                            rendimientosasp= rendimientosw/rendimientosh
                            if rendimientosh > 53:
                                rendimientosw= rendimientosasp*26
                                pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Local - {cuenta}.png', (10.5-rendimientosw/2)*cm, 0*cm, height=26*cm, width=rendimientosw*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                            else:
                                rendimientosh= 19/rendimientosasp
                                pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Local - {cuenta}.png', 1*cm, 26*cm-1*rendimientosh*cm, height=rendimientosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                            pdf.showPage()
                        except:
                            pass
                elif 'Renta Fija Extranjera' in clases:
                    pdf.setTitle('Reporte comitente')
                    pdf.setFillColor('Black')
                    pdf.setFont('Helvetica-Bold',20)
                    pdf.drawString(1*cm,27.2*cm, 'Información sobre Renta Fija')
                    pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                    pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                    
                    pdf.drawString(1*cm,25.5*cm,'Resumen de Renta Fija Extranjera')
                    filepath= f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png'
                    extranjeros= PIL.Image.open(filepath)
                    extranjerosh= extranjeros.height/(1*cm)
                    extranjerosw= extranjeros.width/(1*cm)
                    extranjerosasp= extranjerosw/extranjerosh
                    extranjerosh= 19/extranjerosasp
                    pdf.drawImage(f'{dirG}\\info bonos Renta Fija Extranjera - {cuenta}.png', 1*cm, 25*cm-1*extranjerosh*cm, height=extranjerosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                    pdf.showPage()
                    if pprom=='2': 
                        #Rendimientos, cómo venimos con nuestras inversiones? Arriba abajo? En qué %?
                        pdf.setTitle('Reporte comitente')
                        pdf.setFillColor('Black')
                        pdf.setFont('Helvetica-Bold',20)
                        pdf.drawString(1*cm,27.2*cm, f'Rendimientos - Renta Fija Extranjera')
                        pdf.drawInlineImage('LOGO TRUCCO.png',14*cm,28*cm,width=6*cm, height= 1.5*cm)
                        pdf.line(1*cm,26.8*cm,A4[0] -1*cm,26.8*cm)
                        
                        filepath= f'{dirG}\\tabla rendimientos Renta Fija Extranjera - {cuenta}.png'
                        rendimientos= PIL.Image.open(filepath)
                        rendimientosh= rendimientos.height/(1*cm)
                        #print(f'la altura de la tabla performance {clase} es {performanceh}')
                        rendimientosw= rendimientos.width/(1*cm)
                        rendimientosasp= rendimientosw/rendimientosh
                        if rendimientosh > 53:
                            rendimientosw= rendimientosasp*26
                            pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Extranjera - {cuenta}.png', (10.5-rendimientosw/2)*cm, 0*cm, height=26*cm, width=rendimientosw*cm, preserveAspectRatio=True, mask='auto', anchor='nw')    
                        else:
                            rendimientosh= 19/rendimientosasp
                            pdf.drawImage(f'{dirG}\\tabla rendimientos Renta Fija Extranjera - {cuenta}.png', 1*cm, 26*cm-1*rendimientosh*cm, height=rendimientosh*cm, width=19*cm, preserveAspectRatio=True, mask='auto', anchor='nw')
                        pdf.showPage()
                pdf.save()
        hacer_pdf(cuenta,clases, short ,dir, dirG)
        
        while True:
            mandar_mails= input("Desea mandarle por mail el reporte al cliente? Presione 1 si desea evitarlo, 2 si quiere computarlo: ")
            if mandar_mails in ('1', '2'):
                break
            else:
                print("Opción no válida. Por favor, ingrese 1 o 2.")
        if mandar_mails== '2':
            excel_mails= pd.read_excel('mails.xlsx')
            mail= excel_mails[excel_mails['CTA']==cuenta]['Mail'].iloc[0]
            def mandar_mails(cuenta, dir, mail):
                email = 'ldtbrokers@gmail.com'
                password = 'bmwa yvls guko ehhx'
                send_to_email = mail
                subject = f'Reporte Tenencia del Comitente {cuenta}'
                message = 'Estimado cliente, en el archivo adjunto encontrará el reporte de sus tenencias valorizadas en dólares al día de la fecha'
                file_location = f'{dir}\\Reporte - {cuenta}.pdf'
                
                msg = MIMEMultipart()
                msg['From'] = email
                msg['To'] = send_to_email
                msg['Subject'] = subject
        
                msg.attach(MIMEText(message, 'plain'))
        
                # Setup the attachment
                filename = os.path.basename(file_location)
                attachment = open(file_location, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        
                # Attach the attachment to the MIMEMultipart object
                msg.attach(part)
        
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email, password)
                text = msg.as_string()
                server.sendmail(email, send_to_email, text)
                server.quit()
            try:
                mandar_mails(cuenta, dir, mail)
            except Exception as e:
                print(e)
                pass
        os.startfile(f'{dir}\\Reporte - {cuenta}.pdf')    
        
             