/*
 * CU-03 Registro de Compra – pantalla de la solicitud.
 * Validaciones en el cliente iguales a las de ValidadorSolicitud (DD-05);
 * el servidor vuelve a validar todo antes de guardar.
 */
(() => {
  const MSG = {
    camposVacios: 'Algunos de los campos no han sido llenados',
    sinLineas: 'La solicitud debe tener al menos una línea de producto',
    productoVacio: 'Seleccione un producto',
    productoInvalido: 'El producto no existe o está inactivo',
    productoRepetido: 'El producto ya fue agregado',
    cantidad: 'Ingrese una cantidad válida',
    prioridad: 'Seleccione una prioridad',
    observacionAlta: 'Justifique la prioridad Alta',
    observacionLarga: 'La observación admite máximo 250 caracteres',
  };
  const SELECTORES = {
    codigo: '.in-codigo', cantidad: '.in-cantidad', observacion: '.in-observacion', prioridad: '.in-prioridad',
  };

  const productos = new Map(); // código -> { codigo, nombre, unidad } (productos activos consultados)
  let cuerpo, datalist, caja;

  // ---------- Cabecera (RN-13) ----------
  async function cargarCabecera() {
    const { estado, datos } = await SCPC.api('/api/solicitudes/nueva');
    if (estado !== 200) return;
    document.getElementById('cab-numero').value = datos.numero_provisional;
    document.getElementById('cab-fecha').value = datos.fecha;
    document.getElementById('cab-solicitante').value = datos.solicitante;
  }

  // ---------- Búsqueda de productos ----------
  async function buscarProductos(texto) {
    const { estado, datos } = await SCPC.api(`/api/productos?buscar=${encodeURIComponent(texto)}`);
    if (estado !== 200) return [];
    for (const p of datos.productos) productos.set(p.codigo, p);
    return datos.productos;
  }

  function llenarLista(lista) {
    datalist.innerHTML = '';
    for (const p of lista) {
      const opcion = document.createElement('option');
      opcion.value = p.codigo;
      opcion.label = `${p.nombre} (${p.unidad})`;
      datalist.appendChild(opcion);
    }
  }

  /* Completa el nombre del producto a partir del código (campo Producto automático). */
  async function verificarCodigo(fila) {
    const campo = fila.querySelector('.in-codigo');
    const codigo = campo.value.trim().toUpperCase();
    campo.value = codigo;
    if (codigo && !productos.has(codigo)) await buscarProductos(codigo);
    const p = productos.get(codigo);
    fila.querySelector('.in-producto').value = p ? `${p.nombre} (${p.unidad})` : '';
  }

  // ---------- Filas de la tabla ----------
  function crearFila() {
    const fila = document.createElement('tr');
    fila.innerHTML = `
      <td><input type="text" class="in-codigo" list="lista-productos" maxlength="10"
                 placeholder="Buscar código o nombre" autocomplete="off" required>
          <div class="msg-error"></div></td>
      <td><input type="text" class="in-producto" readonly tabindex="-1"></td>
      <td><input type="number" class="in-cantidad" min="1" max="9999" step="1" required>
          <div class="msg-error"></div></td>
      <td><input type="text" class="in-observacion" maxlength="250">
          <div class="msg-error"></div></td>
      <td><select class="in-prioridad" required>
            <option value="">Seleccione</option>
            <option value="ALTA">Alta</option>
            <option value="MEDIA">Media</option>
            <option value="BAJA">Baja</option>
          </select>
          <div class="msg-error"></div></td>
      <td><button type="button" class="boton-icono btn-quitar" title="Eliminar fila">✕</button></td>`;

    const campoCodigo = fila.querySelector('.in-codigo');
    let temporizador = null;
    campoCodigo.addEventListener('input', () => {
      clearTimeout(temporizador);
      temporizador = setTimeout(async () => {
        llenarLista(await buscarProductos(campoCodigo.value.trim()));
        const p = productos.get(campoCodigo.value.trim().toUpperCase());
        fila.querySelector('.in-producto').value = p ? `${p.nombre} (${p.unidad})` : '';
      }, 250);
    });
    campoCodigo.addEventListener('change', () => verificarCodigo(fila));
    fila.querySelector('.btn-quitar').addEventListener('click', () => fila.remove());
    return fila;
  }

  function agregarFila() {
    const fila = crearFila();
    cuerpo.appendChild(fila);
    fila.querySelector('.in-codigo').focus();
  }

  function reiniciarFormulario() {
    cuerpo.innerHTML = '';
    cuerpo.appendChild(crearFila());
  }

  // ---------- Errores ----------
  function marcarError(fila, campo, texto) {
    const control = fila.querySelector(SELECTORES[campo]);
    if (!control) return;
    control.classList.add('campo-error');
    const msg = control.parentElement.querySelector('.msg-error');
    if (msg) msg.textContent = texto;
  }

  function limpiarErrores() {
    cuerpo.querySelectorAll('.campo-error').forEach((c) => c.classList.remove('campo-error'));
    cuerpo.querySelectorAll('.msg-error').forEach((m) => { m.textContent = ''; });
    SCPC.ocultarMensaje(caja);
  }

  // ---------- Validación en el cliente (mismas reglas que el servidor) ----------
  function validarCliente(filas) {
    const generales = [];
    let valido = true;
    let hayVacios = false;
    const vistos = new Set();

    if (filas.length === 0) { generales.push(MSG.sinLineas); valido = false; }

    for (const fila of filas) {
      const codigo = fila.querySelector('.in-codigo').value.trim().toUpperCase();
      const cantidad = fila.querySelector('.in-cantidad').value.trim();
      const prioridad = fila.querySelector('.in-prioridad').value;
      const observacion = fila.querySelector('.in-observacion').value.trim();

      if (!codigo) { marcarError(fila, 'codigo', MSG.productoVacio); hayVacios = true; valido = false; }
      else if (!productos.has(codigo)) { marcarError(fila, 'codigo', MSG.productoInvalido); valido = false; }
      else if (vistos.has(codigo)) { marcarError(fila, 'codigo', MSG.productoRepetido); valido = false; }
      else vistos.add(codigo);

      if (!cantidad) { marcarError(fila, 'cantidad', MSG.cantidad); hayVacios = true; valido = false; }
      else if (!/^\d+$/.test(cantidad) || Number(cantidad) < 1 || Number(cantidad) > 9999) {
        marcarError(fila, 'cantidad', MSG.cantidad); valido = false;
      }

      if (!prioridad) { marcarError(fila, 'prioridad', MSG.prioridad); hayVacios = true; valido = false; }

      if (observacion.length > 250) { marcarError(fila, 'observacion', MSG.observacionLarga); valido = false; }
      else if (prioridad === 'ALTA' && !observacion) {
        marcarError(fila, 'observacion', MSG.observacionAlta); valido = false;
      }
    }

    if (hayVacios) generales.push(MSG.camposVacios);
    if (!valido) {
      SCPC.mostrarMensaje(caja, generales.length ? generales.join('. ') : 'Revise los campos marcados en rojo.', 'error');
    }
    return valido;
  }

  function aplicarErroresServidor(errores, filas) {
    const generales = (errores && errores.general) || [];
    const porLinea = (errores && errores.lineas) || {};
    for (const [indice, campos] of Object.entries(porLinea)) {
      const fila = filas[Number(indice)];
      if (!fila) continue;
      for (const [campo, texto] of Object.entries(campos)) marcarError(fila, campo, texto);
    }
    SCPC.mostrarMensaje(caja, generales.length ? generales.join('. ') : 'Revise los campos marcados en rojo.', 'error');
  }

  // ---------- Guardar (flujo básico) ----------
  async function guardar() {
    limpiarErrores();
    const filas = Array.from(cuerpo.rows);
    await Promise.all(filas.map(verificarCodigo));
    if (!validarCliente(filas)) return;

    const lineas = filas.map((fila) => ({
      codigo: fila.querySelector('.in-codigo').value.trim().toUpperCase(),
      cantidad: parseInt(fila.querySelector('.in-cantidad').value, 10),
      prioridad: fila.querySelector('.in-prioridad').value,
      observacion: fila.querySelector('.in-observacion').value.trim(),
    }));

    const boton = document.getElementById('btn-guardar');
    boton.disabled = true;
    const { estado, datos } = await SCPC.api('/api/solicitudes', { metodo: 'POST', datos: { lineas } });
    boton.disabled = false;

    if (estado === 201) {
      reiniciarFormulario();
      SCPC.mostrarMensaje(caja, `Solicitud ${datos.numero} registrada correctamente con estado Pendiente.`, 'exito');
      cargarCabecera();
      cargarMisSolicitudes();
    } else if (estado === 400 && datos.errores) {
      aplicarErroresServidor(datos.errores, filas);
    } else if (estado !== 401 && estado !== 403) {
      SCPC.mostrarMensaje(caja, datos.error || 'No se pudo guardar la solicitud. Intente nuevamente.', 'error');
    }
  }

  // ---------- Cancelar (RN-20: solo descarta lo no guardado) ----------
  function cancelar() {
    const hayDatos = Array.from(cuerpo.querySelectorAll('input:not([readonly]), select'))
      .some((c) => c.value.trim() !== '');
    if (hayDatos && !window.confirm('¿Descartar los datos que aún no se han guardado?')) return;
    limpiarErrores();
    reiniciarFormulario();
  }

  // ---------- Mis solicitudes y eliminación de líneas guardadas (RN-19) ----------
  async function cargarMisSolicitudes() {
    const contenedor = document.getElementById('mis-solicitudes');
    const { estado, datos } = await SCPC.api('/api/solicitudes');
    if (estado !== 200) return;

    if (datos.solicitudes.length === 0) {
      contenedor.innerHTML = '<p>Aún no ha registrado solicitudes.</p>';
      return;
    }

    const e = SCPC.escapar;
    contenedor.innerHTML = datos.solicitudes.map((s) => {
      const editable = s.estado === 'PENDIENTE';
      const filas = s.lineas.length
        ? s.lineas.map((l) => `
            <tr>
              <td>${e(l.codigo)}</td>
              <td>${e(l.producto)} (${e(l.unidad)})</td>
              <td>${e(l.cantidad)}</td>
              <td>${e(l.observacion)}</td>
              <td>${e(l.prioridad_texto)}</td>
              <td>${editable
                ? `<button type="button" class="boton-icono btn-eliminar-linea" data-solicitud="${s.id}"
                           data-detalle="${l.id}" data-ultima="${s.lineas.length === 1}">Eliminar</button>`
                : '—'}</td>
            </tr>`).join('')
        : '<tr><td colspan="6">Sin líneas.</td></tr>';
      return `
        <article class="tarjeta-solicitud">
          <header>
            <strong>${e(s.numero)}</strong>
            <span>${e(s.fecha)}</span>
            <span class="estado estado-${e(s.estado.toLowerCase())}">${e(s.estado_texto)}</span>
          </header>
          <table class="tabla tabla-compacta">
            <thead><tr><th>Código</th><th>Producto</th><th>Cantidad</th><th>Observación</th>
                       <th>Prioridad</th><th>Eliminar</th></tr></thead>
            <tbody>${filas}</tbody>
          </table>
        </article>`;
    }).join('');
  }

  async function eliminarLineaGuardada(boton) {
    const esUltima = boton.dataset.ultima === 'true';
    const pregunta = esUltima
      ? 'Es la última línea: la solicitud pasará a estado Cancelada. ¿Desea continuar?'
      : '¿Eliminar esta línea de la solicitud?';
    if (!window.confirm(pregunta)) return;

    const url = `/api/solicitudes/${boton.dataset.solicitud}/detalles/${boton.dataset.detalle}`;
    const { estado, datos } = await SCPC.api(url, { metodo: 'DELETE' });
    if (estado === 204) {
      SCPC.mostrarMensaje(caja, esUltima ? 'Línea eliminada. La solicitud quedó Cancelada.' : 'Línea eliminada.', 'exito');
    } else if (estado !== 401) {
      SCPC.mostrarMensaje(caja, datos.error || 'No se pudo eliminar la línea.', 'error');
    }
    cargarMisSolicitudes();
  }

  // ---------- Inicio ----------
  document.addEventListener('DOMContentLoaded', () => {
    cuerpo = document.getElementById('cuerpo-lineas');
    datalist = document.getElementById('lista-productos');
    caja = document.getElementById('mensaje-solicitud');

    reiniciarFormulario();
    cargarCabecera();
    cargarMisSolicitudes();
    buscarProductos('').then(llenarLista);

    document.getElementById('btn-agregar').addEventListener('click', agregarFila);
    document.getElementById('btn-guardar').addEventListener('click', guardar);
    document.getElementById('btn-cancelar').addEventListener('click', cancelar);
    document.getElementById('mis-solicitudes').addEventListener('click', (evento) => {
      const boton = evento.target.closest('.btn-eliminar-linea');
      if (boton) eliminarLineaGuardada(boton);
    });
  });
})();
