#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ferramenta Unificada: Scraper Lattes + Conversor de IDs
Etapa 1: Busca os pesquisadores e seus IDs reduzidos (requer interação manual no CAPTCHA).
Etapa 2: Converte os IDs reduzidos em IDs de 16 dígitos (roda em background).
"""

import argparse
import csv
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==========================================
# CONFIGURAÇÕES DE LOG
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("lattes_unificado.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

URL_BUSCA = "https://buscatextual.cnpq.br/buscatextual/busca.do"
URL_PREVIEW = "http://buscatextual.cnpq.br/buscatextual/preview.do?metodo=apresentar&id={0}"
ID16_PATTERN = re.compile(r"(?<!\d)(\d{16})(?!\d)")

# ==========================================
# ESTRUTURAS DE DADOS
# ==========================================
@dataclass
class ResultadoConversao:
    id_reduzido: str
    id_16: Optional[str] = None
    status: str = "pendente"  # pendente | ok | nao_encontrado | erro
    tentativas: int = 0
    detalhes_extras: dict = field(default_factory=dict)


# ==========================================
# ETAPA 1: EXTRAÇÃO DE IDS REDUZIDOS
# ==========================================
def executar_extracao_ids(driver_path: str, arquivo_intermediario: str):
    logger.info("=== INICIANDO ETAPA 1: EXTRAÇÃO DE IDs REDUZIDOS ===")
    options = webdriver.FirefoxOptions()
    # Para a busca inicial não usamos headless pois o usuário precisa resolver o CAPTCHA
    
    if not os.path.exists(driver_path):
        raise FileNotFoundError(f"geckodriver não encontrado em: {driver_path}")

    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)
    dados_pesquisadores = []

    try:
        driver.get(URL_BUSCA)
        print("\n" + "="*60)
        print("1. Vá ao Firefox aberto, preencha os filtros e faça a busca.")
        print("2. Resolva o CAPTCHA.")
        print("3. Quando a PRIMEIRA LISTA de resultados aparecer, volte aqui e aperte ENTER.")
        print("="*60 + "\n")
        input("Pressione ENTER para começar a extração em massa... ")

        html_inicial = driver.page_source
        match_total = re.search(r'var intLTotReg = (\d+);', html_inicial)
        
        if not match_total:
            logger.error("Erro: Não foi possível detectar o total de registros no HTML.")
            driver.quit()
            exit(1)

        total_registros = int(match_total.group(1))
        logger.info(f"[OK] Total de pesquisadores na busca: {total_registros}")
        
        passo = 100 
        
        for inicio in range(0, total_registros, passo):
            fim_esperado = min(inicio + passo, total_registros)
            registro_de = inicio + 1
            logger.info(f"Solicitando bloco: registros {registro_de} até {fim_esperado}...")
            
            tentativas = 3
            sucesso_bloco = False
            
            while tentativas > 0 and not sucesso_bloco:
                try:
                    driver.execute_script(f"submeterPaginacao({inicio}, {passo});")
                    
                    WebDriverWait(driver, 15).until(
                        lambda d: re.search(
                            rf"{registro_de}\s*-\s*{fim_esperado}", 
                            d.find_element(By.CLASS_NAME, 'tit_form').text
                        )
                    )
                    
                    time.sleep(random.uniform(2.0, 3.5))
                    
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    links = soup.find_all('a', href=re.compile(r'javascript:abreDetalhe'))
                    
                    novos_neste_bloco = 0
                    for link in links:
                        href = link.get('href')
                        nome = link.text.strip()
                        match = re.search(r"abreDetalhe\('([^']+)'", href)
                        if match:
                            id_reduzido = match.group(1)
                            dados_pesquisadores.append({
                                'id_reduzido': id_reduzido,
                                'nome': nome
                            })
                            novos_neste_bloco += 1
                    
                    logger.info(f" -> Extraídos {novos_neste_bloco} registros com sucesso.")
                    sucesso_bloco = True
                    
                except Exception as e:
                    tentativas -= 1
                    logger.warning(f"[Aviso] Lentidão ou timeout no bloco {registro_de}-{fim_esperado}. Tentativas restantes: {tentativas}")
                    time.sleep(5)

            time.sleep(random.uniform(1.5, 3.0))

    finally:
        driver.quit()

    # Consolidação e salvamento intermediário
    df = pd.DataFrame(dados_pesquisadores)
    if not df.empty:
        df_limpo = df.drop_duplicates(subset=['id_reduzido']).reset_index(drop=True)
        total_capturado = len(df_limpo)
        df_limpo.to_csv(arquivo_intermediario, index=False, encoding='utf-8-sig')
        
        if total_capturado != total_registros:
            logger.warning(
                f"[!] Falha de integridade: Esperado {total_registros}, Capturado {total_capturado}. "
                f"Dados parciais salvos em {arquivo_intermediario}."
            )
        
        logger.info("=== ETAPA 1 FINALIZADA COM SUCESSO ===")
        logger.info(f"Total esperado: {total_registros} | Total capturado: {total_capturado}")
        logger.info(f"Arquivo intermediário gerado: '{arquivo_intermediario}'")
        return df_limpo
    else:
        logger.error("Nenhum registro capturado.")
        exit(1)


# ==========================================
# ETAPA 2: CONVERSÃO DE IDS
# ==========================================
class ConversorLattes:
    def __init__(self, driver_path: str, headless: bool = True, sleep_time: float = 3.0,
                 max_tentativas: int = 3, checkpoint_path: str = "checkpoint.csv"):
        self.driver_path = driver_path
        self.headless = headless
        self.sleep_time = sleep_time
        self.max_tentativas = max_tentativas
        self.checkpoint_path = checkpoint_path
        self.driver = None

    def __enter__(self):
        self._criar_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def _criar_driver(self):
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("permissions.default.image", 2)

        service = Service(self.driver_path)
        self.driver = webdriver.Firefox(service=service, options=options)
        self.driver.set_page_load_timeout(30)

    def _extrair_id16_da_pagina(self) -> Optional[str]:
        html = self.driver.page_source
        match = re.search(r"lattes\.cnpq\.br/(\d{16})", html)
        if match: return match.group(1)
        match = ID16_PATTERN.search(html)
        if match: return match.group(1)
        return None

    def converter_um(self, id_reduzido: str) -> ResultadoConversao:
        resultado = ResultadoConversao(id_reduzido=id_reduzido)

        for tentativa in range(1, self.max_tentativas + 1):
            resultado.tentativas = tentativa
            try:
                url = URL_PREVIEW.format(id_reduzido)
                self.driver.get(url)

                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                try:
                    self.driver.execute_script("abreCV()")
                    time.sleep(self.sleep_time)
                    if len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                except WebDriverException:
                    logger.debug(f"[{id_reduzido}] abreCV() falhou; tentando extrair da tela atual.")

                id16 = self._extrair_id16_da_pagina()

                if id16:
                    resultado.id_16 = id16
                    resultado.status = "ok"
                    logger.info(f"[{id_reduzido}] -> {id16} (tentativa {tentativa})")
                else:
                    time.sleep(2)
                    id16 = self._extrair_id16_da_pagina()
                    if id16:
                        resultado.id_16 = id16
                        resultado.status = "ok"
                        logger.info(f"[{id_reduzido}] -> {id16} (retry interno)")
                    else:
                        resultado.status = "nao_encontrado"
                        logger.warning(f"[{id_reduzido}] ID de 16 dígitos não encontrado.")

                self._fechar_abas_extras()
                if resultado.status == "ok":
                    return resultado

            except TimeoutException:
                logger.warning(f"[{id_reduzido}] Timeout na tentativa {tentativa}/{self.max_tentativas}")
                resultado.status = "erro"
                time.sleep(3)
            except WebDriverException as e:
                logger.error(f"[{id_reduzido}] Erro de WebDriver na tentativa {tentativa}/{self.max_tentativas}: {e}")
                resultado.status = "erro"
                time.sleep(5)

        return resultado

    def _fechar_abas_extras(self):
        handles = self.driver.window_handles
        if len(handles) > 1:
            principal = handles[0]
            for h in handles[1:]:
                self.driver.switch_to.window(h)
                self.driver.close()
            self.driver.switch_to.window(principal)

    def converter_lote(self, ids_reduzidos: list, delay_entre_requisicoes: tuple = (2.0, 4.0)):
        resultados = []
        ja_processados = self._carregar_checkpoint()

        for i, id_reduzido in enumerate(ids_reduzidos, start=1):
            if id_reduzido in ja_processados:
                logger.info(f"[{i}/{len(ids_reduzidos)}] {id_reduzido} já processado (no checkpoint).")
                resultados.append(ja_processados[id_reduzido])
                continue

            logger.info(f"[{i}/{len(ids_reduzidos)}] Processando {id_reduzido}...")
            resultado = self.converter_um(id_reduzido)
            resultados.append(resultado)
            self._salvar_checkpoint_incremental(resultado)
            time.sleep(random.uniform(*delay_entre_requisicoes))

        return resultados

    def _carregar_checkpoint(self) -> dict:
        if not os.path.exists(self.checkpoint_path):
            return {}
        processados = {}
        with open(self.checkpoint_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processados[row["id_reduzido"]] = ResultadoConversao(
                    id_reduzido=row["id_reduzido"],
                    id_16=row.get("id_16") or None,
                    status=row.get("status", "pendente"),
                    tentativas=int(row.get("tentativas", 0) or 0),
                )
        return processados

    def _salvar_checkpoint_incremental(self, resultado: ResultadoConversao):
        existe = os.path.exists(self.checkpoint_path)
        with open(self.checkpoint_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow(["id_reduzido", "id_16", "status", "tentativas"])
            writer.writerow([resultado.id_reduzido, resultado.id_16 or "", resultado.status, resultado.tentativas])


# ==========================================
# FLUXO PRINCIPAL
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Ferramenta Unificada: Scraper e Conversor Lattes")
    
    # Parâmetros padrão solicitados
    parser.add_argument("--input", default="resultados_lattes_ids.csv", help="Arquivo intermediário/entrada CSV (padrão: resultados_lattes_ids.csv)")
    parser.add_argument("--output", default="ids_convertidos.csv", help="Arquivo final de saída CSV (padrão: ids_convertidos.csv)")
    parser.add_argument("--driver-path", default="/usr/bin/geckodriver", help="Caminho para o geckodriver (padrão: /usr/bin/geckodriver)")
    
    # Opções extras de controle
    parser.add_argument("--apenas-converter", action="store_true", help="Pula a etapa 1 de busca manual e vai direto para a conversão lendo o --input")
    parser.add_argument("--sleep", type=float, default=3.0, help="Tempo de espera após abrir CV na conversão (segundos)")
    parser.add_argument("--checkpoint", default="checkpoint.csv", help="Arquivo de checkpoint")

    args = parser.parse_args()

    # ETAPA 1: Extração
    if not args.apenas_converter:
        df_extracao = executar_extracao_ids(args.driver_path, args.input)
    else:
        logger.info(f"Pulando Etapa 1. Lendo dados do arquivo: {args.input}")
        if not os.path.exists(args.input):
            logger.error(f"Arquivo {args.input} não encontrado para iniciar a conversão!")
            exit(1)
        df_extracao = pd.read_csv(args.input)

    # Extrai apenas os IDs da coluna para passar pro conversor
    if 'id_reduzido' not in df_extracao.columns:
        logger.error(f"Coluna 'id_reduzido' não encontrada no DataFrame/Arquivo. Colunas: {df_extracao.columns}")
        exit(1)
        
    ids_para_converter = df_extracao['id_reduzido'].dropna().astype(str).tolist()

    # ETAPA 2: Conversão
    logger.info("=== INICIANDO ETAPA 2: CONVERSÃO DE IDs REDUZIDOS PARA 16 DÍGITOS ===")
    with ConversorLattes(
        driver_path=args.driver_path,
        headless=True,  # Conversão sempre em background
        sleep_time=args.sleep,
        checkpoint_path=args.checkpoint,
    ) as conversor:
        resultados = conversor.converter_lote(ids_para_converter)

    # MESCLAGEM DOS DADOS PARA O CSV FINAL
    logger.info("Mesclando nomes capturados com os novos IDs convertidos...")
    df_resultados = pd.DataFrame([vars(r) for r in resultados])
    
    # Remove a coluna detalhes_extras que é apenas dicionário interno vazio no momento
    if 'detalhes_extras' in df_resultados.columns:
        df_resultados = df_resultados.drop(columns=['detalhes_extras'])
    
    # Faz um JOIN pelo 'id_reduzido' para manter o NOME no arquivo final
    df_final = pd.merge(df_extracao, df_resultados, on='id_reduzido', how='left')

    # Reordenando colunas para ficar bonito: id_reduzido, nome, id_16, status, tentativas
    colunas_ordenadas = ['id_reduzido', 'nome', 'id_16', 'status', 'tentativas']
    df_final = df_final[[c for c in colunas_ordenadas if c in df_final.columns]]

    # Salva o resultado
    df_final.to_csv(args.output, index=False, encoding='utf-8-sig')
    
    total = len(df_final)
    ok = len(df_final[df_final['status'] == 'ok'])
    
    print("\n" + "="*60)
    print("PROCESSO FINALIZADO COM SUCESSO!")
    print(f"IDs extraídos/lidos: {total}")
    print(f"IDs convertidos p/ 16 dígitos: {ok}")
    print(f"Arquivo final gerado: {args.output}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
