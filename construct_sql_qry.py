import parameters
import utils
import pandas as pd
import numpy as np

def construct_ref_enum_map(mssql_db=parameters.mssql_ut):
    tables, fields = utils.get_tables(mssql_db=mssql_db)
    tables_diminished = None
    all_guids = {}
    ans = {}

    enum_fields = [(t[0], t[1]) for t in fields if '_Enum' in t[0]]
    ref_fields = [(t[0], t[1]) for t in fields if '_Reference' in t[0]]

    i = 0
    for t, f in tables.items():
        if ('_Document' in t) | ('_Reference' in t) | ('_Enum' in t):
            df = utils.load_table_pd(t)

    fconn = []




def construct_field_map():
    tables, fields = utils.get_tables(mssql_db=parameters.mssql_ut)
    ans = {}
    enum_tables = [tname for tname, tbody in tables.items() if '_Enum' in tname]
    reference_tables = [tname for tname, tbody in tables.items() if '_Reference' in tname]
    for ft_name, ft_details in parameters._1c_fact_tables.items():
        ans[ft_name] = {}
        ans[ft_name]['enum_tables'] = []
        ans[ft_name]['reference_tables'] = []

        node_table = ft_details['table']
        print(tables[node_table])
        print(ans)
        val = utils.get_table_head(node_table, field=tables[node_table][1][0][0], n=1)[0]
        pretendents = utils.get_table_head(node_table, field=tables[node_table][1][0][0], n=1)[0]

        print(utils.get_table_head(node_table, field=tables[node_table][1][0][0], n=200))

    return ans

def construct_cpattern(mssql_db=parameters.mssql_ut, mssql_fd=parameters.mssql_fd, table = 'ConnPatterns_ut'):
    def unroll(s:str):
        s = s.replace('(','')
        s = s.replace(')', '')
        s = s.replace(' ', '')
        s_list = tuple()
        s_list = tuple(s.split(','))
        ans = tuple(map(lambda x: tuple(x.split('-')), s_list))
        return ans


    tables, fields = utils.get_tables(mssql_db=mssql_db)
    df = utils.load_table_pd(table=table, mssql_db=mssql_fd)
    df = df[df['pattern'].str.contains('_Document134 ')]
    pats = tuple(map(unroll, list(df['pattern'])))
    pats_set = set(pats)

    with open('nodes.txt', 'w') as f:
        for p in pats:
            for node in p:
                f.write(str(node))
                f.write('\n')
            f.write("======================================")
            f.write('\n')
    all_guids = {}
    ans = {}
    return pats


if __name__ == '__main__':
    tables, fields = utils.get_tables(mssql_db=parameters.mssql_ut)
    cpattern = construct_cpattern(mssql_db=parameters.mssql_ut)
    #tables = construct_ref_enum_map()
    #tables = construct_field_map()
