# 💰 Sistema de Control de Gastos Domésticos

Sistema web completo para gestionar gastos personales/familiares con reportes visuales, presupuestos y backups automáticos.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-62%20passing-brightgreen.svg)]()

## 📋 Descripción

Aplicación web Flask para el seguimiento y análisis de gastos domésticos con:

- **Dashboard intuitivo** con resumen mensual de gastos
- **Gráficos interactivos** (Plotly) para visualizar tendencias
- **Presupuestos configurables** con alertas de sobrecosto
- **Backups automáticos** programados de la base de datos
- **Tests completos** (54 unitarios + 8 de integración)

Ideal para llevar control de gastos familiares, analizar patrones de consumo y mantenerse dentro del presupuesto.

---

## ✨ Características Principales

### 🏠 Dashboard de Gastos

- Vista mensual de todos los gastos con totales
- Filtros por mes, año y categoría
- Comparación automática con presupuesto
- Alertas visuales de sobrecosto

### 📊 Reportes y Estadísticas

- **Gráfico de torta**: Distribución de gastos por categoría
- **Gráficos de barras**: Evolución histórica (12 meses)
- **Comparativa presupuesto**: Gastos vs presupuesto mensual
- Análisis por categorías: Compra, Facturas, Gasolina, etc.

### ⚙️ Configuración Flexible

- Gestión de categorías personalizables
- Presupuestos mensuales configurables
- Histórico completo de gastos

### 💾 Sistema de Backups

- Backups automáticos programados (3:00 AM)
- Compresión con WinRAR
- Sincronización automática a OneDrive
- Rotación inteligente (7 diarios / 4 semanales / 12 mensuales)

### 🧪 Calidad de Código

- 62 tests (54 unitarios + 8 de integración)
- Cobertura completa de servicios y queries
- CI/CD con GitHub Actions
- Linting con flake8

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.11+
- MySQL 8.0+
- WinRAR (para backups en Windows)
- Git

### 1. Clonar el Repositorio

```bash
git clone https://github.com/asanlir/gastos_refactor.git
cd gastos_refactor
```

### 2. Configurar Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos

```bash
# Crear base de datos
mysql -u root -p

CREATE DATABASE economia_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE economia_db;

# Ejecutar scripts de base de datos
SOURCE database/schema.sql;
SOURCE database/add_indexes.sql;
SOURCE database/seed.sql;  # Opcional: datos de ejemplo
```

### 5. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=economia_db
DB_PORT=3306

# Flask
SECRET_KEY=tu_clave_secreta_aqui

# Logging (opcional)
LOG_LEVEL=INFO
```

### 6. Iniciar la Aplicación

```bash
python app.py
```

La aplicación estará disponible en: **http://127.0.0.1:5000**

---

## 📁 Estructura del Proyecto

```
gastos_refactor/
├── app/                        # Paquete principal de la aplicación
│   ├── __init__.py            # Factory de Flask
│   ├── config.py              # Configuración por entornos
│   ├── constants.py           # Constantes globales
│   ├── database.py            # Gestión de conexiones BD
│   ├── exceptions.py          # Excepciones personalizadas
│   ├── logging_config.py      # Configuración de logs
│   ├── queries.py             # Queries SQL centralizadas
│   ├── utils.py               # Funciones auxiliares
│   ├── utils_df.py            # Utilidades para DataFrames
│   ├── routes/                # Rutas Flask
│   │   └── main.py            # Endpoints principales
│   └── services/              # Lógica de negocio
│       ├── gastos_service.py
│       ├── categorias_service.py
│       ├── presupuesto_service.py
│       └── charts_service.py
├── database/                   # Scripts de base de datos
│   ├── schema.sql             # Estructura de tablas
│   ├── add_indexes.sql        # Índices optimizados
│   ├── seed.sql               # Datos iniciales
│   └── INDEXES.md             # Documentación de índices
├── scripts/                    # Scripts de utilidad
│   ├── backup_db.ps1          # Backup de base de datos
│   ├── setup_backup_task.ps1  # Configurar tarea programada
│   └── sync_to_cloud.ps1      # Sincronización OneDrive
├── static/                     # Archivos estáticos
│   └── styles.css             # Estilos CSS
├── templates/                  # Templates HTML
│   ├── index.html             # Dashboard principal
│   ├── gastos.html            # Histórico de gastos
│   ├── report.html            # Reportes y gráficos
│   └── config.html            # Configuración
├── tests/                      # Tests automatizados
│   ├── conftest.py            # Configuración pytest
│   ├── test_endpoints.py      # Tests de integración
│   ├── test_services.py       # Tests unitarios servicios
│   ├── test_queries.py        # Tests unitarios queries
│   └── test_utils.py          # Tests utilidades
├── logs/                       # Logs de la aplicación (generado)
├── app.py                      # Punto de entrada
├── requirements.txt            # Dependencias producción
├── requirements-dev.txt        # Dependencias desarrollo
└── .env                        # Variables de entorno (no versionado)
```

---

## 🎯 Uso

### Agregar un Gasto

1. En el dashboard, hacer clic en **"Agregar Gasto"**
2. Seleccionar categoría, descripción y monto
3. Seleccionar mes y año
4. Hacer clic en **"Guardar Gasto"**

### Ver Reportes

1. Ir a **"Estadísticas"** en el menú lateral
2. Seleccionar mes y año
3. Ver gráficos interactivos de distribución y evolución

### Configurar Presupuesto

1. Ir a **"Configuración"** en el menú lateral
2. En la sección "Presupuesto", ingresar monto mensual
3. Seleccionar mes y año
4. Hacer clic en **"Guardar Presupuesto"**

### Gestionar Categorías

1. Ir a **"Configuración"**
2. Agregar nueva categoría o eliminar existentes
3. Las categorías se aplican inmediatamente

---

## 🧪 Testing

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
pytest tests/

# Solo tests unitarios (sin base de datos)
pytest tests/ -m "not integration"

# Tests con cobertura
pytest tests/ --cov=app --cov-report=html

# Tests específicos
pytest tests/test_services.py -v
```

