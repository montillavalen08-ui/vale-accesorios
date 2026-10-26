
import os
import psycopg2
from psycopg2 import Error
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path

# Buscar el archivo .env en la carpeta principal del proyecto.
RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(RUTA_ENV)


def conectar_bd():
    """Establecer la conexión a PostgreSQL."""
    try:
        conexion = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "vale_accesorios"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5433")
        )

        cursor = conexion.cursor()
        print("¡Conexión exitosa a PostgreSQL!")

        return conexion, cursor

    except (Exception, Error) as error:
        print("Error al conectar a PostgreSQL:", error)
        return None, None



def insertar_productos(conexion, cursor, nombre, precio, descripcion, imagen):
    """Insertar un producto en la tabla productos."""
    try:
        consulta = """
            INSERT INTO productos (nombre, precio, descripcion, imagen)
            VALUES (%s, %s, %s, %s)
        """

        valores = (nombre, precio, descripcion, imagen)

        cursor.execute(consulta, valores)
        conexion.commit()

        print(f"Producto '{nombre}' registrado exitosamente.\n")

    except (Exception, Error) as error:
        print("Error al insertar el producto:", error)
        conexion.rollback()


def leer_productos(cursor):
    """Consultar los productos registrados."""
    try:
        consulta = "SELECT * FROM productos ORDER BY id_producto;"
        cursor.execute(consulta)

        registros = cursor.fetchall()

        print(f"Total de productos registrados: {len(registros)}")

        for fila in registros:
            print(fila)

        print()

    except (Exception, Error) as error:
        print("Error al consultar los productos:", error)


def cerrar_conexion(conexion, cursor):
    """Cerrar la conexión de forma segura."""
    if cursor:
        cursor.close()

    if conexion:
        conexion.close()
        print("La conexión a PostgreSQL se ha cerrado exitosamente.")


# CONEXIÓN DEL SERVIDOR CON LA PÁGINA WEB

app = Flask(__name__)
CORS(app)


# REGISTRAR UN PEDIDO DESDE LA PÁGINA WEB

@app.route("/api/pedidos", methods=["POST"])
def registrar_pedido_web():
    conexion = None
    cursor = None

    try:
        datos = request.get_json()

        if not datos:
            return jsonify({"error": "No se recibieron datos."}), 400

        nombre = datos.get("nombre", "").strip()
        telefono = datos.get("telefono", "").strip()
        direccion = datos.get("direccion", "").strip()
        ciudad = datos.get("ciudad", "").strip()
        correo = datos.get("correo", "").strip()
        metodo_pago = datos.get("metodo_pago", "").strip()
        productos = datos.get("productos", [])

        if not all([nombre, telefono, direccion, ciudad, correo, metodo_pago]):
            return jsonify({"error": "Completa todos los datos del cliente."}), 400

        if not isinstance(productos, list) or not productos:
            return jsonify({"error": "El carrito está vacío."}), 400

        conexion, cursor = conectar_bd()

        if conexion is None or cursor is None:
            return jsonify({"error": "No fue posible conectar con PostgreSQL."}), 500

        total = 0
        detalles = []

        # Buscar los productos y calcular el total con los precios de la base de datos.
        for producto in productos:
            nombre_producto = producto.get("nombre", "").strip()
            cantidad = producto.get("cantidad")

            if not nombre_producto or type(cantidad) is not int or cantidad < 1:
                raise ValueError("Hay un producto o una cantidad inválidos.")

            cursor.execute(
                """
                SELECT id_producto, nombre, precio
                FROM productos
                WHERE nombre = %s
                ORDER BY id_producto
                LIMIT 1
                """,
                (nombre_producto,)
            )

            resultado = cursor.fetchone()

            if resultado is None:
                raise ValueError(
                    f"El producto '{nombre_producto}' no existe en la base de datos."
                )

            id_producto, nombre_bd, precio = resultado
            total += precio * cantidad

            detalles.append((id_producto, cantidad, precio))

        # Registrar cliente.
        cursor.execute(
            """
            INSERT INTO clientes (nombre, telefono, direccion, ciudad, correo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_cliente
            """,
            (nombre, telefono, direccion, ciudad, correo)
        )

        id_cliente = cursor.fetchone()[0]

        # Registrar pedido.
        cursor.execute(
            """
            INSERT INTO pedidos (id_cliente, metodo_pago, total)
            VALUES (%s, %s, %s)
            RETURNING id_pedido
            """,
            (id_cliente, metodo_pago, total)
        )

        id_pedido = cursor.fetchone()[0]

        # Registrar cada producto del pedido.
        for id_producto, cantidad, precio in detalles:
            cursor.execute(
                """
                INSERT INTO detalle_pedido
                    (id_pedido, id_producto, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
                """,
                (id_pedido, id_producto, cantidad, precio)
            )

        # Guardar todos los registros juntos.
        conexion.commit()

        return jsonify({
            "mensaje": "Pedido registrado correctamente.",
            "id_pedido": id_pedido,
            "total": float(total)
        }), 201

    except ValueError as error:
        if conexion:
            conexion.rollback()
        return jsonify({"error": str(error)}), 400

    except Exception as error:
        if conexion:
            conexion.rollback()
        print("Error al registrar el pedido:", error)
        return jsonify({"error": "Ocurrió un error al guardar el pedido."}), 500

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


