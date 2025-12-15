from .commands import router as commands_router
from .echo import router as echo_router

# Собираем все роутеры
routers = [
    commands_router,
    echo_router
]