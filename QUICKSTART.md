# Guía Rápida de Despliegue - Backend POS

## 🚀 Despliegue Rápido en VPS

### Requisitos del Servidor
- Ubuntu 20.04+ o Debian 11+
- Mínimo 2GB RAM (recomendado 4GB)
- 20GB espacio en disco
- Acceso root o sudo

### 1. Preparar el Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker --version
docker-compose --version
```

### 2. Clonar el Repositorio

```bash
# Crear directorio
sudo mkdir -p /opt/backend-pos
cd /opt/backend-pos

# Clonar (ajustar según tu repo)
git clone <tu-repositorio> .

# O subir archivos via SCP
scp -r backend-pos/* user@your-vps:/opt/backend-pos/
```

### 3. Configurar Variables de Entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Editar con nano
nano .env
```

**IMPORTANTE - Cambiar estos valores**:
```env
DEBUG=False
SECRET_KEY=<generar-una-clave-segura-de-50+-caracteres>
ALLOWED_HOSTS=tu-dominio.com,tu-ip-vps

DB_NAME=db_pos_production
DB_USER=pos_user_prod
DB_PASSWORD=<password-muy-seguro>
DB_ROOT_PASSWORD=<root-password-muy-seguro>

RABBITMQ_USER=admin_prod
RABBITMQ_PASSWORD=<rabbitmq-password-seguro>
```

**Generar SECRET_KEY seguro**:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Iniciar Servicios

```bash
# Construir imágenes
docker-compose build

# Iniciar en background
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 5. Configuración Inicial

```bash
# Esperar a que los servicios estén listos (30-60 segundos)
sleep 60

# Aplicar migraciones
docker-compose exec django python manage.py migrate

# Crear superusuario
docker-compose exec django python manage.py createsuperuser

# Recolectar archivos estáticos
docker-compose exec django python manage.py collectstatic --noinput
```

### 6. Configurar Nginx como Proxy Reverso

```bash
# Instalar Nginx
sudo apt install nginx -y

# Crear configuración
sudo nano /etc/nginx/sites-available/backend-pos
```

**Contenido del archivo**:
```nginx
upstream backend_pos {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name tu-dominio.com;  # Cambiar por tu dominio
    
    client_max_body_size 10M;
    
    # Archivos estáticos
    location /static/ {
        alias /opt/backend-pos/staticfiles/;
    }
    
    location /media/ {
        alias /opt/backend-pos/media/;
    }
    
    # WebSocket para KDS y actualizaciones en tiempo real
    location /ws/ {
        proxy_pass http://backend_pos;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API REST
    location / {
        proxy_pass http://backend_pos;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/backend-pos /etc/nginx/sites-enabled/

# Probar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 7. Configurar HTTPS con Let's Encrypt (Recomendado)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com

# Renovación automática (ya viene configurado)
sudo certbot renew --dry-run
```

### 8. Configurar Firewall

```bash
# Permitir SSH, HTTP y HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activar firewall
sudo ufw enable

# Ver estado
sudo ufw status
```

## 🔄 Comunicación con Microservicio de Operaciones

### Si ambos servicios están en el mismo VPS:

```yaml
# En docker-compose.yml de backend-pos
rabbitmq:
  # Comentar para usar el RabbitMQ del servicio de operaciones
  # image: rabbitmq:3.12-management-alpine
  
# Cambiar en environment de todos los servicios:
environment:
  - RABBITMQ_HOST=172.17.0.1  # IP del host desde contenedor
  - RABBITMQ_PORT=5672
```

### Si están en VPS separados:

**Opción 1: Exponer RabbitMQ públicamente (con VPN recomendado)**
```bash
# En VPS de Operaciones, exponer puerto en firewall
sudo ufw allow from <IP-VPS-POS> to any port 5672
```

**Opción 2: Usar RabbitMQ externo (CloudAMQP, etc.)**
```env
# En .env de ambos servicios
RABBITMQ_HOST=external-rabbitmq.cloudamqp.com
RABBITMQ_PORT=5672
RABBITMQ_USER=shared_user
RABBITMQ_PASSWORD=shared_password
```

## 🔍 Verificación

### Comprobar que todo funciona:

```bash
# Estado de contenedores
docker-compose ps

# Logs
docker-compose logs django
docker-compose logs celery_worker

# Healthcheck de base de datos
docker-compose exec db mysqladmin ping -h localhost

# Healthcheck de RabbitMQ
docker-compose exec rabbitmq rabbitmq-diagnostics ping

# Test de API
curl http://tu-dominio.com/api/
curl http://tu-dominio.com/admin/
```

### Acceder a interfaces:

- **API REST**: https://tu-dominio.com/api/
- **Admin Django**: https://tu-dominio.com/admin/
- **RabbitMQ Management**: http://tu-ip:15673/ (si está expuesto)

## 📊 Monitoreo y Mantenimiento

### Ver logs en tiempo real:
```bash
docker-compose logs -f django
docker-compose logs -f celery_worker
```

### Reiniciar servicios:
```bash
# Reiniciar todo
docker-compose restart

# Reiniciar servicio específico
docker-compose restart django
docker-compose restart celery_worker
```

### Actualizar aplicación:
```bash
cd /opt/backend-pos

# Detener servicios
docker-compose down

# Actualizar código
git pull origin main

# Reconstruir y levantar
docker-compose build
docker-compose up -d

# Aplicar migraciones si hay nuevas
docker-compose exec django python manage.py migrate
```

### Backup de base de datos:
```bash
# Crear backup
docker-compose exec db mysqldump -u pos_user_prod -p db_pos_production > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T db mysql -u pos_user_prod -p db_pos_production < backup_20241201.sql
```

### Backup automatizado (cron):
```bash
# Editar crontab
crontab -e

# Agregar línea (backup diario a las 3 AM)
0 3 * * * cd /opt/backend-pos && docker-compose exec -T db mysqldump -u pos_user_prod -p<PASSWORD> db_pos_production > /backups/pos_$(date +\%Y\%m\%d).sql
```

## 🐛 Troubleshooting

### Error: Cannot connect to database
```bash
# Ver logs de DB
docker-compose logs db

# Verificar que esté corriendo
docker-compose ps db

# Reiniciar DB
docker-compose restart db
```

### Error: Celery no procesa tareas
```bash
# Ver logs
docker-compose logs celery_worker

# Verificar RabbitMQ
docker-compose logs rabbitmq

# Reiniciar workers
docker-compose restart celery_worker celery_event_listener
```

### Error: 502 Bad Gateway (Nginx)
```bash
# Verificar que Django esté corriendo
docker-compose ps django

# Ver logs de Django
docker-compose logs django

# Verificar que el puerto 8001 esté escuchando
sudo netstat -tulpn | grep 8001
```

### Error: Out of memory
```bash
# Ver uso de memoria
docker stats

# Aumentar memoria swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Hacer permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 📈 Optimización para Producción

### 1. Usar Gunicorn + Nginx en vez de Daphne (opcional)
Si no necesitas WebSockets, Gunicorn es más eficiente:

```yaml
# En docker-compose.yml
django:
  command: gunicorn orders_service.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 2. Configurar límites de recursos:
```yaml
# En docker-compose.yml
django:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 1G
      reservations:
        cpus: '1'
        memory: 512M
```

### 3. Habilitar compresión Gzip en Nginx:
```nginx
# En /etc/nginx/nginx.conf
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

## ✅ Checklist de Despliegue

- [ ] Servidor actualizado y Docker instalado
- [ ] Código clonado en `/opt/backend-pos`
- [ ] Archivo `.env` configurado con valores de producción
- [ ] `SECRET_KEY` único y seguro (50+ caracteres)
- [ ] `DEBUG=False` en producción
- [ ] Passwords de DB y RabbitMQ cambiados
- [ ] Servicios Docker corriendo (`docker-compose up -d`)
- [ ] Migraciones aplicadas
- [ ] Superusuario creado
- [ ] Nginx configurado como proxy reverso
- [ ] HTTPS configurado con Let's Encrypt
- [ ] Firewall configurado (UFW)
- [ ] RabbitMQ compartido entre microservicios
- [ ] Backups automáticos configurados
- [ ] Monitoreo de logs configurado

## 📞 Soporte

Si encuentras problemas durante el despliegue:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica el estado de servicios: `docker-compose ps`
3. Consulta el README.md principal
4. Revisa la sección de Troubleshooting en este documento

---

**¡Listo para producción!** 🎉
