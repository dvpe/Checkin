from .database import Database
from datetime import datetime
import random
import string
import logging
from flask import current_app

class CampanhaEscalavel:
    """Classe para gerenciar campanhas publicitárias escaláveis"""
    
    @staticmethod
    def gerar_codigo_acesso(tamanho=8):
        """Gera um código de acesso aleatório para campanhas"""
        caracteres = string.ascii_uppercase + string.digits
        while True:
            codigo = ''.join(random.choice(caracteres) for _ in range(tamanho))
            
            # Verificar se o código já existe
            query = "SELECT id FROM campanhas_controle WHERE codigo_acesso = %s"
            resultado = Database.execute_query(query, (codigo,))
            
            if not resultado:
                return codigo
    
    @staticmethod
    def listar_campanhas(filtros=None, paginacao=None):
        """
        Lista campanhas de acordo com filtros e paginação
        
        Args:
            filtros (dict): Dicionário com filtros para a consulta
            paginacao (dict): Dicionário com informações de paginação (pagina, por_pagina)
        
        Returns:
            dict: Dicionário com resultado da consulta e metadados de paginação
        """
        try:
            # Preparar a query base
            query = """
                SELECT c.*, 
                       COUNT(DISTINCT cv.van_id) AS vans_associadas
                FROM campanhas_controle c
                LEFT JOIN campanha_van cv ON c.id = cv.campanha_id
            """
            
            where_conditions = []
            params = []
            
            # Adicionar filtros
            if filtros:
                if 'status' in filtros and filtros['status']:
                    where_conditions.append("c.status = %s")
                    params.append(filtros['status'])
                
                if 'cliente' in filtros and filtros['cliente']:
                    where_conditions.append("c.cliente LIKE %s")
                    params.append(f"%{filtros['cliente']}%")
                
                if 'nome' in filtros and filtros['nome']:
                    where_conditions.append("c.nome LIKE %s")
                    params.append(f"%{filtros['nome']}%")
                
                if 'data_inicio' in filtros and filtros['data_inicio']:
                    where_conditions.append("c.data_inicio >= %s")
                    params.append(filtros['data_inicio'])
                
                if 'data_fim' in filtros and filtros['data_fim']:
                    where_conditions.append("c.data_fim <= %s")
                    params.append(filtros['data_fim'])
            
            # Adicionar condições WHERE à query
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Agrupar por ID da campanha
            query += " GROUP BY c.id"
            
            # Ordenar por data de criação decrescente
            query += " ORDER BY c.data_criacao DESC"
            
            # Adicionar paginação se especificada
            count_query = "SELECT COUNT(*) as total FROM campanhas_controle c"
            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)
            
            # Obter total de registros para paginação
            count_result = Database.execute_query(count_query, params)
            total_registros = count_result[0]['total'] if count_result else 0
            
            if paginacao:
                pagina = max(1, paginacao.get('pagina', 1))
                por_pagina = max(1, paginacao.get('por_pagina', 10))
                offset = (pagina - 1) * por_pagina
                
                query += f" LIMIT {por_pagina} OFFSET {offset}"
                
                total_paginas = (total_registros + por_pagina - 1) // por_pagina
            else:
                pagina = 1
                por_pagina = total_registros
                total_paginas = 1
            
            # Executar a query final
            campanhas = Database.execute_query(query, params)
            
            # Para cada campanha, obter os municípios
            for campanha in campanhas:
                municipios_query = """
                    SELECT id, cidade, estado, numero_vans_planejado
                    FROM campanha_municipios
                    WHERE campanha_id = %s
                """
                municipios = Database.execute_query(municipios_query, (campanha['id'],))
                campanha['municipios'] = municipios
            
            return {
                'campanhas': campanhas,
                'paginacao': {
                    'pagina': pagina,
                    'por_pagina': por_pagina,
                    'total_registros': total_registros,
                    'total_paginas': total_paginas
                }
            }
        
        except Exception as e:
            current_app.logger.error(f"Erro ao listar campanhas: {str(e)}")
            raise
    
    @staticmethod
    def obter_campanha(campanha_id):
        """
        Obtém uma campanha específica pelo seu ID
        
        Args:
            campanha_id (int): ID da campanha a ser obtida
        
        Returns:
            dict: Dicionário com dados da campanha, incluindo municípios e vans associadas
        """
        try:
            # Obter dados da campanha
            query = "SELECT * FROM campanhas_controle WHERE id = %s"
            campanhas = Database.execute_query(query, (campanha_id,))
            
            if not campanhas:
                return None
            
            campanha = campanhas[0]
            
            # Obter municípios da campanha
            municipios_query = """
                SELECT id, cidade, estado, numero_vans_planejado
                FROM campanha_municipios
                WHERE campanha_id = %s
            """
            municipios = Database.execute_query(municipios_query, (campanha_id,))
            campanha['municipios'] = municipios
            
            # Obter vans associadas à campanha
            vans_query = """
                SELECT cv.id as campanha_van_id, v.id, v.placa, v.modelo,
                       v.cidade, v.estado, c.nome as condutor_nome
                FROM campanha_van cv
                JOIN vans v ON cv.van_id = v.id
                LEFT JOIN condutores c ON v.condutor_id = c.id
                WHERE cv.campanha_id = %s
            """
            vans = Database.execute_query(vans_query, (campanha_id,))
            
            # Para cada van, obter fotos de checking
            for van in vans:
                fotos_query = """
                    SELECT id, tipo_foto, url_foto, data_upload
                    FROM fotos_checking
                    WHERE campanha_van_id = %s
                """
                fotos = Database.execute_query(fotos_query, (van['campanha_van_id'],))
                van['fotos'] = fotos
            
            campanha['vans'] = vans
            
            return campanha
        
        except Exception as e:
            current_app.logger.error(f"Erro ao obter campanha {campanha_id}: {str(e)}")
            raise
    
    @staticmethod
    def criar_campanha(dados_campanha):
        """
        Cria uma nova campanha publicitária
        
        Args:
            dados_campanha (dict): Dicionário com dados da campanha a ser criada
        
        Returns:
            dict: Dicionário com dados da campanha criada, incluindo o ID
        """
        try:
            # Gerar código de acesso único para a campanha
            codigo_acesso = CampanhaEscalavel.gerar_codigo_acesso()
            
            # Preparar query para inserção da campanha
            query = """
                INSERT INTO campanhas_controle (
                    nome, cliente, descricao, data_inicio, data_fim, 
                    numero_vans_total, codigo_acesso, status, tipo_campanha
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Preparar parâmetros
            params = (
                dados_campanha['nome'],
                dados_campanha['cliente'],
                dados_campanha.get('descricao', ''),
                dados_campanha['data_inicio'],
                dados_campanha['data_fim'],
                dados_campanha['numero_vans_total'],
                codigo_acesso,
                dados_campanha.get('status', 'ativa'),
                dados_campanha.get('tipo_campanha', 'local')
            )
            
            # Inserir campanha e obter o ID
            campanha_id = Database.insert_with_id(query, params)
            
            # Inserir municípios associados à campanha, se fornecidos
            if 'municipios' in dados_campanha and dados_campanha['municipios']:
                for municipio in dados_campanha['municipios']:
                    mun_query = """
                        INSERT INTO campanha_municipios (
                            campanha_id, cidade, estado, numero_vans_planejado
                        ) VALUES (%s, %s, %s, %s)
                    """
                    mun_params = (
                        campanha_id,
                        municipio['cidade'],
                        municipio['estado'],
                        municipio.get('numero_vans_planejado', 1)
                    )
                    Database.insert_with_id(mun_query, mun_params)
            
            # Obter a campanha criada para retornar
            return CampanhaEscalavel.obter_campanha(campanha_id)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao criar campanha: {str(e)}")
            raise
    
    @staticmethod
    def atualizar_campanha(campanha_id, dados_campanha):
        """
        Atualiza uma campanha existente
        
        Args:
            campanha_id (int): ID da campanha a ser atualizada
            dados_campanha (dict): Dicionário com dados da campanha a serem atualizados
        
        Returns:
            dict: Dicionário com dados da campanha atualizada
        """
        try:
            # Verificar se a campanha existe
            campanha_atual = CampanhaEscalavel.obter_campanha(campanha_id)
            if not campanha_atual:
                return None
            
            # Preparar query para atualização da campanha
            update_fields = []
            params = []
            
            # Preparar campos a serem atualizados
            if 'nome' in dados_campanha:
                update_fields.append("nome = %s")
                params.append(dados_campanha['nome'])
            
            if 'cliente' in dados_campanha:
                update_fields.append("cliente = %s")
                params.append(dados_campanha['cliente'])
            
            if 'descricao' in dados_campanha:
                update_fields.append("descricao = %s")
                params.append(dados_campanha['descricao'])
            
            if 'data_inicio' in dados_campanha:
                update_fields.append("data_inicio = %s")
                params.append(dados_campanha['data_inicio'])
            
            if 'data_fim' in dados_campanha:
                update_fields.append("data_fim = %s")
                params.append(dados_campanha['data_fim'])
            
            if 'numero_vans_total' in dados_campanha:
                update_fields.append("numero_vans_total = %s")
                params.append(dados_campanha['numero_vans_total'])
            
            if 'status' in dados_campanha:
                update_fields.append("status = %s")
                params.append(dados_campanha['status'])
            
            if 'tipo_campanha' in dados_campanha:
                update_fields.append("tipo_campanha = %s")
                params.append(dados_campanha['tipo_campanha'])
            
            # Adicionar ID da campanha aos parâmetros
            params.append(campanha_id)
            
            # Atualizar campanha se houver campos para atualizar
            if update_fields:
                query = f"UPDATE campanhas_controle SET {', '.join(update_fields)} WHERE id = %s"
                Database.execute_query(query, params)
            
            # Atualizar municípios se fornecidos
            if 'municipios' in dados_campanha:
                # Primeiro, excluir municípios existentes
                Database.execute_query("DELETE FROM campanha_municipios WHERE campanha_id = %s", (campanha_id,))
                
                # Depois, inserir os novos municípios
                for municipio in dados_campanha['municipios']:
                    mun_query = """
                        INSERT INTO campanha_municipios (
                            campanha_id, cidade, estado, numero_vans_planejado
                        ) VALUES (%s, %s, %s, %s)
                    """
                    mun_params = (
                        campanha_id,
                        municipio['cidade'],
                        municipio['estado'],
                        municipio.get('numero_vans_planejado', 1)
                    )
                    Database.insert_with_id(mun_query, mun_params)
            
            # Obter a campanha atualizada para retornar
            return CampanhaEscalavel.obter_campanha(campanha_id)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar campanha {campanha_id}: {str(e)}")
            raise
    
    @staticmethod
    def excluir_campanha(campanha_id):
        """
        Exclui uma campanha existente
        
        Args:
            campanha_id (int): ID da campanha a ser excluída
        
        Returns:
            bool: True se a campanha foi excluída com sucesso, False caso contrário
        """
        try:
            # Verificar se a campanha existe
            campanha = CampanhaEscalavel.obter_campanha(campanha_id)
            if not campanha:
                return False
            
            # Excluir a campanha (as relações serão excluídas em cascata)
            query = "DELETE FROM campanhas_controle WHERE id = %s"
            result = Database.execute_query(query, (campanha_id,))
            
            return bool(result and result[0]['affected_rows'] > 0)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao excluir campanha {campanha_id}: {str(e)}")
            raise
    
    @staticmethod
    def associar_vans(campanha_id, dados_vans):
        """
        Associa vans a uma campanha
        
        Args:
            campanha_id (int): ID da campanha
            dados_vans (list): Lista de IDs de vans a serem associadas
        
        Returns:
            int: Número de vans associadas com sucesso
        """
        try:
            # Verificar se a campanha existe
            campanha = CampanhaEscalavel.obter_campanha(campanha_id)
            if not campanha:
                return 0
            
            # Inserir as associações
            query = "INSERT INTO campanha_van (campanha_id, van_id) VALUES (%s, %s)"
            params_list = [(campanha_id, van_id) for van_id in dados_vans]
            
            # Usar executemany para inserir múltiplos registros de uma vez
            afetados = Database.execute_many(query, params_list)
            
            return afetados
        
        except Exception as e:
            current_app.logger.error(f"Erro ao associar vans à campanha {campanha_id}: {str(e)}")
            raise
    
    @staticmethod
    def desassociar_van(campanha_id, van_id):
        """
        Desassocia uma van de uma campanha
        
        Args:
            campanha_id (int): ID da campanha
            van_id (int): ID da van a ser desassociada
        
        Returns:
            bool: True se a van foi desassociada com sucesso, False caso contrário
        """
        try:
            # Excluir a associação
            query = "DELETE FROM campanha_van WHERE campanha_id = %s AND van_id = %s"
            result = Database.execute_query(query, (campanha_id, van_id))
            
            return bool(result and result[0]['affected_rows'] > 0)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao desassociar van {van_id} da campanha {campanha_id}: {str(e)}")
            raise
    
    @staticmethod
    def autenticar_por_codigo(codigo_acesso):
        """
        Autentica uma campanha pelo código de acesso
        
        Args:
            codigo_acesso (str): Código de acesso da campanha
        
        Returns:
            dict: Dicionário com dados da campanha, ou None se não encontrada
        """
        try:
            # Buscar campanha pelo código de acesso
            query = """
                SELECT c.*, COUNT(DISTINCT cv.van_id) AS vans_associadas
                FROM campanhas_controle c
                LEFT JOIN campanha_van cv ON c.id = cv.campanha_id
                WHERE c.codigo_acesso = %s
                GROUP BY c.id
            """
            campanhas = Database.execute_query(query, (codigo_acesso,))
            
            if not campanhas:
                return None
            
            campanha = campanhas[0]
            
            # Obter municípios da campanha
            municipios_query = """
                SELECT id, cidade, estado, numero_vans_planejado
                FROM campanha_municipios
                WHERE campanha_id = %s
            """
            municipios = Database.execute_query(municipios_query, (campanha['id'],))
            campanha['municipios'] = municipios
            
            return campanha
        
        except Exception as e:
            current_app.logger.error(f"Erro ao autenticar campanha com código {codigo_acesso}: {str(e)}")
            raise