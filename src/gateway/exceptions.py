class GatewayException(Exception):
    """
    Общая ошибка Gateway
    """

    pass


class AppFileNotExist(Exception):
    """
    Ошибка, возникающая при отсутствии файла apps.json
    """

    def __init__(self, file_path: str):
        super().__init__(f"App file not exist: {file_path}")
        self.file_path = file_path

    def __str__(self):
        return f"App file not exist: {self.file_path}"
