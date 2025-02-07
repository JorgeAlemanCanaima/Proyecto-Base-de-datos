from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pyodbc
from flask_session import Session #manejo de sesiones
from functools import wraps
#import jsonify

app = Flask(__name__)

app.secret_key = 'tu_clave_secreta'  # Asegúrate de establecer una clave secreta

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configura la cadena de conexión para autenticación de Windows
connection_string = (
    "DRIVER={SQL Server};"
    "SERVER=X1-ALEMENDOZA;"
    "DATABASE=quesillos;"
    "Trusted_Connection=yes;"
)

# Conexión con la base de datos
connection = pyodbc.connect(connection_string)

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#ruta para el cierre de sesion


# Ruta para la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT * FROM usuario_empleado WHERE nombre_user = ? AND contra_user = ?
            """, (username, password))
            user = cursor.fetchone()
            
            if not user: 
                print("Este usuario no existe o la contraseña es incorrecta")
                flash("Usuario o Password incorrecta")
                return redirect(url_for('login'))  # Redirige a la página de login
            else:
                session['user_id'] = user[0]  # Ajusta el índice según la estructura de tu tabla
                session['username'] = username  # Almacena el nombre de usuario si lo necesitas
                print("Sesión iniciada correctamente")
                print("User ID guardado en la sesión:", session.get('user_id'))

                return redirect(url_for('index'))
        except pyodbc.Error as e:
            print("Error en la consulta:", e)
            flash("Error al procesar la solicitud. Intenta nuevamente.")
            return redirect(url_for('login'))
    
    return render_template('login.html')
    
@app.route("/logout", methods=['POST'])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Ruta para la página principal
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT FORMAT(fecha_hora, 'yyyy-MM-dd HH:mm') AS fecha_hora, pedidos.id, 
                   clientes.nombre AS cliente_nombre, empleados.nombre AS empleado_nombre, tipo_pedido 
                    FROM pedidos JOIN clientes ON clientes.id = pedidos.clientes_id JOIN
                   empleados ON empleados.id = pedidos.empleado_id
    """)
    table = cursor.fetchall()
        
    return render_template("index.html", info=table)
    

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if request.method == 'POST':
        user = request.form['usuario']
        contra = request.form['password']
    else:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT * FROM usuario_empleado
            """)
            table = cursor.fetchall()
        except:
            print("Error no se pudieron extraer los datos de la base de datos")
        return render_template("usuarios.html", info=table)
    
@app.route('/ingresoproducto', methods=['GET', 'POST'])
@login_required
def ingresoproducto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])

        #codigo = request.form['codigo']
        #cantidad = request.form['cantidad']
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO productos (nombre, precio) VALUES (?, ?)
            """, (nombre, precio))
            flash("Producto Ingresado Correctamente")
            return redirect('ingresoproducto')
            
        except:
            flash("No se pudo ingresar el producto")

        


    else:
        return render_template("registroproducto.html")
    

@app.route('/catalogoproductos', methods=['GET', 'POST'])
@login_required
def catalogoproductos():
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM productos
        """)
        table = cursor.fetchall()
    except:
        print("Error no se pudieron extraer los datos de la base de datos")
    return render_template("catalogoproductos.html", info=table)

@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    return render_template("pedidos.html")

# Ruta para obtener productos de una categoría específica
@app.route('/products/<categoryName>')
def get_products(categoryName):
    cursor = connection.cursor()
    query = "SELECT id, nombre, precio FROM productos WHERE categoria = ?"  # Ajusta el nombre de tu tabla y columnas según sea necesario
    cursor.execute(query, (categoryName,))
    products = cursor.fetchall()
    print(f"Category ID: {categoryName}")
    print(f"Products found: {len(products)}")
    print(products)
    
    # Convertimos los resultados en una lista de diccionarios
    product_list = [{"id": row[0], "nombre": row[1], "precio": row[2]} for row in products]
    print(product_list)
    return jsonify(product_list)


if __name__ == '__main__':
    app.run(debug=True)
