# 🚀 Extrator e Conversor Lattes 

Esta ferramenta automatiza o processo de raspagem (web scraping) e conversão de IDs da Plataforma Lattes (CNPq). O script atua em duas etapas integradas:
1. **Extração:** Coleta os nomes e "IDs reduzidos" (id10) de pesquisadores diretamente da página de Busca Textual do CNPq.
2. **Conversão:** Acessa os currículos de forma invisível (*headless*) e extrai o ID oficial de 16 dígitos (id16) correspondente a cada pesquisador.

---

## 📋 Pré-requisitos

Para rodar este script, você precisará ter instalado em sua máquina:
* **Python 3.8+**
* **Navegador Mozilla Firefox**
* **Geckodriver** (Motor que permite ao Python controlar o Firefox)

### Instalação do Firefox e Geckodriver

**No Linux (Debian/Ubuntu/Xubuntu):**
```bash
sudo apt update
sudo apt install firefox firefox-geckodriver

No Linux (Arch/CachyOS/Manjaro):
Bash

sudo pacman -S firefox geckodriver

No Windows / macOS:

    Instale o Firefox.

    Baixe a versão mais recente do Geckodriver.

    Extraia o executável e adicione-o ao PATH do seu sistema (ou aponte o caminho diretamente na hora de rodar o script usando a flag --driver-path).

🛠️ Instalação do Ambiente Python

É altamente recomendado o uso de um ambiente virtual (venv) para evitar conflitos de bibliotecas.

    Crie o ambiente virtual:

Bash

python3 -m venv venv

    Ative o ambiente virtual:

    Linux/macOS:
    Bash

    source venv/bin/activate

    Windows:
    DOS

    venv\Scripts\activate

    Instale as dependências necessárias:

Bash

pip install pandas beautifulsoup4 selenium

🚀 Como usar
Fluxo Completo (Extração + Conversão)

Para iniciar o processo do zero, basta executar o script sem argumentos:
Bash

python lattes_extrator_unificado.py

O que vai acontecer:

    O Firefox será aberto automaticamente.

    Vá até a janela do navegador, preencha os filtros desejados na Busca Textual e clique em buscar.

    Resolva o CAPTCHA manualmente.

    Assim que a primeira página de resultados aparecer, volte ao terminal e pressione ENTER.

    O script assumirá o controle, paginando os resultados e extraindo os IDs reduzidos.

    Ao finalizar a extração, o script fechará o navegador e iniciará a conversão em modo invisível, salvando o progresso continuamente.

Fluxo Parcial (Apenas Conversão)

Se você já possui um arquivo com os IDs reduzidos (ou se a extração parou no meio e você quer converter apenas o que já foi salvo no arquivo resultados_lattes_ids.csv), use a flag --apenas-converter:
Bash

python lattes_extrator_unificado.py --apenas-converter

Outros Parâmetros Úteis

Você pode customizar o comportamento do script com as seguintes flags:

    --input: Define um arquivo de entrada diferente (Padrão: resultados_lattes_ids.csv).

    --output: Define o nome do arquivo final (Padrão: ids_convertidos.csv).

    --driver-path: Aponta o caminho exato do geckodriver, caso ele não esteja no PATH global (Padrão: /usr/bin/geckodriver).

    --sleep: Define o tempo (em segundos) que o script aguarda a página do currículo carregar antes de extrair o ID de 16 dígitos (Padrão: 4.0). Aumente esse valor se a sua internet estiver lenta.

Exemplo de uso avançado:
Bash

python lattes_extrator_unificado.py --apenas-converter --input meus_dados.csv --sleep 6.0

💾 Sistema de Checkpoint (Save Automático)

O script possui um sistema inteligente de retomada de tarefas.
Durante a Etapa 2 (Conversão), cada tentativa é salva instantaneamente no arquivo checkpoint.csv.

    Pode parar sem medo: Você pode interromper o script a qualquer momento pressionando Ctrl+C. Ao rodar o comando novamente, ele lerá o checkpoint.csv e pulará todos os IDs que já foram convertidos com sucesso.

    Tratamento de Erros: Se a conexão cair ou a página do CNPq der erro (status erro ou nao_encontrado), ao reiniciar o script, ele tentará converter novamente os IDs que falharam anteriormente, garantindo a maior taxa de sucesso possível.

    Para começar do zero: Se desejar ignorar o histórico e reprocessar todos os IDs, basta apagar o arquivo checkpoint.csv antes de iniciar.

📁 Arquivos Gerados

Ao longo da execução, o script gera os seguintes arquivos na pasta raiz:

    resultados_lattes_ids.csv: Arquivo temporário criado na Etapa 1 contendo o nome e o ID reduzido.

    checkpoint.csv: Arquivo de log e save automático da conversão.

    ids_convertidos.csv: O arquivo final. Contém o nome, o ID reduzido, o ID de 16 dígitos convertido e o status da operação.

    lattes_unificado.log: Arquivo de texto contendo todo o histórico do terminal para auditoria ou debug.

