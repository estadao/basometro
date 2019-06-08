'''
Calcula os dados necessários para traçar um
panorama geral da base aliada de cada governo.
Gera os dados necessários para os histogramas.
'''

from basometro.core import core
import pandas as pd

def calcular_governismo(df, governo, partido):

  '''
  Calcula o percentual de governismo de todos os deputados que votaram em
  determinada gestão do executivo. Retorna os valores como dataframe.

  Parâmetros:
  df -> Um dataframe do pandas, gerado pela função coletar_votos
  governo -> Uma string que identifica qual o governo cujas votações devem ser consideradas.
  O valor "todos" pode ser passado para que o cálculo considere todos os governos.
  partido -> Uma string que identifica o partido para o qual o cáluclo deve ser feito.
  '''

  # Checa se o cálculo foi para um dos governos suportados
  if governo not in core.GOVERNOS_SUPORTADOS.keys():
    raise ValueError(f"Atualmente são suportados apenas os seguintes governos: {core.GOVERNOS_SUPORTADOS.keys()}")

  df_ = df.copy()

  df_ = df_ [ df_.governo == governo ]

  if partido != "todos":
    df_ = df_ [df_.partido == partido ]

  # Remove da base dados em que a organização do governo seja 'Liberado'
  df_ = df_[ df_.orientacaoGoverno != 'Liberado' ]

  # Calcula quantas sessões ocorreram neste governo COM ORIENTAÇÃO DA BANCADA
  total_sessoes_governo = df_.idVotacao.unique().shape[0]

  # Para cada deputado na base já filtrada, calcula uma taxa de governismo
  # e outras informações úteis (número total de votos, número de votos pro governo)
  new_df = [ ]
  id_deputados = df_.ideCadastro.unique()

  for id_deputado in id_deputados:

    # Filtra e recupera índices padrão
    temp = df_ [ df_.ideCadastro == id_deputado ]
    temp = temp.reset_index()

    # Pega os últimos nome, uf e partidos usados pelo parlamentar no período
    parlamentar         = temp.loc[ (temp.shape[0] - 1), 'parlamentar' ]
    partido_parlamentar = temp.loc[ (temp.shape[0] - 1), 'partido' ]
    uf_parlamentar      = temp.loc[ (temp.shape[0] - 1), 'UF' ]

    # Contabiliza votos e votações
    total_votes       = temp.shape[0]
    total_sessions    = temp.idVotacao.unique().shape[0]

    # Um deputado não pode votar duas vezes na mesma sessão, mas há dados
    # problemáticos da Câmara em que isso ocorre. O problema deve ter sido
    # resolvido na coleta, mas uma checagem a mais nunca machucou ninguém.
    assert(total_votes == total_sessions)

    # Calcula também o percentual de comparecimento do deputado – ou seja,
    # o percentual de sessões da legislatura em que ele esteve presente.
    assiduidade_parlamentar = round(total_votes / total_sessoes_governo, 2)

    # Calcula a contagem de votos pró e contra governo
    pro_gov_count   = temp [ temp.orientacaoGoverno == temp.voto ].shape[0]
    anti_gov_count  = total_votes - pro_gov_count

    # Calcula o percentual de votos pró e contra governo
    pro_gov_percentage  = round(pro_gov_count / total_votes, 2)
    anti_gov_percentage = round(1 - pro_gov_percentage, 2)

    datapoint = {
      "ideCadastro"              : id_deputado,
      "parlamentar"              : parlamentar,
      "partido"                  : partido_parlamentar,
      "uf"                       : uf_parlamentar,
      "governo"                  : governo,
      "proGovPct"                : pro_gov_percentage,
      "antiGovPct"               : anti_gov_percentage,
      "proGovCtg"                : pro_gov_count,
      "antiGovCtg"               : anti_gov_count,
      "totalVotos"               : total_votes,
      "totalVotacoes"            : total_sessions,
      "totalSessoesGoverno"      : total_sessoes_governo,
      "assiduidadeParlamentar"   : assiduidade_parlamentar,
    }

    new_df.append( datapoint )

  # print()

  # Transforma dataframe e renomeia colunas
  new_df = pd.DataFrame(new_df)

  return new_df
