from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class App(Base):
    """
    Модель подключенных приложений:
        - id - идентификатор приложения
        - name - название приложения
        - redirect_url - URL перенаправления после проверок
        - blocker_check - проводить ли проверку на блокировку перед проксированием
        - auth_check - проводить ли проверку на авторизацию перед проксированием (на данный момент не проводится)
        - max_rpm - максимальное количество запросов в минуту
    """

    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    redirect_url: Mapped[str]

    blocker_check: Mapped[bool] = mapped_column(default=True)
    auth_check: Mapped[bool] = mapped_column(default=False)
    max_rpm: Mapped[int] = mapped_column(default=100)
