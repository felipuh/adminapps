# Linea Base Frontend + Prompt Maestro (AdminApps)

## Objetivo
Estandarizar evolucion frontend con mejoras visuales, accesibilidad y rendimiento sin romper la operacion actual.

## Reglas de Compatibilidad
1. No modificar endpoints ni contratos del cliente API.
2. No romper rutas de Router ni navegacion interna.
3. Mantener integracion de autenticacion y renovacion de token.
4. Preservar estructura de layout (Sidebar/Header/Main).

## Estandar UI/UX
1. Coherencia visual en cards, tablas, formularios y acciones.
2. Componentes con estados: normal, hover, focus, disabled, loading.
3. Espaciado y jerarquia consistentes por tipo de vista.
4. Mensajeria UX clara para operaciones largas o criticas.

## Accesibilidad Operativa
1. Skip link a contenido principal.
2. aria-expanded, aria-controls y aria-haspopup en menus.
3. Cierre por Escape en dropdowns/paneles.
4. Focus visible y navegacion por teclado en toda accion.
5. reduced-motion respetado en animaciones.

## UX de Datos y Tablas
1. Tabla siempre con:
- loading visual
- empty state explicativo
- error state recuperable
2. Acciones destructivas con confirmacion.
3. Feedback post-accion inmediato (toast o estado inline).

## Performance Baseline
1. Separacion de responsabilidades por pagina/componente.
2. Evitar renders en cascada por props inestables.
3. Carga progresiva para paneles secundarios.
4. Reutilizar estilos utilitarios en lugar de duplicar bloques.

## Checklist de PR
- [ ] Flujo de login/logout intacto.
- [ ] Rutas principales intactas.
- [ ] Menus y overlays accesibles por teclado.
- [ ] Estados loading/empty/error cubiertos.
- [ ] Build local OK.

## Prompt Maestro para Nuevos Proyectos
"Actua como Frontend Tech Lead Senior para un panel administrativo B2B en React.

Restricciones:
- No romper rutas, autenticacion, contratos de API ni permisos por rol.
- Mantener estructura de layout existente.

Tareas:
1) Modernizar UI con consistencia profesional.
2) Reforzar accesibilidad real (teclado, ARIA, focus visible, reduced motion).
3) Mejorar UX de feedback en cargas, errores y operaciones.
4) Optimizar componentes para escalabilidad y mantenimiento.

Entregables:
- Cambios seguros por archivo.
- Explicacion de impacto funcional y visual.
- Checklist de regresion.
- Recomendaciones fase 2 para arquitectura de componentes."