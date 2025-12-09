import secrets

from flask import Flask, jsonify, request, session, redirect, url_for, render_template
from routes.routes import rutas
from models.db_mdl import get_db, Usuario, valida_usuario

app = Flask(__name__, template_folder='templates')
app.register_blueprint(rutas, url_prefix="/api")
app.secret_key = secrets.token_hex(24)

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/usuario", methods=["GET"])
def usuario():
    ## Cuando tengamos creado el logín y la ruta correspondiente, eliminaremos las variables en uso
    ## y las reemplazaremos por las siguientes

    ## usrnm = request.form["usuario"]
    ## passwd = request.form["password"]
    usrnm = request.args.get("usuario")
    passwd = request.args.get("password")

    try:
        dtUsr = valida_usuario(usrnm, passwd)

        if dtUsr:
            return jsonify(dtUsr.to_dict())
    except Exception as e:
        print(f"Error al listar usuarios: {e}")
        return {"error": "Error interno del servidor al listar usuarios. Verifique la DB."}

@app.route("/login", methods=["GET", "POST"])
def login():
    msg_out = ""

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = valida_usuario(username, password)

        if user:
            session["user_id"] = user["user_id"]
            session["api_key"] = user["api_key"]
            return redirect(url_for("dashboard"))

        if not user:
            error = "el campo no puede estar vacio"
            return render_template("login.html", error=error)
        return render_template ("login.html", user=user)

    return render_template("login.html", message=msg_out)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)

