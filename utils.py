import decimal
import json
from datetime import datetime
import parameters
import pandas as pd
import numpy as np
import pyodbc
import os
import csv

def GUID_to_hex(GUID):
    return hex(int(GUID[19:23] + GUID[24:36] +GUID[14:18] +GUID[9:13] + GUID[:8], 16))

def make_enum(file):
    ans = {}
    ans_list = []
    curr_enum = ''
    with open(file, 'r',encoding='utf-8') as f:
        s = f.read()
    strokes = s.split('\n')
    for stroke in strokes:
        if (stroke[0] != ' ') and (len(stroke.split(':')) != 3):
            curr_enum = stroke
        else:
            parts = stroke.split(',')
            if len(parts) < 3:
                print(f"ошибка формата строки {stroke} ")
                break
            val =  ', '.join(map(lambda x: x.lstrip(' '), parts[:-2]))
            GUID = GUID_to_hex(parts[-2].split(':')[1])
            ans[GUID] = []
            ans[GUID].append(curr_enum)
            ans[GUID].append(val)
            ans[GUID].append(int(parts[-1].split(':')[1]))
            ans_list.append([
                GUID,
                curr_enum,
                val,
                int(parts[-1].split(':')[1])
            ])
            if len(parts) > 3:
                print(f"строка с запятыми {stroke} -> {ans_list[-1]} ")
    with open(file[:-4] + '_tbl.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(ans_list)

    return ans, ans_list


def get_table_head(table, field='*', n=5, mssql_db=parameters.mssql_ut):
    # returns n first rows of the table
    ans = []
    server = mssql_db['server']
    database = mssql_db['database']
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    query = f"SELECT TOP({n}) {field} FROM {table}"
    cursor.execute(query)
    for row in cursor:
        ans.append(row[0])
    return ans

def load_table_pd(table, mssql_db=parameters.mssql_ut):
    server = mssql_db['server']  # например, 'localhost\sqlexpress'
    database = mssql_db['database']
    username = mssql_db['username']
    password = mssql_db['password']
    tables = {}
    fields = []
    # Строка подключения
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes'

    conn = pyodbc.connect(conn_str)

    # Создание курсора
    cursor = conn.cursor()
    query = f"SELECT * FROM {table}"
    cursor.execute(query)
    rows = cursor.fetchall()
    rows = [list(r) for r in rows]
    col_names = [desc[0] for desc in cursor.description]
    col_types = [desc[1] for desc in cursor.description]
    type_mapping = {
        "VARCHAR": str,
        "INT": np.int64,
        bytearray: object,
        decimal: float,
    }
    pandas_col_types = []
    for db_type in col_types:
        pandas_col_types.append(type_mapping.get(db_type, object))
    #pandas_col_types = [type_mapping.get(db_type, object) for db_type in col_types]


    df = pd.DataFrame(rows, columns=col_names, dtype=str)
    #for col_name, col_type in zip(col_names, pandas_col_types):
        #df[col_name] = df[col_name].astype(col_type)
    return df


def get_tables(mssql_db=parameters.mssql_fd):
    table_file = os.path.join(os.getcwd(), 'data', 'tables_' + mssql_db['database'] + '.json')
    fields_file = os.path.join(os.getcwd(), 'data', 'fields_' + mssql_db['database'] + '.json')
    if os.path.exists(table_file):
        with open(table_file, 'r') as f:
            tables = json.load(f)
        with open(fields_file, 'r') as f:
            fields = json.load(f)
        return tables, fields
    # Параметры подключения
    server = mssql_db['server']  # например, 'localhost\sqlexpress'
    database = mssql_db['database']
    username = mssql_db['username']
    password = mssql_db['password']
    tables = {}
    fields = []
    # Строка подключения
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes'
    #conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    # Подключение к базе данных
    conn = pyodbc.connect(conn_str)

    # Создание курсора
    cursor = conn.cursor()
    cursor1 = conn.cursor()

    # Запрос на получение списка таблиц
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE'")



    # Вывод результатов
    for row in cursor:
        #if ('_Document' in row[0]) & ~('_DocumentChng' in row[0]) & ~('_DocumentJourna' in row[0]):
        name = row[0]
        #tables[name] = [row[0].split('_')[1:], []]
        tables[name] = []



    for t in tables.keys():
        query = f"""
        SELECT 
            COLUMN_NAME, DATA_TYPE
        FROM 
            INFORMATION_SCHEMA.COLUMNS
        WHERE 
            TABLE_NAME = N'{t}'
        """
        cursor.execute(query)
        for row in cursor:
            #tables[t][1].append([row.COLUMN_NAME, row.DATA_TYPE])
            tables[t].append([row.COLUMN_NAME, row.DATA_TYPE])
            fields.append((t,row.COLUMN_NAME, row.DATA_TYPE))



    tables = dict(sorted(tables.items()))
    cursor.close()
    cursor1.close()
    with open(table_file, 'w') as f:
        json.dump(tables, f)
    with open(fields_file, 'w') as f:
        json.dump(fields, f)
    return tables, fields




"""
    doc = ''
    for t, f in tables.items():
        #if not doc: continue
        if ((len(t) == 2) & (doc != t[1])):
            doc_table = t[0]
            doc = t[1]
            fields = f
            continue
        if ((len(t) == 3) & (t[1] == doc)):
            q1 = f"SELECT TOP(1) {f[0][0]} FROM {t[0]}"
            cursor.execute(q1)
            #Take primary key value from first ro in parent table
            ref_key = cursor.fetchone()
            if ref_key: ref_key = '0x' + ref_key[0].hex()
            if ref_key:   # There are rows in parent table
                for field in fields:
                    if field[1] != 'binary': continue
                    q2 = f"SELECT COUNT(*) FROM {doc_table} WHERE {field[0]} = {ref_key}"
                    cursor1.execute(q2)
                    result = cursor1.fetchone()
                    if result:
                        if result[0] != 0:
                            print(f"Найдена связь из {t[0]} в : {t[1]}")


    cursor.close()
    cursor1.close()
    conn.close()


    return tables
"""