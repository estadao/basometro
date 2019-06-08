'''
Esse script deve ser executado para capturar os dados
e montar a estrutura de dados do Basômetro pela primeira vez.
Ao final da execução, são gerados um banco de dados de votos completo
e os arquivos .csv necessários para a geração das visualizações de dados.
'''

from camaraPy.api_original import proposicoes as campy_proposicoes
from basometro import basometro_coleta, basometro_aplicativo
from basometro.core import core as basometro_core
import datetime, glob, os, shutil
import pandas as pd

def instalar_basometro():

  def coletar_dados_api(start_year, end_year, keep_all = False):
    '''
    A função o módulo de coleta do Basômetro para acessar a API da Câmara e armazenar todas as votações
    que ocorreram etre os anos especificados. O parâmetro `keep_all`, nesse caso, significa que vamos
    descartar da base de dados as faltas e situações em que o presidente da Câmara optou por invocar o
    Artigo 17 do regimento interno – dispositivo que permite que ele não participe da votação.

    Parâmetros:
    start_year -> O ano de início da coleta. Pode ser int ou str.
    end_year -> O ano de término da coleta. Pode ser Sint ou str.
    keep_all -> Indica se deve o coletor deve descartar faltas e invocações do Artigo 17. Booleano.
    '''
    database = basometro_coleta.coletar_votos(start_year, end_year, keep_all)

    return database

  def obter_votacoes_faltantes(database):
    '''
    Essa função adiciona manualmente algumas votações que não constam no banco de dados da Câmara dos Deputados.
    Em conversas com a equipe técnica da instituição, fomos informados de que as votações feitas via painel são
    catalogadas automaticamente, mas isso não acontece com as votações por chamada, como nos casos de denúncia de
    responsabilidade contra o presidente – nesse caso, algumas delas foram adicionadas pelo setor responsável e
    outras não.  Nesses casos, compilamos os dados manualmente de acordo com o que foi noticiado pela imprensa à
    época, já que a Câmara não fornece dados oficiais. Nessa função, padronizamos os dados conforme o restante
    da base.

    Parâmetros:
    database -> O banco de dados completo do basômetro, gerado em coletar_dados_api. Formato dataframe.
    '''

    def obter_votos_faltantes(database, missing_session_fpath, names, keep_all):

      def ler_arquivo(missing_session_fpath, names, keep_all):
        '''
        Lê um arquivo csv com os votos de uma sessão faltante.

        Parâmetros:
        missing_session_fpath -> Caminho até o arquivo com os dados de votação.
        names -> Array com os nomes da colunas.
        keep_all -> Indica se deve o coletor deve descartar faltas e invocações do Artigo 17. Booleano.
        '''
        missing_session = pd.read_csv(missing_session_fpath, dtype = str, names = names)

        if not keep_all:
          missing_session = missing_session [ (missing_session.voto != "-") & (missing_session.voto != "Art. 17")]

        return missing_session

      def adicionar_detalhes_votos(missing_session, missing_session_fpath):
        '''
        Adiciona detalhes como data, orientação do governo e tipo de proposição de cada uma das proposições faltantes.

        Parâmetros:
        missing_session -> O dataframe gerado por ler_arquivo
        missing_sessions_fpath -> O caminho até o csv do dataframe. É usada para escolher os dados corretos.
        '''

        if "impeachment-dilma" in missing_session_fpath:

          missing_session["governo"]           = "Dilma 2"
          missing_session["hora"]              = "23:59"
          missing_session["idVotacao"]         = "MANUAL_DCR.1.2016"
          missing_session["numeroProposicao"]  = "1"
          missing_session["tipoProposicao"]    = "DCR"
          missing_session["anoProposicao"]     = 2017
          missing_session["orientacaoGoverno"] = "Não"
          missing_session["data"]              = "2016-04-17"


        elif "primeira-denuncia-temer" in missing_session_fpath:

          missing_session["governo"]           = "Temer 1"
          missing_session["hora"]              = "23:08"
          missing_session["idVotacao"]         = "MANUAL_DCR.1.2017"
          missing_session["numeroProposicao"]  = "1"
          missing_session["tipoProposicao"]    = "DCR"
          missing_session["anoProposicao"]     = 2017
          missing_session["orientacaoGoverno"] = "Sim"
          missing_session["data"]              = "2017-08-02"

        elif "segunda-denuncia-temer" in missing_session_fpath:

          missing_session["governo"]           = "Temer 1"
          missing_session["hora"]              = "23:08"
          missing_session["idVotacao"]         = "MANUAL_DCR.2.2017"
          missing_session["numeroProposicao"]  = "2"
          missing_session["tipoProposicao"]    = "DCR"
          missing_session["anoProposicao"]     = 2017
          missing_session["orientacaoGoverno"] = "Sim"
          missing_session["data"]              = "2017-10-25"

        return missing_session

      def adicionar_id_deputados(database, missing_session, missing_session_fpath):
        '''
        As bases que coletamos manualmente não contém o número identificador
        de cada deputado. Essa função adiciona os valores via pd.merge.
        Entretanto, há alguns parlamentares com grafia diferente. Estes terão
        os identifadores, que foram levantados manualmente, adicionados no braço.

        Parâmetros:
        database -> A base de dados completa do basômetro
        missing_session -> Datafame com os votos faltantes de uma votação específica
        missing_sessions_fpath -> O caminho até o csv do dataframe. É usada para escolher os dados corretos.
        '''

        def substituir_id(row, missing_ids):
          '''
          Executa a substituição via método apply.
          '''
          if row.ideCadastro == "CORRIGIR":
              ideCadastro = missing_ids[ row.parlamentar ]

          else:
              ideCadastro = row.ideCadastro

          return pd.Series({
              "ideCadastro" : ideCadastro
          })

        # Seleciona no banco de dados apenas os parlamentares do governo específico
        if "impeachment-dilma" in missing_session_fpath:
          id_data = database [ database.governo == "Dilma 2" ]
          id_data = id_data[ ['parlamentar', 'ideCadastro'] ].drop_duplicates()

        elif "denuncia-temer" in missing_session_fpath:
          id_data = database [ database.governo == "Temer 1" ]
          id_data = id_data[ ['parlamentar', 'ideCadastro'] ].drop_duplicates()

        # Faz merge com id_data e preenche as entradas sem correspondência com "CORRIGIR"
        missing_session = missing_session.merge(id_data, how = 'left', on = 'parlamentar').fillna("CORRIGIR")

        # Substitui todos os parlamentares que ficaram para ser corrigidos
        missing_ids = {
          "André de Paula"        : "74471",
          "Chico D'Angelo"        : "141439",
          "Dagoberto Nogueira"    : "141411",
          "Delegado Francischini" : "160646",
          "Eduardo Cunha"         : "74173",
          "Evair Vieira de Melo"  : "178871",
          "Franklin"              : "186775",
          "Izalci Lucas"          : "4931",
          "Jozi Araújo"           : "178851",
          "Patrus Ananias"        : "74160",
          "Zeca do PT"            : "178902"
          }

        missing_session[ "ideCadastro" ] = missing_session.apply(substituir_id, args = [ missing_ids ], axis = 1)

        assert "CORRIGIR" not in list(missing_session.ideCadastro)

        return missing_session

      def padronizar_partidos(missing_session):
        '''
        Atualiza o nome do partido para o registro mais recente.
        Assim, entradas como "PMDB" viram "MDB" – a sigla atual.

        Parâmetros:
        missing_session -> O dataframe com votos faltantes.
        '''

        def padronizar_partido(row):
          '''
          Função para ser rodada via o método apply do pandas.
          Ela invoca a função padronizar_partido do módulo core do basômetro.
          '''

          partido = basometro_core.padronizar_partido(row.partido)

          return pd.Series({
              "partido" : partido,
          })

        missing_session['partido'] = missing_session.apply(padronizar_partido, axis = 1)

        return missing_session

      def adicionar_votos_faltantes(database, missing_session):
        '''
        Ao final do processo, resta apenas adicionar os votos recém padronizados
        ao banco de dados completo.

        Parâmetros:
        database -> O banco de dados completo do basômetro, em formato dataframe.
        missing_session -> O banco de dados, já padronizado, de uma sessão da Câmara que não consta na API.
        '''

        database = database.append(missing_session, ignore_index = True)
        return database

      ##############################################
      ### EXECUÇÃO DE obter_votos_faltantes() ###
      ##############################################
      missing_session = ler_arquivo(missing_session_fpath = missing_session_fpath,
                                    names = names,
                                    keep_all = keep_all)

      missing_session = adicionar_detalhes_votos(missing_session = missing_session,
                                                missing_session_fpath = missing_session_fpath)

      missing_session = adicionar_id_deputados(database = database,
                                               missing_session = missing_session,
                                               missing_session_fpath = missing_session_fpath)

      missing_session = padronizar_partidos(missing_session)

      database = adicionar_votos_faltantes(database = database,
                                          missing_session = missing_session)

      return database

    ##############################################
    ### EXECUÇÃO DE obter_votacoes_faltantes() ###
    ##############################################
    names = ['parlamentar', 'voto', 'partido', 'UF']
    missing_session_fpaths = glob.glob("database/votacoes-ausentes/*.csv")

    for missing_session_fpath in missing_session_fpaths:
      database = obter_votos_faltantes(database = database,
                                       missing_session_fpath = missing_session_fpath,
                                       names = names,
                                       keep_all = False)

    return database

  ########################################
  ### EXECUÇÃO DE instalar_basometro() ###
  ########################################

  print("Esse script monta a estrutura de dados necessária para rodar o Basômetro pela primeira vez.\n")

  # Coleta dados da API
  current_year = datetime.datetime.now().year
  database = coletar_dados_api(start_year = 2003,
                               end_year   = current_year,
                               keep_all   = False)

  # Preenche banco de dados com votações faltantes
  print("Agora vamos obter as votações por chamada.")
  database = obter_votacoes_faltantes(database = database)

  # Salva banco de dados em formato csv
  df_path = "./database/basometro.csv"
  database.to_csv(df_path, index = False, encoding = 'utf-8')

  print("E agora vamos gerar os arquivos para a visualização de dados.")

  output_path = "./output/"
  if os.path.exists(output_path):
    shutil.rmtree(output_path)

  freqs = [ "MS" ] # Frequências para criar bins temporais
  basometro_aplicativo.gerar_arquivos_viz(freqs = freqs,
                                          df_path = df_path,
                                          output_path = output_path)
  print("Pronto!")
  return

##############
### main() ###
##############

def main():
  instalar_basometro()

if __name__ == "__main__":
    main()
