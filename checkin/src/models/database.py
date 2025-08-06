# src/models/database.py

import logging
from .database_manager import db_manager

logger = logging.getLogger(__name__)

class Database:
    @staticmethod
    def execute_query(query, params=None):
        connection = None
        cursor = None
        results = []
        is_sqlite = db_manager._current_db_type == 'fallback'

        try:
            connection = db_manager.get_connection()
            cursor = connection.cursor()

            if not is_sqlite:
                 pass # O ideal é que o pool já esteja configurado

            cursor.execute(query, params or ())

            if query.strip().upper().startswith('SELECT'):
                results = [dict(row) for row in cursor.fetchall()]
            else:
                connection.commit()
                results = [{'affected_rows': cursor.rowcount}]
        except Exception as e:
            logger.error(f"Erro ao executar query: {str(e)} no banco de dados {db_manager._current_db_type}")
            if connection and not is_sqlite:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            # Devolve a conexão ao pool (se for do pool) ou não faz nada (SQLite)
            if connection and hasattr(connection, 'close') and not is_sqlite:
                 connection.close()

        return results

    @staticmethod
    def insert_with_id(query, params=None):
        # A lógica é muito similar a execute_query
        connection = None
        cursor = None
        last_id = None
        is_sqlite = db_manager._current_db_type == 'fallback'

        try:
            connection = db_manager.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
            last_id = cursor.lastrowid
        except Exception as e:
            logger.error(f"Erro ao executar inserção: {str(e)} no banco de dados {db_manager._current_db_type}")
            if connection and not is_sqlite:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and hasattr(connection, 'close') and not is_sqlite:
                connection.close()

        return last_id

    # O método execute_many pode ser adaptado de forma similar