# 🚀 Extrator e Conversor Lattes

Esta ferramenta automatiza o processo de raspagem (*web scraping*) e conversão de IDs da Plataforma Lattes (CNPq).

O script atua em duas etapas integradas:

1. **Extração:** coleta os nomes e os **IDs reduzidos (id10)** de pesquisadores diretamente da página de Busca Textual do CNPq.
2. **Conversão:** acessa os currículos de forma invisível (*headless*) e extrai o **ID oficial de 16 dígitos (id16)** correspondente a cada pesquisador.

---

## 📋 Pré-requisitos

Para rodar este script, você precisará ter instalado em sua máquina:

* **Git**
* **Python 3.8+**
* **Navegador Mozilla Firefox**
* **Geckodriver** — motor que permite ao Python controlar o Firefox

---

## 📥 Instalação

### 1. Clone o repositório

Clone o repositório para sua máquina:

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
```

Entre no diretório do projeto:

```bash
cd SEU_REPOSITORIO
```

> Substitua `SEU_USUARIO/SEU_REPOSITORIO` pela URL real do repositório.

---

### 2. Instale o Firefox e o Geckodriver

#### Linux (Debian/Ubuntu/Xubuntu)

```bash
sudo apt update
sudo apt install firefox firefox-geckodriver
```

#### Linux (Arch/CachyOS/Manjaro)

```bash
sudo pacman -S firefox geckodriver
```

#### Windows / macOS

1. Instale o Firefox.
2. Baixe a versão mais recente do Geckodriver.
3. Extraia o executável.
4. Adicione o executável ao `PATH` do sistema.

Alternativamente, você pode informar o caminho diretamente ao executar o script usando a opção `--driver-path`.

---

### 3. Crie o ambiente virtual

É recomendado utilizar um ambiente virtual (`venv`) para evitar conflitos entre bibliotecas Python.

O ambiente virtual será criado **dentro do próprio diretório do repositório**:

```bash
python3 -m venv venv
```

Após esse comando, a estrutura básica do projeto será semelhante a:

```text
SEU_REPOSITORIO/
├── venv/
├── README.md
├── requirements.txt
└── lattes_extrator_unificado.py
```

> O diretório `venv/` é um ambiente local e não deve ser versionado pelo Git.

---

### 4. Ative o ambiente virtual

#### Linux/macOS

```bash
source venv/bin/activate
```

#### Windows

```bat
venv\Scripts\activate
```

Após a ativação, o terminal normalmente exibirá algo semelhante a:

```text
(venv) usuario@computador:~/SEU_REPOSITORIO$
```

---

### 5. Instale as dependências

Com o ambiente virtual ativado, instale todas as dependências do projeto utilizando o `requirements.txt`:

```bash
pip install -r requirements.txt
```

As principais dependências são:

* `pandas`
* `beautifulsoup4`
* `selenium`

O arquivo `requirements.txt` contém a lista oficial de dependências necessárias para executar o projeto.

---

## 🚀 Como usar

### Fluxo completo — Extração + Conversão

Para iniciar o processo do zero, execute:

```bash
python lattes_extrator_unificado.py
```

O processo ocorrerá em duas etapas.

### Etapa 1 — Extração

O Firefox será aberto automaticamente.

1. Vá até a janela do navegador.
2. Preencha os filtros desejados na **Busca Textual do CNPq**.
3. Clique em buscar.
4. Resolva o CAPTCHA manualmente (se for requisitado).
5. Assim que a primeira página de resultados aparecer, volte ao terminal.
6. Pressione **ENTER**.

A partir desse momento, o script assumirá o controle do navegador.

Ele irá:

* percorrer as páginas de resultados;
* extrair os nomes dos pesquisadores;
* extrair os respectivos IDs reduzidos (`id10`);
* salvar os resultados em `resultados_lattes_ids.csv`.

Ao finalizar a extração, o navegador será fechado automaticamente.

---

### Etapa 2 — Conversão

Depois da extração, o script inicia automaticamente a conversão dos IDs reduzidos.

Nesta etapa, o Firefox é executado em modo **headless**, ou seja, sem abrir uma janela visível.

Para cada pesquisador, o script:

1. acessa o currículo Lattes correspondente;
2. identifica o ID oficial de 16 dígitos (`id16`);
3. registra o resultado;
4. salva o progresso no arquivo `checkpoint.csv`.

Ao final, os resultados estarão disponíveis em:

```text
ids_convertidos.csv
```

---

## 🔄 Fluxo parcial — Apenas conversão

Se você já possui um arquivo com IDs reduzidos, ou se a etapa de extração foi interrompida e você deseja continuar apenas com os dados já salvos em `resultados_lattes_ids.csv`, utilize:

```bash
python lattes_extrator_unificado.py --apenas-converter
```

Nesse modo, a etapa de extração não será executada.

O script utilizará diretamente:

```text
resultados_lattes_ids.csv
```

como entrada para a conversão.

---

## ⚙️ Parâmetros disponíveis

O comportamento do script pode ser personalizado por meio das seguintes opções:

| Opção                | Descrição                                                                | Padrão                      |
| -------------------- | ------------------------------------------------------------------------ | --------------------------- |
| `--input`            | Define o arquivo de entrada utilizado na conversão.                      | `resultados_lattes_ids.csv` |
| `--output`           | Define o nome do arquivo final.                                          | `ids_convertidos.csv`       |
| `--driver-path`      | Define o caminho do executável do Geckodriver.                           | `/usr/bin/geckodriver`      |
| `--sleep`            | Define o tempo, em segundos, aguardado para o carregamento do currículo. | `4.0`                       |
| `--apenas-converter` | Executa somente a etapa de conversão.                                    | Desativado                  |

### Exemplo

Para utilizar outro arquivo de entrada e aumentar o tempo de espera para 6 segundos:

```bash
python lattes_extrator_unificado.py \
    --apenas-converter \
    --input meus_dados.csv \
    --sleep 6.0
