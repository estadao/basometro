'''
As funções desse módulo usam o camaraPy, wrapper para a API original das Câmara
dos Deputados desenvolvida pelo Estadão, para acesar o resultado das votações
de todas as proposições que tiveram votação nominal e estão registradas nos
sistemas do Congresso.
'''

from basometro.core import core
from camaraPy.api_original.core import custom_exceptions
from camaraPy.api_original import proposicoes
import datetime
import pandas as pd

###################
# COLETA DE DADOS #
###################

def coletar_votos(start_year, end_year, warn_proposicao_acessoria = False, keep_all = False):

  '''
  Função que coleta todos os votos que aconteceram
  em um determinado intervalo de anos. Essa rotina
  retorna um dataframe com todos os votos do período.

  Parâmetros:
  start_year -> Primeiro ano em que os votos devem ser coletados
  end_year -> Segundo ano em que os votos devem ser coletados
  warn_proposicao_acessoria -> Booleano que determina se deve ser
  printado no console um aviso sempre que o coletor encontrar
  uma proposição acessória, que não tem votos associados.
  keep_all -> Booleano que, se verdadeiro, coleta TODOS os votos,
  incluindo abstenções e invocações do artigo 17.
  '''

  votos_arr = [ ]

  start_year = int(start_year)
  end_year   = int(end_year)

  for year in range(start_year, end_year + 1):

    print(f"Coletando o ano {year}")

    # Faz solicitação para a API
    data = proposicoes.ListarProposicoesVotadasEmPlenario( { "Ano" : year } )

    # Pega os ids únicos de cada votação
    data = data['proposicoes']['proposicao']

    # O método retorna um id para cada vez que a proposição foi votada.
    # Queremos os ids únicos.
    ids_proposicao = list( set( [ item['codProposicao'] for item in data ] ) )

    # Para cada id, faz nova solicitação e pega os parâmetros necessários pata obter as votações
    for index, id_proposicao in enumerate(ids_proposicao):

      print(f"Estamos na proposição {id_proposicao}, que é a número {index + 1} de {len(ids_proposicao)} deste ano".ljust(80), end='\r')

      prop = proposicoes.ObterProposicaoPorID( { "IdProp" : id_proposicao } )
      prop = prop['proposicao']

      params = {
          "Tipo"   : prop['@tipo'].strip(),
          "Numero" : prop['@numero'].strip(),
          "Ano"    : prop['@ano'].strip()
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

      except custom_exceptions.ProposicaoAcessoria as e:
        if warn_proposicao_acessoria:
          print(f"Exceção ProposicaoAcessoria aconteceu no id {id_proposicao}")
        continue

      # Se os dados vêm na forma de lista, a proposição em questão
      # tem ao menos duas votações associadas à ela.
      if isinstance(votacoes, list):

        for votacao in votacoes:

          # Essa checagem é necessária para não pegar todas as votações
          # de uma proposição que apareceu no plenário em mais de um ano
          if votacao["@Data"][-4:] == str(year):

            # Cria um novo elemento que vai ser passado para o objeto Votacao
            votacao["dadosProposicao"] = dados_proposicao

            votacao = core.Votacao(votacao)
            votos_arr.extend(votacao.votos)


      # Se houve apenas uma votação, porém, os dados vêm como um dicionário
      # solto e só precsisamos transformar ela em um objeto votação do basômetro.
      elif isinstance(votacoes, dict):

        # Essa checagem é necessária para não pegar todas as votações
        # de uma proposição que apareceu no plenário em mais de um ano
        if votacoes["@Data"][-4:] == str(year):

          # Cria um novo elemento que vai ser passado para o objeto Votacao
          votacoes["dadosProposicao"] = dados_proposicao

          votacao = core.Votacao(votacoes)
          votos_arr.extend(votacao.votos)
      # print()

    print("\n")

  # Transforma a lista de objetos 'voto' em um DataFrame
  df = pd.DataFrame( [ item.__dict__ for item in votos_arr ] )

  # Converte a coluna de data para um objeto ISO
  df['data'] = pd.to_datetime(df.data, format = "%d/%m/%Y")

  '''
  AVISO

  A solução abaixo é terrível e podemos estar perdendo
  dados relevantes. Entretanto, no estado atual da API,
  é a saída possível.

  Como a API retorna entradas duplicadas, seja porque há
  votações inteiras ou votos individuais repetidos, precisamos
  nos livrar deles. A maneira mais óbvia é um simples df.drop_duplicates().
  Se o voto é rigorosamente igual, feito na mesma hora e na mesma votação
  específica, as chances são altas de que seja uma duplicata.
  Assim, vamos derrubar todas.
  '''

  df = df.drop_duplicates()

  # Remove votos de parlamentares sem id – geralmente, senadores
  df = df[ df.ideCadastro != "" ]

  if keep_all is False:
    # Remove ausências e art. 17
    df = df [ (df.voto != "-") & (df.voto != "Art. 17")]

  return df
