// Función para cargar la lista de documentos desde el backend
function loadDocumentList() {
  fetch('/documents')
    .then(response => response.json())
    .then(data => {
      const list = document.getElementById('documentList');
      list.innerHTML = ''; // Limpiar la lista existente

      // Mostrar documentos (se asume que "todos" es la clave del JSON)
      data.todos.forEach((doc) => {
        const li = document.createElement('li');
        li.textContent = doc;
        li.style.cursor = 'pointer';
        // Al hacer clic, se carga la vista previa del PDF
        li.addEventListener('click', () => {
          const url = `/document/todos/${doc}`;
          console.log("Clic en documento:", url);
          loadPDF(url);
        });
        list.appendChild(li);
      });
    })
    .catch(error => console.error('Error cargando documentos:', error));
}

// Función para renderizar el PDF usando PDF.js en el canvas de vista previa
function loadPDF(url) {
  console.log("Cargando PDF desde:", url);
  const canvas = document.getElementById('pdfPreview');
  if (!canvas) {
    console.error("No se encontró el canvas 'pdfPreview'");
    return;
  }
  const ctx = canvas.getContext('2d');

  // Configurar PDF.js: establecer la ruta del worker
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://mozilla.github.io/pdf.js/build/pdf.worker.js';

  // Cargar el documento PDF
  pdfjsLib.getDocument(url).promise.then(pdf => {
    console.log("PDF cargado. Número de páginas:", pdf.numPages);
    // Renderiza la primera página
    pdf.getPage(1).then(page => {
      const scale = 1.5;
      const viewport = page.getViewport({ scale: scale });
      console.log("Viewport:", viewport);
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const renderContext = {
        canvasContext: ctx,
        viewport: viewport
      };

      page.render(renderContext).promise.then(() => {
        console.log("Página renderizada correctamente.");
      }).catch(err => {
        console.error("Error al renderizar la página:", err);
      });
    }).catch(err => {
      console.error("Error al obtener la página 1 del PDF:", err);
    });
  }).catch(error => {
    console.error('Error al cargar el PDF:', error);
  });
}

// Manejar el envío del formulario para subir documentos
document.getElementById('uploadForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const formData = new FormData(this);

  fetch('/upload', {
    method: 'POST',
    body: formData
  })
    .then(response => response.json())
    .then(result => {
      // Mostrar mensaje de confirmación o error
      document.getElementById('uploadMessage').textContent = result.message || result.error;
      // Recargar la lista después de subir el documento
      loadDocumentList();
    })
    .catch(error => console.error('Error al subir el documento:', error));
});

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  loadDocumentList();
});
