from .commands import router as commands_router
from .echo import router as echo_router
from .auth import router as auth_router

routers = [
    auth_router,
    commands_router,
    echo_router,
]
