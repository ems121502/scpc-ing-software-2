/* CU-01 Inicio de Sesión – validación en la pantalla (RN-01, DD-05) y envío a la API. */
document.addEventListener('DOMContentLoaded', () => {
  const formulario = document.getElementById('form-login');
  const campoUsuario = document.getElementById('usuario');
  const campoContrasena = document.getElementById('contrasena');
  const casillaRecordar = document.getElementById('recordarme');
  const boton = document.getElementById('btn-siguiente');
  const caja = document.getElementById('mensaje-login');

  // "Recuérdame": recuerda el nombre de usuario en este navegador (no la contraseña)
  try {
    const guardado = localStorage.getItem('scpc_usuario');
    if (guardado) { campoUsuario.value = guardado; casillaRecordar.checked = true; }
  } catch (e) { /* almacenamiento no disponible */ }

  if (new URLSearchParams(window.location.search).get('expirada')) {
    SCPC.mostrarMensaje(caja, 'Su sesión expiró o no es válida. Inicie sesión nuevamente.', 'aviso');
  }

  function marcar(campo, idError, texto) {
    campo.classList.add('campo-error');
    document.getElementById(idError).textContent = texto;
  }

  function limpiar() {
    for (const [campo, idError] of [[campoUsuario, 'error-usuario'], [campoContrasena, 'error-contrasena']]) {
      campo.classList.remove('campo-error');
      document.getElementById(idError).textContent = '';
    }
    SCPC.ocultarMensaje(caja);
  }

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiar();

    const usuario = campoUsuario.value.trim();
    const contrasena = campoContrasena.value;
    let valido = true;
    if (!usuario) { marcar(campoUsuario, 'error-usuario', 'Ingrese su usuario'); valido = false; }
    if (!contrasena) { marcar(campoContrasena, 'error-contrasena', 'Ingrese su contraseña'); valido = false; }
    if (!valido) return;

    boton.disabled = true;
    const { estado, datos } = await SCPC.api('/api/auth/login', {
      metodo: 'POST', datos: { usuario, contrasena },
    });
    boton.disabled = false;

    if (estado === 200) {
      try {
        if (casillaRecordar.checked) localStorage.setItem('scpc_usuario', usuario);
        else localStorage.removeItem('scpc_usuario');
      } catch (e) { /* sin almacenamiento */ }
      window.location.href = datos.redirigir || '/menu/';
      return;
    }

    // Se conserva el usuario escrito y se limpia la contraseña (Fase 2, 7.1)
    campoContrasena.value = '';
    const tipo = estado === 423 ? 'aviso' : 'error';
    SCPC.mostrarMensaje(caja, datos.error || 'Ocurrió un error inesperado. Intente nuevamente.', tipo);
  });
});