```

### Utilizando um Geckodriver em outro local

Caso o Geckodriver não esteja no `PATH` do sistema:

```bash
python lattes_extrator_unificado.py \
    --driver-path /caminho/para/geckodriver
```

Por exemplo:

```bash
python lattes_extrator_unificado.py \
    --driver-path /usr/local/bin/geckodriver
```

---

## 💾 Sistema de Checkpoint

O script possui um sistema automático de checkpoint para permitir a retomada da conversão.

Durante a **Etapa 2**, cada tentativa é registrada no arquivo:

```text
checkpoint.csv
```

### ⏯️ Retomada automática

O processamento pode ser interrompido a qualquer momento pressionando:

```text
Ctrl+C
```

Ao executar o script novamente, ele verificará o `checkpoint.csv`.

Os IDs que já foram convertidos com sucesso serão ignorados, permitindo que o processamento continue de onde parou.

Isso é especialmente útil para processamentos grandes ou quando a conexão com o CNPq apresenta instabilidades.

---

### ⚠️ Tratamento de erros

Caso uma tentativa de conversão falhe, por exemplo devido a:

* perda de conexão;
* erro no carregamento da página;
* indisponibilidade temporária do CNPq;
* currículo não encontrado;

o resultado será registrado no checkpoint.

IDs que apresentarem determinados status de erro, como:

```text
erro
nao_encontrado
```

poderão ser novamente processados em uma execução posterior.

Dessa forma, o script evita repetir desnecessariamente as conversões que já foram realizadas com sucesso.

---

### 🔄 Começar a conversão do zero

Para ignorar o histórico existente e reprocessar todos os IDs, apague o arquivo:

```text
checkpoint.csv
```

antes de executar novamente o script.

> **Atenção:** apagar o `checkpoint.csv` fará com que o histórico de processamento seja perdido.

---

## 📁 Arquivos gerados

Durante a execução, o script gera os seguintes arquivos:

| Arquivo                     | Descrição                                                                                    |
| --------------------------- | -------------------------------------------------------------------------------------------- |
| `resultados_lattes_ids.csv` | Arquivo criado na **Etapa 1**, contendo os nomes e IDs reduzidos (`id10`) dos pesquisadores. |
| `checkpoint.csv`            | Arquivo utilizado para salvar automaticamente o progresso da conversão.                      |
| `ids_convertidos.csv`       | Arquivo final contendo nome, ID reduzido, ID de 16 dígitos e status da operação.             |
| `lattes_unificado.log`      | Arquivo de log contendo o histórico da execução para auditoria e *debug*.                    |

---

## 🔁 Fluxo do processamento

O funcionamento geral da ferramenta pode ser representado da seguinte maneira:

```text
Busca Textual do CNPq
        │
        ▼
