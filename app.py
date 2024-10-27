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

### PRODUCTO ###

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

    mostrar_productos=True

    return render_template("carga_producto.html", mostrar_productos=mostrar_productos)


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

    flash(f"Producto '{nombre}' insertado correctamente.", "success")

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    # print(f"Producto {nombre} insertado correctamente")
    return redirect(url_for("obtener_productos")) # hay que poner el método, no la pagina

# RUTA PARA EDITAR UN PRODUCTO
@app.route("/editar_producto/<int:id_producto>", methods=['GET', 'POST'])
def editar_producto(id_producto):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Inicializa nombre
    nombre = None

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

        flash(f"Producto '{nombre}' editado correctamente.", "success")
        return redirect(url_for("obtener_productos")) # me lleva al método de la pagina central

    # Si es un GET, obtener el producto existente
    cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id_producto,))
    producto = cursor.fetchone()

    # Guardar cambios
    conn.commit()

    
    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("editar_producto.html", producto=producto, mostrar_productos=mostrar_productos)


# RUTA PARA ELIMINAR UN PRODUCTO
@app.route("/eliminar_producto/<int:id_producto>", methods=['GET'])
def eliminar_producto(id_producto):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Verificar si el producto tiene stock asociado
    cursor.execute("SELECT COUNT(*) AS stock_asociado FROM stock WHERE id_producto = %s", (id_producto,))
    stock_asociado = cursor.fetchone()['stock_asociado']

    if stock_asociado > 0:
        # Si hay stock asociado, no permitir la eliminación y mostrar un mensaje
        flash("No se puede eliminar el producto porque tiene productos en stock asociado.", "danger")
    else:
        # Si no hay stock asociado, proceder con la eliminación
        cursor.execute("SELECT nombre FROM productos WHERE id_producto = %s", (id_producto,))
        producto = cursor.fetchone()

        if producto:  # Verificamos si el producto existe
            nombre = producto['nombre']
            cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
            conn.commit()
            flash(f"Producto '{nombre}' eliminado correctamente.", "success")
        else:
            flash("El producto no se encontró.", "danger")

    cursor.close()
    conn.close()

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

    # Comprobar si se encontraron resultados
    if productos:
        flash(f"Producto '{query}' encontrado.", "success")
    else:
        flash(f"No se encontró el producto '{query}'.", "danger")

    mostrar_productos=True

    return render_template('productos.html', productos=productos, mostrar_productos=mostrar_productos)


### VENTAS ###

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

    # Ejecuta la consulta para obtener productos en stock
    cursor.execute("""
        SELECT s.id_stock, p.nombre, p.descripcion, p.talle, s.cantidad
        FROM stock s
        JOIN productos p ON s.id_producto = p.id_producto
        WHERE s.cantidad > 0
    """)
    stock_disponible = cursor.fetchall()  # Obtiene los productos en stock como una lista de diccionarios

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("carga_venta.html", stock=stock_disponible, mostrar_productos=mostrar_productos)


# Clave secreta
app.secret_key = 'clave_secreta'  # Cambia esto a algo único y secreto

# RUTA PARA CARGAR UNA VENTA
# @app.route("/carga_venta", methods=['POST'])
# def insertar_venta():
#     id_stock = request.form['producto']  # Obtener el id_stock del formulario
#     precio = request.form['precio']
#     cantidad_vendida = int(request.form['cantidad_vendida'])
#     metodopago = request.form['metodopago']
#     fechavendida = request.form['fechavendida']

#     # Conexión a la base de datos
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Consultar el stock disponible y fecha de ingreso
#     cursor.execute("SELECT cantidad, fechaingreso FROM stock WHERE id_stock = %s", (id_stock,))
#     stock = cursor.fetchone()

#     if not stock:
#         flash("No se pudo encontrar el stock para este producto.", "danger")
#         cursor.close()
#         conn.close()
#         return redirect(url_for("cargar_venta"))

