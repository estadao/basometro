'''
As funções desse programa servem para cumprir tarefas necessárias
à manutenção do aplicativo, como atualizar o banco de dados completo
e gerar arquivos CSV para a elaboração das visualizações de dados.
'''

from basometro import basometro_governos, basometro_partidos, basometro_deputados
from basometro.core import core
from camaraPy.api_original import proposicoes
from camaraPy.api_original.core import custom_exceptions
import datetime, glob, json, os
import pandas as pd

'''
TO DO LIST:
- Otimizar a atualização de forma que não seja necessário carregar
o banco de dados inteiro na memória sempre que a função for executada.
Pode ser feito mantendo um log de texto externo e appendando os valores
usando a biblioteca csv do Python.
- Fazer com que as funções operem diretamente em um DataFrame
e não precisem mais ler o arquivo inteiro. Isso evita processamento
duplicado e vai melhorar a performance.
'''

################################
### ATUALIZAR BANCO DE DADOS ###
################################

def atualizar_banco_de_dados(df_path, keep_all = False):
  '''
  Essa função atualiza a base de dados de votos do Basômetro com
  todas as votações realizadas entre a data do último registro e a
  data de execução.

  Parâmetros:
  df_path -> O caminho para o arquivo CSV
  keep_all ->  Boleano que, se verdadeiro, determina a coleta TODOS os votos,
  incluindo abstenções e invogações do artigo 17. O padrão é False.
  '''

  def selecionar_intervalo_de_datas(df):
    '''
    Seleciona intervalo de datas entre o último
    registro e data de hoje. Retorna um par de valores.

    Parâmetros:

    df -> O banco de dados de votos do basômetro.
    '''

    df_ = df.copy()

    df_ [ 'data' ] = pd.to_datetime(df_.data, format = "%Y-%m-%d %H:%M:%S")
    latest_entry  = df_.data.max()
    # Adicione data manualmente para testar
    #latest_entry   = pd.to_datetime("2019-04-20", format = "%Y-%m-%d %H:%M:%S")

    today = datetime.datetime.now()

    return latest_entry, today

  def extrair_novos_votos(latest_entry, today):
    '''
    Obtém as proposições votadas entre a data da última entrada
    do banco de dados e o dia de hoje.

    Parâmetros:
    latest_entry -> Data da última votação do banco de dados atual,
    obtida em selecionar_intervalo_de_datas(). Objeto datetime.
    today -> Data atual, gerada em selecionar_intervalo_de_datas(). Objeto datetime.
    df -> O banco de dados do basômetro, gerado na função principal
    '''

    def extrair_dados_proposicao(new_prop, latest_entry):
      '''
      Faz solicitações para a API e obtém os votos de uma proposição específica.

      Parâmetros:
      new_prop-> Uma das proposições na lista obtida por listar_novas_proposicoes().
      '''

      # Cria objetos a partir das votações
      votos_arr = [ ] # Esse array será populado

      id_proposicao = new_prop['codProposicao']

      new_prop = proposicoes.ObterProposicaoPorID( { "IdProp" : id_proposicao } )
      new_prop = new_prop['proposicao']

      params = {
          "Tipo"   : new_prop['@tipo'].strip(),
          "Numero" : new_prop['@numero'].strip(),
          "Ano"    : new_prop['@ano'].strip()
      }

      # Acessa as votações da proposta
      try:
        votacoes = proposicoes.ObterVotacaoProposicao(params)

        dados_proposicao = {
          "tipoProposicao"   : votacoes['proposicao']['Sigla'].strip(),
          "numeroProposicao" : votacoes['proposicao']['Numero'].strip(),
          "anoProposicao"    : votacoes['proposicao']['Ano'].strip()
        }

        votacoes = votacoes['proposicao']['Votacoes']['Votacao']

        # Se os dados vêm na forma de lista, a proposição em questão
        # tem ao menos duas votações associadas à ela.
        if isinstance(votacoes, list):

          for votacao in votacoes:

            # Essa checagem é necessária para não pegar todas as votações
            # de uma proposição que apareceu no plenário em mais de um ano
            data_votacao = pd.to_datetime(votacao["@Data"], format = "%d/%m/%Y")
            if data_votacao > latest_entry:

              # Cria um novo elemento que vai ser passado para o objeto Votacao
              votacao["dadosProposicao"] = dados_proposicao

              votacao = core.Votacao(votacao)
              votos_arr.extend(votacao.votos)


        # Se houve apenas uma votação, porém, os dados vêm como um dicionário
        # solto e só precsisamos transformar ela em um objeto votação do basômetro.
        elif isinstance(votacoes, dict):

          # Essa checagem é necessária para não pegar todas as votações
          # de uma proposição que apareceu no plenário em mais de um ano
          data_votacao = pd.to_datetime(votacoes["@Data"], format = "%d/%m/%Y")
          if data_votacao > latest_entry:

            # Cria um novo elemento que vai ser passado para o objeto Votacao
            votacoes["dadosProposicao"] = dados_proposicao

            votacao = core.Votacao(votacoes)
            votos_arr.extend(votacao.votos)

      except custom_exceptions.ProposicaoAcessoria as e:
        votos_arr = [ ]

      return votos_arr

    # Caso aconteça uma virada de ano entre a data do último voto
    # e a data de requisição, vamos precisar fazer uma solicitação
    # a mais para evitar perder dados.
    if latest_entry.year != today.year:
      years = [ latest_entry.year, today.year ]

    else:
      years = [ today.year ]

    votes_arr = [ ]
    for year in years:

      # Faz requisição para a API, recuperando as votações do ano atual
      props = proposicoes.ListarProposicoesVotadasEmPlenario( { "Ano" : today.year } )
      props = props['proposicoes']['proposicao']

      for prop in props:

        if pd.to_datetime( prop [ "dataVotacao" ], format = "%d/%m/%Y") > latest_entry:
          new_votes = extrair_dados_proposicao(prop, latest_entry)
          votes_arr.extend(new_votes)

    return votes_arr

  ##########################
  ### EXECUÇÃO PRINCIPAL ###
  ##########################

  # Lê a base de dados
  df = pd.read_csv(df_path, dtype = str)

  # Pega os intervalos de data
  latest_entry, today = selecionar_intervalo_de_datas(df)

  # Obtém as votações que transcorreram desde a última data adicionada
  new_votes = extrair_novos_votos(latest_entry, today)

  # Transforma em dataframe
  new_votes = pd.DataFrame( [ item.__dict__ for item in new_votes ] )

  if new_votes.shape[0] > 0:

    # Converte a coluna de data para um objeto ISO
    new_votes [ 'data' ] = pd.to_datetime(new_votes.data, format = "%d/%m/%Y")

    # Faz checagens de duplicatas para derrubar um bug observado
    # em algumas das votações registradas na api_original
    new_votes = new_votes.drop_duplicates()

    # Remove votos de parlamentares sem id – geralmente, senadores
    new_votes = new_votes [ new_votes.ideCadastro != "" ]

    # Remove ausências e art. 17, se assim determinado
    if keep_all is False:
      new_votes = new_votes [ (new_votes.voto != "-") & (new_votes.voto != "Art. 17") ]

  # Adiciona os novos votos ao df original e salva
  df = df.append(new_votes, ignore_index = True)
  df.to_csv(df_path, index = False)

