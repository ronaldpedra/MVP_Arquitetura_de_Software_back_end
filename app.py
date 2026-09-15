from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import requests
from database import db
from models import Room
import os

app = Flask(__name__)

# Configurações do Banco de Dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hotel.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Habilita CORS para permitir requisições do front-end
CORS(app)

# Inicializa o banco de dados
db.init_app(app)

# Configuração do Swagger para documentação
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config, template={
    "info": {
        "title": "API MVP Gestão de Hotel",
        "description": "API REST para gerenciamento de quartos e consulta de clima local.",
        "version": "1.0.0"
    }
})

# Cria as tabelas do banco no primeiro acesso
with app.app_context():
    db.create_all()

@app.route('/rooms', methods=['GET'])
def get_rooms():
    """
    Lista todos os quartos cadastrados
    ---
    responses:
      200:
        description: Lista de quartos
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              number:
                type: string
              type:
                type: string
              price:
                type: number
              is_available:
                type: boolean
    """
    rooms = Room.query.all()
    return jsonify([room.to_dict() for room in rooms]), 200

@app.route('/rooms', methods=['POST'])
def create_room():
    """
    Adiciona um novo quarto
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - number
            - type
            - price
          properties:
            number:
              type: string
              example: "101A"
            type:
              type: string
              example: "Standard"
            price:
              type: number
              example: 150.00
            is_available:
              type: boolean
              example: true
    responses:
      201:
        description: Quarto criado com sucesso
      400:
        description: Dados inválidos ou quarto já existe
    """
    data = request.get_json()
    
    if not data or not 'number' in data or not 'type' in data or not 'price' in data:
        return jsonify({'message': 'Dados inválidos. Envie number, type e price.'}), 400
    
    existing_room = Room.query.filter_by(number=data['number']).first()
    if existing_room:
        return jsonify({'message': 'Quarto com este número já existe.'}), 400

    new_room = Room(
        number=data['number'],
        type=data['type'],
        price=float(data['price']),
        is_available=data.get('is_available', True)
    )
    
    db.session.add(new_room)
    db.session.commit()
    
    return jsonify(new_room.to_dict()), 201

@app.route('/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    """
    Atualiza as informações de um quarto
    ---
    parameters:
      - in: path
        name: room_id
        type: integer
        required: true
        description: ID numérico do quarto
      - in: body
        name: body
        schema:
          type: object
          properties:
            number:
              type: string
            type:
              type: string
            price:
              type: number
            is_available:
              type: boolean
    responses:
      200:
        description: Quarto atualizado com sucesso
      404:
        description: Quarto não encontrado
    """
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'message': 'Quarto não encontrado.'}), 404
        
    data = request.get_json()
    if 'number' in data:
        # Verifica se o novo número já existe em outro quarto
        if data['number'] != room.number:
            exists = Room.query.filter_by(number=data['number']).first()
            if exists:
                return jsonify({'message': 'Número de quarto já em uso.'}), 400
        room.number = data['number']
        
    if 'type' in data:
        room.type = data['type']
    if 'price' in data:
        room.price = float(data['price'])
    if 'is_available' in data:
        room.is_available = bool(data['is_available'])
        
    db.session.commit()
    return jsonify(room.to_dict()), 200

@app.route('/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    """
    Remove um quarto do sistema
    ---
    parameters:
      - in: path
        name: room_id
        type: integer
        required: true
        description: ID numérico do quarto
    responses:
      200:
        description: Quarto deletado com sucesso
      404:
        description: Quarto não encontrado
    """
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'message': 'Quarto não encontrado.'}), 404
        
    db.session.delete(room)
    db.session.commit()
    return jsonify({'message': 'Quarto deletado com sucesso.'}), 200

@app.route('/weather', methods=['GET'])
def get_weather():
    """
    Consome a API externa Open-Meteo para retornar o clima do local do hotel
    ---
    responses:
      200:
        description: Dados climáticos atuais retornados pela API externa
      500:
        description: Erro ao buscar os dados da API externa
    """
    # Latitude e longitude fixas para o hotel (Exemplo: Rio de Janeiro, RJ)
    lat = -22.9064
    lon = -43.1822
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        current_weather = data.get('current_weather', {})
        
        return jsonify({
            'city': 'Rio de Janeiro (Local do Hotel)',
            'temperature': current_weather.get('temperature'),
            'windspeed': current_weather.get('windspeed'),
            'weathercode': current_weather.get('weathercode'),
            'time': current_weather.get('time')
        }), 200
    except Exception as e:
        return jsonify({'message': 'Não foi possível buscar os dados do clima na API Externa.', 'error': str(e)}), 500

if __name__ == '__main__':
    # Roda em 0.0.0.0 para aceitar requisições de fora do container Docker
    app.run(host='0.0.0.0', port=5000, debug=True)
