# 🍽️ Backend POS (Punto de Venta) - En Construcción

## 📋 Estado del Proyecto

✅ **Estructura Base Creada**
- Carpeta `backend-pos` creada
- Archivos de configuración base listos
- Requirements.txt con todas las dependencias
- Dockerfile y docker-entrypoint.sh configurados

## 🎯 Arquitectura Planificada

### Apps Django a Implementar

1. **pos** - Gestión de Mesas y Zonas
   - `Zone`: Zonas del restaurante
   - `Table`: Mesas con estados (disponible, ocupada, reservada)

2. **menu** - Carta y Platos Vendibles
   - `MenuCategory`: Categorías del menú
   - `MenuItem`: Platos vendibles con precios
   - `MenuItemComponent`: Componentes (productos/recetas)

3. **orders** - Órdenes y Pagos
   - `Order`: Órdenes con estados
   - `OrderItem`: Ítems de cada orden
   - `Payment`: Pagos (efectivo, tarjeta, convenio)

4. **catalog_mirror** - Réplicas Locales
   - `MirroredProduct`: Copia de productos de Operaciones
   - `MirroredRecipe`: Copia de recetas de Operaciones

## 🔄 Flujos de Negocio

### Flujo de Creación de Orden
1. Seleccionar mesa (cambiar estado a "ocupada")
2. Crear orden vinculada a la mesa
3. Agregar ítems del menú
4. Enviar a cocina (KDS via WebSockets)

### Flujo de Pago
1. Calcular total de la orden
2. Registrar pago (puede ser dividido)
3. Si está completamente pagada:
   - Cambiar estado de orden a "paid"
   - Liberar mesa
   - **Publicar evento `ORDEN_PAGADA`** →  Servicio de Operaciones descuenta stock

### Flujo de Sincronización
1. Servicio de Operaciones publica `PRODUCT_UPDATED`
2. POS consume evento y actualiza `MirroredProduct`
3. Se recalculan costos de `MenuItem` afectados

## 📡 Eventos

### Eventos Publicados
- `ORDEN_PAGADA`: Detalle de ítems vendidos para descontar stock
  ```json
  {
    "order_id": 123,
    "items_sold": [
      {
        "component_origin_id": 5,
        "component_type": "PRODUCT",
        "quantity": 2.5
      }
    ]
  }
  ```

### Eventos Consumidos
- `PRODUCT_STOCK_UPDATED`: Actualizar productos replicados
- `RECIPE_UPDATED`: Actualizar recetas replicadas y costos

## 🌐 API REST Endpoints Planificados

```
# Autenticación
POST   /api/token/
POST   /api/token/refresh/

# Mesas
GET    /api/pos/tables/
GET    /api/pos/tables/{id}/
PATCH  /api/pos/tables/{id}/
POST   /api/pos/tables/{id}/occupy/
POST   /api/pos/tables/{id}/release/

# Menú
GET    /api/pos/menu/
GET    /api/pos/menu/categories/
GET    /api/pos/menu/items/
GET    /api/pos/menu/items/{id}/

# Órdenes
GET    /api/pos/orders/
POST   /api/pos/orders/
GET    /api/pos/orders/{id}/
PATCH  /api/pos/orders/{id}/
POST   /api/pos/orders/{id}/items/
DELETE /api/pos/orders/{id}/items/{item_id}/
POST   /api/pos/orders/{id}/pay/
GET    /api/pos/orders/active/

# Validaciones
POST   /api/pos/validate-convenio/
```

## 🔌 WebSockets (Django Channels)

### Canales Planificados
- `table-status`: Estado de mesas en tiempo real
- `kds-orders`: Nuevas órdenes para cocina
- `order-updates`: Actualizaciones de órdenes

## 🗄️ Base de Datos: db_pos

```sql
-- Tablas Principales
pos_zone
pos_table
menu_menucategory
menu_menuitem
menu_menuitemcomponent
orders_order
orders_orderitem
orders_payment
catalog_mirror_mirroredproduct
catalog_mirror_mirroredrecipe
```

## 🚀 Próximos Pasos de Implementación

### Fase 1: Configuración Base (Completada Parcialmente)
- [x] Crear estructura de proyecto
- [x] Configurar Docker y requirements
- [ ] Crear settings.py completo
- [ ] Configurar Celery
- [ ] Configurar Django Channels

