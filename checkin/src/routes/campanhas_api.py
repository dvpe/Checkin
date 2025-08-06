from flask import Blueprint, request, jsonify, current_app
from models.campanha_escalavel import CampanhaEscalavel

campanhas_bp = Blueprint('campanhas_bp', __name__)

@campanhas_bp.route('/', methods=['GET'])
def listar_campanhas():
    """Lista campanhas com filtros e paginação"""
    try:
        # Obter parâmetros de filtro
        filtros = {}
        if 'status' in request.args:
            filtros['status'] = request.args.get('status')
        if 'cliente' in request.args:
            filtros['cliente'] = request.args.get('cliente')
        if 'nome' in request.args:
            filtros['nome'] = request.args.get('nome')
        if 'data_inicio' in request.args:
            filtros['data_inicio'] = request.args.get('data_inicio')
        if 'data_fim' in request.args:
            filtros['data_fim'] = request.args.get('data_fim')
        
        # Obter parâmetros de paginação
        pagina = int(request.args.get('pagina', 1))
        por_pagina = int(request.args.get('por_pagina', 10))
        paginacao = {'pagina': pagina, 'por_pagina': por_pagina}
        
        # Obter campanhas
        resultado = CampanhaEscalavel.listar_campanhas(filtros, paginacao)
        
        return jsonify(resultado)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao listar campanhas: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/<int:campanha_id>', methods=['GET'])
def obter_campanha(campanha_id):
    """Obtém uma campanha específica pelo ID"""
    try:
        campanha = CampanhaEscalavel.obter_campanha(campanha_id)
        
        if not campanha:
            return jsonify({'erro': 'Campanha não encontrada'}), 404
        
        return jsonify(campanha)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao obter campanha {campanha_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/', methods=['POST'])
def criar_campanha():
    """Cria uma nova campanha"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados or 'nome' not in dados or 'cliente' not in dados:
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        # Criação da campanha
        campanha = CampanhaEscalavel.criar_campanha(dados)
        
        return jsonify(campanha), 201
    
    except Exception as e:
        current_app.logger.error(f"Erro ao criar campanha: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/<int:campanha_id>', methods=['PUT'])
def atualizar_campanha(campanha_id):
    """Atualiza uma campanha existente"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados:
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        # Atualização da campanha
        campanha = CampanhaEscalavel.atualizar_campanha(campanha_id, dados)
        
        if not campanha:
            return jsonify({'erro': 'Campanha não encontrada'}), 404
        
        return jsonify(campanha)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar campanha {campanha_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/<int:campanha_id>', methods=['DELETE'])
def excluir_campanha(campanha_id):
    """Exclui uma campanha existente"""
    try:
        resultado = CampanhaEscalavel.excluir_campanha(campanha_id)
        
        if not resultado:
            return jsonify({'erro': 'Campanha não encontrada'}), 404
        
        return jsonify({'mensagem': f'Campanha {campanha_id} excluída com sucesso'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao excluir campanha {campanha_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/<int:campanha_id>/vans', methods=['POST'])
def associar_vans(campanha_id):
    """Associa vans a uma campanha"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados or 'vans_ids' not in dados:
            return jsonify({'erro': 'Lista de IDs de vans não fornecida'}), 400
        
        # Associação das vans
        quantidade = CampanhaEscalavel.associar_vans(campanha_id, dados['vans_ids'])
        
        return jsonify({'mensagem': f'{quantidade} vans associadas à campanha {campanha_id}'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao associar vans à campanha {campanha_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/<int:campanha_id>/vans/<int:van_id>', methods=['DELETE'])
def desassociar_van(campanha_id, van_id):
    """Desassocia uma van de uma campanha"""
    try:
        resultado = CampanhaEscalavel.desassociar_van(campanha_id, van_id)
        
        if not resultado:
            return jsonify({'erro': 'Associação não encontrada'}), 404
        
        return jsonify({'mensagem': f'Van {van_id} desassociada da campanha {campanha_id}'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao desassociar van {van_id} da campanha {campanha_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@campanhas_bp.route('/autenticar', methods=['POST'])
def autenticar_campanha():
    """Autentica uma campanha pelo código de acesso"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados or 'codigo_acesso' not in dados:
            return jsonify({'erro': 'Código de acesso não fornecido'}), 400
        
        # Autenticação da campanha
        campanha = CampanhaEscalavel.autenticar_por_codigo(dados['codigo_acesso'])
        
        if not campanha:
            return jsonify({'erro': 'Código de acesso inválido'}), 401
        
        return jsonify(campanha)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao autenticar campanha: {str(e)}")
        return jsonify({'erro': str(e)}), 500