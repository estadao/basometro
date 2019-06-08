'''
Calcula os dados necessários para traçar a evolução
do governismo de cada um dos partidos ao longo do tempo.
Gera os dados necessários para os gráficos de linha.
'''
from basometro.core import core
import datetime
import pandas as pd


class NoVotes(ValueError):
  '''
  Exceção para o caso específico de deputado que
  não têm nenhum voto registado em votações nas quais
  o governo emitiu uma orientação para a base aliada.
  '''
  pass

def calcular_governismo(df, partido, governo , freq = "MS", ajustar_bins_bool = True):

  '''
  Calcula a média de votos pró-governo do partido selecionado, agrupando
  os dados no intervalo de tempo determinado no parâmetro janela.

  Parâmetros:
  df -> A base de dados de votos do Basômetro, criada no módulo basometro_coleta
  partido -> Uma string com o nome do partido desejado. ("PT", por exemplo). É possível, também, passar
  o parâmetro "TODOS" para calcular o governismo de toda a Câmara dos Deputados no período.
  governo -> Uma string que determina o período do governo para analisar. ("Lula 1", por exemplo.)
  freq -> O intervalo de tempo em que os dados de votação devem ser agrupados para cálculo da média de governismo
  ajustar_bins_bool -> Booleano. Caso verdadeiro, intervalos de tempo em que não houve nenhum voto registrado
  são "normalizados", fazendo com que o datapoint acesse o percentual de governismo do datapoint imediatamnte
  anterior – ou, caso ele seja o primeiro da série, seja removido do banco de dados Default: True.
  '''

  ##########################
  ### FUNÇÕES AUXILIARES ###
  ##########################

  def calcular_governismo_por_intervalos(df, partido, governo, freq):
    '''
    Essa função será chamada para criar uma lista de pontos temporais, que posteriormente será
    transformada em dataframe e retornada pela função principal.

    Primeiro, ela cria uma estrutura de dados vazia para ser preenchida com os novos dados.
    Então, divide o período total em bins de tempo igualitárias. Para cada uma das bins, seleciona
    todos os votos que estão no intervalo de tempo, aplica o cálculo para descobrir o governismo
    e adiciona o resultado para a estrutura de dados criada anteriormente.

    Parâmetros:
    df -> A base de dados já filtrada por partido e governo
    partido -> O partido, herdado da função principal
    governo -> O governo, herado da função principal
    freq -> O intervalo de tempo para agrupar os dados, herdado da função principal
    '''

    # Constante que representa um segundo.
    # Vai ser usada para evitar que as bins temporais se sobreponham.
    one_second = datetime.timedelta(seconds = 1)

    new_df = [ ]

    # Seleciona as datas de início e fim do governo
    date_extent = core.GOVERNOS_SUPORTADOS[governo]
    assert len(date_extent) == 2

    # A partir delas, cria um intervalo de datas
    date_range = [ pd.to_datetime(item, format = "%d/%m/%Y") for item in date_extent ]
    date_range = list( pd.date_range( start = date_range[0], end = date_range[1], freq = freq ) )    # Referência: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.date_range.html

    # É preciso adicionar o último dia de governo de cada um dos presidentes.
    # Ele acaba cortado pela função pd.date_range, que só pega os inícios de mês
    end_of_term = pd.to_datetime(date_extent[1], format = "%d/%m/%Y").replace(hour = 23, minute = 59, second = 59)
    date_range.append(end_of_term)

    # Cria pares com datas iniciais e finais para selecionar os dados
    date_pairs = [ ]
    for start, end in zip( date_range[:-1], date_range[1:] ):
      if end != end_of_term:
        end = end - one_second

      date_pair = (start, end)
      date_pairs.append(date_pair)

    # O governo Temer é o único que não se inicia em um começo de mês.
    # Assim, precisamos adicionar um par de datas inicial manualmente.
    if governo == "Temer 1":

      date_pair = ( pd.to_datetime("2016-05-13"), date_pairs[0][0] - one_second )
      date_pairs.insert(0, date_pair)

    # Checa se o primeiro e último dia dos intervalos correspondem às datas do governo
    assert date_pairs[0][0].date()   == pd.to_datetime(core.GOVERNOS_SUPORTADOS[governo][0], format = "%d/%m/%Y").date()
    assert date_pairs[-1][-1].date() == pd.to_datetime(core.GOVERNOS_SUPORTADOS[governo][1], format = "%d/%m/%Y").date()

    # Seleciona os votos que ocorream dentro do período e calcula o governismo nesse intervalo
    for date_pair in date_pairs:

      assert len(date_pair) == 2

      start = date_pair[0]
      end = date_pair[1]

      temp = df [ start : end ]
      total_sessions = temp.idVotacao.unique().shape[0]

      total_votes    = temp.shape[0]
      pro_gov_count  = temp [ temp.voto == temp.orientacaoGoverno ].shape[0]
      anti_gov_count = total_votes - pro_gov_count

      if total_votes != 0:
        pro_gov_percentage  = round(pro_gov_count / total_votes, 2)
        anti_gov_percentage = round(1 - pro_gov_percentage, 2)

      else:
        pro_gov_percentage  = "NO_VOTES"
        anti_gov_percentage = "NO_VOTES"

      datapoint = {
        "partido"       : partido,
        "governo"       : governo,
        "proGovPct"     : pro_gov_percentage,
        "antiGovPct"    : anti_gov_percentage,
        "proGovCtg"     : pro_gov_count,
        "antiGovCtg"    : anti_gov_count,
        "totalVotos"    : total_votes,
        "totalVotacoes" : total_sessions,
        "dataInicio"    : start,
        "dataFim"       : end,
      }


      new_df.append(datapoint)

    return new_df

  def ajustar_bins(arr):
    '''
    Essa função só é executada caso o parâmetro "ajustar_bins" da função principal
    seja verdadeiro. Ela opera sobre intervalos de tempo onde não houve nenhum voto,
    fazendo com que estes datapoints registrem o percentual de governismo do datapoints
    imediatamente anterior (ou, caso seja o primeiro da série, remove da lista). Isso
    é útil para evitar que gráficos gerados a partir dos dados mostrem oscilanções
    que, na prática, nunca ocorreram.
    '''

    def trim(arr):
      '''
      Recursivamente, remove pontos temporais sem votos das bordas da lista
      '''

      if (arr[0]["proGovPct"] != "NO_VOTES") and (arr[-1]["proGovPct"] != "NO_VOTES"):
        return arr

      else:

        for index, item in enumerate(arr):

          if item["proGovPct"] == "NO_VOTES":

            if index == 0 or index == len(arr) - 1:
              arr.pop(index)

        return trim(arr)

    def replace(arr):
      '''
      Substitui os itens sem votos (já que restaram apenas os do meio da array) pelo
      pelo valor de governismo do item imediatamente anterior
      '''
      for index, item in enumerate(arr):
        if item["proGovPct"] == "NO_VOTES":

          arr[index]["proGovPct"]  = arr[index - 1]["proGovPct"]
          arr[index]["antiGovPct"] = arr[index - 1]["antiGovPct"]

      return arr

    arr = trim(arr)
    arr = replace(arr)
    return arr

