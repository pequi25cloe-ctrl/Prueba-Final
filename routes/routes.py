from functools import wraps
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models.db_mdl import get_db, Producto, Mercado, Usuario

rutas = Blueprint("rutas", __name__)

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.args.get("api_key")

        if not key:
            return {"error": "API Key requerida"}, 401

        try:
            with get_db() as db:
                user = db.query(Usuario).filter(Usuario.api_key == key).first()

                if not user:
                    return {"error": "API Key inválida"}, 403
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return func(*args, **kwargs)
    return wrapper

@rutas.route("/productos", methods=["GET"])
@require_api_key
def listar_productos():
    """Listar productos incluyendo el nombre de su mercado"""
    try:
        with get_db() as db:
            # Usamos joinedload para optimizar la consulta y traer el nombre del mercado
            page_get = request.args.get("page")
            per_page_get = request.args.get("per_page")

            page = int(page_get) if page_get else 1
            per_page = int(per_page_get) if per_page_get else 5

            offset = (page - 1) * per_page

            productos = db.query(Producto).options(joinedload(Producto.origen_mercado)).offset(offset).limit(per_page).all()
            return jsonify([p.to_dict() for p in productos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos", methods=["POST"])
@require_api_key
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
@require_api_key
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
@require_api_key
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