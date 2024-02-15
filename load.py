import pandas as pd
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder
import chardet
import parameters
import json
import os
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date
from sqlalchemy.dialects.postgresql import insert
import psycopg2
import datetime
import utils
from sqlalchemy import inspect



def load_all(tables=None):
    try:
        with open(parameters.transform_modification_time_file, 'r') as file:
            transform_mod_time = json.load(file)
    except:
        transform_mod_time = {}
    try:
        with open(parameters.load_modification_time_file, 'r') as file:
            load_mod_time = json.load(file)
    except:
        load_mod_time = {}

    for table_name in list(parameters.tables_to_extract.keys()):
        try:
            table_passed = (tables and (table_name in tables.keys()))
            transform_table_was_stored = (os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv') in transform_mod_time.keys())
            load_is_uptodate = (
                        (os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv') in transform_mod_time.keys()) \
                        and (os.path.join(parameters.etl_dir,  'load_' + table_name) in load_mod_time.keys()) \
                        and (transform_mod_time[os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv')] <= load_mod_time[os.path.join(parameters.etl_dir,  'load_' + table_name)])
            )
            if load_is_uptodate:
                print(f"{table_name} is uptodate. It will not be reloaded")
                continue
            elif table_passed:
                table = tables[table_name]
            elif transform_table_was_stored and ((table_name not in load_mod_time.keys()) or (transform_mod_time[table_name] >= load_mod_time[table_name])):
                table = pd.read_csv(os.path.join(parameters.etl_dir,  'transform_' + table_name + '.csv'), sep=";", encoding='utf-8',low_memory=False)

            # Создание SSH-туннеля
            with SSHTunnelForwarder(
                (parameters.ssh_host, parameters.ssh_port),
                ssh_username=parameters.ssh_user,
                ssh_password=parameters.ssh_password,
                remote_bind_address=(parameters.db_host, parameters.db_port)
            ) as tunnel:
                # Создание подключения к базе данных с использованием SQLAlchemy
                engine = create_engine(f'postgresql://{parameters.db_user}:{parameters.db_password}@localhost:{tunnel.local_bind_port}/{parameters.db_name}')
                print("Подключение установлено")

                """
                # Чтение данных из базы данных (пример)
                result = pd.read_sql_query("SELECT * FROM some_table;", con=engine)
                databases = pd.read_sql_query('SELECT datname FROM pg_database;', con=engine)
                print(result)

                # Запись DataFrame в базу данных
                df.to_sql('new_table', con=engine, if_exists='replace', index=False)
                df1 = pd.read_sql_query('SELECT start_date, COUNT(*) FROM new_table group by start_date order by start_date;', con=engine)
                """
                # ==========================================================================================================

                # Еще один пример


                # Список с определениями типов столбцов, соответствующих вашему DataFrame
                # Пример: [('name', String), ('age', Integer), ('salary', Float), ('birthdate', Date)]
                ##column_types = utils.create_typelist_for_table_creating(parameters.tables_to_extract[table_name]['types'], parameters.tables_to_extract[table_name]['lengths'])


                # Создание объекта MetaData
                ##metadata = MetaData()

                # Определение таблицы со столбцами
                # Название таблицы 't' и определение столбцов с типами данных
                ##t = Table(table_name, metadata,
                ##           *(Column(column_name, column_type) for column_name, column_type in column_types))

                # Создание таблицы в базе данных, если она еще не существует


                ##try:
                ##    t.create(bind=engine, checkfirst=True)
                ##except Exception as e:
                ##    print(f"Произошла ошибка при создании таблицы {table_name}: {e}")
                #inspector = inspect(engine)
                # Проверка существования таблицы
                #if not inspector.has_table(table_name):
                #    # Создание таблицы, если она не существует
                #    t.create(bind=engine, checkfirst=True)

                #if engine.dialect.has_table(engine, table_name):
                #    t.create(bind=engine, checkfirst=True)

                # Запись данных из DataFrame в таблицу PostgreSQL

                # Сделать копию таблицы table_name в таблицу table_name_old
                try:
                    with engine.connect() as con:
                        con.execute(f"DROP TABLE IF EXISTS {table_name}_old")
                        con.execute(f"CREATE TABLE {table_name}_old AS TABLE {table_name}")
                except Exception as e:
                    print(f"Произошла ошибка при создании таблицы {table_name}_old: {e}")

                # Удалить данные из таблицы table_name
                try:
                    with engine.connect() as con:
                        con.execute(f"DELETE FROM {table_name}")
                except Exception as e:
                    print(f"Произошла ошибка при удалении данных из таблицы {table_name}: {e}")

                # Записать данные из DataFrame в таблицу table_name
                try:
                    table.to_sql(table_name, con=engine, if_exists='append', index=False, chunksize=1000)
                except Exception as e:
                    print(f"Произошла ошибка при записи данных в таблицу {table_name}: {e}")

                try:
                    with open(os.path.join(parameters.etl_dir, f"load_{table_name}"), 'w') as file:
                        file.write(f"{str(datetime.datetime.now())} : {table.shape[0]} was loaded")
                    utils.change_mod_time(parameters.load_modification_time_file, load_mod_time,
                                      os.path.join(parameters.etl_dir, f"load_{table_name}"))
                    print(f"{table_name} has been loaded")
                except Exception as e:
                    print(f"Произошла ошибка при изменении времени модификации {table_name}: {e}")



        except Exception as ee:
            print(f"Произошла ошибка {ee} при загрузке в БД таблицы {table_name}")



if __name__ == '__main__':
    #tables = transform.transform_all()
    tables = load_all()