┌─────────────────────────┐
│ Extração dos resultados │
└─────────────────────────┘
        │
        ▼
resultados_lattes_ids.csv
        │
        ▼
┌─────────────────────────┐
│ Conversão dos IDs id10  │
│ para IDs oficiais id16  │
└─────────────────────────┘
        │
        ├──────────────► checkpoint.csv
        │
        ▼
ids_convertidos.csv
```

O `checkpoint.csv` funciona como ponto de retomada da segunda etapa do processamento.

---

## 🗂️ Estrutura do projeto

A estrutura esperada do repositório é:

```text
script_lattes_id/
│
├── .gitignore
├── README.md
├── requirements.txt
├── lattes_extrator_unificado.py
│
└── venv/
    └── ...
```

O diretório `venv/` existe apenas na máquina local e **não deve ser enviado para o repositório Git**.

Os arquivos gerados durante a execução também são arquivos locais e devem permanecer fora do controle de versão.

---

## 🧹 `.gitignore`

Recomenda-se utilizar um `.gitignore` semelhante ao seguinte:

```gitignore
# Ambiente virtual Python
venv/

# Arquivos gerados pelo script
resultados_lattes_ids.csv
checkpoint.csv
ids_convertidos.csv
lattes_unificado.log

# Cache do Python
__pycache__/
*.py[cod]

# Arquivos de configuração locais
.env
```

---

## 🔧 Atualizando o projeto

Caso uma nova versão do script seja disponibilizada no repositório, primeiro atualize os arquivos:

```bash
git pull
```

Depois, com o ambiente virtual ativado, atualize as dependências:

```bash
pip install -r requirements.txt
```

Isso garante que eventuais novas bibliotecas adicionadas ao projeto sejam instaladas.

---

## 📌 Resumo da instalação

Em uma máquina Linux, depois de instalar o Git, Firefox e Geckodriver, a instalação completa pode ser feita com:

```bash
git clone https://github.com/gavieira/script_lattes_id.git
cd script_lattes_id 

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Depois, execute:

```bash
python lattes_extrator_unificado.py
```

---

## 🤖 Uso de Inteligência Artificial

O desenvolvimento deste projeto contou com o auxílio de ferramentas de **Inteligência Artificial (IA)**.

A IA foi utilizada como ferramenta de apoio durante o desenvolvimento, incluindo atividades como:

* elaboração e revisão de código;
* identificação e correção de erros;
* desenvolvimento e aprimoramento de funcionalidades;
* documentação e organização do projeto.

O código foi revisado, adaptado e integrado pelo autor do projeto. A utilização de ferramentas de IA não implica atribuição de autoria ou responsabilidade a essas ferramentas.


## 📄 Licença

Este projeto é distribuído sob os termos da GNU General Public License v3.0 (GPL-3.0).

Você pode usar, copiar, modificar e redistribuir este software, desde que respeite os termos estabelecidos pela licença.

Para consultar o texto completo da licença, acesse:

https://www.gnu.org/licenses/gpl-3.0.html
