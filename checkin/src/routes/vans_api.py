from flask import Blueprint, request, jsonify, current_app
from models.van_model import VanModel

vans_bp = Blueprint('vans_bp', __name__)

@vans_bp.route('/', methods=['GET'])
def listar_vans():
    """Lista vans com filtros e paginação"""
    try:
        # Obter parâmetros de filtro
        filtros = {}
        if 'placa' in request.args:
            filtros['placa'] = request.args.get('placa')
        if 'cidade' in request.args:
            filtros['cidade'] = request.args.get('cidade')
        if 'estado' in request.args:
            filtros['estado'] = request.args.get('estado')
        if 'status' in request.args:
            filtros['status'] = request.args.get('status')
        if 'campanha_id' in request.args:
            filtros['campanha_id'] = int(request.args.get('campanha_id'))
        if 'nao_associada' in request.args and request.args.get('nao_associada').lower() == 'true':
            filtros['nao_associada'] = True
        
        # Obter parâmetros de paginação
        pagina = int(request.args.get('pagina', 1))
        por_pagina = int(request.args.get('por_pagina', 10))
        paginacao = {'pagina': pagina, 'por_pagina': por_pagina}
        
        # Obter vans
        resultado = VanModel.listar_vans(filtros, paginacao)
        
        return jsonify(resultado)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao listar vans: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@vans_bp.route('/<int:van_id>', methods=['GET'])
def obter_van(van_id):
    """Obtém uma van específica pelo ID"""
    try:
        van = VanModel.obter_van(van_id)
        
        if not van:
            return jsonify({'erro': 'Van não encontrada'}), 404
        
        return jsonify(van)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao obter van {van_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@vans_bp.route('/', methods=['POST'])
def adicionar_van():
    """Adiciona uma nova van"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados or 'placa' not in dados:
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        # Adição da van
        van = VanModel.adicionar_van(dados)
        
        return jsonify(van), 201
    
    except Exception as e:
        current_app.logger.error(f"Erro ao adicionar van: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@vans_bp.route('/<int:van_id>', methods=['PUT'])
def atualizar_van(van_id):
    """Atualiza uma van existente"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados:
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        # Atualização da van
        van = VanModel.atualizar_van(van_id, dados)
        
        if not van:
            return jsonify({'erro': 'Van não encontrada'}), 404
        
        return jsonify(van)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar van {van_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@vans_bp.route('/<int:van_id>', methods=['DELETE'])
def excluir_van(van_id):
    """Exclui uma van existente"""
    try:
        resultado = VanModel.excluir_van(van_id)
        
        if not resultado:
            return jsonify({'erro': 'Van não encontrada'}), 404
        
        return jsonify({'mensagem': f'Van {van_id} excluída com sucesso'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao excluir van {van_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@vans_bp.route('/buscar-por-municipio', methods=['POST'])
def buscar_vans_por_municipio():
    """Busca vans disponíveis por município"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados or 'cidade' not in dados or 'estado' not in dados:
            return jsonify({'erro': 'Dados incompletos (cidade e estado são obrigatórios)'}), 400
        
        # Preparar filtros
        filtros = {
            'cidade': dados['cidade'],
            'estado': dados['estado'],
            'status': 'ativa'
        }
        
        if 'campanha_id' in dados:
            filtros['campanha_id'] = dados['campanha_id']
            filtros['nao_associada'] = True
        
        # Buscar vans
        resultado = VanModel.listar_vans(filtros)
        
        return jsonify(resultado)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar vans por município: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@vans_bp.route('/disponibilidade', methods=['POST'])
def verificar_disponibilidade():
    """Verifica a disponibilidade de vans para uma campanha"""
    try:
        dados = request.json
        
        # Validação básica dos dados
        if not dados or 'municipios' not in dados:
            return jsonify({'erro': 'Lista de municípios não fornecida'}), 400
        
        resultados = []
        
        # Para cada município, verificar vans disponíveis
        for municipio in dados['municipios']:
            if 'cidade' not in municipio or 'estado' not in municipio:
                continue
            
            # Preparar filtros
            filtros = {
                'cidade': municipio['cidade'],
                'estado': municipio['estado'],
                'status': 'ativa'
            }
            
            if 'campanha_id' in dados:
                filtros['campanha_id'] = dados['campanha_id']
                filtros['nao_associada'] = True
            
            # Buscar vans
            resultado = VanModel.listar_vans(filtros)
            
            # Adicionar resultados
            resultados.append({
                'cidade': municipio['cidade'],
                'estado': municipio['estado'],
                'vans_disponiveis': len(resultado['vans']),
                'vans_solicitadas': municipio.get('numero_vans_planejado', 0)
            })
        
        return jsonify({'resultados': resultados})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar disponibilidade de vans: {str(e)}")
        return jsonify({'erro': str(e)}), 500