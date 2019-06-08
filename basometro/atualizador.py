'''
Esse script deve ser executado em um intervalo fixo de tempo para atualizar o
banco de dados do Basômetro e os arquivos usados para gerar as visualizações.

TO DO: Talvez essas funções devessem estar em basometro_alicativo
'''

from basometro import basometro_aplicativo
import pandas as pd
import os, shutil

def atualizar_basometro():

  def fazer_backup_database(df_path, df_backup_path):
    backup = pd.read_csv(df_path, dtype = str)
    backup.to_csv(df_backup_path, index = False)

  def atualizar_database(df_path, df_backup_path):

    try:
      basometro_aplicativo.atualizar_banco_de_dados(df_path = df_path,
                                                    keep_all = False)
    except Exception as e:
      print("Um erro inesperado aconteceu ao atualizar o banco de dados. Vamos encerrar a operação e restaurar os arquivos ao estado anterior.")
      shutil.copy(df_backup_path, df_path)
      raise

  def fazer_backup_viz(output_path, backup_path):
    if os.path.exists(backup_path):
      shutil.rmtree(backup_path)
    shutil.move(output_path, backup_path)

  def atualizar_viz(df_path, temp_path, output_path, backup_path):

    def substituir_diretorios(temp_path, output_path):
      shutil.move(temp_path, output_path)

    ###################################
    ### EXECUÇÃO DE atualizar_viz() ###
    ###################################

    try:
      # Gerar arquivos de visualização em um diretório temporário
      basometro_aplicativo.gerar_arquivos_viz(freqs = [ "MS" ],
                                              df_path = df_path,
                                              output_path = temp_path)
    except Exception as e:
      print("Um erro inesperado aconteceu ao gerar os arquivos da visualização. Vamos encerrar a operação e restaurar os arquivos ao estado anterior.")

      # Copia o backup para o output; deleta o diretório temporário
      shutil.copytree(backup_path, output_path)
      if os.path.exists(temp_path):
        shutil.rmtree(temp_path)

      raise

    substituir_diretorios(temp_path, output_path)

  #########################################
  ### EXECUÇÃO de atualizar_basometro() ###
  #########################################

  # Database
  df_path              = "database/basometro.csv"
  df_backup_path       = "database/basometro-backup.csv"

  # Viz
  output_path      = "./output"
  backup_path      = "./backup-output"
  temp_path        = "./temp-output"

  assert os.path.isfile(df_path)
  assert os.path.exists(output_path)
  assert not os.path.exists(temp_path)

  print("Atualizando o Basômetro e as visualizações de dados.")

  fazer_backup_database(df_path, df_backup_path)
  atualizar_database(df_path, df_backup_path)

  fazer_backup_viz(output_path, backup_path)
  atualizar_viz(df_path, temp_path, output_path, backup_path)

  assert os.path.exists(output_path)
  assert not os.path.exists(temp_path)

  print("Pronto!")

##############
### main() ###
##############

def main():
  atualizar_basometro()

if __name__ == "__main__":
  main()
