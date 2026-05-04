#!/usr/bin/env python3
"""
Meta Ads Scheduler
Executa meta_ads_control.py toda segunda-feira às 08:00.
Mantenha este processo rodando em background (ou use Task Scheduler no Windows).

Uso:
    python scheduler.py
"""

import logging
import sys
import os

try:
    import schedule
    import time
except ImportError:
    print("ERROR: pip install schedule")
    sys.exit(1)

# Importa o script principal do mesmo diretório
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_ads_control import main as run_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def job():
    logger.info("Iniciando geração do relatório semanal Meta Ads...")
    try:
        path = run_report()
        logger.info("Relatório gerado com sucesso: %s", path)
    except Exception as exc:
        logger.error("Falha ao gerar relatório: %s", exc, exc_info=True)


if __name__ == "__main__":
    # Gera imediatamente na primeira execução
    logger.info("Scheduler iniciado. Próxima execução automática: segunda-feira às 08:00.")
    logger.info("Gerando relatório inicial agora...")
    job()

    # Agenda para toda segunda-feira às 08:00
    schedule.every().monday.at("08:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)