#     cantidad_disponible, fechaingreso = stock

#     # Verificar que la fecha de venta no sea anterior a la fecha de ingreso
#     if fechavendida < fechaingreso.strftime('%Y-%m-%d'):
#         flash("La fecha de venta no puede ser anterior a la fecha de ingreso del producto.", "danger")
#         cursor.close()
#         conn.close()
#         return redirect(url_for("cargar_venta"))

#     # Consultar la suma de las cantidades vendidas para el stock seleccionado
#     cursor.execute("SELECT COALESCE(SUM(cantidad_vendida), 0) FROM ventas WHERE id_stock = %s", (id_stock,))
#     total_vendido = cursor.fetchone()[0]

#     # Comprobar que la cantidad vendida no exceda el stock disponible
#     if (total_vendido + cantidad_vendida) <= cantidad_disponible:  
#         # Inserción de la venta
#         cursor.execute("""
#             INSERT INTO ventas (id_stock, precio, cantidad_vendida, metodopago, fechavendida) 
#             VALUES (%s, %s, %s, %s, %s)
#         """, (id_stock, precio, cantidad_vendida, metodopago, fechavendida))

#         # Actualización de la cantidad en stock
#         nueva_cantidad_stock = cantidad_disponible - cantidad_vendida
#         cursor.execute("""
#             UPDATE stock SET cantidad = %s WHERE id_stock = %s
#         """, (nueva_cantidad_stock, id_stock))

#         # Si la cantidad llega a 0, muestra un mensaje
#         if nueva_cantidad_stock == 0:
#             flash(f"Se han vendido todas las unidades del producto.", "danger")

#         conn.commit()
#         flash("Venta registrada y stock actualizado correctamente.", "success")
#     else:
#         flash("La cantidad total vendida excede el stock disponible.", "danger")

#     cursor.close()
#     conn.close()
#     return redirect(url_for("obtener_ventas"))


