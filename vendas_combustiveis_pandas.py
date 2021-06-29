import pandas as pd
import numpy as np
import locale
from pandas._libs.tslibs.timestamps import Timestamp

# define o idioma como português brasileiro e o enconding como utf-8
locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

# define as variáveis globais
path = 'vendas-combustiveis-m3.xls'
derivados = 'derivados'
oleodiesel = 'oleodiesel'

# define a função main, responsável por rodar todo o código
def main(name):
        extract = read_tabela(name)
        transform = transformar(extract)
        load = write_df(transform, name)
        return load

# cria o dataframe a partir da leitura do arquivo .xls, preenche valores nulos com 0 e retira caracteres especiais
def read_tabela(name):
        pd_df = pd.read_excel(path, name).fillna(0)
        pd_df.columns = pd_df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
        cols = pd_df.select_dtypes(include=[np.object]).columns
        pd_df[cols] = pd_df[cols].apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
        return pd_df

# define a função que realizas as principais transformações
def transformar(df):
        inicial_df = df
        result = formatar(df)
        print("checando somas...")
        if primeiro_check(result, inicial_df) == False:
                consertado = consertar_valores(inicial_df)
                formatado = formatar(consertado)
                if segundo_check(formatado, consertado) == False:
                        print("As somas estão diferentes, é preciso checar.")
                elif segundo_check(formatado, consertado) == True:
                        print("As somas estão iguais.")
                        year_month_adicionado = year_month(formatado)
                        print(year_month_adicionado)
                        if segundo_check(year_month_adicionado, consertado) == False:
                                print("As somas estão diferentes, é preciso checar.")
                        elif segundo_check(year_month_adicionado, consertado) == True:
                                print("As somas estão iguais.")
                                ajustado = ajustes_finais(year_month_adicionado)
                                print(ajustado)
                                print(ajustado.dtypes)
                                return ajustado
        elif primeiro_check(result, inicial_df) == True:
                year_month_adicionado = year_month(result)
                if segundo_check(year_month_adicionado,inicial_df) == False:
                        print("As somas estão diferentes, é preciso checar.")
                elif segundo_check(year_month_adicionado,inicial_df) == True:
                        print("As somas estão iguais.")  
                        ajustado = ajustes_finais(year_month_adicionado)
                        print(ajustado)
                        return ajustado

# formata o dataframe e renomeia as colunas
def formatar(df):
        format_pd_df = df.drop(
                columns=['REGIAO', 'TOTAL']).rename(
                        columns={'COMBUSTIVEL':'product','ANO':'year','ESTADO':'uf','UNIDADE':'unit'}).melt(
                                id_vars=["product", "year", "uf", "unit"], var_name="month", value_name="volume")
        return format_pd_df

# primeiro check das somas
def primeiro_check(df, inicial_df):
        formatada_df = df.groupby(['year','uf','product','unit'])['volume'].sum()
        primeira_df = inicial_df[['ANO','ESTADO','COMBUSTIVEL','UNIDADE','TOTAL']]
        check_sum = pd.merge(formatada_df,primeira_df,how='inner',left_on=['year','uf','product','unit'],right_on=['ANO','ESTADO','COMBUSTIVEL','UNIDADE'])
        if check_sum['volume'].equals(check_sum['TOTAL']) == False:
                print("As somas estão diferentes, é preciso checar.")
                provar_erro(check_sum,inicial_df)
                return False
        elif check_sum['volume'].equals(check_sum['TOTAL']) == True:
                print("As somas estão iguais")
                return True

# prova que a tabela possui um erro de soma nos dados iniciais
def provar_erro(check_sum, inicial_df):
        print("checando somas na base de dados iniciais...")
        check_sum['volume_igual_total'] = np.where(check_sum['volume'] == check_sum['TOTAL'] , 'igual', 'diferente')
        check_sum = check_sum.loc[check_sum['volume_igual_total']=='diferente'] #seleciona apenas as linhas em que as somas estão diferentes
        print(check_sum)
        check_total_inicial = inicial_df.loc[(inicial_df['COMBUSTIVEL']=="QUEROSENE ILUMINANTE (m3)")& (inicial_df['ANO']==2020)]
        check_total_inicial['sum_meses'] = check_total_inicial['Jan']+check_total_inicial['Fev']+check_total_inicial['Mar']+check_total_inicial['Abr']+check_total_inicial['Mai']+check_total_inicial['Jun']+check_total_inicial['Jul']+check_total_inicial['Ago']+check_total_inicial['Set']+check_total_inicial['Out']+check_total_inicial['Nov']+check_total_inicial['Dez']
        check_total_inicial['sum_meses_igual_TOTAL'] = np.where( check_total_inicial['sum_meses'] == check_total_inicial['TOTAL'] , 'igual', 'diferente')
        print(check_total_inicial) 
        print("isso mostra que inicialmente os dados totais estavam errados") #prova que inicialmente os dados estavam errados

# conserta valores possivelmente errados
def consertar_valores(inicial_df):
        print("consertando valores...")
        inicial_df['sum_meses'] = inicial_df['Jan']+inicial_df['Fev']+inicial_df['Mar']+inicial_df['Abr']+inicial_df['Mai']+inicial_df['Jun']+inicial_df['Jul']+inicial_df['Ago']+inicial_df['Set']+inicial_df['Out']+inicial_df['Nov']+inicial_df['Dez']
        inicial_df['sum_meses_igual_TOTAL'] = np.where(inicial_df['sum_meses'] == inicial_df['TOTAL'] , 'igual', 'diferente')
        inicial_df.loc[inicial_df.sum_meses_igual_TOTAL == 'diferente', "TOTAL"] = inicial_df.sum_meses
        inicial_df = inicial_df.drop(['sum_meses','sum_meses_igual_TOTAL'], axis = 1)
        print("consertado!")
        return inicial_df

# segundo check das somas
def segundo_check(df,inicial_df):
        format_df = df.groupby(['year','uf','product','unit'])['volume'].sum()
        inicial_df = inicial_df[['ANO','ESTADO','COMBUSTIVEL','UNIDADE','TOTAL']]
        check_sum = pd.merge(format_df,inicial_df,how='inner',left_on=['year','uf','product','unit'],right_on=['ANO','ESTADO','COMBUSTIVEL','UNIDADE'])
        if check_sum['volume'].equals(check_sum['TOTAL']) == False:
                return False
        elif check_sum['volume'].equals(check_sum['TOTAL']) == True:
                return True

# adiciona coluna de year_month, transformando mês de nome para número e concatenando com ano
def year_month(df):
        df['month'] = pd.to_datetime(df['month'], format='%b').astype(str).str[5:7]
        df['created_at'] = Timestamp.now()
        df['year_month'] = df["year"].astype(str) + "-" + df["month"]
        df['year_month'] = pd.to_datetime(df['year_month'], format='%Y-%m-%d')
        return df

# retira as colunas não utilizadas e reordena as colunas finais
def ajustes_finais(df):
        df = df.drop(['month','year'],1)
        df = df[['year_month', 'uf', 'product', 'unit', 'volume', 'created_at']]
        return df

# salva dataframe em um arquivo .xlsx
def write_df(df, name):
        filename = '%s.csv' % name
        df.to_csv(filename, header=True, index=False)

main (derivados)
main (oleodiesel)