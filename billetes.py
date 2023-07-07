import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = "pruebas.db"

def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tabla():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    codigo INT PRIMARY KEY,
                    descripcion VARCHAR(255),
                    stock INT,
                    precio FLOAT)
            """)
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS carrito (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo INT,
                    descripcion VARCHAR(255),
                    cantidad INT,
                    precio FLOAT)
            """)
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/productos', methods=['POST'])
def alta_producto():
    data = request.get_json()
    if 'codigo' not in data or 'descripcion' not in data or 'stock' not in data or 'precio' not in data:
        return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
                    INSERT INTO productos(codigo, descripcion, stock, precio)
                    VALUES(?,?,?,?) """,
                    (data['codigo'], data['descripcion'], data['stock'], data['precio']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'mensaje': 'Alta efectuada correctamente'}), 201
    except:
        return jsonify({'error': 'Error al dar de alta el producto'}), 500

@app.route('/productos/<int:codigo>', methods=['GET'])
def consultar_producto(codigo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM productos 
                            WHERE codigo=?""", (codigo,))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404
        else:
            return jsonify({
                'codigo': producto['codigo'],
                'descripcion': producto['descripcion'],
                'stock': producto['stock'],
                'precio': producto['precio']
            })
    except:
        return jsonify({'error': 'Error al consultar el producto'}), 500

@app.route('/productos/<int:codigo>', methods=['PUT'])
def modificar_producto(codigo):
    data = request.get_json()
    if 'descripcion' not in data or 'stock' not in data or 'precio' not in data:
        return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM productos WHERE codigo=?""", (codigo,))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404
        else:
            cursor.execute("""UPDATE productos SET descripcion=?, stock=?, precio=?
                                WHERE codigo=?""", (data['descripcion'], data['stock'], data['precio'], codigo))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'mensaje': 'Producto modificado correctamente'}), 200
    except:
        return jsonify({'error': 'Error al modificar el producto'}), 500

@app.route('/productos', methods=['GET'])
def listar_productos():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        response = []
        for producto in productos:
            response.append({
                'codigo': producto['codigo'],
                'descripcion': producto['descripcion'],
                'stock': producto['stock'],
                'precio': producto['precio']
            })
        return jsonify(response)
    except:
        return jsonify({'error': 'Error al listar los productos'}), 500

@app.route('/carrito', methods=['POST'])
def agregar_al_carrito():
    data = request.get_json()
    if 'codigo' not in data or 'cantidad' not in data:
        return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM productos WHERE codigo=?""", (data['codigo'],))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404

        cantidad = int(data['cantidad'])
        if cantidad <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor a cero'}), 400

        if producto['stock'] < cantidad:
            return jsonify({'error': 'No hay suficiente stock disponible'}), 400

        cursor.execute("""SELECT * FROM carrito WHERE codigo=?""", (data['codigo'],))
        item_carrito = cursor.fetchone()
        if item_carrito is None:
            cursor.execute("""INSERT INTO carrito(codigo, descripcion, cantidad, precio)
                              VALUES(?,?,?,?)""",
                           (producto['codigo'], producto['descripcion'], cantidad, producto['precio']))
        else:
            nueva_cantidad = item_carrito['cantidad'] + cantidad
            cursor.execute("""UPDATE carrito SET cantidad=? WHERE codigo=?""",
                           (nueva_cantidad, data['codigo']))

        nuevo_stock = producto['stock'] - cantidad
        cursor.execute("""UPDATE productos SET stock=? WHERE codigo=?""",
                       (nuevo_stock, data['codigo']))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'mensaje': 'Producto agregado al carrito correctamente'}), 201
    except:
        return jsonify({'error': 'Error al agregar el producto al carrito'}), 500

@app.route('/carrito', methods=['GET'])
def obtener_carrito():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM carrito")
        productos_carrito = cursor.fetchall()
        response = []
        for producto in productos_carrito:
            response.append({
                'id': producto['id'],
                'codigo': producto['codigo'],
                'descripcion': producto['descripcion'],
                'cantidad': producto['cantidad'],
                'precio': producto['precio']
            })
        return jsonify(response)
    except:
        return jsonify({'error': 'Error al obtener el carrito de compras'}), 500

@app.route('/carrito/<int:id>', methods=['DELETE'])
def eliminar_del_carrito(id):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM carrito WHERE id=?""", (id,))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado en el carrito'}), 404

        cursor.execute("""DELETE FROM carrito WHERE id=?""", (id,))
        conn.commit()

        cursor.execute("""SELECT * FROM productos WHERE codigo=?""", (producto['codigo'],))
        producto_stock = cursor.fetchone()
        nuevo_stock = producto_stock['stock'] + producto['cantidad']
        cursor.execute("""UPDATE productos SET stock=? WHERE codigo=?""", (nuevo_stock, producto['codigo']))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({'mensaje': 'Producto eliminado del carrito correctamente'}), 200
    except:
        return jsonify({'error': 'Error al eliminar el producto del carrito'}), 500

@app.route('/productos/<int:codigo>', methods=['DELETE'])
def eliminar_producto(codigo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM productos WHERE codigo=?""", (codigo,))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404

        cursor.execute("""DELETE FROM productos WHERE codigo=?""", (codigo,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'mensaje': 'Producto eliminado correctamente'}), 200
    except:
        return jsonify({'error': 'Error al eliminar el producto'}), 500


@app.route('/', methods=['GET'])
def inicio():
    return "Hola Codo a Codo"


if __name__ == '__main__':
    crear_tabla()
    app.run()