### Fase 2: Modelos
- [ ] Implementar app `pos` (Zone, Table)
- [ ] Implementar app `menu` (MenuItem, MenuItemComponent)
- [ ] Implementar app `orders` (Order, OrderItem, Payment)
- [ ] Implementar app `catalog_mirror`

### Fase 3: API REST
- [ ] Serializers para todos los modelos
- [ ] ViewSets con lógica de negocio
- [ ] URLs y routing

### Fase 4: Lógica de Negocio
- [ ] Servicio de gestión de órdenes
- [ ] Servicio de pagos (incluye validación de convenios)
- [ ] Cálculo de totales y propinas
- [ ] Lógica de descuento de stock

### Fase 5: Eventos
- [ ] Tasks de Celery para publicar eventos
- [ ] Listeners para eventos de Operaciones
- [ ] Sincronización de catálogo

### Fase 6: WebSockets
- [ ] Routing de Channels
- [ ] Consumers para mesas y órdenes
- [ ] Integración con KDS

### Fase 7: Testing y Documentación
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Documentación API
- [ ] Guías de usuario

## 📦 Dependencias Instaladas

- Django 4.2.7
- Django REST Framework 3.14.0
- Django Channels 4.0.0 (WebSockets)
- Celery 5.3.4
- MySQL client
- Redis
- RabbitMQ (via kombu)

## 🔗 Integración con Microservicios

### Con Servicio de Operaciones
- Consume eventos de actualización de productos/recetas
- Publica eventos de órdenes pagadas para descuento de stock

### Con API Gateway (futuro)
- Expone endpoints REST
- Maneja autenticación JWT

### Con Frontend POS (futuro)
- API REST para operaciones
- WebSockets para actualizaciones en tiempo real

### Con KDS - Kitchen Display System (futuro)
- WebSockets para mostrar órdenes en cocina
- Actualizaciones de estado de platos

## 💡 Características Clave Planificadas

1. **Gestión de Mesas en Tiempo Real**
   - Estado visual de todas las mesas
   - Ocupación y liberación automática
   - Editor visual de distribución (posiciones x,y)

2. **Sistema de Órdenes Completo**
   - Órdenes por mesa o para llevar
   - Modificación de ítems
   - Notas para cocina
   - División de cuentas

3. **Múltiples Métodos de Pago**
   - Efectivo
   - Tarjeta
   - Convenio (validación de empleados)
   - Pagos divididos
   - Propinas

4. **Sincronización de Catálogo**
   - Réplica local de productos y recetas
   - Actualización automática de costos
   - Cálculo de rentabilidad por plato

5. **Integración en Tiempo Real**
   - WebSockets para KDS
   - Actualizaciones instantáneas de mesas
   - Notificaciones de nuevas órdenes

## 📝 Notas de Implementación

### Cálculo de Descuento de Stock
Cuando se paga una orden:
```python
for order_item in order.items.all():
    for component in order_item.menu_item.components.all():
        quantity_to_deduct = component.quantity_needed * order_item.quantity
        # Publicar al evento bus
        publish_stock_deduction({
            'component_origin_id': component.component_origin_id,
            'component_type': component.component_type,
            'quantity': quantity_to_deduct
        })
```

### Validación de Convenio
```python
def validate_convenio(employee_rut):
    # Buscar en tabla local de empleados de convenio
    # (replicada desde servicio de Convenios o parte de este servicio)
    return ConvenioEmployee.objects.filter(
        rut=employee_rut,
        is_active=True
    ).exists()
```

## 🎯 Comandos Rápidos (cuando esté completo)

```powershell
# Iniciar con Docker
docker-compose up -d

# Ver logs
docker-compose logs -f pos_service

# Ejecutar migraciones
docker-compose exec pos_service python manage.py migrate

# Crear superusuario
docker-compose exec pos_service python manage.py createsuperuser
```

## 📧 Soporte

Para continuar con la implementación completa de este servicio, se necesita:

1. Completar la configuración de Django
2. Crear todos los modelos de las 4 apps
3. Implementar serializers y views
4. Configurar Django Channels
5. Implementar la lógica de eventos
6. Crear tests
7. Documentación completa

---

**Estado**: 🟡 En Desarrollo Inicial  
**Próximo Paso**: Crear settings.py, celery.py y modelos base  
**Estimación**: 4-6 horas de desarrollo adicional para MVP funcional  
