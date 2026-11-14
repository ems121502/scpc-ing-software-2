/* Cliente de la API REST del SCPC (Fase 2, sección 7.2). Usado por todas las pantallas. */
const SCPC = (() => {
  function leerCookie(nombre) {
    const partes = document.cookie ? document.cookie.split('; ') : [];
    for (const parte of partes) {
      const [clave, ...valor] = parte.split('=');
      if (clave === nombre) return decodeURIComponent(valor.join('='));
    }
    return null;
  }

  /**
   * Llama a la API y devuelve { estado, datos }.
   * - 401 (sesión vencida, RN-06): vuelve a la pantalla de inicio de sesión.
   * - 403 "Acceso restringido" (RN-10): regresa al menú principal con el aviso.
   */
  async function api(url, { metodo = 'GET', datos = null } = {}) {
    const opciones = { method: metodo, credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (metodo !== 'GET') opciones.headers['X-CSRFToken'] = leerCookie('csrftoken') || '';
    if (datos !== null) {
      opciones.headers['Content-Type'] = 'application/json';
      opciones.body = JSON.stringify(datos);
    }

    let respuesta;
    try {
      respuesta = await fetch(url, opciones);
    } catch (e) {
      return { estado: 0, datos: { error: 'No se pudo conectar con el servidor.' } };
    }

    let cuerpo = {};
    if (respuesta.status !== 204) {
      try { cuerpo = await respuesta.json(); } catch (e) { cuerpo = {}; }
    }

    if (respuesta.status === 401 && !url.startsWith('/api/auth/login')) {
      window.location.href = '/login/?expirada=1';
    } else if (respuesta.status === 403 && cuerpo.error === 'Acceso restringido') {
      window.location.href = '/menu/?restringido=1';
    }
    return { estado: respuesta.status, datos: cuerpo };
  }

  function escapar(texto) {
    const div = document.createElement('div');
    div.textContent = texto == null ? '' : String(texto);
    return div.innerHTML;
  }

  function mostrarMensaje(caja, texto, tipo) {
    caja.textContent = texto;
    caja.className = `mensaje mensaje-${tipo}`;
  }

  function ocultarMensaje(caja) {
    caja.textContent = '';
    caja.className = 'mensaje oculto';
  }

  return { api, escapar, leerCookie, mostrarMensaje, ocultarMensaje };
})();
