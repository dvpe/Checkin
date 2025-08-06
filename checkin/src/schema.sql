-- Criação das tabelas do sistema
BEGIN;

-- Tabela para condutores de vans
CREATE TABLE IF NOT EXISTS condutores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(100),
    documento VARCHAR(20) UNIQUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para vans
CREATE TABLE IF NOT EXISTS vans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(10) NOT NULL UNIQUE,
    modelo VARCHAR(50),
    ano INT,
    condutor_id INT,
    cidade VARCHAR(100),
    estado CHAR(2),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    status ENUM('ativa', 'inativa', 'manutenção') DEFAULT 'ativa',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (condutor_id) REFERENCES condutores(id) ON DELETE SET NULL
);

-- Tabela para escolas
CREATE TABLE IF NOT EXISTS escolas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    endereco TEXT,
    cidade VARCHAR(100),
    estado CHAR(2),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de relação entre vans e escolas
CREATE TABLE IF NOT EXISTS van_escola (
    id INT AUTO_INCREMENT PRIMARY KEY,
    van_id INT NOT NULL,
    escola_id INT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (van_id) REFERENCES vans(id) ON DELETE CASCADE,
    FOREIGN KEY (escola_id) REFERENCES escolas(id) ON DELETE CASCADE,
    UNIQUE KEY van_escola_unique (van_id, escola_id)
);

-- Tabela para campanhas publicitárias
CREATE TABLE IF NOT EXISTS campanhas_controle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cliente VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    numero_vans_total INT NOT NULL,
    codigo_acesso VARCHAR(20) UNIQUE NOT NULL,
    status ENUM('ativa', 'concluida', 'cancelada', 'pendente') DEFAULT 'ativa',
    tipo_campanha ENUM('local', 'regional', 'nacional') DEFAULT 'local',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela para municípios da campanha
CREATE TABLE IF NOT EXISTS campanha_municipios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campanha_id INT NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    numero_vans_planejado INT NOT NULL DEFAULT 1,
    FOREIGN KEY (campanha_id) REFERENCES campanhas_controle(id) ON DELETE CASCADE
);

-- Tabela de relação entre campanhas e vans
CREATE TABLE IF NOT EXISTS campanha_van (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campanha_id INT NOT NULL,
    van_id INT NOT NULL,
    municipio_id INT,
    data_associacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campanha_id) REFERENCES campanhas_controle(id) ON DELETE CASCADE,
    FOREIGN KEY (van_id) REFERENCES vans(id) ON DELETE CASCADE,
    FOREIGN KEY (municipio_id) REFERENCES campanha_municipios(id) ON DELETE SET NULL,
    UNIQUE KEY campanha_van_unique (campanha_id, van_id)
);

-- Tabela para fotos de checking
CREATE TABLE IF NOT EXISTS fotos_checking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campanha_van_id INT NOT NULL,
    tipo_foto ENUM('inicial', 'adesivo', 'final') NOT NULL,
    url_foto VARCHAR(255) NOT NULL,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campanha_van_id) REFERENCES campanha_van(id) ON DELETE CASCADE
);

-- Índices para melhorar performance
CREATE INDEX idx_vans_cidade_estado ON vans(cidade, estado);
CREATE INDEX idx_vans_status ON vans(status);
CREATE INDEX idx_campanhas_status ON campanhas_controle(status);
CREATE INDEX idx_campanhas_data_inicio ON campanhas_controle(data_inicio);
CREATE INDEX idx_campanhas_data_fim ON campanhas_controle(data_fim);
CREATE INDEX idx_fotos_tipo ON fotos_checking(tipo_foto);

COMMIT;