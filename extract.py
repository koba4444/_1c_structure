import pandas as pd
import os

import _3p_extract
import parameters
import datetime
import chardet
import json
import utils



def replace_char(value, old_char, new_char):
    if isinstance(value, str):
        return value.replace(old_char, new_char)
    return value


def loadcsvfile_and_rename_columns(path, cols: dict = None, sep=";", encoding=None, skiprows=0):
    try:
        with open(path,'r', encoding=encoding) as f:
            print(f"file - open file {path} with encoding {encoding}")
            df = pd.read_csv(f, sep=sep, encoding=encoding, low_memory=False, dtype=str, skiprows=skiprows, on_bad_lines='warn')
    except Exception as e:
        print(f"Err while extracting file {path} : {e}")
        with open(path, 'rb') as f:
            guess_encoding = chardet.detect(f.read())['encoding']
            print(f"file - {guess_encoding} if right encoding fo file {path} :{datetime.datetime.now().strftime('%H:%M:%S')}?")
        with open(path, 'r', encoding=guess_encoding) as f:
            print(f"file - open file {path} with encoding {guess_encoding}")
            df = pd.read_csv(f, sep=sep, encoding=guess_encoding, low_memory=False, dtype=str, skiprows=skiprows, on_bad_lines='warn')

    if cols is not None:
        if type(cols) == dict:
            df = df.rename(columns=cols)
            df = df[[cols[i] for i in cols.keys()]]
        elif type(cols) == list:
            df.columns = cols
        
    return df


def loadcsv_from_dir_and_rename_columns(path, cols: dict = None, sep=";", encoding=None):
    sale_files = os.listdir(path)
    df = pd.DataFrame()
    for file in sale_files:
        try:
            file_path = os.path.join(path, file)
            with open(file_path, 'r', encoding=encoding) as f:
                df = pd.concat([df, pd.read_csv(f, sep=sep, encoding=encoding, dtype=str)])
        except Exception as e:
            print(f"While extracting {file} from dir {path}: {e}")
            with open(os.path.join(path, file), 'rb') as f:
                guess_encoding = chardet.detect(f.read())['encoding']
                print(f"dir - {guess_encoding} if right encoding fo file {path}:{datetime.datetime.now().strftime('%H:%M:%S')}?")

            file_path = os.path.join(path, file)
            with open(file_path, 'r', encoding=guess_encoding) as f:
                print(f"dir - open file {file_path} with encoding {guess_encoding}")
                df = pd.concat([df, pd.read_csv(f, sep=sep, encoding=guess_encoding, dtype=str)])
    if cols is not None:
        df = df.rename(columns=cols)
        df = df[[cols[i] for i in cols.keys()]]
    return df



def extract_table(**kwargs):
    if kwargs['type'] == 'csv':
        if kwargs['file_or_dir'] == 'file':
            return loadcsvfile_and_rename_columns(kwargs['source'],
                                                  kwargs['columns'],
                                                  encoding=kwargs['encoding'],
                                                  skiprows=kwargs['skiprows'] if 'skiprows' in kwargs.keys() else 0,
                                                  sep=kwargs['delimiter'] if 'delimiter' in kwargs.keys() else ';')
        elif kwargs['file_or_dir'] == 'dir':
            return loadcsv_from_dir_and_rename_columns(kwargs['source'], kwargs['columns'], encoding=kwargs['encoding'])
    elif kwargs['type'] == 'excel':
        if kwargs['source'][-3:] == 'xls':
            eng = 'xlrd'
        elif kwargs['source'][-4:] == 'xlsx':
            eng = 'openpyxl'
        df = pd.read_excel(kwargs['source'], sheet_name=kwargs['sheet_name'], engine=eng)
        result = df.iloc[kwargs['v_slice'], kwargs['h_slice']].set_axis(kwargs['columns'], axis=1).dropna(how='all')
    elif kwargs['type'] == 'internet':
        result = kwargs['extract_spec_proc']()
    return result


def extract_all():
    try:
        with open(parameters.extract_modification_time_file, 'r') as file:
            extract_mod_time = json.load(file)
    except:
        extract_mod_time = {}
    tables_to_extract = {}
    # 3p tables are extracted logically separately from another tables =======

    #temporarily commented:

    #tables_to_extract.update(_3p_extract.wb_extract())
    #tables_to_extract.update(_3p_extract.ym_extract())
    #update(_3p_extract.ozon_extract())
    # =======================================================================
    for table_name in parameters.tables_to_extract.keys():
        extract_everytime = ('extract_everytime' in parameters.tables_to_extract[table_name].keys()) and \
                            (parameters.tables_to_extract[table_name]['extract_everytime'])
        extract_table_was_stored = (os.path.join(parameters.etl_dir, 'extract_' + table_name + '.csv') in extract_mod_time.keys()) \
                and (os.path.exists(os.path.join(parameters.etl_dir, 'extract_' + table_name + '.csv'))) \

        if  (not extract_everytime) and (('source' in parameters.tables_to_extract[table_name].keys()) and \
                (utils.uptodate(extract_mod_time, parameters.tables_to_extract[table_name]['source']) and \
                (os.path.exists(os.path.join(parameters.etl_dir,  'extract_' + table_name + '.csv'))))):
            tables_to_extract[table_name] = pd.read_csv(os.path.join(parameters.etl_dir,  'extract_' + table_name + '.csv'), sep=";", encoding='utf-8', low_memory=False, dtype=str)
            print(f"{table_name} is uptodate. It will not be reextracted")
        else:
            try:
                tables_to_extract[table_name] = extract_table(**parameters.tables_to_extract[table_name])
                print(f"{table_name} is being extracted to {parameters.etl_dir}")
                tables_to_extract[table_name].to_csv(os.path.join(parameters.etl_dir,  'extract_' + table_name + '.csv'), sep=";", encoding='utf-8', index=False)
                utils.change_mod_time(parameters.extract_modification_time_file,extract_mod_time, parameters.tables_to_extract[table_name]['source'])
            except Exception as e:
                print(f"{table_name} has not been extracted properly")
                print(f"Error happened: {e}")
    return tables_to_extract
