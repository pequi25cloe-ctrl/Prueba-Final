from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models.db_mdl import get_db, Producto, Mercado

rutas = Blueprint("rutas", __name__)
# Verifica si se ha enviado una API-Key en la cabecera de la solicitud
def get_api_key_from_request():
    # Verifica la cabecera, luego otros parámetros del request
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    return api_key

# --- Decorador de Autenticación Simple ---
def require_auth(f):
    """Decorador simple para verificar si el usuario está logeado."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica si se envía API-Key en el request y retorna un error si no existe
        api_key = get_api_key_from_request()
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        # Se realiza validación con la base de datos
        user = is_user_api_key(api_key)
        # Si no hay usuario para el API Key enviado, retorna error
        if not user:
            # Devuelve una respuesta JSON si no está autenticado
            return jsonify({'message': 'Acceso no autorizado. API Key inválida.'}), 403
        # se agrega el user a las variables del request
        request.current_user = user
        return f(*args, **kwargs)

    return decorated_function

@rutas.route("/productos", methods=["GET"])
def listar_productos():
    """Listar productos incluyendo el nombre de su mercado"""
    try:
        with get_db() as db:
            # Usamos joinedload para optimizar la consulta y traer el nombre del mercado
            productos = db.query(Producto).options(joinedload(Producto.origen_mercado)).all()
            return jsonify([p.to_dict() for p in productos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos", methods=["POST"])
def crear_producto():
    data = request.get_json()
    reqFld = ['nombre', 'idOrigen', 'uMedida', 'precio']

    if not all(r in data for r in reqFld):
        return jsonify({"error": f"Faltan campos: {reqFld}"}), 400

    try:
        with get_db() as db:
            mercado = db.query(Mercado).filter(Mercado.id == data["idOrigen"]).first()
            if not mercado:
                return jsonify({"error": "Ha ingresado un mercado inválido"}), 404

            nProd = Producto(
                nombre = data["nombre"],
                idOrigen = data["idOrigen"],
                uMedida = data["uMedida"],
                precio = data["precio"]
            )

            db.add(nProd)
            db.commit()
            db.refresh(nProd)
            return jsonify({"Confirmación": "Producto creado", "Producto": nProd.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos/<int:idprd>", methods=["PUT"])
def actualizar_producto(idprd):
    data = request.get_json()

    try:
        with get_db() as db:
            prod = db.query(Producto).filter(Producto.id == idprd).first()
            if not prod:
                return jsonify({"error": "Intenta actualizar un producto que no existe"}), 404

            if "nombre" in data: prod.nombre = data["nombre"]
            if "uMedida" in data: prod.uMedida = data["uMedida"]
            if "precio" in data: prod.precio = data["precio"]

            if "idOrigen" in data:
                mercado = db.query(Mercado).filter(Mercado.id == data["idOrigen"]).first()

                if not mercado:
                    return jsonify({"error": "El mercado a modificar no existe"}), 404

                prod.idOrigen = data["idOrigen"]

            db.commit()
            db.refresh(prod)
            return jsonify({"Confirmación": "Producto actualizado", "Producto": prod.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos/<int:idprd>", methods=["DELETE"])
def eliminar_producto(idprd):
    try:
        with get_db() as db:
            prod = db.query(Producto).filter(Producto.id == idprd).first()
            if not prod:
                return jsonify({"error": "Intenta eliminar un producto que no existe"}), 404

            db.delete(prod)
            db.commit()
            return jsonify({"Confirmación": "Producto eliminado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
