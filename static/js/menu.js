/* CU-02 Seleccionar Tarea: dibuja SOLO las opciones que devuelve el servidor (RN-08). */
document.addEventListener('DOMContentLoaded', async () => {
  const lista = document.getElementById('opciones-menu');
  if (!lista) return;

  if (new URLSearchParams(window.location.search).get('restringido')) {
    const avisos = document.getElementById('mensajes-globales');
    const div = document.createElement('div');
    div.className = 'mensaje mensaje-error';
    div.textContent = 'Acceso restringido';
    avisos.appendChild(div);
  }

  const { estado, datos } = await SCPC.api('/api/menu');
  if (estado !== 200) return;

  lista.innerHTML = '';
  for (const opcion of datos.opciones) {
    const li = document.createElement('li');
    if (opcion.codigo === 'FINALIZAR_SESION') {
      const boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'opcion-salir';
      boton.textContent = opcion.nombre;
      boton.addEventListener('click', cerrarSesion);
      li.appendChild(boton);
    } else {
      const enlace = document.createElement('a');
      enlace.href = opcion.ruta;
      enlace.textContent = opcion.nombre;
      if (window.location.pathname.startsWith(opcion.ruta)) enlace.classList.add('activo');
      li.appendChild(enlace);
    }
    lista.appendChild(li);
  }
});

/* RN-11: invalida la sesión en el servidor y vuelve al inicio de sesión. */
async function cerrarSesion() {
  await SCPC.api('/api/auth/logout', { metodo: 'POST' });
  window.location.href = '/login/';
}
