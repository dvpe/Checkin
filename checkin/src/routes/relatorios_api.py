from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from models.database import Database

relatorios_bp = Blueprint('relatorios_bp', __name__)

@relatorios_bp.route('/estatisticas/campanhas', methods=['GET'])
def estatisticas_campanhas():
    """Obtém estatísticas gerais de campanhas"""
    try:
        # Estatísticas de status de campanhas
        status_query = """
            SELECT status, COUNT(*) as total 
            FROM campanhas_controle 
            GROUP BY status
        """
        status_stats = Database.execute_query(status_query)
        
        # Total de vans associadas a campanhas ativas
        vans_ativas_query = """
            SELECT COUNT(DISTINCT cv.van_id) as total 
            FROM campanha_van cv
            JOIN campanhas_controle cc ON cv.campanha_id = cc.id
            WHERE cc.status = 'ativa'
        """
        vans_ativas = Database.execute_query(vans_ativas_query)
        
        # Campanhas ativas por município
        municipios_query = """
            SELECT cm.cidade, cm.estado, COUNT(DISTINCT cm.campanha_id) as total_campanhas,
                   SUM(cm.numero_vans_planejado) as vans_planejadas
            FROM campanha_municipios cm
            JOIN campanhas_controle cc ON cm.campanha_id = cc.id
            WHERE cc.status = 'ativa'
            GROUP BY cm.cidade, cm.estado
            ORDER BY total_campanhas DESC
        """
        municipios_stats = Database.execute_query(municipios_query)
        
        # Campanhas que estão para iniciar nos próximos 7 dias
        hoje = datetime.now().strftime('%Y-%m-%d')
        proximas_query = """
            SELECT id, nome, cliente, data_inicio, numero_vans_total
            FROM campanhas_controle
            WHERE status = 'ativa' AND data_inicio > %s
            ORDER BY data_inicio
            LIMIT 5
        """
        proximas_campanhas = Database.execute_query(proximas_query, (hoje,))
        
        return jsonify({
            'status_campanhas': {item['status']: item['total'] for item in status_stats},
            'vans_ativas': vans_ativas[0]['total'] if vans_ativas else 0,
            'campanhas_por_municipio': municipios_stats,
            'proximas_campanhas': proximas_campanhas
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas de campanhas: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/progresso/<int:campanha_id>', methods=['GET'])
def progresso_campanha(campanha_id):
    """Obtém informações de progresso de uma campanha específica"""
    try:
        # Verificar se a campanha existe
        campanha_query = "SELECT * FROM campanhas_controle WHERE id = %s"
        campanhas = Database.execute_query(campanha_query, (campanha_id,))
        
        if not campanhas:
            return jsonify({'erro': 'Campanha não encontrada'}), 404
        
        campanha = campanhas[0]
        
        # Obter vans associadas à campanha
        vans_query = """
            SELECT cv.id as campanha_van_id, v.id as van_id, v.placa, 
                   c.nome as condutor_nome, v.cidade, v.estado
            FROM campanha_van cv
            JOIN vans v ON cv.van_id = v.id
            LEFT JOIN condutores c ON v.condutor_id = c.id
            WHERE cv.campanha_id = %s
        """
        vans = Database.execute_query(vans_query, (campanha_id,))
        
        # Para cada van, obter fotos de checking
        for van in vans:
            fotos_query = """
                SELECT tipo_foto, COUNT(*) as count 
                FROM fotos_checking 
                WHERE campanha_van_id = %s 
                GROUP BY tipo_foto
            """
            fotos = Database.execute_query(fotos_query, (van['campanha_van_id'],))
            
            # Inicializar contadores
            van['fotos'] = {
                'inicial': 0,
                'adesivo': 0,
                'final': 0
            }
            
            # Preencher com dados reais
            for f in fotos:
                if f['tipo_foto'] in van['fotos']:
                    van['fotos'][f['tipo_foto']] = f['count']
            
            # Calcular progresso
            if van['fotos']['final'] > 0:
                van['progresso'] = 'concluido'  # 100%
            elif van['fotos']['adesivo'] > 0:
                van['progresso'] = 'em_andamento'  # 50%
            elif van['fotos']['inicial'] > 0:
                van['progresso'] = 'iniciado'  # 25% 
            else:
                van['progresso'] = 'pendente'  # 0%
        
        # Resumo por município
        municipios_query = """
            SELECT cm.cidade, cm.estado, cm.numero_vans_planejado
            FROM campanha_municipios cm
            WHERE cm.campanha_id = %s
        """
        municipios = Database.execute_query(municipios_query, (campanha_id,))
        
        # Para cada município, calcular estatísticas
        for municipio in municipios:
            # Filtrar vans do município
            vans_municipio = [v for v in vans if v['cidade'] == municipio['cidade'] and v['estado'] == municipio['estado']]
            
            # Calcular estatísticas
            municipio['vans_associadas'] = len(vans_municipio)
            municipio['vans_concluidas'] = len([v for v in vans_municipio if v['progresso'] == 'concluido'])
            municipio['vans_em_andamento'] = len([v for v in vans_municipio if v['progresso'] == 'em_andamento'])
            municipio['vans_iniciadas'] = len([v for v in vans_municipio if v['progresso'] == 'iniciado'])
            municipio['vans_pendentes'] = len([v for v in vans_municipio if v['progresso'] == 'pendente'])
            
            # Calcular percentual de conclusão
            if municipio['vans_associadas'] > 0:
                municipio['percentual_conclusao'] = round(
                    (municipio['vans_concluidas'] * 100 + 
                     municipio['vans_em_andamento'] * 50 + 
                     municipio['vans_iniciadas'] * 25) / 
                    municipio['vans_associadas'], 
                    2
                )
            else:
                municipio['percentual_conclusao'] = 0
        
        # Calcular estatísticas gerais da campanha
        total_vans = len(vans)
        vans_concluidas = len([v for v in vans if v['progresso'] == 'concluido'])
        vans_em_andamento = len([v for v in vans if v['progresso'] == 'em_andamento'])
        vans_iniciadas = len([v for v in vans if v['progresso'] == 'iniciado'])
        vans_pendentes = len([v for v in vans if v['progresso'] == 'pendente'])
        
        # Calcular percentual geral de conclusão
        percentual_conclusao = 0
        if total_vans > 0:
            percentual_conclusao = round(
                (vans_concluidas * 100 + vans_em_andamento * 50 + vans_iniciadas * 25) / total_vans,
                2
            )
        
        return jsonify({
            'campanha': campanha,
            'estatisticas': {
                'total_vans_associadas': total_vans,
                'vans_planejadas': campanha['numero_vans_total'],
                'vans_concluidas': vans_concluidas,
                'vans_em_andamento': vans_em_andamento,
                'vans_iniciadas': vans_iniciadas,
                'vans_pendentes': vans_pendentes,
                'percentual_conclusao': percentual_conclusao
            },
            'municipios': municipios,
            'vans': vans
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro ao obter progresso da campanha {campanha_id}: {str(e)}")
        return jsonify({'erro': str(e)}), 500