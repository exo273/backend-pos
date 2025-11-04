# Comandos Esenciales - Backend POS

## 🚀 Inicio Rápido

### Primer despliegue
```bash
# 1. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar SECRET_KEY y passwords

# 2. Construir e iniciar
docker-compose build
docker-compose up -d

# 3. Esperar a que los servicios estén listos
sleep 60

# 4. Aplicar migraciones
docker-compose exec django python manage.py migrate

# 5. Crear superusuario
docker-compose exec django python manage.py createsuperuser

# 6. Crear datos de ejemplo (opcional)
docker-compose exec django python create_sample_data.py

# 7. Recolectar archivos estáticos
docker-compose exec django python manage.py collectstatic --noinput
```

---

## 📦 Gestión de Servicios

### Ver estado de servicios
```bash
docker-compose ps
```

### Ver logs
```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f django
docker-compose logs -f celery_worker
docker-compose logs -f celery_event_listener
```

### Reiniciar servicios
```bash
# Todos
docker-compose restart

# Específico
docker-compose restart django
docker-compose restart celery_worker
```

### Detener servicios
```bash
# Detener
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar TODO (¡CUIDADO! Borra la base de datos)
docker-compose down -v
```

---

## 🗄️ Base de Datos

### Migraciones
```bash
# Crear migraciones
docker-compose exec django python manage.py makemigrations

# Aplicar migraciones
docker-compose exec django python manage.py migrate

# Ver estado de migraciones
docker-compose exec django python manage.py showmigrations

# Revertir migración
docker-compose exec django python manage.py migrate app_name migration_name
```

### Backup
```bash
# Crear backup
docker-compose exec db mysqldump -u pos_user -p db_pos > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose exec -T db mysql -u pos_user -p db_pos < backup_20241201_120000.sql
```

### Acceder a MySQL
```bash
# Desde contenedor
docker-compose exec db mysql -u pos_user -p db_pos

# Ver tablas
SHOW TABLES;

# Salir
EXIT;
```

---

## 🐍 Django Commands

### Shell interactivo
```bash
docker-compose exec django python manage.py shell
```

```python
# Ejemplos en shell
from pos.models import Zone, Table
from orders.models import Order

# Listar zonas
Zone.objects.all()

# Crear zona
zone = Zone.objects.create(name="VIP", display_order=3)

# Listar órdenes del día
from django.utils import timezone
today = timezone.now().date()
Order.objects.filter(created_at__date=today)
```

### Crear superusuario
```bash
docker-compose exec django python manage.py createsuperuser
```

### Cambiar contraseña de usuario
```bash
docker-compose exec django python manage.py changepassword username
```

### Limpiar sesiones expiradas
```bash
docker-compose exec django python manage.py clearsessions
```

---

## 🧪 Tests

### Ejecutar todos los tests
```bash
docker-compose exec django python manage.py test
```

### Tests de una app específica
```bash
docker-compose exec django python manage.py test pos
docker-compose exec django python manage.py test menu
docker-compose exec django python manage.py test orders
docker-compose exec django python manage.py test catalog_mirror
```

### Tests con coverage
```bash
# Ejecutar con coverage
docker-compose exec django coverage run --source='.' manage.py test

# Ver reporte
docker-compose exec django coverage report

# Generar HTML
docker-compose exec django coverage html
```

### Test específico
```bash
docker-compose exec django python manage.py test pos.tests.TableAPITest.test_create_table
```

---

## 🔄 Celery

### Ver tareas activas
```bash
docker-compose exec celery_worker celery -A orders_service inspect active
```

### Ver tareas registradas
```bash
docker-compose exec celery_worker celery -A orders_service inspect registered
```

### Ver estadísticas
```bash
docker-compose exec celery_worker celery -A orders_service inspect stats
```

### Purgar todas las tareas pendientes (¡CUIDADO!)
```bash
docker-compose exec celery_worker celery -A orders_service purge
```

---

## 🐰 RabbitMQ

### Acceder a Management UI
```
http://localhost:15673/
Usuario: admin (o el configurado en .env)
Password: (el configurado en .env)
```

### Ver colas
```bash
docker-compose exec rabbitmq rabbitmqctl list_queues
```

### Ver exchanges
```bash
docker-compose exec rabbitmq rabbitmqctl list_exchanges
```

### Ver bindings
```bash
docker-compose exec rabbitmq rabbitmqctl list_bindings
```

---

## 🔧 Mantenimiento

