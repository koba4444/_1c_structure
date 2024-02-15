import pandas as pd
import datetime
import xml.etree.ElementTree as ET
import requests
import os
import parameters


def product(df):
    return df

def curr_rates():
    def get_currency_rate(root):
        dates = []
        rates = []
        for record in root.findall('Record'):
            date = datetime.datetime.strptime(record.get('Date'), "%d.%m.%Y")
            value = record.find('Value').text.replace(',', '.')
            dates.append(date)
            rates.append(float(value))
        return pd.DataFrame({'date': dates, 'rate': rates})

    start_date = "01/01/2005"  # Start date of the period
    end_date = datetime.datetime.now().strftime('%d/%m/%Y')  # End date of the period
    currency_code_USD = "R01235"  # Currency code for USD, use "R01239" for EUR
    currency_code_EUR = "R01239"
    currency_code_CNY = "R01375"



    url_USD = f"http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={start_date}&date_req2={end_date}&VAL_NM_RQ={currency_code_USD}"
    url_EUR = f"http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={start_date}&date_req2={end_date}&VAL_NM_RQ={currency_code_EUR}"
    url_CNY = f"http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={start_date}&date_req2={end_date}&VAL_NM_RQ={currency_code_CNY}"
    response_USD = requests.get(url_USD)
    response_EUR = requests.get(url_EUR)
    response_CNY = requests.get(url_CNY)
    root_USD = ET.fromstring(response_USD.content)
    root_EUR = ET.fromstring(response_EUR.content)
    root_CNY = ET.fromstring(response_CNY.content)
    curr_rates = get_currency_rate(root_USD)
    curr_rates['rate_EUR'] = get_currency_rate(root_EUR)['rate']
    curr_rates['rate_CNY'] = get_currency_rate(root_CNY)['rate']
    curr_rates.rename(columns={'rate': 'rate_USD'}, inplace=True)
    df = pd.date_range(start=start_date, end=datetime.datetime.now())
    df = pd.DataFrame(df, columns=['date'])
    df['date'] = pd.to_datetime(df['date'])
    curr_rates = pd.merge(df, curr_rates, how='left', left_on='date', right_on='date').ffill() #.fillna(method='ffill')
    curr_rates = curr_rates[['date', 'rate_USD', 'rate_EUR', 'rate_CNY']]
    return curr_rates


def sim_purchase(df):
    df.columns = [f"col{str(k).zfill(2)}" for k in range(30)]
    try:
        sim_purchase_df = pd.read_csv(os.path.join(parameters.etl_dir, 'transform_sim_purchase.csv'), sep=';', encoding='utf-8', low_memory=False)
    except:
        sim_purchase_df = pd.DataFrame(dtype=str)
        sim_purchase_df = pd.DataFrame(columns=['sim_code', 'purchase_code','purchase_title', 'purchase_date', 'purchase_qty', 'seller', 'main_seller', 'purchase_responsible', 'purchase_price', 'purchase_currency', 'purchase_underwriter', 'manager', 'commentary', 'curr_rate', 'purchase_initiator'])
    new_block = False
    df.fillna('', inplace=True)
    df = df.astype(str)
    purchase_initiator = ''
    main_seller = ''
    sim_code = ''
    for _, r in df.iterrows():
        if not new_block:
            if str(r['col02']).replace(' ', '') == '':
                new_block = True
                main_seller = r['col01']
                sim_code = r['col00']
                purchase_title = r['col02']
            else:
                continue
        else:
            if str(r['col02']).replace(' ','') != '':
                if 'Поступл' in str(r['col03']):
                    d = {'sim_code': [sim_code],
                         'purchase_code': [r['col00']],
                         'purchase_title': [purchase_title],
                         'purchase_date': [str(r['col03'])[-9:-1]],
                         'purchase_qty': [r['col09']],
                         'seller': [r['col01']],
                         'main_seller': [main_seller],
                         'purchase_responsible': [r['col02']],
                         'purchase_price': [r['col16']],
                         'purchase_currency': [r['col18']],
                         'purchase_underwriter': [r['col12']],
                         'manager': [r['col02']],
                         'commentary': [r['col23']],
                         'curr_rate': [r['col19']],
                         'purchase_initiator': [purchase_initiator]
                         }
                    df1 = pd.DataFrame(d, dtype=str)
                    sim_purchase_df = pd.concat([sim_purchase_df, df1], ignore_index=True)
                elif 'Заказ' in str(r['col03']):
                    purchase_initiator = r['col02']
                    continue
                else:
                    continue
            else:
                main_seller = r['col01']
                sim_code = r['col00']
    sim_purchase_df = sim_purchase_df.drop_duplicates()
    return sim_purchase_df



def cost(df):
    df.columns = [f"col{str(k).zfill(2)}" for k in range(10)]
    try:
        cost_df = pd.read_csv(os.path.join(parameters.etl_dir, 'transform_cost.csv'), sep=';', encoding='utf-8', low_memory=False)
    except:
        cost_df = pd.DataFrame()
        cost_df = pd.DataFrame(columns=['product_code','sim_code', 'qty_required'])
    new_block = False
    df.fillna('', inplace=True)
    df = df.astype(str)
    for _, r in df.iterrows():
        if not new_block:
            if str(r['col02']).replace(' ', '') != '':
                new_block = True
                product_code = r['col00']
            else:
                continue
        else:
            if str(r['col02']).replace(' ','') == '':
                d = {'product_code': [product_code], 'sim_code': [r['col00']], 'qty_required': [r['col04']]}
                df1 = pd.DataFrame(d)
                cost_df = pd.concat([cost_df, df1], ignore_index=True)
            else:
                product_code = r['col00']
    cost_df = cost_df.drop_duplicates()
    
    return cost_df

def sim(df):
    df.columns = [f"col{str(k).zfill(2)}" for k in range(10)]
    try:
        sim_df = pd.read_csv(os.path.join(parameters.etl_dir, 'transform_sim.csv'), sep=';', encoding='utf-8', low_memory=False)
    except:
        sim_df = pd.DataFrame()
        sim_df = pd.DataFrame(columns=['sim_article', 'sim_code', 'sim_title', 'sim_unit', 'sim_date', 'sim_price', 'sim_currency'])

    new_block = False
    df.fillna('', inplace=True)
    for _, r in df.iterrows():
        if not new_block:
            if str(r['col02']).replace(' ', '') != '':
                new_block = True
                product_code = r['col00']
            else:
                continue
        else:
            if str(r['col02']).replace(' ','') == '':
                d = {'sim_article': [r['col01']],'sim_code': [r['col00']], 'sim_title': [r['col03']], 'sim_unit': [r['col05']], 'sim_date': [r['col06']], 'sim_price': [r['col07']], 'sim_currency': [r['col08']]}
                df1 = pd.DataFrame(d)
                sim_df = pd.concat([sim_df, df1], ignore_index=True)
            else:
                product_code = r['col00']
    sim_df = sim_df.drop_duplicates()
    sim_df = sim_df.dropna(subset=['sim_date'])
    sim_df = sim_df[~sim_df['sim_date'].str.contains(' ')]
    sim_df = sim_df.sort_values(by=['sim_code', 'sim_date'])
    filtered_df = sim_df.groupby('sim_code').filter(lambda x: len(x) > 1)
    unique_values = filtered_df['sim_code'].unique()
    print(unique_values)
    sim_df = sim_df.drop_duplicates(subset=['sim_code', 'sim_date'], keep='last')

    
    return sim_df