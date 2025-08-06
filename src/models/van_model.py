from .database import Database
from flask import current_app

class VanModel:
    """Classe para gerenciar vans de publicidade"""
    
    @staticmethod
    def listar_vans(filtros=None, paginacao=None):
        """
        Lista vans de acordo com filtros e paginação
        
        Args:
            filtros (dict): Dicionário com filtros para a consulta
            paginacao (dict): Dicionário com informações de paginação (pagina, por_pagina)
        
        Returns:
            dict: Dicionário com resultado da consulta e metadados de paginação
        """
        try:
            # Preparar a query base
            query = """
                SELECT v.*, c.nome as condutor_nome
                FROM vans v
                LEFT JOIN condutores c ON v.condutor_id = c.id
            """
            
            where_conditions = []
            params = []
            
            # Adicionar filtros
            if filtros:
                if 'placa' in filtros and filtros['placa']:
                    where_conditions.append("v.placa LIKE %s")
                    params.append(f"%{filtros['placa']}%")
                
                if 'cidade' in filtros and filtros['cidade']:
                    where_conditions.append("v.cidade LIKE %s")
                    params.append(f"%{filtros['cidade']}%")
                
                if 'estado' in filtros and filtros['estado']:
                    where_conditions.append("v.estado = %s")
                    params.append(filtros['estado'])
                
                if 'status' in filtros and filtros['status']:
                    where_conditions.append("v.status = %s")
                    params.append(filtros['status'])
                    
                if 'campanha_id' in filtros and filtros['campanha_id']:
                    query = """
                        SELECT v.*, c.nome as condutor_nome
                        FROM vans v
                        LEFT JOIN condutores c ON v.condutor_id = c.id
                        JOIN campanha_van cv ON v.id = cv.van_id
                    """
                    where_conditions.append("cv.campanha_id = %s")
                    params.append(filtros['campanha_id'])
                
                if 'nao_associada' in filtros and filtros['nao_associada'] and 'campanha_id' in filtros and filtros['campanha_id']:
                    query = """
                        SELECT v.*, c.nome as condutor_nome
                        FROM vans v
                        LEFT JOIN condutores c ON v.condutor_id = c.id
                        LEFT JOIN campanha_van cv ON v.id = cv.van_id AND cv.campanha_id = %s
                    """
                    params.append(filtros['campanha_id'])
                    where_conditions.append("cv.id IS NULL")
                    
                    # Adicionar condições de cidade/estado se existirem na campanha
                    if 'municipios' in filtros and filtros['municipios']:
                        cidades_estados = []
                        for m in filtros['municipios']:
                            cidades_estados.append(f"(v.cidade = '{m['cidade']}' AND v.estado = '{m['estado']}')")
                        where_conditions.append("(" + " OR ".join(cidades_estados) + ")")
            
            # Adicionar condições WHERE à query
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Ordenar por ID
            query += " ORDER BY v.id"
            
            # Adicionar paginação se especificada
            count_query = "SELECT COUNT(*) as total FROM vans v"
            
            # Adaptar query de contagem se tiver junções específicas
            if 'campanha_id' in filtros and filtros['campanha_id']:
                if 'nao_associada' in filtros and filtros['nao_associada']:
                    count_query = """
                        SELECT COUNT(*) as total
                        FROM vans v
                        LEFT JOIN campanha_van cv ON v.id = cv.van_id AND cv.campanha_id = %s
                    """
                else:
                    count_query = """
                        SELECT COUNT(*) as total
                        FROM vans v
                        JOIN campanha_van cv ON v.id = cv.van_id
                    """
            
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
            vans = Database.execute_query(query, params)
            
            # Para cada van, obter suas escolas
            for van in vans:
                escolas_query = """
                    SELECT e.*
                    FROM escolas e
                    JOIN van_escola ve ON e.id = ve.escola_id
                    WHERE ve.van_id = %s
                """
                escolas = Database.execute_query(escolas_query, (van['id'],))
                van['escolas'] = escolas
            
            return {
                'vans': vans,
                'paginacao': {
                    'pagina': pagina,
                    'por_pagina': por_pagina,
                    'total_registros': total_registros,
                    'total_paginas': total_paginas
                }
            }
        
        except Exception as e:
            current_app.logger.error(f"Erro ao listar vans: {str(e)}")
            raise
    
    @staticmethod
    def obter_van(van_id):
        """
        Obtém uma van específica pelo seu ID
        
        Args:
            van_id (int): ID da van a ser obtida
        
        Returns:
            dict: Dicionário com dados da van, incluindo condutor e escolas
        """
        try:
            # Obter dados da van
            query = """
                SELECT v.*, c.nome as condutor_nome, c.telefone as condutor_telefone, c.email as condutor_email
                FROM vans v
                LEFT JOIN condutores c ON v.condutor_id = c.id
                WHERE v.id = %s
            """
            vans = Database.execute_query(query, (van_id,))
            
            if not vans:
                return None
            
            van = vans[0]
            
            # Obter escolas associadas à van
            escolas_query = """
                SELECT e.*
                FROM escolas e
                JOIN van_escola ve ON e.id = ve.escola_id
                WHERE ve.van_id = %s
            """
            escolas = Database.execute_query(escolas_query, (van_id,))
            van['escolas'] = escolas
            
            # Obter campanhas associadas à van
            campanhas_query = """
                SELECT cc.id, cc.nome, cc.cliente, cc.data_inicio, cc.data_fim, cc.status
                FROM campanhas_controle cc
                JOIN campanha_van cv ON cc.id = cv.campanha_id
                WHERE cv.van_id = %s
            """
            campanhas = Database.execute_query(campanhas_query, (van_id,))
            van['campanhas'] = campanhas
            
            return van
        
        except Exception as e:
            current_app.logger.error(f"Erro ao obter van {van_id}: {str(e)}")
            raise
    
    @staticmethod
    def adicionar_van(dados_van):
        """
        Adiciona uma nova van
        
        Args:
            dados_van (dict): Dicionário com dados da van a ser adicionada
        
        Returns:
            dict: Dicionário com dados da van adicionada, incluindo o ID
        """
        try:
            # Verificar se o condutor existe ou criar um novo
            condutor_id = dados_van.get('condutor_id')
            if not condutor_id and 'condutor_nome' in dados_van:
                # Tentar encontrar o condutor pelo nome
                condutor_query = "SELECT id FROM condutores WHERE nome = %s"
                condutor = Database.execute_query(condutor_query, (dados_van['condutor_nome'],))
                
                if condutor:
                    condutor_id = condutor[0]['id']
                elif 'condutor_nome' in dados_van:
                    # Criar novo condutor
                    condutor_query = """
                        INSERT INTO condutores (nome, telefone, email, documento)
                        VALUES (%s, %s, %s, %s)
                    """
                    condutor_params = (
                        dados_van['condutor_nome'],
                        dados_van.get('condutor_telefone'),
                        dados_van.get('condutor_email'),
                        dados_van.get('condutor_documento')
                    )
                    condutor_id = Database.insert_with_id(condutor_query, condutor_params)
            
            # Preparar query para inserção da van
            query = """
                INSERT INTO vans (
                    placa, modelo, ano, condutor_id, cidade, estado, 
                    latitude, longitude, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Preparar parâmetros
            params = (
                dados_van['placa'],
                dados_van.get('modelo'),
                dados_van.get('ano'),
                condutor_id,
                dados_van.get('cidade'),
                dados_van.get('estado'),
                dados_van.get('latitude'),
                dados_van.get('longitude'),
                dados_van.get('status', 'ativa')
            )
            
            # Inserir van e obter o ID
            van_id = Database.insert_with_id(query, params)
            
            # Associar escolas, se fornecidas
            if 'escolas' in dados_van and dados_van['escolas']:
                for escola_id in dados_van['escolas']:
                    escola_query = "INSERT INTO van_escola (van_id, escola_id) VALUES (%s, %s)"
                    Database.execute_query(escola_query, (van_id, escola_id))
            
            # Obter a van adicionada para retornar
            return VanModel.obter_van(van_id)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao adicionar van: {str(e)}")
            raise
    
    @staticmethod
    def atualizar_van(van_id, dados_van):
        """
        Atualiza uma van existente
        
        Args:
            van_id (int): ID da van a ser atualizada
            dados_van (dict): Dicionário com dados da van a serem atualizados
        
        Returns:
            dict: Dicionário com dados da van atualizada
        """
        try:
            # Verificar se a van existe
            van_atual = VanModel.obter_van(van_id)
            if not van_atual:
                return None
            
            # Atualizar condutor se necessário
            condutor_id = dados_van.get('condutor_id')
            if not condutor_id and 'condutor_nome' in dados_van:
                # Tentar encontrar o condutor pelo nome
                condutor_query = "SELECT id FROM condutores WHERE nome = %s"
                condutor = Database.execute_query(condutor_query, (dados_van['condutor_nome'],))
                
                if condutor:
                    condutor_id = condutor[0]['id']
                else:
                    # Criar novo condutor
                    condutor_query = """
                        INSERT INTO condutores (nome, telefone, email, documento)
                        VALUES (%s, %s, %s, %s)
                    """
                    condutor_params = (
                        dados_van['condutor_nome'],
                        dados_van.get('condutor_telefone'),
                        dados_van.get('condutor_email'),
                        dados_van.get('condutor_documento')
                    )
                    condutor_id = Database.insert_with_id(condutor_query, condutor_params)
                
                # Atualizar o condutor_id nos dados da van
                dados_van['condutor_id'] = condutor_id
            
            # Preparar query para atualização da van
            update_fields = []
            params = []
            
            # Preparar campos a serem atualizados
            if 'placa' in dados_van:
                update_fields.append("placa = %s")
                params.append(dados_van['placa'])
            
            if 'modelo' in dados_van:
                update_fields.append("modelo = %s")
                params.append(dados_van['modelo'])
            
            if 'ano' in dados_van:
                update_fields.append("ano = %s")
                params.append(dados_van['ano'])
            
            if 'condutor_id' in dados_van:
                update_fields.append("condutor_id = %s")
                params.append(dados_van['condutor_id'])
            
            if 'cidade' in dados_van:
                update_fields.append("cidade = %s")
                params.append(dados_van['cidade'])
            
            if 'estado' in dados_van:
                update_fields.append("estado = %s")
                params.append(dados_van['estado'])
            
            if 'latitude' in dados_van:
                update_fields.append("latitude = %s")
                params.append(dados_van['latitude'])
            
            if 'longitude' in dados_van:
                update_fields.append("longitude = %s")
                params.append(dados_van['longitude'])
            
            if 'status' in dados_van:
                update_fields.append("status = %s")
                params.append(dados_van['status'])
            
            # Adicionar ID da van aos parâmetros
            params.append(van_id)
            
            # Atualizar van se houver campos para atualizar
            if update_fields:
                query = f"UPDATE vans SET {', '.join(update_fields)} WHERE id = %s"
                Database.execute_query(query, params)
            
            # Atualizar escolas se fornecidas
            if 'escolas' in dados_van:
                # Primeiro, excluir associações existentes
                Database.execute_query("DELETE FROM van_escola WHERE van_id = %s", (van_id,))
                
                # Depois, inserir as novas associações
                for escola_id in dados_van['escolas']:
                    escola_query = "INSERT INTO van_escola (van_id, escola_id) VALUES (%s, %s)"
                    Database.execute_query(escola_query, (van_id, escola_id))
            
            # Obter a van atualizada para retornar
            return VanModel.obter_van(van_id)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar van {van_id}: {str(e)}")
            raise
    
    @staticmethod
    def excluir_van(van_id):
        """
        Exclui uma van existente
        
        Args:
            van_id (int): ID da van a ser excluída
        
        Returns:
            bool: True se a van foi excluída com sucesso, False caso contrário
        """
        try:
            # Verificar se a van existe
            van = VanModel.obter_van(van_id)
            if not van:
                return False
            
            # Excluir as associações com escolas
            Database.execute_query("DELETE FROM van_escola WHERE van_id = %s", (van_id,))
            
            # Excluir associações com campanhas
            Database.execute_query("DELETE FROM campanha_van WHERE van_id = %s", (van_id,))
            
            # Excluir a van
            query = "DELETE FROM vans WHERE id = %s"
            result = Database.execute_query(query, (van_id,))
            
            return bool(result and result[0]['affected_rows'] > 0)
        
        except Exception as e:
            current_app.logger.error(f"Erro ao excluir van {van_id}: {str(e)}")
            raise