# RUTA PARA CARGAR UNA VENTA
@app.route("/carga_venta", methods=['POST'])
def insertar_venta():
    id_stock = request.form['producto']  # Obtener el id_stock del formulario
    precio = request.form['precio']
    cantidad_vendida = request.form['cantidad_vendida']
    metodopago = request.form['metodopago']
    fechavendida = request.form['fechavendida']

    # Validación en el backend para cantidad_vendida y precio
    try:
        precio = float(precio)
        cantidad_vendida = int(cantidad_vendida)
        
        if cantidad_vendida <= 0:
            flash("La cantidad vendida debe ser un número positivo mayor que cero.", "danger")
            return redirect(url_for("cargar_venta"))

        if precio <= 0:
            flash("El precio debe ser un valor positivo mayor que cero.", "danger")
            return redirect(url_for("cargar_venta"))
    except ValueError:
        flash("La cantidad vendida y el precio deben ser valores numéricos válidos.", "danger")
        return redirect(url_for("cargar_venta"))

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consultar el stock disponible y fecha de ingreso
    cursor.execute("SELECT cantidad, fechaingreso FROM stock WHERE id_stock = %s", (id_stock,))
    stock = cursor.fetchone()

    if not stock:
        flash("No se pudo encontrar el stock para este producto.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("cargar_venta"))

    cantidad_disponible, fechaingreso = stock

    # Verificar que la fecha de venta no sea anterior a la fecha de ingreso
    if fechavendida < fechaingreso.strftime('%Y-%m-%d'):
        flash("La fecha de venta no puede ser anterior a la fecha de ingreso del producto.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("cargar_venta"))

    # Consultar la suma de las cantidades vendidas para el stock seleccionado
    cursor.execute("SELECT COALESCE(SUM(cantidad_vendida), 0) FROM ventas WHERE id_stock = %s", (id_stock,))
    total_vendido = cursor.fetchone()[0]

    # Comprobar que la cantidad vendida no exceda el stock disponible
    if (total_vendido + cantidad_vendida) <= cantidad_disponible:  
        # Inserción de la venta
        cursor.execute("""
            INSERT INTO ventas (id_stock, precio, cantidad_vendida, metodopago, fechavendida) 
            VALUES (%s, %s, %s, %s, %s)
        """, (id_stock, precio, cantidad_vendida, metodopago, fechavendida))

        # Actualización de la cantidad en stock
        nueva_cantidad_stock = cantidad_disponible - cantidad_vendida
        cursor.execute("""
            UPDATE stock SET cantidad = %s WHERE id_stock = %s
        """, (nueva_cantidad_stock, id_stock))

        # Si la cantidad llega a 0, muestra un mensaje
        if nueva_cantidad_stock == 0:
            flash("Se han vendido todas las unidades del producto.", "danger")

        conn.commit()
        flash("Venta registrada y stock actualizado correctamente.", "success")
    else:
        flash("La cantidad total vendida excede el stock disponible.", "danger")

    cursor.close()
    conn.close()
    return redirect(url_for("obtener_ventas"))


# # RUTA PARA EDITAR UNA VENTA
@app.route("/editar_venta/<int:id_venta>", methods=['GET', 'POST'])
def editar_venta(id_venta):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Inicializa el nombre del producto
    nombre_producto = None

    # Obtener los detalles de la venta original antes de editarla
    cursor.execute("SELECT * FROM ventas WHERE id_venta = %s", (id_venta,))
    venta_original = cursor.fetchone()

    if not venta_original:
        flash("Venta no encontrada.", "danger")
        return redirect(url_for("obtener_ventas"))

    id_stock = venta_original['id_stock']
    cantidad_original_vendida = venta_original['cantidad_vendida']  # Cantidad vendida original antes de editar

    # Obtener el nombre del producto desde la base de datos
    cursor.execute("SELECT p.nombre, s.fechaingreso FROM productos p JOIN stock s ON p.id_producto = s.id_producto WHERE s.id_stock = %s", (id_stock,))
    producto = cursor.fetchone()

    nombre_producto = producto['nombre'] if producto else "Producto no encontrado."
    fechaingreso = producto['fechaingreso']  # Fecha de ingreso del producto

    if request.method == 'POST':
        # Nuevos datos de la venta
        precio = request.form['precio']
        cantidad_vendida_nueva = int(request.form['cantidad_vendida'])  # Nueva cantidad
        fechavendida = request.form['fechavendida']
        metodopago = request.form['metodopago']

        # Validar que la fecha de venta no sea anterior a la fecha de ingreso
        if fechavendida < fechaingreso.strftime('%Y-%m-%d'):
            flash("La fecha de venta no puede ser anterior a la fecha de ingreso del producto.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("editar_venta", id_venta=id_venta))

        # Calcular la diferencia entre la cantidad original y la nueva
        diferencia_cantidad = cantidad_vendida_nueva - cantidad_original_vendida

        # Actualizar la cantidad en stock basándonos en la diferencia
        cursor.execute("SELECT cantidad FROM stock WHERE id_stock = %s", (id_stock,))
        stock = cursor.fetchone()

        if not stock:
            flash("Stock no encontrado.", "danger")
            return redirect(url_for("obtener_ventas"))

        cantidad_disponible_stock = stock['cantidad']

        # Asegúrate de que la nueva cantidad no exceda el stock disponible
        if cantidad_disponible_stock - diferencia_cantidad < 0:
            flash("La cantidad editada excede el stock disponible.", "danger")
        else:
            # Actualiza la venta en la base de datos
            cursor.execute("""
                UPDATE ventas 
                SET precio=%s, cantidad_vendida=%s, fechavendida=%s, metodopago=%s 
                WHERE id_venta=%s
            """, (precio, cantidad_vendida_nueva, fechavendida, metodopago, id_venta))

            # Actualiza la cantidad en stock
            nueva_cantidad_stock = cantidad_disponible_stock - diferencia_cantidad
            cursor.execute("""
                UPDATE stock SET cantidad=%s WHERE id_stock=%s
            """, (nueva_cantidad_stock, id_stock))

            # Si la cantidad llega a 0, muestra un mensaje
            if nueva_cantidad_stock == 0:
                flash(f"Se han vendido todas las unidades del producto '{nombre_producto}'.", "danger")

            # Guardar los cambios
            conn.commit()

            flash(f"Venta y stock del producto '{nombre_producto}' actualizados correctamente.", "success")

        cursor.close()
        conn.close()

        return redirect(url_for("obtener_ventas"))

    cursor.close()
    conn.close()

    mostrar_productos = True

    return render_template("editar_venta.html", venta=venta_original, nombre_producto=nombre_producto, mostrar_productos=mostrar_productos)


# RUTA PARA ELIMINAR UNA VENTA
@app.route("/eliminar_venta/<int:id_venta>", methods=['GET'])
def eliminar_venta(id_venta):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Primero, obtenemos los detalles de la venta, incluyendo id_stock y cantidad_vendida
    cursor.execute("SELECT id_stock, cantidad_vendida FROM ventas WHERE id_venta = %s", (id_venta,))
    venta = cursor.fetchone()

    nombre_producto = None  # Inicializa la variable para el nombre del producto

    if venta:  # Verificamos si la venta existe
        id_stock = venta['id_stock']
        cantidad_vendida = venta['cantidad_vendida']

        # Usamos id_stock para obtener el id_producto
        cursor.execute("SELECT id_producto, cantidad FROM stock WHERE id_stock = %s", (id_stock,))
        stock = cursor.fetchone()

        if stock:
            id_producto = stock['id_producto']
            cantidad_actual = stock['cantidad']
            
            # Ahora obtenemos el nombre del producto
            cursor.execute("SELECT nombre FROM productos WHERE id_producto = %s", (id_producto,))
            producto = cursor.fetchone()
            if producto:
                nombre_producto = producto['nombre']
            
            # Actualizar la cantidad en stock sumando la cantidad vendida
            nueva_cantidad = cantidad_actual + cantidad_vendida
            cursor.execute("UPDATE stock SET cantidad = %s WHERE id_stock = %s", (nueva_cantidad, id_stock))

        # Ahora eliminamos la venta
        cursor.execute("DELETE FROM ventas WHERE id_venta = %s", (id_venta,))
        conn.commit()

        if nombre_producto:
            flash(f"Venta de producto '{nombre_producto}' eliminada correctamente y el stock ha sido actualizado.", "success")
        else:
            flash("Venta eliminada, pero no se pudo encontrar el nombre del producto.", "warning")
    else:
        flash("La venta no se encontró.", "danger")

    cursor.close()
    conn.close()

    return redirect(url_for("obtener_ventas"))


# FUNCIÓN PARA BUSCAR VENTAS POR EL NOMBRE DEL PRODUCTO
# Utilizando id_stock como párametro común entre productos y ventas.
def buscar_ventas(query):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Consulta SQL que busca ventas cuyo nombre de producto contenga el término de búsqueda (query)
    cursor.execute("""
        SELECT ventas.*, productos.nombre
        FROM ventas
        JOIN stock ON ventas.id_stock = stock.id_stock
        JOIN productos ON stock.id_producto = productos.id_producto
        WHERE productos.nombre ILIKE %s
    """, ('%' + query + '%',))
    #en stock solo seleccionamos las filas de ventas que tengan id_stock
    #en productos solo seleccionamos las filas de stock que tengas id_producto

    ventas = cursor.fetchall()

    cursor.close()
    conn.close()

    return ventas

# RUTA PARA BUSCAR UNA VENTA 
@app.route('/buscar_venta')
def buscar_venta():
    query = request.args.get('query')

    # Si no hay término de búsqueda, muestra todas las ventas
    if not query:
        return redirect(url_for('obtener_ventas'))

    ventas = buscar_ventas(query)  # Llamar a la función que busca las ventas

    # Comprobar si se encontraron resultados
    if ventas:
        flash(f"Venta de producto '{query}' encontrado.", "success")
    else:
        flash(f"No se encontró venta para el producto '{query}'.", "danger")

    mostrar_productos = True

    return render_template('ventas.html', ventas=ventas, mostrar_productos=mostrar_productos)


### STOCK ####

# RUTA PARA MOSTRAR STOCK
@app.route("/stock", methods=['GET'])
def obtener_stock():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Ejecuta una consulta para obtener el stock junto con el nombre del producto
    cursor.execute("""
        SELECT s.id_stock, s.cantidad, s.fechaingreso, p.nombre, p.descripcion, p.talle
        FROM Stock s
        JOIN Productos p ON s.id_producto = p.id_producto
    """)

    stock = cursor.fetchall()

    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("stock.html", stock=stock, mostrar_productos=mostrar_productos)

# RUTA PARA MOSTRAR EL FORMULARIO DE CARGA DE STOCK (GET)
@app.route("/carga_stock", methods=['GET'])
def cargar_stock():
    
    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # Utiliza RealDictCursor para obtener un dict en lugar de una tupla

    # Ejecuta la consulta para obtener todos los productos, junto con su talle y descripcion
    cursor.execute("SELECT id_producto, nombre, descripcion, talle FROM productos")
    productos = cursor.fetchall()  # Obtiene todos los productos como una lista de diccionarios

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("carga_stock.html", productos=productos, mostrar_productos=mostrar_productos)


# RUTA PARA CARGAR STOCK
@app.route("/carga_stock", methods=['POST'])
def insertar_stock():
    id_producto = request.form['producto']  # Obtener el producto_id del formulario
    cantidad = request.form['cantidad']
    fechaingreso = request.form['fechaingreso']

    # Validación de cantidad en el backend
    try:
        cantidad = int(cantidad)  # Convertir a entero para la validación
        if cantidad <= 0:
            flash("La cantidad debe ser un número positivo mayor que cero.", "danger")
            return redirect(url_for("carga_stock"))
    except ValueError:
        flash("La cantidad debe ser un número válido.", "danger")
        return redirect(url_for("carga_stock"))

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consultar los detalles del producto usando el producto_id
    cursor.execute("SELECT nombre, descripcion, talle FROM productos WHERE id_producto = %s", (id_producto,))
    producto = cursor.fetchone()

    # Verificar si el producto existe
    if not producto:
        flash("Producto no encontrado.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("carga_stock"))
    
    # Inserción del stock
    cursor.execute("""INSERT INTO stock (id_producto, cantidad, fechaingreso) 
                      VALUES (%s, %s, %s)""",
                   (id_producto, cantidad, fechaingreso))
    
    # Guardar los cambios
    conn.commit()
    
    flash(f"Stock de producto '{producto[0]}' insertado correctamente.", "success")

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    return redirect(url_for("obtener_stock"))


# RUTA PARA EDITAR STOCK
@app.route("/editar_stock/<int:id_stock>", methods=['GET', 'POST'])
def editar_stock(id_stock):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Inicializa nombre
    nombre_producto = None

    if request.method == 'POST':
        # Actualiza el stock en la base de datos
        cantidad = request.form['cantidad']
        fechaingreso = request.form['fechaingreso']

        cursor.execute(""" 
            UPDATE stock SET cantidad=%s, fechaingreso=%s WHERE id_stock=%s 
        """, (cantidad, fechaingreso, id_stock))

        conn.commit()

        # Obtener el id_producto para el mensaje
        cursor.execute("SELECT id_producto FROM stock WHERE id_stock = %s", (id_stock,))
        stock = cursor.fetchone()
        
        if stock:
            id_producto = stock['id_producto']
            # Ahora obtenemos el nombre del producto
            cursor.execute("SELECT nombre FROM productos WHERE id_producto = %s", (id_producto,))
            producto = cursor.fetchone()
            if producto:
                nombre_producto = producto['nombre']

        cursor.close()
        conn.close()

        if nombre_producto:
            flash(f"Stock del producto '{nombre_producto}' modificado correctamente.", "success")
        else:
            flash("Stock modificado, pero no se pudo encontrar el nombre del producto.", "warning")

        return redirect(url_for("obtener_stock"))  # me lleva al método de la página central

    # Si es un GET, obtener el stock existente
    cursor.execute("SELECT * FROM stock WHERE id_stock = %s", (id_stock,))
    stock = cursor.fetchone()

    cursor.close()
    conn.close()

    mostrar_productos=True

    return render_template("editar_stock.html", stock=stock, mostrar_productos=mostrar_productos)


# RUTA PARA ELIMINAR STOCK
@app.route("/eliminar_stock/<int:id_stock>", methods=['GET'])
def eliminar_stock(id_stock):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Verificar si existe alguna venta relacionada con el id_stock
    cursor.execute("SELECT COUNT(*) AS ventas_relacionadas FROM ventas WHERE id_stock = %s", (id_stock,))
    ventas_relacionadas = cursor.fetchone()['ventas_relacionadas']

    if ventas_relacionadas > 0:
        # Si hay ventas relacionadas, no permitir la eliminación y mostrar un mensaje
        flash("No se puede eliminar el producto en stock porque tiene ventas asociadas.", "danger")
    else:
        # Si no hay ventas, proceder con la eliminación
        cursor.execute("SELECT id_producto FROM stock WHERE id_stock = %s", (id_stock,))
        stock = cursor.fetchone()

        if stock:  # Verificamos si el stock existe
            id_producto = stock['id_producto']
            # Ahora obtenemos el nombre del producto
            cursor.execute("SELECT nombre FROM productos WHERE id_producto = %s", (id_producto,))
            producto = cursor.fetchone()

            if producto:  # Verificamos si se encontró el producto
                nombre_producto = producto['nombre']
            else:
                nombre_producto = "desconocido"  # Nombre desconocido si no se encuentra

            # Procedemos a eliminar el stock
            cursor.execute("DELETE FROM stock WHERE id_stock = %s", (id_stock,))
            conn.commit()
            
            flash(f"Stock del producto '{nombre_producto}' eliminado correctamente.", "success")
        else:
            flash("El stock no se encontró.", "danger")

    cursor.close()
    conn.close()

    return redirect(url_for("obtener_stock"))  # Redirige a la página de stock


# FUNCIÓN PARA BUSCAR STOCK POR EL NOMBRE DEL PRODUCTO
# Utilizando id_producto
def def_buscar_stock(query):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Consulta SQL que busca ventas cuyo nombre de producto contenga el término de búsqueda (query)
    cursor.execute("""
        SELECT stock.*, productos.nombre, productos.descripcion, productos.talle
        FROM stock
        JOIN productos ON stock.id_producto = productos.id_producto  
        WHERE productos.nombre ILIKE %s
    """, ('%' + query + '%',))
    #en productos solo seleccionamos las filas de stock que tengas id_producto
    stock = cursor.fetchall()

    cursor.close()
    conn.close()

    return stock

# RUTA PARA BUSCAR UNA STOCK 
@app.route('/buscar_stock')
def buscar_stock():
    query = request.args.get('query')

    # Si no hay término de búsqueda, muestra todas las ventas
    if not query:
        return redirect(url_for('obtener_stock'))

    stock = def_buscar_stock(query)  # Llamar a la función que busca las ventas

    # Comprobar si se encontraron resultados
    if stock:
        flash(f"Stock de producto '{query}' encontrado.", "success")
    else:
        flash(f"No se encontró stock para el producto '{query}'.", "danger")

    mostrar_productos = True

    return render_template('stock.html', stock=stock, mostrar_productos=mostrar_productos)