######################################
### GERAR ARQUIVOS DA VISUALIZAÇÃO ###
######################################

def gerar_arquivos_viz(freqs, df_path, output_path):
  '''
  Acessa o banco de dados do Basômetro para gerar os
  arquivos de texto necessários para as visualizações.

  Parâmetros:
  freqs -> Os intervalos de tempo pelos quais os dados de votação
  devem ser agrupados. São necessariamente múltiplos de "MS" (month-start).
  df_path -> O caminho até a base de dados com todos os votos do Basômetro.
  output_path -> O caminho até o diretório raiz onde os dados devem ser salvos.
  '''

  def gerar_arquivos_deputados(freqs, df, output_path):
    '''
    Gera arquivos para a visualização que mostra todas as
    votações de um deputado ao longo do tempo.

    Parâmetros:
    freqs -> Herdado da função principal
    df -> O banco de dados com votos do basômetro. Ele é definido pela função principal.
    output_path -> Herdado da função principal.
    '''

    subdir = f"{output_path}/deputados"
    if not os.path.exists(subdir):
      os.makedirs(subdir)

    for freq in freqs:

      ids_cadastro = list( df.ideCadastro.unique() )

      for ideCadastro in ids_cadastro:

        temp = df [ df.ideCadastro == ideCadastro ]

        csv_files = [ ]
        for governo in temp.governo.unique():

          try:
            file = basometro_deputados.calcular_governismo(df = temp,
                                                           ideCadastro = ideCadastro,
                                                           governo = governo,
                                                           freq = freq,
                                                           ajustar_bins_bool = True)

          except basometro_deputados.NoVotes:
            continue

          csv_files.append(file)

        if len(csv_files) > 0:
            file = pd.concat(csv_files)
            file.to_csv(f"{subdir}/{ideCadastro}-{freq}.csv", index = False)

    return

  def gerar_arquivos_partidos(freqs, df, output_path):
    '''
    Gera arquivos para a visualização que mostra todas as
    votações de um deputado ao longo do tempo.

    Parâmetros:
    freqs -> Herdado da função principal
    df -> O banco de dados com votos do basômetro. Ele é definido pela função principal.
    output_path -> Herdado da função principal.
    '''

    subdir = f"{output_path}/partidos"
    if not os.path.exists(subdir):
      os.makedirs(subdir)

    for freq in freqs:

      partidos = list( df.partido.unique() )
      partidos.append("todos") # A palavra-chave 'todos' indica para as funções
                              # do módulo invocado que todos os partidos
                              # devem ser considerados

      for partido in partidos:

        if partido == "todos":
          temp = df.copy()

        else:
          temp = df [ df.partido == partido ]

        csv_files = [ ]
        for governo in temp.governo.unique():

          try:
            file = basometro_partidos.calcular_governismo(df = temp,
                                                           partido = partido,
                                                           governo = governo,
                                                           freq = freq,
                                                           ajustar_bins_bool = True)

          except basometro_partidos.NoVotes:
            continue

          csv_files.append(file)

        if len(csv_files) > 0:
            file = pd.concat(csv_files)
            file.to_csv(f"{subdir}/{partido}-{freq}.csv", index = False)

    return

  def gerar_arquivos_governos(df, output_path):
    '''
    Gera arquivos para a primeira visualização do aplicativo: um histograma
    que agrega o resultado de todas as votações de um determinado governo.

    Parâmetros:
    df -> O banco de dados com votos do basômetro. Ele é definido pela função principal.
    output_path -> Herdado da função principal.
    '''

    subdir = f"{output_path}/governos"
    if not os.path.exists(subdir):
      os.makedirs(subdir)

    for governo in df.governo.unique():

      temp = df [ df.governo == governo ]

      partidos = list( temp.partido.unique() )
      partidos.append("todos")

      for partido in partidos:
        file = basometro_governos.calcular_governismo(df = temp,
                                                      governo = governo,
                                                      partido = partido)

        file.to_csv(f"{subdir}/{governo}-{partido}.csv", index = False)

    return

  def calcular_apoio_historico(df, output_path):
    '''
    Calcula o total de apoio em cada um dos governos e o total histórico.
    Esses valores são então salvos para um json. Eles são necessários para
    calcular uma legenda dinâmica na visualização de dados.

    Parâmetros:
    df -> O dataframe com todos os votos, localizado no diretório df_path, que é lido pela função principal.
    output_path -> O caminho até o diretório raiz onde os dados devem ser salvos.
    '''

    def pegar_historico_df(data):
      # Calcular a média histórica de apoio
      pro_votes   = data [ (data.voto) == (data.orientacaoGoverno) ].shape[0]
      opp_votes   = data [ (data.voto) != (data.orientacaoGoverno) ].shape[0]
      total_votes = data.shape[0]

      value = pro_votes / total_votes
      value = round(value, 2)

      return value

    # Cópia para evitar alterações inplace
    df_ = df.copy()

    # Remove votos sem orientação do governo
    df_ = df_ [ df_.orientacaoGoverno != "Liberado" ]

    # Dicionário para salvar os valores históricos
    json_obj = { }

    historical_value = pegar_historico_df(data = df_)
    json_obj['historico'] = historical_value

    governos = df_.governo.unique()

    for governo in governos:
      temp = df_ [ df_.governo == governo ]
      this_gov_value = pegar_historico_df(data = temp)
      json_obj[governo] = this_gov_value

    with open(f"{output_path}/historicos.json", "w+") as outfile:
      json.dump(json_obj, outfile)

  def gerar_nomes_partidos(df, output_path):
    '''
    Gera um JSON com o nome e id de todos os partidos do banco de dados
    para alimentar o sistema de busca autocomplete.
    '''

    parties = df.drop_duplicates(subset = "partido")
    parties = parties [ [ "partido" ] ]

    json_obj = [ ]

    for index, row in parties.iterrows():

      name = f"{row.partido}"
      id_  = name # Por enquanto, não há necessidade de um id numérico – pode mudar se notarmos queda significativa de performance
      
      obj = { "name" : name, "id" : id_ }
    
      json_obj.append(obj)

    with open(f"{output_path}/partidos.json", "w+") as outfile:
      json.dump(json_obj, outfile)

  def gerar_nomes_deputados(df, output_path):
    '''
    Gera um JSON com o nome e id de todos os deputados do banco de dados
    para alimentar o sistema de busca autocomplete.
    '''

    deps = df.sort_values(by = "data")
    deps = deps.drop_duplicates(subset = "ideCadastro", keep = "last")
    
    deps = deps [ [ "parlamentar", "ideCadastro", "partido", "UF"] ]

    json_obj = [ ]

    for index, row in deps.iterrows():

      name = f"{row.parlamentar} | {row.partido} - {row.UF}"
      id_  = f"{row.ideCadastro}"
      
      obj = { "name" : name, "id" : id_ }
      
      json_obj.append(obj)

    with open(f"{output_path}/deputados.json", "w+") as outfile:
      json.dump(json_obj, outfile)

  def gerar_correspondencias(df, output_path):
    '''
    Gera um objeto JSON com correspondências necessárias
    para adicionar legendas completas à visualização.
    Reúne o deputado com seu último partido e o partido
    com seu nome completo.
    '''

    df_ = df.sort_values(by = "data")

    deps = df_.drop_duplicates(subset = "ideCadastro", keep = "last")
    deps = deps [ [ "parlamentar", "ideCadastro", "partido", "UF"] ]

    parties = df_.drop_duplicates(subset = "partido")
    parties = parties [ ["partido", "descricaoPartido"] ]

    json_obj = { }
    json_obj[ "deputados" ] = { }
    json_obj[ "partidos" ]  = { }

    for index, row in deps.iterrows():

      name =  f"{row.parlamentar}"
      id_   = f"{row.ideCadastro}"
      party = f" {row.partido}"
      uf    = f"{row.UF}"
      
      json_obj["deputados"][id_] = { 
        "name"  : name, 
        "id"    : id_, 
        "party" : party,
        "uf"    : uf 
      }

    for index, row in parties.iterrows():

      party = f"{row.partido}"
      desc  = f"{row.descricaoPartido}"

      json_obj["partidos"][party] = {
        "party"       : party,
        "description" : desc
      }

    with open(f"{output_path}/entity-corresp.json", "w+") as outfile:
      json.dump(json_obj, outfile)

  def definir_valores_escalas(output_path):
    '''
    Esse script é usado para alterar um arquivo json que contém o valor
    máximo de votos nos conjuntos de arquivos de deputados e partidos.
    Isso é necessário porque as escalas dos gráficos de cada partido, de cada
    deputado e de todos os partidos são diferentes.

    Parâmetros:
    output_path -> O caminho até o diretório raiz onde os dados devem ser salvos.
    '''

    def get_max_value(df):

        anti_gov = df.antiGovCtg.tolist()
        pro_gov  = df.proGovCtg.tolist()
        max_vl = max( anti_gov + pro_gov )

        return max_vl

    subdirs = [ "partidos", "deputados" ]

    json_obj = { }

    # Pega os maiores valores para as escalas de partidos ou deputados individuais
    for subdir in subdirs:

        files = glob.glob(f"{output_path}/{subdir}/*.csv")

        df = pd.concat ([ pd.read_csv(file) for file in files if "todos" not in file ])

        max_value = get_max_value(df)

        json_obj[subdir] = max_value

    # Pega o maior valor para a escala de todos os partidos
    df = pd.read_csv(f"{output_path}/partidos/todos-MS.csv")

    max_value = get_max_value(df)

    json_obj["todos"] = max_value

    with open(f"{output_path}/escalas.json", "w+") as outfile:
        json.dump(json_obj, outfile)

  def definir_hora_atualizacao(output_path):
    '''
    Gera json com data da última atualização
    '''

    json_obj = { }
    date = datetime.datetime.now()

    json_obj["lastUpdate"] = str(date)

    with open(f"{output_path}/last-update.json", "w+") as outfile:
      json.dump(json_obj, outfile)

  ############################
  ### Execução da função   ###
  ### gerar_arquivos_viz() ###
  ############################

  df = pd.read_csv(df_path, dtype = str)

  if not os.path.exists(output_path):
    os.makedirs(output_path)

  gerar_arquivos_governos(df, output_path)

  calcular_apoio_historico(df, output_path)
  gerar_nomes_partidos(df, output_path)
  gerar_nomes_deputados(df, output_path)
  gerar_correspondencias(df, output_path)

  gerar_arquivos_partidos(freqs, df, output_path)
  gerar_arquivos_deputados(freqs, df, output_path)

  definir_valores_escalas(output_path)
  definir_hora_atualizacao(output_path)

  return