### Actualizar código
```bash
# Detener servicios
docker-compose down

# Actualizar código (git pull o subir archivos)
git pull origin main

# Reconstruir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Aplicar migraciones si hay nuevas
docker-compose exec django python manage.py migrate
```

### Limpiar Docker
```bash
# Eliminar contenedores detenidos
docker container prune

# Eliminar imágenes no usadas
docker image prune

# Eliminar volúmenes no usados (¡CUIDADO!)
docker volume prune

# Limpieza completa
docker system prune -a
```

### Ver uso de recursos
```bash
# En tiempo real
docker stats

# Uso de disco
docker system df
```

---

## 📊 Monitoreo

### Logs en tiempo real con filtros
```bash
# Solo errores
docker-compose logs -f django | grep ERROR

# Solo warnings y errores
docker-compose logs -f django | grep -E 'ERROR|WARNING'

# Últimas 100 líneas
docker-compose logs --tail=100 django
```

### Verificar salud de servicios
```bash
# MySQL
docker-compose exec db mysqladmin ping -h localhost

# Redis
docker-compose exec redis redis-cli ping

# RabbitMQ
docker-compose exec rabbitmq rabbitmq-diagnostics ping
```

---

## 🌐 API Testing

### Con curl
```bash
# Obtener token
curl -X POST http://localhost:8001/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'

# Usar token (reemplazar YOUR_TOKEN)
curl http://localhost:8001/api/zones/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Crear zona
curl -X POST http://localhost:8001/api/zones/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Nueva Zona","display_order":1}'
```

### Con httpie (más legible)
```bash
# Instalar httpie
pip install httpie

# Obtener token
http POST http://localhost:8001/api/token/ username=admin password=yourpassword

# Listar zonas
http GET http://localhost:8001/api/zones/ "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Debugging

### Ver variables de entorno
```bash
docker-compose exec django env
```

### Ejecutar comando Python
```bash
docker-compose exec django python -c "from django.conf import settings; print(settings.DATABASES)"
```

### Acceder a shell del contenedor
```bash
docker-compose exec django bash
```

### Ver procesos dentro del contenedor
```bash
docker-compose exec django ps aux
```

### Ver configuración de Django
```bash
docker-compose exec django python manage.py diffsettings
```

---

## 📝 Datos de Prueba

### Crear datos de ejemplo
```bash
docker-compose exec django python create_sample_data.py
```

### Eliminar todos los datos (¡CUIDADO!)
```bash
docker-compose exec django python manage.py flush
```

### Resetear base de datos (¡CUIDADO!)
```bash
# Método 1: Flush + migrate
docker-compose exec django python manage.py flush --noinput
docker-compose exec django python manage.py migrate

# Método 2: Eliminar volumen y recrear
docker-compose down
docker volume rm backend-pos_pos_db_data
docker-compose up -d
docker-compose exec django python manage.py migrate
```

---

## 🚨 Troubleshooting

### Error: No se puede conectar a la base de datos
```bash
# Verificar que DB esté corriendo
docker-compose ps db

# Ver logs de DB
docker-compose logs db

# Esperar a healthcheck
watch docker-compose ps db
```

### Error: Puerto ya en uso
```bash
# Ver qué proceso usa el puerto 8001
sudo netstat -tulpn | grep 8001

# Cambiar puerto en docker-compose.yml
# De: "8001:8000"
# A:  "8002:8000"
```

### Error: Permission denied
```bash
# Dar permisos a docker-entrypoint.sh
chmod +x docker-entrypoint.sh

# Reconstruir
docker-compose build
```

### Contenedor se reinicia constantemente
```bash
# Ver logs del contenedor
docker-compose logs django

# Ver eventos de Docker
docker events

# Verificar healthcheck
docker inspect backend-pos_django | grep -A 10 Health
```

---

## 📚 Recursos Adicionales

### Documentación
- README.md - Documentación principal
- QUICKSTART.md - Guía de despliegue VPS
- IMPLEMENTATION_GUIDE.md - Detalles técnicos
- COMPLETION_SUMMARY.md - Resumen del proyecto

### Interfaces Web
- Admin: http://localhost:8001/admin/
- API Browsable: http://localhost:8001/api/
- RabbitMQ Management: http://localhost:15673/

### WebSocket Testing
```javascript
// En consola del navegador
const ws = new WebSocket('ws://localhost:8001/ws/tables/');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

**¡Mantén este archivo a mano para referencia rápida!** 📖
