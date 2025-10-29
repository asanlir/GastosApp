# 🚀 Guía de Deployment

## Visión General

Esta guía cubre el deployment de la aplicación de **Gestión de Gastos** en diferentes entornos: local, Heroku y Docker.

---

## Tabla de Contenidos

- [Pre-requisitos](#pre-requisitos)
- [1. Deployment Local](#1-deployment-local)
- [2. Deployment en Heroku](#2-deployment-en-heroku)
- [3. Deployment con Docker](#3-deployment-con-docker)
- [4. Configuración de Base de Datos](#4-configuración-de-base-de-datos)
- [5. Variables de Entorno](#5-variables-de-entorno)
- [6. Monitoreo y Logs](#6-monitoreo-y-logs)
- [7. Backups](#7-backups)
- [8. Troubleshooting](#8-troubleshooting)

---

## Pre-requisitos

### Software Requerido

| Herramienta     | Versión Mínima | Propósito                |
|-----------------|----------------|--------------------------|
| Python          | 3.11+          | Runtime de aplicación    |
| MySQL           | 8.0+           | Base de datos            |
| Git             | 2.0+           | Control de versiones     |
| pip             | 23.0+          | Gestor de paquetes       |

### Conocimientos Recomendados

- Bash/PowerShell básico
- Git básico
- Configuración de servidores web
- Conceptos de networking (puertos, DNS)

---

## 1. Deployment Local

### 1.1 Instalación Inicial

#### Windows

```powershell
# 1. Clonar repositorio
git clone https://github.com/asanlir/gastos-casa.git
cd gastos-casa

# 2. Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar MySQL (ver sección 4)

# 5. Crear archivo .env (ver sección 5)

# 6. Inicializar base de datos
mysql -u root -p < database/schema.sql
mysql -u root -p gastos_db < database/seed.sql
```

#### Linux/macOS

```bash
# 1. Clonar repositorio
git clone https://github.com/asanlir/gastos-casa.git
cd gastos-casa

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar MySQL (ver sección 4)

# 5. Crear archivo .env (ver sección 5)

# 6. Inicializar base de datos
mysql -u root -p < database/schema.sql
mysql -u root -p gastos_db < database/seed.sql
```

---

### 1.2 Ejecutar con Waitress (Producción Local)

**Waitress** es un servidor WSGI production-ready para Windows/Linux.

```bash
# Instalar waitress
pip install waitress

# Ejecutar servidor
waitress-serve --host=127.0.0.1 --port=8080 app:app
```

**Acceder a la aplicación**: http://localhost:8080

---

### 1.3 Ejecutar con Flask Dev Server (Solo Desarrollo)

```bash
# Modo debug
python run.py
```

⚠️ **NUNCA usar en producción** - el dev server no es seguro ni eficiente.

---

### 1.4 Ejecutar como Servicio de Windows

```powershell
# Crear servicio con NSSM
nssm install GastosCasa "C:\path\to\venv\Scripts\python.exe" "C:\path\to\run.py"
nssm set GastosCasa AppDirectory "C:\path\to\gastos-casa"
nssm start GastosCasa
```

---

### 1.5 Auto-iniciar con el Sistema (Linux)

```bash
# Crear archivo de servicio systemd
sudo nano /etc/systemd/system/gastos.service
```

**Contenido**:

```ini
[Unit]
Description=Gastos Casa Flask App
After=network.target mysql.service

[Service]
User=usuario
WorkingDirectory=/home/usuario/gastos-casa
Environment="PATH=/home/usuario/gastos-casa/venv/bin"
ExecStart=/home/usuario/gastos-casa/venv/bin/waitress-serve --host=127.0.0.1 --port=8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Activar**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gastos.service
sudo systemctl start gastos.service
sudo systemctl status gastos.service
```

---

## 2. Deployment en Heroku

### 2.1 Preparación

#### Archivos Requeridos

1. **`Procfile`** (ya incluido):

```
web: waitress-serve --port=$PORT app:app
```

2. **`requirements.txt`** (ya incluido)

3. **`runtime.txt`** (crear si no existe):

```
python-3.11.9
```

---

### 2.2 Proceso de Deployment

```bash
# 1. Instalar Heroku CLI
# Windows: https://devcenter.heroku.com/articles/heroku-cli
# macOS: brew install heroku/brew/heroku
# Linux: curl https://cli-assets.heroku.com/install.sh | sh

# 2. Login
heroku login

# 3. Crear aplicación
heroku create gastos-casa-app

# 4. Agregar MySQL (JawsDB)
heroku addons:create jawsdb:kitefin

# 5. Obtener credenciales de BD
heroku config:get JAWSDB_URL
# Formato: mysql://usuario:password@host:puerto/database

# 6. Configurar variables de entorno
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=tu-secret-key-generado

# 7. Deploy
git push heroku main

# 8. Inicializar BD (una sola vez)
heroku run bash
mysql -h host -u usuario -p database < database/schema.sql
exit

# 9. Abrir app
heroku open
```

---

### 2.3 Configuración de JawsDB

**Extraer credenciales**:

```bash
heroku config:get JAWSDB_URL
# Output: mysql://user:pass@host.jawsdb.com:3306/dbname
```

**Agregar a `.env` (local)**:

```env
# Heroku Production
DB_HOST=host.jawsdb.com
DB_USER=user
DB_PASSWORD=pass
DB_NAME=dbname
DB_PORT=3306
```

---

### 2.4 Monitoreo en Heroku

```bash
# Ver logs en tiempo real
heroku logs --tail

# Ver logs de errores
heroku logs --source app

# Escalar dynos
heroku ps:scale web=1

# Reiniciar app
heroku restart
```

---

## 3. Deployment con Docker

### 3.1 Dockerfile

**Crear `Dockerfile`**:

```dockerfile
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8080

# Comando de inicio
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]
```

---

### 3.2 Docker Compose

**Crear `docker-compose.yml`**:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - DB_HOST=db
      - DB_USER=gastos_user
      - DB_PASSWORD=gastos_pass
      - DB_NAME=gastos_db
      - DB_PORT=3306
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: gastos_db
      MYSQL_USER: gastos_user
      MYSQL_PASSWORD: gastos_pass
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./database/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql
    restart: unless-stopped

volumes:
  db_data:
```

---

### 3.3 Comandos Docker

```bash
# Build
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Detener servicios
docker-compose down

# Reiniciar solo web
docker-compose restart web

# Acceder a contenedor
docker-compose exec web bash

# Ver base de datos
docker-compose exec db mysql -u gastos_user -p gastos_db
```

**Acceder a la aplicación**: http://localhost:8080

---

### 3.4 Docker en Producción

**Recomendaciones**:

1. **Usar volúmenes para logs**:

```yaml
volumes:
  - ./logs:/app/logs
```

2. **Configurar límites de recursos**:

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
```

3. **Usar secrets para credenciales**:

```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## 4. Configuración de Base de Datos

### 4.1 MySQL Local

#### Windows

```powershell
# Instalar MySQL
# https://dev.mysql.com/downloads/installer/

# Crear base de datos
mysql -u root -p
```

```sql
CREATE DATABASE gastos_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gastos_user'@'localhost' IDENTIFIED BY 'gastos_pass';
GRANT ALL PRIVILEGES ON gastos_db.* TO 'gastos_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### Linux

```bash
# Instalar MySQL
sudo apt-get install mysql-server

# Iniciar servicio
sudo systemctl start mysql
sudo systemctl enable mysql

# Crear base de datos
sudo mysql
```

```sql
CREATE DATABASE gastos_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gastos_user'@'localhost' IDENTIFIED BY 'gastos_pass';
GRANT ALL PRIVILEGES ON gastos_db.* TO 'gastos_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### 4.2 Inicializar Schema

```bash
# Importar schema
mysql -u gastos_user -p gastos_db < database/schema.sql

# Importar datos semilla (opcional)
mysql -u gastos_user -p gastos_db < database/seed.sql

# Agregar índices (recomendado)
mysql -u gastos_user -p gastos_db < database/add_indexes.sql
```

---

### 4.3 Verificar Instalación

```bash
# Conectar a BD
mysql -u gastos_user -p gastos_db

# Listar tablas
SHOW TABLES;

# Ver estructura
DESCRIBE gastos;
DESCRIBE categorias;
DESCRIBE presupuesto;

# Contar registros
SELECT COUNT(*) FROM categorias;
```

---

## 5. Variables de Entorno

### 5.1 Archivo .env Local

**Crear `.env` en raíz del proyecto**:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DB_HOST=localhost
DB_USER=gastos_user
DB_PASSWORD=gastos_pass
DB_NAME=gastos_db
DB_PORT=3306

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log

# App Configuration
HOST=127.0.0.1
PORT=5000
AUTO_OPEN_BROWSER=true
```

---

### 5.2 Variables por Entorno

#### Development

```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key
LOG_LEVEL=DEBUG
AUTO_OPEN_BROWSER=true
```

#### Testing

```env
FLASK_ENV=testing
DB_NAME=gastos_test
LOG_LEVEL=WARNING
AUTO_OPEN_BROWSER=false
```

#### Production

```env
FLASK_ENV=production
SECRET_KEY=<generar-con-secrets.token_urlsafe(32)>
LOG_LEVEL=WARNING
AUTO_OPEN_BROWSER=false
DB_HOST=<ip-o-dominio-de-produccion>
```

---

### 5.3 Generar SECRET_KEY

```python
# Python
import secrets
print(secrets.token_urlsafe(32))
```

```bash
# Bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Output**:
```
kR8nF3mQ7vL2pW9xE5tY1oU6sI4aZ0cB3jH8gD7fV2n
```

---

## 6. Monitoreo y Logs

### 6.1 Logs de Aplicación

**Ubicación**: `logs/app.log`

**Rotación**: Automática (10 MB, 5 backups)

**Ver logs en tiempo real**:

```bash
# Windows
Get-Content logs\app.log -Wait -Tail 50

# Linux/macOS
tail -f logs/app.log
```

---

### 6.2 Niveles de Log

| Nivel     | Desarrollo | Testing | Producción |
|-----------|------------|---------|------------|
| DEBUG     | ✅         | ❌      | ❌         |
| INFO      | ✅         | ✅      | ❌         |
| WARNING   | ✅         | ✅      | ✅         |
| ERROR     | ✅         | ✅      | ✅         |
| CRITICAL  | ✅         | ✅      | ✅         |

---

### 6.3 Analizar Logs

```bash
# Buscar errores
grep "ERROR" logs/app.log

# Contar warnings
grep -c "WARNING" logs/app.log

# Ver últimas 100 líneas
tail -n 100 logs/app.log

# Filtrar por fecha
grep "2025-10-29" logs/app.log
```

---

### 6.4 Herramientas de Monitoreo

#### Sentry (Recomendado)

```bash
# Instalar
pip install sentry-sdk[flask]
```

```python
# app/__init__.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://tu-dsn.sentry.io",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

#### NewRelic

```bash
pip install newrelic
newrelic-admin generate-config YOUR_LICENSE_KEY newrelic.ini
newrelic-admin run-program waitress-serve app:app
```

---

## 7. Backups

### 7.1 Backup Automático (PowerShell)

**Script**: `scripts/backup_db.ps1` (ya incluido)

```powershell
# Ejecutar backup manual
.\scripts\backup_db.ps1
```

**Configurar tarea programada**:

```powershell
# Ejecutar script de setup
.\scripts\setup_backup_task.ps1
```

**Resultado**: Backup diario a las 02:00 AM en `scripts/backups/daily/`

---

### 7.2 Backup Manual

```bash
# MySQL dump
mysqldump -u gastos_user -p gastos_db > backup_$(date +%Y%m%d).sql

# Con compresión
mysqldump -u gastos_user -p gastos_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

### 7.3 Restaurar Backup

```bash
# Desde archivo SQL
mysql -u gastos_user -p gastos_db < backup_20251029.sql

# Desde archivo comprimido
gunzip < backup_20251029.sql.gz | mysql -u gastos_user -p gastos_db
```

---

### 7.4 Backup en Heroku

```bash
# Crear backup
heroku addons:create jawsdb:kitefin

# Descargar backup
heroku run bash
mysqldump -h host -u user -p database > backup.sql
exit

# Alternativa: usar heroku pg:backups (para PostgreSQL)
```

---

## 8. Troubleshooting

### 8.1 Error: "Can't connect to MySQL server"

**Síntomas**:
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**Causas y Soluciones**:

1. **MySQL no está corriendo**:
   ```bash
   # Windows
   net start MySQL80
   
   # Linux
   sudo systemctl start mysql
   ```

2. **Credenciales incorrectas**:
   - Verificar `.env`
   - Probar conexión manual: `mysql -u gastos_user -p`

3. **Host incorrecto**:
   - Cambiar `DB_HOST=localhost` a `DB_HOST=127.0.0.1`

---

### 8.2 Error: "Table doesn't exist"

**Síntomas**:
```
pymysql.err.ProgrammingError: (1146, "Table 'gastos_db.gastos' doesn't exist")
```

**Solución**:
```bash
# Importar schema
mysql -u gastos_user -p gastos_db < database/schema.sql
```

---

### 8.3 Error: "Port 5000 already in use"

**Síntomas**:
```
OSError: [WinError 10048] Only one usage of each socket address
```

**Solución**:

```bash
# Windows: Encontrar proceso usando puerto 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :5000
kill -9 <PID>

# Alternativa: cambiar puerto en .env
PORT=8080
```

---

### 8.4 Error: "ModuleNotFoundError"

**Síntomas**:
```
ModuleNotFoundError: No module named 'flask'
```

**Solución**:

```bash
# Activar entorno virtual
# Windows
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

---

### 8.5 Error: "Secret key required"

**Síntomas**:
```
RuntimeError: The session is unavailable because no secret key was set.
```

**Solución**:

```bash
# Generar y agregar a .env
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Agregar a .env
SECRET_KEY=<key-generada>
```

---

### 8.6 Logs no se generan

**Causas**:

1. **Directorio `logs/` no existe**:
   ```bash
   mkdir logs
   ```

2. **Permisos insuficientes**:
   ```bash
   # Linux
   chmod 755 logs/
   ```

3. **LOG_FILE mal configurado**:
   ```env
   LOG_FILE=logs/app.log  # Path relativo
   ```

---

### 8.7 Performance lenta

**Diagnóstico**:

1. **Verificar índices**:
   ```sql
   SHOW INDEX FROM gastos;
   ```

2. **Agregar índices faltantes**:
   ```bash
   mysql -u gastos_user -p gastos_db < database/add_indexes.sql
   ```

3. **Analizar queries lentas**:
   ```sql
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;
   ```

---

## 9. Checklist de Deployment

### Pre-Deployment

- [ ] Tests pasan: `pytest`
- [ ] Linting OK: `ruff check .`
- [ ] `.env.example` actualizado
- [ ] README actualizado
- [ ] Changelog actualizado
- [ ] Backup de BD de producción

### Deployment

- [ ] Variables de entorno configuradas
- [ ] Base de datos inicializada
- [ ] Índices creados
- [ ] Logs configurados
- [ ] Backup automático activado

### Post-Deployment

- [ ] Aplicación accesible
- [ ] Login funciona
- [ ] CRUD de gastos funciona
- [ ] Reportes se generan
- [ ] Logs se están escribiendo
- [ ] Monitoreo activo

---

## 10. Recursos Adicionales

### Documentación Oficial

- [Flask Deployment](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Waitress Documentation](https://docs.pylonsproject.org/projects/waitress/)
- [Heroku Python](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Docker Documentation](https://docs.docker.com/)
- [MySQL Documentation](https://dev.mysql.com/doc/)

### Tutoriales

- [Deploy Flask to Heroku](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Flask + Docker](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
- [Production Flask Apps](https://realpython.com/flask-by-example-part-1-project-setup/)

---

**Última actualización**: 29 de octubre de 2025
