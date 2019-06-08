# Basômetro

O Basômetro é uma ferramenta do **Estadão** que monitora o apoio do Governo Federal na Câmara dos Deputados.

### Eu só quero acessar os dados, nem sei o que tô fazendo aqui nesse site

Se você quer baixar os dados do Basômetro em formato de planilha, pode acessar esse [link](https://drive.google.com/file/d/1QKQJlEGyOFkEbXABOGJ_9IdRd_6IgpjQ/view?usp=sharing). Entretanto, um aviso: **o arquivo é atualizado com pouca frequência**.

### Eu sou um desenvolvedor e quero replicar a ferramenta

Oba! Tudo o que você precisa está nesse repositório. Resolvemos deixar o código público justamente para garantir que o projeto seja reproduzível. Com uma linha de Python, é possível recriar o o banco de dados da ferramenta em sua própria maquina. Com outra linha, é possível atualizar as informações.

#### Requerimentos

- O [Python](https://www.python.org/) 3.6 ou mais recente
- O [`camaraPy`](https://pypi.org/project/camaraPy/) – um wrapper para a API da Câmara dos Deputados.
- O [`pandas`](https://github.com/pandas-dev/pandas) – um pacote de data science e estatística.

Ambos os pacotes podem ser instalados via pip: `pip install pandas camaraPy`


#### Criando o banco de dados

O primeiro passo é fazer o download desse repositório para o seu computador. Em uma sessão do Python, execute os seguintes comandos:

```
from basometro import instalador

instalador.instalar_basometro()
```

O programa vai fazer requisições para a API da Câmara dos Deputados e salvar no diretório `database` um arquivo CSV com todos os votos registrados em sessões onde a liderança do governo emitiu orientação para bancada entre 2003 e hoje.

Além disso, o script vai criar diversos arquivos CSV com os dados agregados nos formatos necessários para gerar as visualizações de dados da ferramenta.

Assim, **é importante que você execute os comandos no diretório raiz desse repositório**.

Também é possível fazer isso sem uma sessão interativa – simplesmente execute o arquivo `instalar.py`.

O processo deve demorar um pouco – paciência!

#### Atualizando o banco de dados

De forma semelhante, **depois que o banco de dados já tiver sido criado**, você pode executar o seguinte código em uma sessão interativa  para manter o conteúdo em dia:

```
from basometro import atualizador

atualizador.atualizar_basometro()
```

É possível fazer a mesma tarefa executando o script em `atualizar.py` – isso pode ser especialmente útil para automatizar o processo usando um cron ou outra ferramenta do gênero.

O programa vai pegar todas as votações transcorridas entre o último registros do banco de dados e a data atual. Os arquivos necessários para as visualizações de dados também são atualizados.

De novo: paciência, demora um pouco.

#### Coisas técnicas

Todo o processo de coleta e análise de dados é feito pelos arquivos contidos no diretório `basometro`. Em suma, eles fazem requisições para a API da Câmara e calculam quantas vezes cada deputado votou de acordo com a orientação do líder do governo ou contra ela. Outras operações envolvem agregar os dados por partido e computar uma linha do tempo mensal.

O módulo também adiciona aos dados algumas votações cujo resultado foi compilado manualmente, contidas em `database/votacoes-ausentes`. Isso foi feito porque o banco de dados da Câmara não lista todas as votações feitas por chamada – apenas votações feitas usando o painel são catalogadas de forma automática.

#### Metodologia

O Basômetro mede o governismo dos deputados e partidos na Câmara. Para fazer isso, a ferramenta calcula quantos votos de cada parlamentar ou legenda seguiram a orientação do líder do governo, percentualmente.

Consideramos que um voto a favor do governo é aquele que segue exatamente a orientação da liderança. Por exemplo, caso a indicação seja “sim”, apenas votos “sim” são considerados pró-situação. Todos os demais (“não”, “obstrução” ou “abstenção”) são considerados votos contra o governo – ainda que, em situações específicas, possam ter sido benéficos para as intenções do Executivo.

Quando o governo não registrou uma orientação e liberou o posicionamento da bancada, os dados relacionados foram descartados. Assim, a taxa de governismo e assiduidade dos parlamentares são calculadas levando em consideração apenas as votações em que o Executivo assumiu posição explicitamente.

Na ferramenta, são usados os dados disponibilizados pelo Portal de Dados Abertos da Câmara dos Deputados através da API (espécie de sistema que permite a automatização da coleta e publicação de dados) da instituição.

Foram feitas consultas para obter os resultados de cada uma das votações nominais que aconteceram na Câmara desde 1º de janeiro de 2003.

O banco de dados da Câmara atualmente se encontra incompleto: votações que são feitas por chamada não constam no sistema. Assim, foram adicionados manualmente os votos da abertura do processo de impeachment de Dilma Rousseff e das duas acusações criminais contra Michel Temer.
