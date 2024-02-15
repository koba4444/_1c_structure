import parameters
import pandas as pd
import json
import os
import datetime

import utils


def dropna(df, subset=None):
    df.dropna(subset=subset, inplace=True)
    return df

def transform_all(tables=None):
    try:
        with open(parameters.transform_modification_time_file, 'r') as file:
            transform_mod_time = json.load(file)
    except Exception as e:
        transform_mod_time = {}
    try:
        with open(parameters.extract_modification_time_file, 'r') as file:
            extract_mod_time = json.load(file)
    except Exception as e:
        extract_mod_time = {}

    for table_name in parameters.tables_to_extract.keys():
        extract_everytime = ('extract_everytime' in parameters.tables_to_extract[table_name].keys()) and \
                            (parameters.tables_to_extract[table_name]['extract_everytime'])
        try:
            table_passed = (tables and (table_name in tables.keys()))
            
            try:
                extract_path = parameters.files_to_copy[table_name]
            except:
                extract_path = parameters.dirs_to_copy[table_name]
            extract_table_was_stored = (extract_path in extract_mod_time.keys())
            transform_table_was_stored_and_uptodate = (
                        (os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv') in transform_mod_time.keys()) \
                        and (extract_path in extract_mod_time.keys()) \
                        and (os.path.exists(os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv'))) \
                        and (transform_mod_time[os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv')] >= extract_mod_time[extract_path]))
            if (not extract_everytime) and transform_table_was_stored_and_uptodate:
                try:
                    print(f"{table_name} is uptodate. It will not be retransformed")
                    table = pd.read_csv(os.path.join(parameters.etl_dir, 'transform_' + table_name + '.csv'), sep=";",
                                        encoding='utf-8', low_memory=False, dtype=str)
                    continue
                except Exception as e:
                    print(f"Произошла нефатальная ошибка при чтении файла transform_{table_name} из папки {parameters.etl_dir}")

            elif table_passed:
                table = tables[table_name]
            elif extract_table_was_stored:
                table = pd.read_csv(os.path.join(parameters.etl_dir,  'extract_' + table_name + '.csv'), sep=";", encoding='utf-8', low_memory=False, dtype=str)

            # Here is the place to write down the transformation code
            # Выбросить строки с пустыми значениями в заданных столбцах
            for dropna_in_column in parameters.tables_to_extract[table_name]['dropna']:
                try:
                    table.dropna(subset=[dropna_in_column], inplace=True)
                except Exception as e:
                    print(f"Произошла ошибка при удалении пустых строк: {e} в таблице {table_name}")

            # Выбросить дубликаты строк
            try:
                table.drop_duplicates(inplace=True)
            except Exception as e:
                print(f"Произошла ошибка при удалении дубликатов: {e} в таблице {table_name}")

            # Привести формат даты к заданному в parameters.py



            for column in parameters.tables_to_extract[table_name]['date_formats'].keys():
                try:
                    if column != '':
                        table[column] = table[column].astype('str').apply(
                            lambda x: datetime.datetime.strptime(str(x), parameters.tables_to_extract[table_name]['date_formats'][column]).strftime('%Y-%m-%d') if (pd.notna(x) and (x != 'nan') and x.strip() != '') else None)
                except Exception as e:
                    print(f"Произошла ошибка при приведении форматов дат: {e} в таблице {table_name}")

            # Заменить разделители десятичных разрядов в числовых столбцах

            for column in parameters.tables_to_extract[table_name]['decimal_delimiters'].keys():
                for replace_case in parameters.tables_to_extract[table_name]['decimal_delimiters'][column]:
                    try:
                        if column != '':
                            table[column] = table[column].astype('str').apply(lambda x: x.replace(
                                replace_case['from'],
                                replace_case['to']))
                    except Exception as e:
                        print(
                            f"Произошла ошибка при замене разделителей десятичных разрядов в числовых столбцах: {e} в таблице {table_name}")

            # Установить типы столбцов в соответствии с заданными в parameters.py

            for column in parameters.tables_to_extract[table_name]['types'].keys():
                try:
                    if parameters.tables_to_extract[table_name]['types'][column] == 'str':
                        table[column] = table[column].fillna('')
                    elif (parameters.tables_to_extract[table_name]['types'][column] == 'int') or (parameters.tables_to_extract[table_name]['types'][column] == 'float'):
                        table[column] = table[column].fillna('0')
                    if column != '':
                        table[column] = table[column].astype(parameters.tables_to_extract[table_name]['types'][column], errors='ignore')
                except Exception as e:
                    print(f"Произошла ошибка при установлении типов: {e} в таблице {table_name}")

            # Подогнать длины строк под заданные в parameters.py

            for column in parameters.tables_to_extract[table_name]['lengths'].keys():
                try:
                    if column != '':
                        table[column] = table[column].apply(lambda x: x[:parameters.tables_to_extract[table_name]['lengths'][column]])

                except Exception as e:
                    print(f"Произошла ошибка при подгонке длин строк: {e} в таблице {table_name}")

            #Special processing if any
            if parameters.tables_to_extract[table_name].get('spec_proc'):
                table = parameters.tables_to_extract[table_name]['spec_proc'](table)



            table.to_csv(os.path.join(parameters.etl_dir, 'transform_' + table_name + '.csv'), sep=";", encoding='utf-8', index=False)
            utils.change_mod_time(parameters.transform_modification_time_file, transform_mod_time, os.path.join(parameters.etl_dir, 'transform_' + table_name + '.csv'))
            print(f"{table_name} has been transformed")
        except Exception as e:
            print(f"{table_name} has not been transformed properly")
            print(f"Error happened: {e}")
        a = 1
        print(f"transform table finished: {table_name}")


if __name__ == '__main__':
    tables = transform_all()



