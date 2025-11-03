# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir al Sistema de Control de Gastos Domésticos! Este documento te guiará en el proceso.

## 📋 Código de Conducta

- Sé respetuoso y profesional en todas las interacciones
- Acepta críticas constructivas de forma positiva
- Enfócate en lo que es mejor para la comunidad
- Muestra empatía hacia otros miembros de la comunidad

## 🚀 Cómo Contribuir

### Reportar Bugs

Si encuentras un bug, por favor abre un issue con:

1. **Título descriptivo**: Resume el problema en una línea
2. **Pasos para reproducir**: Lista detallada de pasos
3. **Comportamiento esperado**: Qué debería pasar
4. **Comportamiento actual**: Qué está pasando
5. **Entorno**: Sistema operativo, versión de Python, versión de MySQL
6. **Capturas de pantalla**: Si es relevante

### Sugerir Mejoras

Para sugerir nuevas funcionalidades o mejoras:

1. Verifica que no exista ya un issue similar
2. Abre un issue describiendo:
   - El problema que resuelve
   - La solución propuesta
   - Alternativas consideradas
   - Impacto en usuarios existentes

### Pull Requests

1. **Fork el repositorio** y crea tu rama desde `main`:

   ```bash
   git checkout -b feature/nombre-descriptivo
   ```

2. **Configura el entorno de desarrollo**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   pip install -r requirements-dev.txt
   ```

3. **Realiza tus cambios**:

   - Sigue las convenciones de código existentes
   - Añade tests para nuevas funcionalidades
   - Actualiza la documentación si es necesario

4. **Ejecuta los tests**:

   ```bash
   pytest tests/
   ```

5. **Verifica el linting**:

   ```bash
   flake8 app/ tests/
   ```

6. **Commit con mensajes descriptivos**:

   ```bash
   git commit -m "feat: añadir funcionalidad X"
   ```

   Usa prefijos convencionales:

   - `feat:` - Nueva funcionalidad
   - `fix:` - Corrección de bug
   - `docs:` - Cambios en documentación
   - `style:` - Formato, sin cambios de código
   - `refactor:` - Refactorización de código
   - `test:` - Añadir o corregir tests
   - `chore:` - Mantenimiento, dependencias

7. **Push tu rama**:

   ```bash
   git push origin feature/nombre-descriptivo
   ```

8. **Abre un Pull Request** describiendo:
   - Qué cambios incluye
   - Por qué son necesarios
   - Cómo probarlos
   - Issues relacionados (si aplica)

## 📝 Estándares de Código

### Python

- **PEP 8**: Sigue las convenciones de estilo de Python
- **Docstrings**: Documenta funciones y clases
- **Type Hints**: Usa anotaciones de tipo cuando sea apropiado
- **Imports**: Ordena imports (stdlib, third-party, local)

Ejemplo:

```python
def calcular_total(gastos: list[dict]) -> float:
    """
    Calcula el total de una lista de gastos.

    Args:
        gastos: Lista de diccionarios con información de gastos

    Returns:
        Total sumado de todos los gastos
    """
    return sum(g['importe'] for g in gastos)
```

### Tests

- Escribe tests para toda nueva funcionalidad
- Mantén cobertura >80%
- Usa fixtures para datos de prueba
- Nombra tests descriptivamente: `test_descripcion_del_caso`

### Documentación

- Actualiza README.md si cambias funcionalidad visible
- Documenta cambios en archivos `docs/` relevantes
- Incluye comentarios inline para lógica compleja

## 🏗️ Estructura del Proyecto

```
gastos_refactor/
├── app/              # Código principal de la aplicación
│   ├── routes/       # Endpoints Flask
│   ├── services/     # Lógica de negocio
│   └── ...
├── database/         # Scripts SQL
├── docs/             # Documentación técnica
├── scripts/          # Scripts de utilidad
├── static/           # CSS, JS, imágenes
├── templates/        # Templates HTML
└── tests/            # Suite de tests
```

## 🔍 Proceso de Review

Los Pull Requests serán revisados considerando:

1. **Funcionalidad**: El código hace lo que dice
2. **Tests**: Hay tests adecuados y pasan
3. **Documentación**: Cambios están documentados
4. **Estilo**: Sigue las convenciones del proyecto
5. **Performance**: No introduce problemas de rendimiento
6. **Seguridad**: No introduce vulnerabilidades

## ❓ ¿Necesitas Ayuda?

- Abre un issue con la etiqueta `question`
- Revisa la [documentación](docs/)
- Consulta issues existentes

## 📜 Licencia

Al contribuir, aceptas que tus contribuciones se licenciarán bajo la [Licencia MIT](LICENSE).

---

¡Gracias por contribuir! 🎉
