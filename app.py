from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
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


# RUTAS
# RUTA INICIO
@app.route("/")
def inicio ():
    mostrar_productos=False
    return render_template("inicio.html", mostrar_productos=mostrar_productos)

# RUTA PARA MOSTRAR PRODUCTOS
@app.route("/productos", methods=['GET'])
def obtener_productos():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Ejecuta una consulta
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("productos.html", productos=productos, mostrar_productos=mostrar_productos)

# RUTA PARA MOSTRAR EL FORMULARIO DE CARGA DE PRODUCTO (GET)
@app.route("/carga_producto", methods=['GET'])
def cargar_producto():
    return render_template("carga_producto.html")


# RUTA PARA CARGAR UN PRODUCTO
@app.route("/carga_producto", methods=['POST'])
def insertar_producto():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    talle = request.form['talle']

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta SQL para insertar el producto en la tabla productos
    cursor.execute("""
        INSERT INTO productos (nombre, descripcion, talle) 
        VALUES (%s, %s, %s)
    """, (nombre, descripcion, talle))

    # Guardar los cambios
    conn.commit()

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    print(f"Producto {nombre} insertado correctamente")
    return redirect(url_for("obtener_productos")) # hay que poner el método, no la pagina

# RUTA PARA EDITAR UN PRODUCTO
@app.route("/editar_producto/<int:id_producto>", methods=['GET', 'POST'])
def editar_producto(id_producto):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        # Actualiza el producto en la base de datos
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        talle = request.form['talle']

        print(cursor.rowcount)

        cursor.execute("""
            UPDATE productos SET nombre=%s, descripcion=%s, talle=%s WHERE id_producto=%s
        """, (nombre, descripcion, talle, id_producto))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Producto {nombre} modificado correctamente")
        return redirect(url_for("obtener_productos")) # me lleva al método de la pagina central

    # Si es un GET, obtener el producto existente
    cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id_producto,))
    producto = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template("editar_producto.html", producto=producto)

# RUTA PARA ELIMINAR UN PRODUCTO
@app.route("/eliminar_producto/<int:id_producto>", methods=['GET'])
def eliminar_producto(id_producto):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
    conn.commit()

    cursor.close()
    conn.close()

   # poner un mensaje de borrado
    return redirect(url_for("obtener_productos"))


# RUTA PARA BUSCAR UN PRODUCTO 
# método
def buscar_productos(query):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Consulta SQL que busca productos cuyo nombre contenga el término de búsqueda (query)
    cursor.execute("SELECT * FROM productos WHERE nombre ILIKE %s", ('%' + query + '%',))

    productos = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return productos

# ruta
@app.route('/buscar_producto')
def buscar_producto():
    query = request.args.get('query')

    # Si no hay término de búsqueda, muestra todos los productos
    if not query:
        return redirect(url_for('obtener_productos'))
    
    productos = buscar_productos(query)  # Llamas a la función auxiliar que busca los productos
    mostrar_productos=True

    return render_template('productos.html', productos=productos, mostrar_productos=mostrar_productos)


# RUTA PARA MOSTRAR VENTAS
@app.route("/ventas", methods=['GET'])
def obtener_ventas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Ejecuta una consulta
    # cursor.execute("SELECT * FROM productos")
    # productos = cursor.fetchall()

    # cursor.execute("SELECT * FROM ventas")

    # Ejecuta una consulta para obtener los detalles de las ventas junto con el nombre del producto
    cursor.execute("""
        SELECT v.id_venta, p.nombre, v.precio, v.cantidad_vendida, v.fechavendida, v.metodopago
        FROM Ventas v
        JOIN Stock s ON v.id_stock = s.id_stock
        JOIN Productos p ON s.id_producto = p.id_producto
    """)

    ventas = cursor.fetchall()

    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("ventas.html", ventas=ventas, mostrar_productos=mostrar_productos)

# RUTA PARA MOSTRAR LA CARGA DE UNA VENTA DE PRODUCTO (GET)
@app.route("/carga_venta", methods=['GET'])
def cargar_venta():
    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # Utiliza RealDictCursor para obtener un dict en lugar de una tupla

    # Ejecuta la consulta para obtener todos los productos
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()  # Obtiene todos los productos como una lista de diccionarios

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    return render_template("carga_venta.html", productos=productos)


# Clave secreta
app.secret_key = 'clave_secreta'  # Cambia esto a algo único y secreto

