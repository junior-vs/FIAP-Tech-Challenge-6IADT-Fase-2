"""
Módulo de configuração de logging para a aplicação TSP Genetic Algorithm.

Este módulo centraliza todas as configurações de logging, permitindo
controle unificado dos logs da aplicação.

Autor: Projeto FIAP Tech Challenge
Versão: 1.0
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class ExcludePerfFilter(logging.Filter):
    """Filtro que remove logs de performance do console."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra mensagens que contenham [PERF] para não aparecerem no console.
        
        Args:
            record: Record de log a ser avaliado
            
        Returns:
            True se o log deve ser exibido, False caso contrário
        """
        try:
            msg = record.getMessage()
        except Exception:
            return True
        return "[PERF]" not in msg


def configurar_logging(
    nome_ficheiro: Optional[str] = None,
    nivel_consola: int = logging.INFO,
    nivel_ficheiro: int = logging.DEBUG
) -> None:
    """
    Configura o sistema de logging para a aplicação.

    Esta função configura o logger principal (root logger) para enviar logs
    tanto para a consola quanto para um ficheiro, com diferentes níveis
    de detalhamento.

    Args:
        nome_ficheiro: Nome do arquivo de log. Se None, usa timestamp automático
        nivel_consola: Nível de logging para saída na consola (padrão: INFO)
        nivel_ficheiro: Nível de logging para arquivo (padrão: DEBUG)

    Example:
        >>> configurar_logging()  # Usa configurações padrão
        >>> configurar_logging('meu_app.log', logging.WARNING, logging.INFO)
    """
    # Criar pasta logs se não existir
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Gerar nome automático se não fornecido
    if nome_ficheiro is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_ficheiro = f'app_log_{timestamp}.log'
    
    # Caminho completo para o arquivo de log
    log_path = logs_dir / nome_ficheiro

    # Configurar o logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Nível mais baixo para capturar tudo

    # Limpar handlers existentes para evitar duplicação
    logger.handlers.clear()

    # 1. Formato da mensagem de log
    formato = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 2. Handler para a consola (stdout) - SEM logs de performance
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(nivel_consola)
    handler_consola.setFormatter(formato)
    handler_consola.addFilter(ExcludePerfFilter())  # <- Filtrar [PERF] do console
    logger.addHandler(handler_consola)

    # 3. Handler para arquivo - COM todos os logs incluindo performance
    try:
        # Caminho completo para o arquivo de log
        log_path = logs_dir / nome_ficheiro
        
        handler_ficheiro = logging.FileHandler(
            log_path, 
            mode='a', 
            encoding='utf-8'
        )
        handler_ficheiro.setLevel(nivel_ficheiro)  # DEBUG: mantém [PERF] no arquivo
        handler_ficheiro.setFormatter(formato)
        logger.addHandler(handler_ficheiro)
        
        logging.info(f"Sistema de logging configurado com sucesso! Arquivo: {log_path}")
        logging.info("Logs de performance [PERF] serão salvos apenas no arquivo")
    except (IOError, OSError) as e:
        logging.warning(f"Não foi possível configurar logging para arquivo: {e}")


def get_logger(nome_modulo: str) -> logging.Logger:
    """
    Obtém um logger específico para um módulo.

    Args:
        nome_modulo: Nome do módulo (normalmente __name__)

    Returns:
        Logger configurado para o módulo específico

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensagem do meu módulo")
    """
    return logging.getLogger(nome_modulo)


def log_performance(func):
    """
    Decorator para logging automático de performance de funções.

    Args:
        func: Função a ser decorada

    Returns:
        Função decorada com logging de performance

    Example:
        >>> @log_performance
        ... def minha_funcao():
        ...     pass
    """
    import time
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        logger.debug(f"Iniciando execução de {func.__name__}")
        try:
            resultado = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.debug(f"Função {func.__name__} executada em {elapsed_time:.4f}s")
            return resultado
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Erro em {func.__name__} após {elapsed_time:.4f}s: {e}",
                exc_info=True
            )
            raise
    
    return wrapper


def simular_operacao(valor: float) -> Optional[float]:
    """
    Simula uma operação que pode gerar diferentes tipos de logs.
    
    Função de exemplo para demonstrar diferentes níveis de logging.

    Args:
        valor: Valor para operação de divisão

    Returns:
        Resultado da operação ou None em caso de erro
    """
    logger = get_logger(__name__)
    
    logger.debug(f"Iniciando simulação da operação com valor={valor}")
    
    try:
        if valor == 0:
            raise ZeroDivisionError("Divisão por zero não permitida")
            
        resultado = 100 / valor
        logger.info(f"Operação concluída com sucesso. Resultado: {resultado}")
        return resultado
        
    except ZeroDivisionError:
        logger.error("Erro: Tentativa de dividir por zero!", exc_info=True)
        return None
        
    except Exception as e:
        logger.critical(f"Erro CRÍTICO inesperado: {e}", exc_info=True)
        return None


# Configuração de logging para o módulo
if __name__ == "__main__":
    # Teste do módulo de logging
    configurar_logging()
    logger = get_logger(__name__)
    
    logger.info("=== Teste do módulo de logging ===")
    
    # Teste das diferentes operações
    simular_operacao(5)    # INFO: Operação normal
    simular_operacao(0)    # ERROR: Divisão por zero  
    simular_operacao(10)   # INFO: Operação normal
    
    logger.warning("Exemplo de warning")
    logger.critical("Exemplo de log crítico")
    
    logger.info("=== Fim dos testes ===")