##########################
### EXECUÇÃO PRINCIPAL ###
##########################

  if freq not in ['MS', '2MS', '3MS', '4MS',
                  '5MS', '6MS', '7MS', '8MS',
                  '9MS', '10MS', '11MS', '12MS']:
    raise TypeError("As frequências suportados são apenas MS ou múltiplos (2MS, 3MS, etc.)")

  # Checa se o governo é suportado pelo Basômetro
  if governo not in core.GOVERNOS_SUPORTADOS.keys():
    raise TypeError(f"Os governos suportados são os seguintes: {core.GOVERNOS_SUPORTADOS.keys()}")

  # Copia para evitar mudanças indesejadas no objeto original
  df_ = df.copy()

  # Remove da base dados em que a organização do governo seja 'Liberado'
  df_ = df_[ df_.orientacaoGoverno != 'Liberado' ]

  if partido.lower() == "todos":
    # Caso positivo, os dados levam em conta os votos registrados por toda a Câmara dos Deputados
    df_ = df_ [ df_.governo == governo ]

  else:
    # Filtra para manter apenas os partidos e o governo relevantes no banco de dados
    df_ = df_ [ (df_.partido == partido) & (df_.governo == governo) ]

  # Se não há votos, retornar nada
  if df_.shape[0] == 0:
    raise NoVotes(f"O partido {partido} não votou em nenhuma votação na qual houve orientação do governo")

  # Coloca data no índice
  df_["data"] = pd.to_datetime(df_.data)
  df_ = df_.set_index("data")
  df_ = df_.sort_index()

  # Executa cálculo
  new_df = calcular_governismo_por_intervalos(df = df_, partido = partido, governo = governo, freq = freq)
  assert len(new_df) > 0

  # Preenche os valores com NO_VOTE usando o datapoint imediatamente anterior
  if ajustar_bins_bool is True:
    new_df = ajustar_bins(new_df)

  new_df = pd.DataFrame(new_df)
  return new_df
