from camaraPy.api_original.core import core, custom_exceptions
from camaraPy.api_original import proposicoes, deputados
import datetime
import pandas as pd

######################
#                    #
# PARÂMETROS GLOBAIS #
#                    #
######################


GOVERNOS_SUPORTADOS = {
  "Lula 1"      : (  "1/1/2003",  "31/12/2006" ),
  "Lula 2"      : (  "1/1/2007",  "31/12/2010" ),
  "Dilma 1"     : (  "1/1/2011",  "31/12/2014" ),
  "Dilma 2"     : (  "1/1/2015",  "12/5/2016"  ),
  "Temer 1"     : (  "13/5/2016",  "31/12/2018"),
  "Bolsonaro 1" : (  "1/1/2019",  "31/12/2021" ),
}

###########
# CLASSES #
###########

class Voto(object):
  def __init__(self, dictionary):
    self.parlamentar       = dictionary['@Nome'].strip()
    self.ideCadastro       = dictionary['@ideCadastro'].strip()
    self.UF                = dictionary['@UF'].strip()
    self.voto              = dictionary['@Voto'].strip()
    self.partido           = padronizar_partido(dictionary['@Partido'].strip())
    self.descricaoPartido  = pegar_descricao_partido(f"{self.partido}")

    # Estes abaixos serão preenhcidos apenas quando o objeto
    # Voto for gerado dentro de um objeto da classe Votacao
    self.orientacaoGoverno = 'NOT_INITIATED'
    self.data              = 'NOT_INITIATED'
    self.hora              = 'NOT_INITIATED'
    self.governo           = 'NOT_INITIATED'
    self.idVotacao         = 'NOT_INITIATED'
    self.tipoProposicao    = 'NOT_INITIATED'
    self.numeroProposicao  = 'NOT_INITIATED'
    self.anoProposicao     = 'NOT_INITIATED'

class Votacao(object):
  def __init__(self, dictionary):
    self.tipoProposicao    = dictionary["dadosProposicao"]["tipoProposicao"]
    self.anoProposicao     = dictionary["dadosProposicao"]["anoProposicao"]
    self.numeroProposicao  = dictionary["dadosProposicao"]["numeroProposicao"]
    self.resumo            = dictionary['@Resumo'].strip()
    self.data              = dictionary['@Data'].strip()
    self.hora              = dictionary['@Hora'].strip()
    self.objVotacao        = dictionary['@ObjVotacao'].strip()
    self.codSessao         = dictionary['@codSessao'].strip()
    self.governo           = descobrir_governo(self.data)
    self.idVotacao         = f"{self.data.strip()}.{self.hora.strip()}.{self.codSessao.strip()}".replace("/","-").replace(":",".")

    if 'orientacaoBancada' in dictionary.keys():
      orientacoes = dictionary['orientacaoBancada']['bancada']
      # Itera via next até encontrar a orientação do governo. Caso não tenha, retorna 'Liberado'
      self.orientacaoGoverno = next( (item["@orientacao"].strip() for item in orientacoes if item["@Sigla"].strip() == "GOV."), 'Liberado')

    # Em alguns casos, não há orientação das bancadas. Tratamos como 'Liberado'
    else:
      self.orientacaoGoverno = 'Liberado'

    # Inicializa os votos contados
    self.votos             = [ Voto(item) for item in dictionary['votos']['Deputado'] ]
    for voto in self.votos:
      voto.orientacaoGoverno = self.orientacaoGoverno
      voto.idVotacao         = self.idVotacao
      voto.data              = self.data
      voto.hora              = self.hora
      voto.governo           = self.governo
      voto.tipoProposicao    = self.tipoProposicao
      voto.numeroProposicao  = self.numeroProposicao
      voto.anoProposicao     = self.anoProposicao

class Parlamentar(object):
  '''
  Objetos devem ser inicializados a partir de um dicionário que contém todos os seus votos,
  junto com os dados biográficos/políticos (como histórico de comisssões de cada um deles.
  '''
  def __init__(self, dict):
    self.nomeParlamentar             = ''
    self.ideCadastro                 = ''
    self.votos                       = ''
    self.UF                          = '' # Vale colocar as ufs por período?
    self.participacaoComissoes       = ''


######################
#                    #
# FUNÇÕES AUXILIARES #
#                    #
######################

