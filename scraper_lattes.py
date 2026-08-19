import random
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.FirefoxOptions()
# options.add_argument("--headless")

driver = webdriver.Firefox(options=options)
dados_pesquisadores = []

try:
    url_busca = "https://buscatextual.cnpq.br/buscatextual/busca.do"
    driver.get(url_busca)
    
    print("1. Vá ao Firefox, preencha os filtros e faça a busca.")
    print("2. Resolva o CAPTCHA.")
    print("3. Quando a primeira lista aparecer, volte aqui e aperte ENTER.")
    input("Pressione ENTER para começar a extração... ")

    html_inicial = driver.page_source
    match_total = re.search(r'var intLTotReg = (\d+);', html_inicial)
    
    if not match_total:
        print("Erro: Não foi possível detectar o total de registros no HTML.")
        driver.quit()
        exit()

    total_registros = int(match_total.group(1))
    print(f"\n[OK] Total de pesquisadores na busca: {total_registros}")
    
    # 100 é o tamanho de batch ideal para estabilidade de backend
    passo = 300 
    
    for inicio in range(0, total_registros, passo):
        fim_esperado = min(inicio + passo, total_registros)
        registro_de = inicio + 1
        print(f"\nSolicitando bloco: registros {registro_de} até {fim_esperado}...")
        
        tentativas = 3
        sucesso_bloco = False
        
        while tentativas > 0 and not sucesso_bloco:
            try:
                # 1. Injeta a requisição do batch
                driver.execute_script(f"submeterPaginacao({inicio}, {passo});")
                
                # 2. Espera inteligente com Regex: aguarda o intervalo EXATO aparecer no cabeçalho
                WebDriverWait(driver, 15).until(
                    lambda d: re.search(
                        rf"{registro_de}\s*-\s*{fim_esperado}", 
                        d.find_element(By.CLASS_NAME, 'tit_form').text
                    )
                )
                
                # 3. Pequena pausa de estabilização do DOM
                time.sleep(random.uniform(2.0, 3.5))
                
                # 4. Extração dos dados do bloco atual
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                links = soup.find_all('a', href=re.compile(r'javascript:abreDetalhe'))
                
                novos_neste_bloco = 0
                for link in links:
                    href = link.get('href')
                    nome = link.text.strip()
                    match = re.search(r"abreDetalhe\('([^']+)'", href)
                    if match:
                        dados_pesquisadores.append({
                            'Nome': nome,
                            'ID_Alfa': match.group(1)
                        })
                        novos_neste_bloco += 1
                
                print(f" -> Extraídos {novos_neste_bloco} registros com sucesso.")
                sucesso_bloco = True
                
            except Exception as e:
                tentativas -= 1
                print(f" [Aviso] Lentidão ou timeout no bloco {registro_de}-{fim_esperado}. Tentativas restantes: {tentativas}")
                time.sleep(5) # Pausa para o servidor se recuperar antes de tentar de novo

        # Delay de cortesia entre requisições sucessivas (evita ban de IP)
        time.sleep(random.uniform(1.5, 3.0))

finally:
    driver.quit()

# Consolidação, higienização e trava de segurança
df = pd.DataFrame(dados_pesquisadores)

if not df.empty:
    df_limpo = df.drop_duplicates(subset=['ID_Alfa']).reset_index(drop=True)
    total_capturado = len(df_limpo)
    
    # 1. Salva o CSV com o que foi extraído, independentemente de erro ou sucesso
    df_limpo.to_csv('resultados_lattes_ids.csv', index=False, encoding='utf-8-sig')
    
    # 2. Avalia a integridade
    if total_capturado != total_registros:
        mensagem_erro = (
            f"\n[!] FALHA DE INTEGRIDADE NA EXTRAÇÃO:\n"
            f"O CNPq relatou {total_registros} pesquisadores na interface, "
            f"mas o script capturou apenas {total_capturado}.\n"
            f"Os dados parciais foram salvos em 'resultados_lattes_ids.csv'."
        )
        raise ValueError(mensagem_erro)
        
    print(f"\n=======================================================")
    print(f"Extração finalizada com sucesso absoluto!")
    print(f"Total esperado: {total_registros} | Total capturado: {total_capturado}")
    print(f"Arquivo gerado: 'resultados_lattes_ids.csv'")
    print(f"=======================================================")
else:
    print("\nNenhum registro capturado.")
