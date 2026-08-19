import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

options = webdriver.FirefoxOptions()
driver = webdriver.Firefox(options=options)
dados_pesquisadores = []

try:
    url_busca = "https://buscatextual.cnpq.br/buscatextual/busca.do"
    driver.get(url_busca)
    
    print("1. Vá ao Firefox, preencha os filtros e faça a busca.")
    print("2. Resolva o CAPTCHA.")
    print("3. Quando a primeira lista aparecer, volte aqui e aperte ENTER.")
    input("Pressione ENTER para começar a extração acelerada... ")

    # Pega o HTML atual para descobrir o total de registros
    html_inicial = driver.page_source
    
    # O CNPq guarda o total de resultados numa variável JS chamada 'intLTotReg'
    match_total = re.search(r'var intLTotReg = (\d+);', html_inicial)
    
    if match_total:
        total_registros = int(match_total.group(1))
        print(f"\nTotal encontrado: {total_registros} pesquisadores.")
        
        # Número de registros por página
        passo = 500 
        
        for inicio in range(0, total_registros, passo):
            print(f"Baixando bloco de pesquisadores {inicio + 1} até {min(inicio + passo, total_registros)}...")
            
            # Injeta o JavaScript direto no navegador pedindo 100 resultados de uma vez!
            driver.execute_script(f"submeterPaginacao({inicio}, {passo});")
            
            # Aguarda o servidor do CNPq processar a lista pesada
            time.sleep(4) 
            
            # Lê o HTML da nova página com 100 resultados
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extrai os IDs
            links_curriculo = soup.find_all('a', href=re.compile(r'javascript:abreDetalhe'))
            for link in links_curriculo:
                href = link.get('href')
                nome = link.text.strip()
                
                match = re.search(r"abreDetalhe\('([^']+)'", href)
                if match:
                    dados_pesquisadores.append({
                        'Nome': nome,
                        'ID_Alfa': match.group(1)
                    })
    else:
        print("Não foi possível encontrar o total de registros. A busca retornou vazia?")

finally:
    driver.quit()

# Limpa e salva os dados
df = pd.DataFrame(dados_pesquisadores)

if not df.empty:
    df = df.drop_duplicates(subset=['ID_Alfa'])
    df.to_csv('resultados_lattes_ids.csv', index=False, encoding='utf-8-sig')
    print(f"\nExtração concluída! {len(df)} registros limpos salvos em 'resultados_lattes_ids.csv'.")
else:
    print("\nNenhum dado foi extraído.")
