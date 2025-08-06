import mysql.connector
from mysql.connector import Error
from flask import current_app
import os
import json
import logging

class Database:
    """Classe para gerenciar conexões com o banco de dados MySQL"""
    
    connection_pool = None
    
    @staticmethod
    def initialize():
        """Inicializa o pool de conexões com o banco de dados"""
        try:
            # Verificar se já existe um pool de conexões
            if Database.connection_pool is not None:
                current_app.logger.info("Pool de conexões já inicializado")
                return
            
            # Obter configurações do banco de dados
            db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'user': os.environ.get('DB_USER', 'root'),
                'password': os.environ.get('DB_PASSWORD', ''),
                'database': os.environ.get('DB_NAME', 'controle_campanhas'),
                'pool_name': 'controle_campanhas_pool',
                'pool_size': 5
            }
            
            # Criar pool de conexões
            Database.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
            current_app.logger.info("Pool de conexões inicializado com sucesso")
        
        except Error as e:
            current_app.logger.error(f"Erro ao inicializar pool de conexões: {str(e)}")
            # Em ambiente de desenvolvimento, usar um modo de fallback com SQLite
            if os.environ.get('FLASK_ENV') == 'development':
                current_app.logger.warning("Usando modo de fallback com SQLite")
                Database._initialize_sqlite()
            else:
                raise
    
    @staticmethod
    def _initialize_sqlite():
        """Inicializa conexão SQLite para ambiente de desenvolvimento"""
        try:
            import sqlite3
            # Criar conexão SQLite (apenas para desenvolvimento)
            Database.connection_pool = {
                'sqlite': True,
                'connection': sqlite3.connect('app.db', check_same_thread=False)
            }
            # Usar dicionários como resultado
            Database.connection_pool['connection'].row_factory = sqlite3.Row
            current_app.logger.info("Conexão SQLite inicializada para desenvolvimento")
        except Exception as e:
            current_app.logger.error(f"Erro ao inicializar SQLite: {str(e)}")
            raise
    
    @staticmethod
    def get_connection():
        """Obtém uma conexão do pool"""
        try:
            if Database.connection_pool is None:
                Database.initialize()
            
            # Verificar se estamos usando SQLite (ambiente de desenvolvimento)
            if isinstance(Database.connection_pool, dict) and Database.connection_pool.get('sqlite'):
                return Database.connection_pool['connection']
            
            # Obter conexão do pool MySQL
            return Database.connection_pool.get_connection()
        
        except Error as e:
            current_app.logger.error(f"Erro ao obter conexão: {str(e)}")
            raise
    
    @staticmethod
    def close_connection(connection, cursor=None):
        """Fecha uma conexão e seu cursor"""
        try:
            # Fechar cursor se existir
            if cursor is not None:
                cursor.close()
            
            # Verificar se estamos usando SQLite (não fecha a conexão, apenas commit)
            if isinstance(Database.connection_pool, dict) and Database.connection_pool.get('sqlite'):
                connection.commit()
                return
            
            # Fechar conexão MySQL
            if connection.is_connected():
                connection.close()
        
        except Error as e:
            current_app.logger.error(f"Erro ao fechar conexão: {str(e)}")
    
    @staticmethod
    def execute_query(query, params=None):
        """
        Executa uma query e retorna os resultados
        
        Args:
            query (str): Query SQL a ser executada
            params (tuple): Parâmetros para a query
        
        Returns:
            list: Lista de dicionários com os resultados da query
        """
        connection = None
        cursor = None
        results = []
        
        try:
            # Obter conexão
            connection = Database.get_connection()
            
            # Verificar se estamos usando SQLite
            is_sqlite = isinstance(Database.connection_pool, dict) and Database.connection_pool.get('sqlite')
            
            # Criar cursor
            if is_sqlite:
                cursor = connection.cursor()
            else:
                cursor = connection.cursor(dictionary=True)
            
            # Executar query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Obter resultados se for SELECT
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                
                # Converter rows SQLite para dicionários se necessário
                if is_sqlite:
                    results = [dict(row) for row in results]
            else:
                # Para INSERTs, UPDATEs, DELETEs, retornar informações de affected rows
                connection.commit()
                affected_rows = cursor.rowcount
                results = [{'affected_rows': affected_rows}]
        
        except Error as e:
            if connection:
                connection.rollback()
            current_app.logger.error(f"Erro ao executar query: {str(e)}")
            raise
        
        finally:
            # Fechar conexão e cursor
            Database.close_connection(connection, cursor)
        
        return results
    
    @staticmethod
    def insert_with_id(query, params=None):
        """
        Executa uma query de inserção e retorna o ID gerado
        
        Args:
            query (str): Query SQL de inserção
            params (tuple): Parâmetros para a query
        
        Returns:
            int: ID gerado pela inserção
        """
        connection = None
        cursor = None
        
        try:
            # Obter conexão
            connection = Database.get_connection()
            
            # Verificar se estamos usando SQLite
            is_sqlite = isinstance(Database.connection_pool, dict) and Database.connection_pool.get('sqlite')
            
            # Criar cursor
            if is_sqlite:
                cursor = connection.cursor()
            else:
                cursor = connection.cursor(dictionary=True)
            
            # Executar query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Commit para efetivar a inserção
            connection.commit()
            
            # Obter o ID gerado
            if is_sqlite:
                last_id = cursor.lastrowid
            else:
                last_id = cursor.lastrowid
            
            return last_id
        
        except Error as e:
            if connection:
                connection.rollback()
            current_app.logger.error(f"Erro ao executar inserção: {str(e)}")
            raise
        
        finally:
            # Fechar conexão e cursor
            Database.close_connection(connection, cursor)
    
    @staticmethod
    def execute_many(query, params_list):
        """
        Executa uma query múltiplas vezes com diferentes parâmetros
        
        Args:
            query (str): Query SQL a ser executada
            params_list (list): Lista de tuplas com parâmetros
        
        Returns:
            int: Número de linhas afetadas
        """
        connection = None
        cursor = None
        
        try:
            # Obter conexão
            connection = Database.get_connection()
            
            # Criar cursor
            if isinstance(Database.connection_pool, dict) and Database.connection_pool.get('sqlite'):
                cursor = connection.cursor()
            else:
                cursor = connection.cursor(dictionary=True)
            
            # Executar query múltiplas vezes
            cursor.executemany(query, params_list)
            
            # Commit para efetivar as operações
            connection.commit()
            
            # Retornar número de linhas afetadas
            return cursor.rowcount
        
        except Error as e:
            if connection:
                connection.rollback()
            current_app.logger.error(f"Erro ao executar executemany: {str(e)}")
            raise
        
        finally:
            # Fechar conexão e cursor
            Database.close_connection(connection, cursor)