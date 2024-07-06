"""
Julián Zenteno S.

The idea of this work is to construct a sample of the price of stocks in high social unrest (SU) events.
"""

# Call the packages to use
import pandas as pd
import refinitiv.data as rd

# Open the session in Refinitiv - Necessary to download data
rd.open_session()

# Import the data
DF = pd.read_csv("Panel_ESG.csv")
SU = pd.read_csv("EI.csv")

# Filter US stocks
DF = DF[DF['ISSUER_CNTRY_DOMICILE'] != 'US']

# Subset the important variables
DF = DF[['ISSUER_TICKER', 'ISSUER_ISIN', 'ISSUER_CNTRY_DOMICILE', 'AS_OF_DATE', 'SOCIAL_PILLAR_SCORE']]

# Rename the variables
DF.rename(columns={'AS_OF_DATE': 'Date', 'ISSUER_TICKER':'Ticker', 'ISSUER_ISIN':'ISIN', 'ISSUER_CNTRY_DOMICILE':'Cntry', 'SOCIAL_PILLAR_SCORE':'Social'}, inplace=True)

# Filter the missing values
DF = DF.dropna(subset=['ISIN', 'Social', 'Cntry', 'Date'])

# Change the date format
DF['Date'] = pd.to_datetime(DF['Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
DF['Date'] = pd.to_datetime(DF['Date'])

# Define the events list
SU['Event'] = SU['Date'] + '_' + SU['Pais_A2']

# Select the important variables
SU = SU[['Date', 'Pais_A2', 'Event']]

# Define 'Date' column to datetime format
SU['Date'] = pd.to_datetime(SU['Date'])

# Rename the variables
SU.rename(columns={'Pais_A2':'Cntry'}, inplace=True)

# Filter US events
SU = SU[SU['Cntry'] != 'US']

# Define the sample window
SU['SDate'] = SU['Date'] - pd.DateOffset(months=3)
SU['EDate'] = SU['Date'] + pd.DateOffset(months=3)

# Create a data frame for the results
DF_Final = []

# Loop on the events in order to construct the long data frame
for index, row in SU.iterrows():
    Cntry = row['Cntry'] 
    SDate = row['SDate']
    EDate = row['EDate']
    Event = row['Event']
    Ev_Date = row['Date']

    DF_i = DF[(DF['Cntry'] == Cntry) & (DF['Date'] >= SDate) & (DF['Date'] <= EDate)]

    DF_i['Event'] = Event
    DF_i['SDate'] = SDate
    DF_i['EDate'] = EDate
    DF_i['Ev_Date'] = Ev_Date

    DF_Final.append(DF_i)
    del DF_i

# Concat the individual results
DF_Final = pd.concat(DF_Final, ignore_index=True)

# Events differences
dif_ev = set(SU['Event'].unique()) - set(DF_Final['Event'].unique())

"""
There are 86 missing events. 73 are before 2007. Of the 13 events in 2007 or after, five occur in Kuwait.
"""

# Filter the events with MSCI data
SU = SU[~SU['Event'].isin(dif_ev)]

# Define Social dummy
DF_Final['Social_Dummy'] = DF_Final['Social'].apply(lambda x: 1 if pd.notna(x) and x != '' else 0)

# Delete the unusefull objects
del Ev_Date, DF, Cntry, EDate, SDate, Event, index, row, SU, dif_ev

############################### Price download ################################

# Rename the DF
DF = DF_Final

# Delete the old DF
del DF_Final

# Create a list with the events
Eventos = DF['Event'].unique().tolist()

# Define a auxiliary data frame
DF_aux = pd.DataFrame()

# For each event download the price of the stocks involved
for evento in Eventos:
    
    DF_i = DF[DF['Event'] == evento] # Select the event
    tickers = DF_i['ISIN'].unique().tolist() # Create a list with the firms' ISIN to download their prices
    SDate = pd.to_datetime(DF_i['SDate'].min()).strftime('%Y-%m-%d') # Define the start date of the event
    EDate = pd.to_datetime(DF_i['EDate'].max()).strftime('%Y-%m-%d') # Define the end date of the event
    
    try:
        # download the prices
        data = rd.get_history(tickers, fields=['TR.ClosePrice'], interval="1D", start=SDate, end=EDate)
        
        # check the download and reformat the data frame
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
    # Notify if the download does not work
    except Exception as e:
        print(f"Error with: {e}")
        continue
    
    if not data.empty:
        
        data_cleaned = data.dropna(axis=1, how='all') # Filter the missing values
        del data # Delete the used data
        tickers_finales = data_cleaned.columns.tolist() # Create a list with the successful tickers

        # Create the date variable
        data_cleaned.reset_index(inplace=True)
        data_cleaned.reset_index(drop=True, inplace=True)
        data_cleaned.rename(columns={'index': 'Date'}, inplace=True)
        
        if tickers_finales:
            
            data_long = pd.melt(data_cleaned, id_vars=['Date'], value_vars=tickers_finales, var_name='ISIN', value_name='Price') # Create the long DF with the necessary variables
            data_long['Event'] = evento # Add the event variable
            DF_aux = pd.concat([DF_aux, data_long], ignore_index=True) # Save the data
            del data_cleaned, data_long  # Delete the used data
    
del DF_i, EDate, SDate, evento, Eventos, tickers, tickers_finales

# Create an auxiliary variable
DF['aux'] = DF['ISIN'] + '_' + DF['Date'].dt.strftime('%Y-%m')
DF_aux['aux'] = DF_aux['ISIN'] + '_' + DF_aux['Date'].dt.strftime('%Y-%m')

################################# Merge the data ##############################

# Variables to merge
variables = ['Ticker', 'Cntry', 'Social', 'Ev_Date']

# Create a dictionary for each variable and then map to the base data frame
for var in variables:
    DF_aux[var] = DF['aux'].map(DF.set_index('aux')[var].to_dict())
    
# Rename the data frame
DF = DF_aux

# Delete the aux data frame
del var, variables, DF_aux

# Save the data frame as a csv document
DF.to_csv('DF_Social.csv', index=False)

# Delete all
del DF

###############################################################################
# If the previous work has already been done, there is the option to start from here
######################## Creation of the full data frame ######################

# Package to be used
import numpy as np

# Reimport the data
DF = pd.read_csv("DF_Social.csv")
DF_FULL = pd.read_csv("DF_FINAL.csv")

# Rename and redefine variables
DF.rename(columns={'Price': 'StockP', 'Ev_Date' : 'EDate', 'Cntry' : 'Pais'}, inplace=True)
DF['Event'] = DF['Pais'] + '_' + DF['EDate']

# Check date format
DF['Date'] = pd.to_datetime(DF['Date'])
DF_FULL['Date'] = pd.to_datetime(DF_FULL['Date'])

# Create an auxiliary variable
DF['aux'] = DF['ISIN'] + '_' + DF['Date'].dt.strftime('%Y-%m-%d') + '_' + DF['Event']
DF_FULL['aux'] = DF_FULL['ISIN'] + '_' + DF_FULL['Date'].dt.strftime('%Y-%m-%d') + '_' + DF_FULL['Event']

# Create a serie of the auxilar variable
DF_FINAL = pd.concat([DF['aux'], DF_FULL['aux']])

# Delete dupllicate auxiliary observations
DF_FINAL = DF_FINAL.drop_duplicates().reset_index(drop=True)

# Create the new df
DF_FINAL = pd.DataFrame(DF_FINAL, columns=['aux'])

# List of the variable to merge
variables = ['Date', 'StockP', 'Event', 'EDate', 'Pais', 'Ticker', 'ISIN']

# Loop on the varibles to merge them
for var in variables:
    # Creat the dictionary
    aux_to_var = pd.concat([DF[['aux', var]], DF_FULL[['aux', var]]]).drop_duplicates().set_index('aux')[var].to_dict()
    
    # Map the values
    DF_FINAL[var] = DF_FINAL['aux'].map(aux_to_var)
    
# Merge social score
aux = DF[['aux', 'Social']].drop_duplicates().set_index('aux')['Social'].to_dict()
DF_FINAL['Social'] = DF_FINAL['aux'].map(aux)

# Merge Local MI
DF_FULL['aux'] = DF_FULL['Pais'] + '_' + DF_FULL['Date'].dt.strftime('%Y-%m-%d')
DF_FINAL['aux'] = DF_FINAL['Pais'] + '_' + DF_FINAL['Date'].dt.strftime('%Y-%m-%d')
aux = DF_FULL[['aux', 'LMI']].drop_duplicates().set_index('aux')['LMI'].to_dict()
DF_FINAL['LMI'] = DF_FINAL['aux'].map(aux)

# Merge World MI
aux = DF_FULL[['Date', 'WMI']].drop_duplicates().set_index('Date')['WMI'].to_dict()
DF_FINAL['WMI'] = DF_FINAL['Date'].map(aux)

# Drop auxiliary variable
DF = DF_FINAL.drop(columns=['aux'])

# Save the data frame as a csv document
DF.to_csv('DF_FULL.csv', index=False)

del aux_to_var, DF_FINAL, DF_FULL, var, variables, aux, DF

###############################################################################
# If the previous work has already been done, there is the option to start from here
################################# Social Score ################################ 

# Load the data
DF = pd.read_csv("DF_FULL.csv")
Social = pd.read_csv("Panel_ESG.csv")

# Filter US stocks
Social = Social[Social['ISSUER_CNTRY_DOMICILE'] != 'US']

# Subset the importent variables
Social = Social[['ISSUER_TICKER', 'ISSUER_ISIN', 'ISSUER_CNTRY_DOMICILE', 'AS_OF_DATE', 'SOCIAL_PILLAR_SCORE']]

# Rename the variables
Social.rename(columns={'AS_OF_DATE': 'Date', 'ISSUER_TICKER':'Ticker', 'ISSUER_ISIN':'ISIN', 'ISSUER_CNTRY_DOMICILE':'Cntry', 'SOCIAL_PILLAR_SCORE':'Social'}, inplace=True)

# Filter the missing values
Social = Social.dropna(subset=['ISIN', 'Social', 'Cntry', 'Date'])

# Change the date format
DF['Date'] = pd.to_datetime(DF['Date'])
Social['Date'] = pd.to_datetime(Social['Date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
Social['Date'] = pd.to_datetime(Social['Date'])

# Create an auxiliary varible
DF['aux'] = DF['ISIN'] + '_' + DF['Date'].dt.strftime('%Y-%m')
Social['aux'] = Social['ISIN'] + '_' + Social['Date'].dt.strftime('%Y-%m')

# Merge Social
aux = Social[['aux', 'Social']].drop_duplicates().set_index('aux')['Social'].to_dict()
DF['Social'] = DF['aux'].map(aux)

# Drop auxiliary variable
DF = DF.drop(columns=['aux'])

# Save the data frame as a csv document
DF.to_csv('DF_FULL.csv', index=False)

# delet unuseful variables
del aux, Social, DF

###############################################################################
# If the previous work has already been done, there is the option to start from here
################################ Barret et al. ################################ 

# Load the new data
DF = pd.read_csv("DF_FULL.csv")

# Make sure about the Date format
DF['Date'] = pd.to_datetime(DF['Date'])
DF['EDate'] = pd.to_datetime(DF['EDate'])

# Define an Index variable
DF['Index'] = DF['Event'] + '_' + DF['ISIN']

# Calculate R_i, R_lm, R_wm
DF['R_i'] = np.log(DF.groupby('Index')['StockP'].transform(lambda x: x / x.shift(1)))
DF['R_lm'] = np.log(DF.groupby('Index')['LMI'].transform(lambda x: x / x.shift(1)))
DF['R_wm'] = np.log(DF.groupby('Index')['WMI'].transform(lambda x: x / x.shift(1)))

# Winsorization of the 0.5% atypical extreme returns
DF['R_i'] = np.where(DF['R_i'] < DF['R_i'].quantile(0.0025), DF['R_i'].quantile(0.0025), np.where(DF['R_i'] > DF['R_i'].quantile(0.9975), DF['R_i'].quantile(0.9975), DF['R_i']))

# Correction the Na to zero
DF[['R_i', 'R_lm', 'R_wm']] = DF[['R_i', 'R_lm', 'R_wm']].fillna(0)

# Measure the difference in days between the day t and the event s
DF['dif_days'] = (DF['Date'] - DF['EDate']).dt.days

# Make sure of the sample window
DF = DF[(DF['dif_days'] >= -90) & (DF['dif_days'] <= 90)]

# Calculate mean(R_i) during the estimation window
DF['R_im'] = DF['Index'].map(DF[(DF['dif_days'] <= -10) & (DF['dif_days'] >= -50)].groupby('Index')['R_i'].mean())

# Drop auxiliary variable
DF = DF.drop(columns=['Index'])

# Save the data frame as a csv document
DF.to_csv('DF_FULL.csv', index=False)

# Clean the ambient
del DF

###############################################################################
# If the previous work has already been done, there is the option to start from here
################################### Industry ################################## 

# Load the data
DF = pd.read_csv("DF_FULL.csv")

# Create a list with each ISIN code (stock)
ISIN = DF[['ISIN', 'Pais']].drop_duplicates()

# Creat a lis with each country
pais = ISIN['Pais'].unique().tolist()

# Create a data frame for the results
DF_INDS = pd.DataFrame()

# Loop on every country to download the firm's industry in the country 'i
for i in pais:
    aux = ISIN[ISIN['Pais'] == i]
    aux = aux['ISIN'].unique().tolist()
    data = rd.get_data(aux, fields=['TR.TRBCIndustryGroup'])
    DF_INDS = pd.concat([DF_INDS, data], ignore_index=True)
    del aux, data

# Rename the columns
DF_INDS.rename(columns={'Instrument': 'ISIN', 'TRBC Industry Group Name':'Industry'}, inplace=True)

# Assign the industry to every stock
DF['Industry'] = DF['ISIN'].map(DF_INDS.set_index('ISIN')['Industry'].to_dict())

del i, ISIN, pais, DF_INDS

# Save the data frame as a csv document
DF.to_csv('DF_FULL.csv', index=False)

del DF

###############################################################################
# If the previous work has already been done, there is the option to start from here
################################ Event Study ##################################

DF = pd.read_csv("DF_FULL.csv")

# Define Event Study windows
DF_EST_W = DF[(DF['dif_days'] <= -10) & (DF['dif_days'] >= -50)] # Ventana de estimación
DF_EVT_W = DF[(DF['dif_days'] >= -5) & (DF['dif_days'] <= 30)] # Ventana del evento

# Save the data
DF_EST_W.to_csv('DF_EST.csv', index=False)
DF_EVT_W.to_csv('DF_EVT.csv', index=False)