# INICIAR EL SERVIDOR

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)


# TABLA CLIENTES

def insertar_cliente(conexion, cursor, nombre, telefono,
                     direccion, ciudad, correo):
    """Registrar un cliente en la base de datos."""

    try:
        consulta = """
            INSERT INTO clientes
                (nombre, telefono, direccion, ciudad, correo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_cliente;
        """

        valores = (nombre, telefono, direccion, ciudad, correo)

        cursor.execute(consulta, valores)
        id_cliente = cursor.fetchone()[0]
        conexion.commit()

        print(f"Cliente registrado con ID: {id_cliente}")
        return id_cliente

    except (Exception, Error) as error:
        conexion.rollback()
        print("Error al registrar el cliente:", error)
        return None


def leer_clientes(cursor):
    """Consultar los clientes registrados."""

    try:
        cursor.execute("SELECT * FROM clientes ORDER BY id_cliente;")

        registros = cursor.fetchall()

        print("\nCLIENTES REGISTRADOS")

        for fila in registros:
            print(fila)

        print(f"Total de clientes: {len(registros)}")

    except (Exception, Error) as error:
        print("Error al consultar los clientes:", error)


# TABLA PEDIDOS

def insertar_pedido(conexion, cursor, id_cliente,
                    metodo_pago, total):
    """Registrar un pedido y devolver su ID."""

    try:
        consulta = """
            INSERT INTO pedidos
                (id_cliente, metodo_pago, total)
            VALUES (%s, %s, %s)
            RETURNING id_pedido;
        """

        valores = (id_cliente, metodo_pago, total)

        cursor.execute(consulta, valores)
        id_pedido = cursor.fetchone()[0]
        conexion.commit()

        print(f"Pedido registrado con ID: {id_pedido}")
        return id_pedido

    except (Exception, Error) as error:
        conexion.rollback()
        print("Error al registrar el pedido:", error)
        return None


def leer_pedidos(cursor):
    """Consultar los pedidos registrados."""

    try:
        cursor.execute("SELECT * FROM pedidos ORDER BY id_pedido;")

        registros = cursor.fetchall()

        print("\nPEDIDOS REGISTRADOS")

        for fila in registros:
            print(fila)

        print(f"Total de pedidos: {len(registros)}")

    except (Exception, Error) as error:
        print("Error al consultar los pedidos:", error)


# TABLA DETALLE_PEDIDO

def insertar_detalle_pedido(conexion, cursor, id_pedido,
                            id_producto, cantidad, precio_unitario):
    """Registrar un producto dentro de un pedido."""

    try:
        consulta = """
            INSERT INTO detalle_pedido
                (id_pedido, id_producto, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s);
        """

        valores = (
            id_pedido,
            id_producto,
            cantidad,
            precio_unitario
        )

        cursor.execute(consulta, valores)
        conexion.commit()

        print("Producto agregado al detalle del pedido.")

        return True

    except (Exception, Error) as error:
        conexion.rollback()
        print("Error al registrar el detalle:", error)
        return False


def leer_detalle_pedido(cursor):
    """Consultar los productos de cada pedido."""

    try:
        cursor.execute("""
            SELECT
                dp.id_detalle,
                dp.id_pedido,
                p.nombre,
                dp.cantidad,
                dp.precio_unitario,
                dp.cantidad * dp.precio_unitario AS subtotal
            FROM detalle_pedido dp
            INNER JOIN productos p
                ON dp.id_producto = p.id_producto
            ORDER BY dp.id_detalle;
        """)

        registros = cursor.fetchall()

        print("\nDETALLE DE LOS PEDIDOS")

        for fila in registros:
            print(fila)

        print(f"Total de detalles registrados: {len(registros)}")

    except (Exception, Error) as error:
        print("Error al consultar los detalles:", error)


# CONSULTAR PEDIDOS CON CLIENTES Y PRODUCTOS

def leer_compras_completas(cursor):
    """Mostrar los pedidos junto con sus clientes y productos."""

    try:
        consulta = """
            SELECT
                c.nombre AS cliente,
                c.telefono,
                pe.id_pedido,
                pe.fecha,
                pe.metodo_pago,
                pe.estado,
                pr.nombre AS producto,
                dp.cantidad,
                dp.precio_unitario,
                pe.total
            FROM clientes c
            INNER JOIN pedidos pe
                ON c.id_cliente = pe.id_cliente
            INNER JOIN detalle_pedido dp
                ON pe.id_pedido = dp.id_pedido
            INNER JOIN productos pr
                ON dp.id_producto = pr.id_producto
            ORDER BY pe.id_pedido DESC;
        """

        cursor.execute(consulta)
        registros = cursor.fetchall()

        print("\nCOMPRAS COMPLETAS")

        for fila in registros:
            print(fila)

        if not registros:
            print("Todavía no hay compras registradas.")

    except (Exception, Error) as error:
        print("Error al consultar las compras:", error)




if __name__ == "__main__":
    conn, cur = conectar_bd()

    if conn and cur:
        try:
            leer_productos(cur)
            leer_clientes(cur)
            leer_pedidos(cur)
            leer_detalle_pedido(cur)
            leer_compras_completas(cur)
        finally:
            cerrar_conexion(conn, cur)