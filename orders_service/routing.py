"""
Routing de WebSockets para Django Channels.
"""

from django.urls import re_path
from pos import consumers as pos_consumers
from orders import consumers as orders_consumers

websocket_urlpatterns = [
    re_path(r'ws/tables/$', pos_consumers.TableStatusConsumer.as_asgi()),
    re_path(r'ws/kds/$', orders_consumers.KDSConsumer.as_asgi()),
    re_path(r'ws/orders/(?P<order_id>\w+)/$', orders_consumers.OrderUpdateConsumer.as_asgi()),
]
