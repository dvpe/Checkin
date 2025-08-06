import os
import sqlite3
import logging
import threading
import mysql.connector
from mysql.connector import Error, pooling

# Configura um logger para este módulo
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_db_type = None  # 'primary' ou 'fallback'
        self._primary_pool = None
        self._fallback_conn = None
        self.app = None

    def initialize(self, app):
        """Tenta inicializar a conexão primária, senão, usa o fallback."""
        self.app = app
        with self._lock:
            logger.info("Iniciando gerenciador de banco de dados...")
            if self._try_connect_primary():
                logger.info("Conexão com banco de dados primário (AWS) estabelecida com sucesso.")
            else:
                logger.warning("Falha ao conectar ao banco primário. Usando fallback (SQLite).")
                self._connect_fallback()

    def _get_primary_config(self):
        return {
            'host': os.environ.get('DB_HOST'),
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'database': os.environ.get('DB_NAME'),
            'pool_name': 'primary_pool',
            'pool_size': 5,
            'connection_timeout': 10 # Timeout de 10 segundos
        }

    def _try_connect_primary(self):
        """Tenta criar um pool de conexões com o banco primário."""
        try:
            config = self._get_primary_config()
            # Verifica se as variáveis de ambiente essenciais estão presentes
            if not all([config['host'], config['user'], config['password'], config['database']]):
                logger.error("Variáveis de ambiente do banco de dados primário não configuradas.")
                return False

            pool = pooling.MySQLConnectionPool(**config)
            # Testa a conexão pegando e devolvendo uma conexão
            conn_test = pool.get_connection()
            conn_test.close()

            self._primary_pool = pool
            self._current_db_type = 'primary'
            return True
        except Error as e:
            logger.error(f"Erro ao conectar ao banco primário (AWS): {e}")
            self._primary_pool = None
            return False

    def _connect_fallback(self):
        """Cria e configura a conexão de fallback com SQLite."""
        try:
            self._fallback_conn = sqlite3.connect('fallback.db', check_same_thread=False)
            self._fallback_conn.row_factory = sqlite3.Row
            self._current_db_type = 'fallback'
            logger.info("Conexão de fallback (SQLite) criada com sucesso.")
        except Exception as e:
            logger.critical(f"Falha CRÍTICA ao criar conexão de fallback com SQLite: {e}")
            self._current_db_type = None


    def get_connection(self):
        """Obtém uma conexão do pool ativo (primário ou fallback)."""
        with self._lock:
            if self._current_db_type == 'primary' and self._primary_pool:
                try:
                    # Tenta obter uma conexão. Se falhar, pode ter caído.
                    conn = self._primary_pool.get_connection()
                    # Verifica se a conexão ainda está viva
                    if not conn.is_connected():
                         raise Error("Conexão perdida.")
                    return conn
                except Error as e:
                    logger.error(f"Conexão com o banco primário perdida: {e}. Acionando fallback.")
                    self._connect_fallback()
                    return self._fallback_conn

            elif self._current_db_type == 'fallback':
                return self._fallback_conn
            else:
                raise Exception("Gerenciador de banco de dados não inicializado ou sem conexão.")

    def schedule_reconnect_check(self):
        """Função a ser chamada pelo agendador para tentar reconectar."""
        with self._lock:
            # Só tenta reconectar se estivermos no modo de fallback
            if self._current_db_type == 'fallback':
                logger.info("[AGENDADOR] Verificando se o banco de dados primário está online...")
                if self._try_connect_primary():
                    logger.info("[AGENDADOR] SUCESSO! Reconectado ao banco de dados primário. Novas requisições usarão a AWS.")
                    # O estado já foi alterado para 'primary' dentro de _try_connect_primary
                    if self._fallback_conn:
                        self._fallback_conn.close()
                        self._fallback_conn = None
                else:
                    logger.info("[AGENDADOR] Banco de dados primário ainda indisponível. Tentando novamente em 5 minutos.")

# Instância única para ser usada em toda a aplicação
db_manager = DatabaseManager()