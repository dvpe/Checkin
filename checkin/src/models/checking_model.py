import os
import time
from datetime import datetime
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from .database import Database

class CheckingModel:
    """Classe para gerenciar o processo de checking de campanhas"""
    
    TIPOS_FOTO_VALIDOS = ['inicial', 'adesivo', 'final']
    EXTENSOES_PERMITIDAS = {'png', 'jpg', 'jpeg'}
    
    @staticmethod
    def _extensao_arquivo_valida(filename):
        """Verifica se a extensão do arquivo é permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in CheckingModel.EXTENSOES_PERMITIDAS
    
    @staticmethod
    def _gerar_nome_arquivo(filename, tipo_foto):
        """Gera um nome único para o arquivo"""
        extensao = filename.rsplit('.', 1)[1].lower()
        timestamp = int(time.time())
        nome_unico = f"{tipo_foto}_{timestamp}_{str(uuid.uuid4().hex)[:8]}.{extensao}"
        return nome_unico
    
    @staticmethod
    def _obter_caminho_upload():
        """Obtém o caminho para o diretório de uploads"""
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        return upload_folder
    
    @staticmethod
    def listar_vans_por_codigo_acesso(codigo_acesso):
        """
        Lista vans associadas a uma campanha através do código de acesso
        
        Args:
            codigo_acesso (str): Código de acesso da campanha
        
        Returns:
            list: Lista de vans associadas à campanha
        """
        try:
            # Obter ID da campanha pelo código de acesso
            query = "SELECT id FROM campanhas_controle WHERE codigo_acesso = %s"
            campanhas = Database.execute_query(query, (codigo_acesso,))
            
            if not campanhas:
                return []
            
            campanha_id = campanhas[0]['id']
            
            # Obter vans associadas à campanha
            vans_query = """
                SELECT cv.id as campanha_van_id, v.id, v.placa, v.modelo, 
                       c.nome as condutor_nome, v.cidade, v.estado
                FROM campanha_van cv
                JOIN vans v ON cv.van_id = v.id
                LEFT JOIN condutores c ON v.condutor_id = c.id
                WHERE cv.campanha_id = %s
            """
            vans = Database.execute_query(vans_query, (campanha_id,))
            
            # Para cada van, obter fotos de checking já enviadas
            for van in vans:
                fotos_query = """
                    SELECT tipo_foto, url_foto, data_upload
                    FROM fotos_checking
                    WHERE campanha_van_id = %s
                """
                fotos = Database.execute_query(fotos_query, (van['campanha_van_id'],))
                van['fotos'] = {tipo: None for tipo in CheckingModel.TIPOS_FOTO_VALIDOS}
                
                # Marcar quais tipos de fotos já foram enviados
                for foto in fotos:
                    van['fotos'][foto['tipo_foto']] = {
                        'url': foto['url_foto'],
                        'data': foto['data_upload']
                    }
            
            return vans
        
        except Exception as e:
            current_app.logger.error(f"Erro ao listar vans por código de acesso {codigo_acesso}: {str(e)}")
            raise
    
    @staticmethod
    def validar_campanha_van(campanha_van_id):
        """
        Verifica se uma relação campanha-van é válida
        
        Args:
            campanha_van_id (int): ID da relação campanha-van
        
        Returns:
            dict: Dados da relação campanha-van, ou None se não for válida
        """
        try:
            query = """
                SELECT cv.id, cv.campanha_id, cv.van_id, 
                       cc.nome as campanha_nome, cc.status as campanha_status,
                       v.placa as van_placa
                FROM campanha_van cv
                JOIN campanhas_controle cc ON cv.campanha_id = cc.id
                JOIN vans v ON cv.van_id = v.id
                WHERE cv.id = %s
            """
            result = Database.execute_query(query, (campanha_van_id,))
            
            if not result or result[0]['campanha_status'] != 'ativa':
                return None
                
            return result[0]
        
        except Exception as e:
            current_app.logger.error(f"Erro ao validar campanha-van {campanha_van_id}: {str(e)}")
            raise
    
    @staticmethod
    def salvar_foto_checking(campanha_van_id, tipo_foto, arquivo):
        """
        Salva uma foto de checking
        
        Args:
            campanha_van_id (int): ID da relação campanha-van
            tipo_foto (str): Tipo da foto (inicial, adesivo ou final)
            arquivo (FileStorage): Objeto do arquivo enviado
        
        Returns:
            dict: Dados da foto salva
        """
        try:
            # Validar tipo de foto
            if tipo_foto not in CheckingModel.TIPOS_FOTO_VALIDOS:
                raise ValueError(f"Tipo de foto inválido: {tipo_foto}")
            
            # Validar campanha-van
            campanha_van = CheckingModel.validar_campanha_van(campanha_van_id)
            if not campanha_van:
                raise ValueError(f"Relação campanha-van inválida: {campanha_van_id}")
            
            # Validar arquivo
            if not arquivo or not CheckingModel._extensao_arquivo_valida(arquivo.filename):
                raise ValueError("Arquivo inválido ou extensão não permitida")
            
            # Gerar nome único para o arquivo
            nome_arquivo = CheckingModel._gerar_nome_arquivo(arquivo.filename, tipo_foto)
            
            # Obter caminho de upload
            upload_folder = CheckingModel._obter_caminho_upload()
            
            # Criar estrutura de pastas
            campanha_folder = os.path.join(upload_folder, f"campanha_{campanha_van['campanha_id']}")
            if not os.path.exists(campanha_folder):
                os.makedirs(campanha_folder)
            
            van_folder = os.path.join(campanha_folder, f"van_{campanha_van['van_id']}")
            if not os.path.exists(van_folder):
                os.makedirs(van_folder)
            
            # Caminho completo do arquivo
            caminho_arquivo = os.path.join(van_folder, nome_arquivo)
            
            # Salvar arquivo
            arquivo.save(caminho_arquivo)
            
            # Caminho relativo para armazenar no banco
            caminho_relativo = f"uploads/campanha_{campanha_van['campanha_id']}/van_{campanha_van['van_id']}/{nome_arquivo}"
            
            # Verificar se já existe uma foto deste tipo para esta relação campanha-van
            check_query = """
                SELECT id FROM fotos_checking 
                WHERE campanha_van_id = %s AND tipo_foto = %s
            """
            foto_existente = Database.execute_query(check_query, (campanha_van_id, tipo_foto))
            
            if foto_existente:
                # Atualizar o registro existente
                update_query = """
                    UPDATE fotos_checking 
                    SET url_foto = %s, data_upload = CURRENT_TIMESTAMP 
                    WHERE campanha_van_id = %s AND tipo_foto = %s
                """
                Database.execute_query(update_query, (caminho_relativo, campanha_van_id, tipo_foto))
                foto_id = foto_existente[0]['id']
            else:
                # Inserir novo registro
                insert_query = """
                    INSERT INTO fotos_checking (campanha_van_id, tipo_foto, url_foto)
                    VALUES (%s, %s, %s)
                """
                foto_id = Database.insert_with_id(insert_query, (campanha_van_id, tipo_foto, caminho_relativo))
            
            # Retornar dados da foto
            return {
                'id': foto_id,
                'campanha_van_id': campanha_van_id,
                'tipo_foto': tipo_foto,
                'url_foto': caminho_relativo,
                'data_upload': datetime.now().isoformat()
            }
        
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar foto de checking: {str(e)}")
            raise
    
    @staticmethod
    def obter_progresso_van(campanha_van_id):
        """
        Obtém o progresso de checking de uma van
        
        Args:
            campanha_van_id (int): ID da relação campanha-van
        
        Returns:
            dict: Dados de progresso da van
        """
        try:
            # Validar campanha-van
            campanha_van = CheckingModel.validar_campanha_van(campanha_van_id)
            if not campanha_van:
                raise ValueError(f"Relação campanha-van inválida: {campanha_van_id}")
            
            # Obter fotos de checking
            fotos_query = """
                SELECT tipo_foto, url_foto, data_upload
                FROM fotos_checking
                WHERE campanha_van_id = %s
            """
            fotos = Database.execute_query(fotos_query, (campanha_van_id,))
            
            # Inicializar contagem de fotos
            progresso = {
                'inicial': False,
                'adesivo': False,
                'final': False
            }
            
            # Verificar quais fotos já foram enviadas
            for foto in fotos:
                progresso[foto['tipo_foto']] = True
            
            # Calcular percentual de conclusão
            if progresso['final']:
                percentual = 100
                status = 'concluido'
            elif progresso['adesivo']:
                percentual = 50
                status = 'em_andamento'
            elif progresso['inicial']:
                percentual = 25
                status = 'iniciado'
            else:
                percentual = 0
                status = 'pendente'
            
            return {
                'campanha_van_id': campanha_van_id,
                'campanha': {
                    'id': campanha_van['campanha_id'],
                    'nome': campanha_van['campanha_nome']
                },
                'van': {
                    'id': campanha_van['van_id'],
                    'placa': campanha_van['van_placa']
                },
                'progresso': progresso,
                'percentual': percentual,
                'status': status
            }
        
        except Exception as e:
            current_app.logger.error(f"Erro ao obter progresso de van {campanha_van_id}: {str(e)}")
            raise