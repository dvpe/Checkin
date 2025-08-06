from flask import Blueprint, request, jsonify, current_app
from models.checking_model import CheckingModel
from werkzeug.utils import secure_filename
import os

checking_bp = Blueprint('checking_bp', __name__)

@checking_bp.route('/vans/<string:codigo_acesso>', methods=['GET'])
def listar_vans_por_codigo(codigo_acesso):
    """Lista vans associadas a uma campanha através do código de acesso"""
    try:
        vans = CheckingModel.listar_vans_por_codigo_acesso(codigo_acesso)
        
        if not vans:
            return jsonify({'mensagem': 'Nenhuma van encontrada para este código de acesso'}), 404
        
        return jsonify({'vans': vans})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao listar vans por código de acesso {codigo_acesso}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@checking_bp.route('/foto/<int:campanha_van_id>', methods=['POST'])
def enviar_foto(campanha_van_id):
    """Envia uma foto de checking para uma relação campanha-van"""
    try:
        # Verificar se o tipo de foto foi informado
        if 'tipo_foto' not in request.form:
            return jsonify({'erro': 'Tipo de foto não informado'}), 400
        
        tipo_foto = request.form['tipo_foto']
        
        # Verificar se o tipo de foto é válido
        if tipo_foto not in CheckingModel.TIPOS_FOTO_VALIDOS:
            return jsonify({'erro': f'Tipo de foto inválido. Tipos válidos: {", ".join(CheckingModel.TIPOS_FOTO_VALIDOS)}'}), 400
        
        # Verificar se o arquivo foi enviado
        if 'foto' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['foto']
        
        # Verificar se o arquivo está vazio
        if arquivo.filename == '':
            return jsonify({'erro': 'Nome de arquivo vazio'}), 400
        
        # Verificar extensão do arquivo
        if not CheckingModel._extensao_arquivo_valida(arquivo.filename):
            return jsonify({'erro': f'Extensão de arquivo não permitida. Extensões válidas: {", ".join(CheckingModel.EXTENSOES_PERMITIDAS)}'}), 400
        
        # Salvar a foto
        resultado = CheckingModel.salvar_foto_checking(campanha_van_id, tipo_foto, arquivo)
        
        return jsonify(resultado), 201
    
    except ValueError as e:
        current_app.logger.error(f"Erro de validação ao enviar foto: {str(e)}")
        return jsonify({'erro': str(e)}), 400
    
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar foto para campanha-van {campanha_van_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@checking_bp.route('/progresso/<int:campanha_van_id>', methods=['GET'])
def obter_progresso(campanha_van_id):
    """Obtém o progresso de checking de uma van"""
    try:
        progresso = CheckingModel.obter_progresso_van(campanha_van_id)
        
        if not progresso:
            return jsonify({'erro': 'Relação campanha-van não encontrada ou inválida'}), 404
        
        return jsonify(progresso)
    
    except ValueError as e:
        current_app.logger.error(f"Erro de validação ao obter progresso: {str(e)}")
        return jsonify({'erro': str(e)}), 400
    
    except Exception as e:
        current_app.logger.error(f"Erro ao obter progresso da campanha-van {campanha_van_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500