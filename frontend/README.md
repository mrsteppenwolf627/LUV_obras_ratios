# LUV Obras Ratios - Frontend

Este es el panel de control (Dashboard) para el sistema de análisis de ratios de LUV Studio. Construido con React 18, TypeScript y Tailwind CSS, siguiendo la identidad visual de "Luxury of Precision".

## Tecnologías

- **React 18** + **Vite**
- **TypeScript** para seguridad de tipos
- **Tailwind CSS** para estilos elegantes y responsivos
- **Recharts** para visualización de datos
- **Lucide React** para iconografía
- **React Toastify** para notificaciones
- **Axios** para comunicación con el Backend

## Requisitos

- Node.js 18+
- Backend activo en `http://localhost:8000`

## Instalación y Uso

1. Instalar dependencias:
   ```bash
   npm install
   ```

2. Iniciar en modo desarrollo:
   ```bash
   npm run dev
   ```

3. El dashboard estará disponible en `http://localhost:5173`.

## Estructura

- `/import`: Subida de archivos .xlsx y .bc3.
- `/master`: Tabla consolidada con filtros de búsqueda y validación.
- `/archived`: Historial de importaciones con trazabilidad SHA-256.
- `/ratios`: Gráficos de distribución y tendencias.

## Identidad Visual

- **Primario:** #1a1a1a (Negro)
- **Acento:** #8b7355 (Taupe/Tierra)
- **Secundario:** #f5f2f0 (Beige)
- **Tipografía:** Playfair Display (Serif) & Montserrat (Sans)
