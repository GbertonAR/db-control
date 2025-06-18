document.addEventListener('DOMContentLoaded', () => {
    const parametrosTableBody = document.querySelector('#parametros-table tbody');
    const parametroForm = document.getElementById('parametro-form');
    const parametroIdInput = document.getElementById('parametro-id');
    const nombreParametroInput = document.getElementById('nombre_parametro');
    const valorParametroInput = document.getElementById('valor_parametro');
    const tipoDatoSelect = document.getElementById('tipo_dato');
    const descripcionTextarea = document.getElementById('descripcion');
    const submitButton = document.getElementById('submit-button');
    const cancelEditButton = document.getElementById('cancel-edit-button');
    const messageArea = document.getElementById('message-area');

    const API_BASE_URL = '/api/parametros_seteos'; // URL de la API de Flask

    // Función para mostrar mensajes de éxito o error
    function showMessage(message, type) {
        messageArea.textContent = message;
        messageArea.className = `message-area ${type}`; // 'success' o 'error'
        messageArea.style.display = 'block';
        setTimeout(() => {
            messageArea.style.display = 'none';
            messageArea.textContent = '';
        }, 5000); // Ocultar después de 5 segundos
    }

    // Función para cargar los parámetros en la tabla
    async function loadParametros() {
        try {
            const response = await fetch(API_BASE_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const parametros = await response.json();
            parametrosTableBody.innerHTML = ''; // Limpiar tabla
            parametros.forEach(param => {
                const row = parametrosTableBody.insertRow();
                row.innerHTML = `
                    <td>${param.id}</td>
                    <td>${param.nombre_parametro}</td>
                    <td>${param.valor_parametro}</td>
                    <td>${param.tipo_dato || 'N/A'}</td>
                    <td>${param.descripcion || 'N/A'}</td>
                    <td>${param.ultima_modificacion || 'N/A'}</td>
                    <td class="actions">
                        <button class="edit" data-id="${param.id}">Editar</button>
                        <button class="delete" data-id="${param.id}">Eliminar</button>
                    </td>
                `;
            });
        } catch (error) {
            console.error('Error al cargar parámetros:', error);
            showMessage('Error al cargar los parámetros.', 'error');
        }
    }

    // Función para resetear el formulario
    function resetForm() {
        parametroIdInput.value = '';
        nombreParametroInput.value = '';
        valorParametroInput.value = '';
        tipoDatoSelect.value = '';
        descripcionTextarea.value = '';
        submitButton.textContent = 'Añadir Parámetro';
        cancelEditButton.style.display = 'none';
    }

    // Manejar el envío del formulario (Añadir/Editar)
    parametroForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const id = parametroIdInput.value;
        const nombre_parametro = nombreParametroInput.value.trim();
        const valor_parametro = valorParametroInput.value.trim();
        const tipo_dato = tipoDatoSelect.value || null; // Si no selecciona, enviar null
        const descripcion = descripcionTextarea.value.trim() || null; // Si vacío, enviar null

        const data = {
            nombre_parametro,
            valor_parametro,
            tipo_dato,
            descripcion
        };

        try {
            let response;
            if (id) {
                // Editar existente
                response = await fetch(`${API_BASE_URL}/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                // Añadir nuevo
                response = await fetch(API_BASE_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            showMessage(id ? 'Parámetro actualizado exitosamente.' : 'Parámetro añadido exitosamente.', 'success');
            resetForm();
            loadParametros(); // Recargar la tabla
        } catch (error) {
            console.error('Error al guardar parámetro:', error);
            showMessage(`Error al guardar parámetro: ${error.message}`, 'error');
        }
    });

    // Manejar clics en los botones de la tabla (Editar/Eliminar)
    parametrosTableBody.addEventListener('click', async (event) => {
        const target = event.target;
        const paramId = target.dataset.id;

        if (target.classList.contains('edit')) {
            // Cargar datos para edición
            try {
                const response = await fetch(`${API_BASE_URL}/${paramId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const param = await response.json();
                parametroIdInput.value = param.id;
                nombreParametroInput.value = param.nombre_parametro;
                valorParametroInput.value = param.valor_parametro;
                tipoDatoSelect.value = param.tipo_dato || '';
                descripcionTextarea.value = param.descripcion || '';
                submitButton.textContent = 'Actualizar Parámetro';
                cancelEditButton.style.display = 'inline-block';
            } catch (error) {
                console.error('Error al cargar parámetro para edición:', error);
                showMessage('Error al cargar parámetro para edición.', 'error');
            }
        } else if (target.classList.contains('delete')) {
            // Eliminar parámetro
            if (confirm('¿Está seguro de que desea eliminar este parámetro?')) {
                try {
                    const response = await fetch(`${API_BASE_URL}/${paramId}`, {
                        method: 'DELETE'
                    });
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                    }
                    showMessage('Parámetro eliminado exitosamente.', 'success');
                    loadParametros(); // Recargar la tabla
                } catch (error) {
                    console.error('Error al eliminar parámetro:', error);
                    showMessage(`Error al eliminar parámetro: ${error.message}`, 'error');
                }
            }
        }
    });

    // Manejar el botón de cancelar edición
    cancelEditButton.addEventListener('click', resetForm);

    // Cargar los parámetros al cargar la página
    loadParametros();
});