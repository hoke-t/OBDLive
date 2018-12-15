from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.urls import path

from obd.consumers import DashboardConsumer, DTCConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('', DashboardConsumer),
            path('dtcs/', DTCConsumer),
        ])
    ),
})