def padronizar_partido(string):
  '''
  A API retorna o nome do partido como existia na época da votação.
  Assim, votos de uma mesma agremiação podem estar registrados de forma
  diferente. Essa função faz o ajuste histórico, além de corrigir inconsistências
  meio inexplicáveis no retorno da API.
  '''

  # Dicionário com as correções necessárias
  corresp = {

  "PPB"        : "Progressistas",
  "PP"         : "Progressistas",
  "PPS"        : "Cidadania",
  "CIDADANIA"  : "Cidadania",
  "PFL"        : "DEM",
  "PMDB"       : "MDB",
  "S.Part."    : "Sem Partido",
  "PMR"        : "PRB",
  "PTdoB"      : "Avante",
  "PEN"        : "Patriota",
  "SD"         : "Solidariedade",
  "SDD"        : "Solidariedade",
  "Solidaried" : "Solidariedade",
  "PSDC"       : "DC",
  "PTN"        : "Podemos",
  "PODE"       : "Podemos",
  "PODEMOS"    : "Podemos",
  "NOVO"       : "NOVO",
  "PR"         : "PL",

  }

  if string in corresp.keys():
    return corresp[string]

  else:
    return string

def pegar_descricao_partido(string):
  '''
  Pega o nome completo da sigla do partido e, usando
  um dicionário, traz uma descrição detalhada do significado
  da sigla ou outra informação adicional relevante.
  '''

  corresp = {
   'MDB'          : "Movimento Democrático Brasileiro",
   'Cidadania'    : "Antigo Partido Popular Socialista (PPS)",
   'PDT'          : "Partido Democrático Trabalhista",
   'PT'           : "Partido dos Trabalhadores",
   'PSB'          : "Partido Socialista Brasileiro",
   'DEM'          : "Democratas",
   'PTB'          : "Partido Trabalhista Brasileiro",
   'PL'           : "Partido Liberal – antigo Partido da República (PR)",
   'Progressistas': "Antigo Partido Progresista (PP)",
   'PSDB'         : "Partido da Social Democracia Brasileira",
   'PCdoB'        : "Partido Comunista do Brasil (PCdoB)",
   'Sem Partido'  : " ",
   'PRONA'        : "Partido de Reedificação da Ordem Nacional",
   'PV'           : "Partido Verde",
   'PSC'          : "Partido Social Cristão",
   'PMN'          : "Partido da Mobilização Nacional",
   'PST'          : "Partido Social Trabalhista",
   'PSL'          : "Partido Social Liberal",
   'PRP'          : "Partido Republicano Progressista",
   'PSOL'         : "Partido Socialismo e Liberdade",
   'PRB'          : "Partido Republicano Brasileiro",
   'PTC'          : "Partido Trabalhista Cristão",
   'PR'           : "Partido da República",
   'PAN'          : "Partido dos Aposentados da Nação",
   'Avante'       : "Antigo Partido Trabalhista do Brasil (PTdoB)",
   'PHS'          : "Partido Humanista da Solidariedade",
   'PRTB'         : "Partido Renovador Trabalhista Brasileiro",
   'PSD'          : "Partido Social Democrático",
   'Patriota'     : "Antigo Partido Ecológico Nacional (PEN)",
   'Solidariedade': " ",
   'PROS'         : "Partido Republicano da Ordem Social (PROS)",
   'DC'           : "Democracia Cristã",
   'Podemos'      : "Antigo Partido Trabalhista Nacional (PTN)",
   'REDE'         : "Rede Sustentabilidade",
   'PMB'          : "Partido da Mulher Brasileira",
   'PPL'          : "Partido Pátria Livre",
   'NOVO'         : "Partido Novo"
  }

  if string in corresp.keys():
    return corresp[string]

  else:
    return " "

def converter_datetime(string):
  return datetime.datetime.strptime(string, "%d/%m/%Y")

def descobrir_governo(data):

  '''
  Função que recebe uma data em formato d/m/yyyy
  e retorna o presidente que estava governando o
  país na época.
  '''

  # Transforma a string passada pelo usuário em um bojeto de data
  datetime_obj = converter_datetime(data)

  # Itera pelos itens do dicionário até encontrar o governo correto.
  for gov, dates in GOVERNOS_SUPORTADOS.items():
    if converter_datetime(dates[0]) <= datetime_obj <= converter_datetime(dates[1]):
      return gov
