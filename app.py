from flask import Flask, render_template, jsonify, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor

app=Flask(__name__)

# Configuraciones de la base de datos (postgres)
def get_db_connection():
    connection = psycopg2.connect(
        host="localhost", 
        database="tienda_ropa",
        user="sol",
        password="123456789"
    )

    return connection


# Rutas
@app.route("/productos", methods=['GET'])
def obtener_productos():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Ejecuta una consulta
    cursor.execute("SELECT * FROM empleados")
    empleados = cursor.fetchall()

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("productos.html", empleados=empleados, productos=productos)

# Ruta para mostrar el formulario de carga de productos (GET)
@app.route("/carga_producto", methods=['GET'])
def cargar_producto():
    return render_template("carga_producto.html")


# En esta ruta se crea un producto
@app.route("/carga_producto", methods=['POST'])
def insertar_producto():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    talle = request.form['talle']
    fechaingreso = request.form['fechaingreso']
    cantidad = request.form['cantidad']

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta SQL para insertar el producto en la tabla productos
    cursor.execute("""
        INSERT INTO productos (nombre, descripcion, precio, talle, fechaingreso, cantidad) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (nombre, descripcion, precio, talle, fechaingreso, cantidad))

    # Guardar los cambios
    conn.commit()

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    print(f"Producto {nombre} insertado correctamente")
    return redirect(url_for("obtener_productos")) # hay que poner el método, no la pagina

# Ruta inicio
@app.route("/")
def inicio ():
    return render_template("inicio.html")

# Ruta db prueba
@app.route("/db")
def prueba_DB ():
    return render_template("prueba_DB.html")

# Ruta inicio de sesion
@app.route("/inicio_sesion")
def inicio_sesion ():
    return render_template("inicio_sesion.html")

# Ruta inicio de sesion
@app.route("/venta_producto")
def venta_producto ():
    return render_template("venta_producto.html")

# Rutas para editar
@app.route("/editar_producto/<int:id>", methods=['GET', 'POST'])
def editar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        # Actualiza el producto en la base de datos
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        talle = request.form['talle']
        fechaingreso = request.form['fechaingreso']
        cantidad = request.form['cantidad']

        print(cursor.rowcount)

        cursor.execute("""
            UPDATE productos SET nombre=%s, descripcion=%s, precio=%s, talle=%s, fechaingreso=%s, cantidad=%s WHERE id=%s
        """, (nombre, descripcion, precio, talle, fechaingreso, cantidad, id))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Producto {nombre} modificado correctamente")
        return redirect(url_for("obtener_productos")) # me lleva al método de la pagina central

    # Si es un GET, obtener el producto existente
    cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template("editar_producto.html", producto=producto)

# Rutas para eliminar
@app.route("/eliminar_producto/<int:id>", methods=['GET'])
def eliminar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

   # poner un mensaje de borrado
    return redirect(url_for("obtener_productos"))


# Ruta para buscar un producto 
def buscar_productos(query):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Consulta SQL que busca productos cuyo nombre contenga el término de búsqueda (query)
    cursor.execute("SELECT * FROM productos WHERE nombre ILIKE %s", ('%' + query + '%',))

    productos = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return productos

@app.route('/buscar_producto')
def buscar_producto():
    query = request.args.get('query')

    # Si no hay término de búsqueda, muestra todos los productos
    if not query:
        return redirect(url_for('obtener_productos'))
    
    productos = buscar_productos(query)  # Llamas a la función auxiliar que busca los productos

    return render_template('productos.html', productos=productos)