# RUTA PARA CARGAR UNA VENTA
@app.route("/carga_venta", methods=['POST'])
def insertar_venta():
    id_producto = request.form['producto']  # Obtener el producto_id del formulario
    # se debe poner 'producto', ya que asi esta definido en carga_venta.html
    precio = request.form['precio']
    cantidad_vendida = int(request.form['cantidad_vendida'])
    metodopago = request.form['metodopago']
    fechavendida = request.form['fechavendida']

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Consultar los detalles del producto usando el producto_id
    cursor.execute("SELECT nombre, descripcion, talle FROM productos WHERE id_producto = %s", (id_producto,))
    producto = cursor.fetchone()

    # Aparte nos fijamos si esta el producto
    if not producto:
        flash("Producto no encontrado", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("carga_venta"))  # Redirige si no se encuentra el producto

    # Consultar la cantidad disponible en stock
    cursor.execute("SELECT cantidad FROM stock WHERE id_producto = %s", (id_producto,))
    stock = cursor.fetchone()

    # Consultar la suma de las cantidades vendidas para ese producto
    cursor.execute("""
        SELECT SUM(cantidad_vendida) 
        FROM ventas 
        WHERE id_stock = %s
    """, (id_producto,))
    total_vendido = cursor.fetchone()[0] or 0  # Sumar las cantidades vendidas, inicializar en 0 si no hay ventas

    # Comprobar que la suma de lo vendido + la cantidad que se quiere vender no exceda el stock
    if stock and (total_vendido + cantidad_vendida) <= stock[0]:  
        # Inserción de la venta
        cursor.execute("""INSERT INTO ventas (id_stock, precio, cantidad_vendida, metodopago, fechavendida) 
                          VALUES (%s, %s, %s, %s, %s)""",
                       (id_producto, precio, cantidad_vendida, metodopago, fechavendida))
        # Guardar los cambios
        conn.commit()
        flash(f"Venta de producto {producto[0]} insertada correctamente", "success")
    else:
        flash("La cantidad total vendida excede el stock disponible.", "danger")

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    return redirect(url_for("obtener_ventas"))  # Redirigir al método que muestra las ventas

# RUTA PARA BUSCAR PRODUCTO ESPECIFÍCO
@app.route('/obtener_producto/<int:producto_id>', methods=['GET'])
def obtener_producto_por_id(producto_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # Utiliza RealDictCursor para obtener un dict en lugar de una tupla
    
    # Ejecuta la consulta para obtener el producto por su ID
    cursor.execute("SELECT descripcion, precio, talle, fechaingreso FROM productos WHERE id = %s", (producto_id,))
    producto = cursor.fetchone()  # Devuelve un único registro
    
    cursor.close()
    conn.close()

    # Verifica si se encontró el producto
    if producto:
        return jsonify({
            'descripcion': producto['descripcion'],
            'precio': producto['precio'],
            'talle': producto['talle'],
            'fechaingreso': producto['fechaingreso']
        })
    else:
        return jsonify({'error': 'Producto no encontrado'}), 404


# RUTA PARA EDITAR UNA VENTA 
@app.route("/editar_venta/<int:id_venta>", methods=['GET', 'POST'])
def editar_venta(id_venta):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        # Actualiza la venta en la base de datos
        precio = request.form['precio']
        cantidad_vendida = request.form['cantidad_vendida']
        fechavendida = request.form['fechavendida']
        metodopago = request.form['metodopago']

        print(cursor.rowcount)

        cursor.execute("""
            UPDATE ventas SET  precio=%s, cantidad_vendida=%s, fechavendida=%s, metodopago=%s WHERE id=%s
        """, (precio, cantidad_vendida, fechavendida, metodopago, id))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Venta  modificado correctamente")
        return redirect(url_for("obtener_ventas")) # me lleva al método de la pagina central

    # Si es un GET, obtener la venta existente
    cursor.execute("SELECT * FROM ventas WHERE id_venta = %s", (id_venta,))
    venta = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template("editar_venta.html", venta=venta)

# RUTA PARA ELIMINAR UNA VENTA
@app.route("/eliminar_venta/<int:id_venta>", methods=['GET'])
def eliminar_venta(id_venta):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ventas WHERE id_venta = %s", (id_venta,))
    conn.commit()

    cursor.close()
    conn.close()

   # poner un mensaje de borrado
    return redirect(url_for("obtener_ventas"))

# RUTA PARA BUSCAR UNA VENTA 
# método
def buscar_ventas(query):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Consulta SQL que busca ventas cuyo nombre contenga el término de búsqueda (query)
    cursor.execute("SELECT * FROM ventas WHERE nombre ILIKE %s", ('%' + query + '%',))

    ventas = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return ventas

# ruta
@app.route('/buscar_venta')
def buscar_venta():
    query = request.args.get('query')

    # Si no hay término de búsqueda, muestra todos las ventas
    if not query:
        return redirect(url_for('obtener_ventas'))
    
    ventas = buscar_ventas(query)  # Llamas a la función auxiliar que busca las ventas
    mostrar_productos=True

    return render_template('ventas.html', ventas=ventas, mostrar_productos=mostrar_productos)



# RUTA PARA MOSTRAR PRODUCTOS
@app.route("/stock", methods=['GET'])
def obtener_stock():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Ejecuta una consulta para obtener el stock junto con el nombre del producto
    cursor.execute("""
        SELECT s.id_stock, s.cantidad, s.fechaingreso, p.nombre
        FROM Stock s
        JOIN Productos p ON s.id_producto = p.id_producto
    """)

    stock = cursor.fetchall()

    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("stock.html", stocks=stock, mostrar_productos=mostrar_productos)