### Cobertura de Tests

- ✅ **54 tests unitarios**: Servicios, queries, utilidades
- ✅ **8 tests de integración**: Endpoints y flujos completos
- ✅ **CI/CD**: GitHub Actions ejecuta tests automáticamente

---

## 💾 Sistema de Backups

### ⚠️ Gestión Segura de Base de Datos

**IMPORTANTE**: Para evitar pérdida accidental de datos, consulta la guía completa:

📖 **[docs/DATABASE_MANAGEMENT.md](docs/DATABASE_MANAGEMENT.md)** - Guía de Gestión de Base de Datos

**Reglas básicas:**

```bash
# ✅ Para verificar el estado de la BD
python check_db.py

# ✅ Para agregar una tabla específica (SEGURO con datos existentes)
python add_table.py presupuesto

# ❌ NO ejecutar con datos existentes (puede causar pérdida)
python init_db.py  # Solo para BD vacías
```

### Configuración de Backups Automáticos

```powershell
# Ejecutar como Administrador
cd scripts
.\setup_backup_task.ps1
```

Esto creará una tarea programada de Windows que:

- Se ejecuta diariamente a las 3:00 AM
- Hace backup de la base de datos con `mysqldump`
- Comprime el backup con WinRAR
- Sincroniza a OneDrive automáticamente
- Mantiene rotación de backups (7/4/12)

### Backup Manual

```powershell
.\scripts\backup_db.ps1
```

### Restaurar Backup

```bash
# Descomprimir el archivo
# Luego:
mysql -u root -p economia_db < backup_file.sql
```

---

## 🏗️ Arquitectura

### Patrón de Diseño

La aplicación sigue una **arquitectura en capas**:

1. **Presentación** (`routes/`): Endpoints Flask
2. **Lógica de Negocio** (`services/`): Servicios reutilizables
3. **Acceso a Datos** (`queries.py`): Queries SQL parametrizadas
4. **Base de Datos**: MySQL con índices optimizados

### Decisiones Técnicas

- **Factory Pattern**: `create_app()` permite múltiples entornos
- **Dependency Injection**: Servicios desacoplados
- **Query Builders**: SQL centralizado y seguro (anti-SQL injection)
- **Context Managers**: Gestión automática de conexiones BD
- **Excepciones Tipadas**: Manejo de errores específico

---

## 🔧 Configuración Avanzada

### Entornos

```python
# Desarrollo (default)
app = create_app('development')  # DEBUG=True, LOG_LEVEL=DEBUG

# Producción
app = create_app('production')   # DEBUG=False, LOG_LEVEL=WARNING

# Testing
app = create_app('testing')      # TESTING=True, test_economia_db
```

### Logging

Los logs se guardan en `logs/gastos.log` con rotación automática:

- **DEBUG**: Desarrollo (todas las operaciones)
- **INFO**: Producción (operaciones importantes)
- **WARNING**: Solo errores y advertencias

```python
# Cambiar nivel de logging
# En .env:
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## 🚢 Deployment

### Opción 1: Servidor Local (Windows)

```bash
# Producción con Waitress
pip install waitress
waitress-serve --port=5000 app:app
```

### Opción 2: Heroku

```bash
# Asegurarse de tener Procfile
heroku create tu-app-gastos
heroku addons:create jawsdb:kitefin  # MySQL en Heroku
git push heroku main
```

### Opción 3: Docker

```dockerfile
# Dockerfile (ejemplo)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código

- Seguir PEP 8
- Añadir docstrings a funciones públicas
- Escribir tests para nuevas features
- Mantener cobertura de tests > 80%

---

## 📝 Changelog

### v2.1.0 (2025-10-30)

**✨ Finalización refactorización y mejoras UX**

- 🎨 Mejoras de Experiencia de Usuario
- 🛡️ Protección de Datos
- 🧹 Limpieza y Optimización
- ✅ Calidad: 68/68 tests pasando
- 🚀 Lista para producción


### v2.0.0 (2025-01-29)

- ✨ **Refactor completo** a arquitectura modular
- 🧪 Suite completa de 62 tests
- 📊 Sistema de logging robusto
- 🔒 Excepciones tipadas y manejo de errores
- 💾 Sistema de backups automáticos
- 📚 Documentación completa


### v1.0.0 (2024-xx-xx)

- 🎉 Versión inicial monolítica

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 👤 Autor

**Alejandro Sánchez**

- GitHub: [@asanlir](https://github.com/asanlir)
- Repository: [gastos_refactor](https://github.com/asanlir/gastos_refactor)

---

## 🙏 Agradecimientos

- [Flask](https://flask.palletsprojects.com/) - Framework web
- [Plotly](https://plotly.com/python/) - Gráficos interactivos
- [PyMySQL](https://pymysql.readthedocs.io/) - Connector MySQL
- [Pytest](https://pytest.org/) - Framework de testing

---

## 📞 Soporte

Si encuentras algún problema o tienes sugerencias:

- 🐛 [Reportar un bug](https://github.com/asanlir/gastos_refactor/issues)
- 💡 [Solicitar una feature](https://github.com/asanlir/gastos_refactor/issues)
- 📧 Contacto: [Crear issue en GitHub]

---

**⭐ Si este proyecto te fue útil, considera darle una estrella!**
