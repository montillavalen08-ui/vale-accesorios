function mostrarSeccion(seccion) {
    let secciones = document.querySelectorAll(".seccion");

    secciones.forEach(function(elemento) {
        elemento.style.display = "none";
    });

    document.getElementById(seccion).style.display = "block";
}

mostrarSeccion("inicio");


let contador = 0;
let productosCarrito = [];

document.querySelectorAll(".btn-comprar").forEach(function(boton) {
    boton.addEventListener("click", function() {

        let producto = boton.closest(".producto");
        let nombre = producto.querySelector("h3").textContent;
        let precio = producto.querySelector("p").textContent;

       contador++;

let productoExistente = productosCarrito.find(function(producto) {
    return producto.nombre === nombre;
});

if (productoExistente) {
    productoExistente.cantidad++;
} else {
    productosCarrito.push({
        nombre: nombre,
        precio: precio,
        cantidad: 1
    });
}

document.getElementById("contador-carrito").textContent = contador;

let mensaje = document.getElementById("mensaje-carrito");

mensaje.textContent = "💙 ¡" + nombre + " agregado al carrito!";

setTimeout(function() {
    mensaje.textContent = "";
}, 2500);

if (document.getElementById("lista-carrito").style.display === "block") {
    actualizarCarrito();
}
    });
});

function actualizarCarrito() {
    let lista = document.getElementById("lista-carrito");
    let botonFinalizar = document.querySelector(".btn-finalizar");

    if (productosCarrito.length === 0) {
    lista.innerHTML = "<p>El carrito está vacío.</p>";

    if (botonFinalizar) {
        botonFinalizar.style.display = "none";
    }

    return;
}

if (botonFinalizar) {
    botonFinalizar.style.display = "inline-block";
}

    lista.innerHTML = "<h3>Productos en tu carrito:</h3>";

    let total = 0;

    productosCarrito.forEach(function(producto) {

        let precioNumero = parseInt(
            producto.precio.replace("$", "").replace(".", "")
        );

        let subtotal = precioNumero * producto.cantidad;

total += subtotal;

lista.innerHTML +=
    "<p>🛍️ " + producto.nombre +
    " — $" + subtotal.toLocaleString("es-CO") +
    " <button onclick=\"cambiarCantidad('" + producto.nombre + "', -1)\">➖</button>" +
    " " + producto.cantidad + " " +
    "<button onclick=\"cambiarCantidad('" + producto.nombre + "', 1)\">➕</button>" +
    " <button onclick=\"eliminarProducto('" + producto.nombre + "')\">🗑️</button></p>";
});

    lista.innerHTML +=
    "<h3>Total: $" + total.toLocaleString("es-CO") + "</h3>";

lista.innerHTML +=
    "<button onclick='vaciarCarrito()'>🗑️ Vaciar carrito</button>";
}


function mostrarCarrito() {
    let lista = document.getElementById("lista-carrito");

    if (lista.style.display === "block") {
        lista.style.display = "none";
        return;
    }

    lista.style.display = "block";

    actualizarCarrito();
}

function vaciarCarrito() {
    productosCarrito = [];
    contador = 0;

    document.getElementById("contador-carrito").textContent = contador;

    actualizarCarrito();
}

function eliminarProducto(nombreProducto) {
    let producto = productosCarrito.find(function(producto) {
        return producto.nombre === nombreProducto;
    });

    if (producto) {
        contador -= producto.cantidad;

        productosCarrito = productosCarrito.filter(function(producto) {
            return producto.nombre !== nombreProducto;
        });
    }

    document.getElementById("contador-carrito").textContent = contador;

    actualizarCarrito();
}

function cambiarCantidad(nombreProducto, cambio) {
    let producto = productosCarrito.find(function(producto) {
        return producto.nombre === nombreProducto;
    });

    if (!producto) {
        return;
    }

    producto.cantidad += cambio;

    if (producto.cantidad <= 0) {
        productosCarrito = productosCarrito.filter(function(producto) {
            return producto.nombre !== nombreProducto;
        });
    }

    contador = 0;

    productosCarrito.forEach(function(producto) {
        contador += producto.cantidad;
    });

    document.getElementById("contador-carrito").textContent = contador;

    actualizarCarrito();
}

function mostrarFormulario() {
    let formulario = document.getElementById("formulario-compra");

    if (productosCarrito.length === 0) {
        alert("Primero debes agregar un producto al carrito.");
        return;
    }

    formulario.style.display = "block";
}


async function confirmarPedido() {
    let nombre = document.getElementById("nombre").value.trim();
    let telefono = document.getElementById("telefono").value.trim();
    let direccion = document.getElementById("direccion").value.trim();
    let ciudad = document.getElementById("ciudad").value.trim();
    let correo = document.getElementById("correo").value.trim();
    let pago = document.getElementById("pago").value;

    if (
        nombre === "" ||
        telefono === "" ||
        direccion === "" ||
        ciudad === "" ||
        correo === "" ||
        pago === ""
    ) {
        alert("Por favor, completa todos los datos para continuar.");
        return;
    }

    if (productosCarrito.length === 0) {
        alert("Tu carrito está vacío.");
        return;
    }

    const boton = document.querySelector(".btn-finalizar");
    if (boton) boton.disabled = true;

    try {
        const respuesta = await fetch(
            "http://127.0.0.1:5000/api/pedidos",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    nombre: nombre,
                    telefono: telefono,
                    direccion: direccion,
                    ciudad: ciudad,
                    correo: correo,
                    metodo_pago: pago,
                    productos: productosCarrito.map(producto => ({
                        nombre: producto.nombre,
                        cantidad: producto.cantidad
                    }))
                })
            }
        );

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                resultado.error || "No se pudo registrar el pedido."
            );
        }

        let mensajePedido = document.getElementById("mensaje-pedido");

if (mensajePedido) {
    mensajePedido.textContent =
        "💙 ¡Pedido registrado con éxito! Número de pedido: " +
        resultado.id_pedido +
        ". Total: $" +
        resultado.total.toLocaleString("es-CO") +
        ". Gracias por comprar en Vale Accesorios.";

    mensajePedido.style.display = "block";
} else {
    alert(
        "💙 Tu pedido se guardó correctamente. Número de pedido: " +
        resultado.id_pedido
    );
}
       
console.log("mensajePedido:", document.getElementById("mensaje-pedido"));
console.log("formulario-compra:", document.getElementById("formulario-compra"));
console.log("datos-transferencia:", document.getElementById("datos-transferencia"));
        

const formularioCompra = document.getElementById("formulario-compra");

if (formularioCompra) {
    formularioCompra.style.display = "none";
}

        const datosTransferencia =
            document.getElementById("datos-transferencia");

        if (datosTransferencia) {
            datosTransferencia.style.display =
                ["Transferencia", "Nequi"].includes(pago)
                    ? "block"
                    : "none";
        }

        productosCarrito = [];
        contador = 0;

        document.getElementById("contador-carrito").textContent = contador;

        actualizarCarrito();

    } catch (error) {
        alert(
            "No se pudo guardar la compra en la base de datos. " +
            "Tu carrito se conserva. Detalle: " + error.message
        );

        console.error("Error al registrar el pedido:", error);

    } finally {
        if (boton) boton.disabled = false;
    }
}
