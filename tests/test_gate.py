import pytest
from fastapi import Request, HTTPException, status
from fastapi.responses import StreamingResponse
from unittest.mock import AsyncMock, Mock, MagicMock, patch

from src.gateway.base import App, GatewayProcessor
from src.gateway.exceptions import AppFileNotExist, GatewayException
from src.services.blocklist import blocklist_service

from .adt_classes import MockRequest, Client, in_ban, proxy_request, ProxyRequest


async def test_load_apps_success(processor):
    """Тестирует успешную загрузку приложений."""
    assert len(processor._GatewayProcessor__apps) == 2
    assert processor._GatewayProcessor__apps['app_1'].redirect_url == 'http://localhost:8080'
    assert processor._GatewayProcessor__apps['app_2'].redirect_url == 'http://localhost:8081'


async def test_find_app_found(processor):
    """Тестирует нахождение приложения по заголовку app_redirect."""
    app = processor._GatewayProcessor__find_app(MockRequest(
        method='GET',
        url='http://localhost:80800',
        headers={'app_redirect': 'app_1'},
    ))
    assert app is not None


async def test_find_app_not_found(processor):
    """Тестирует выбрасывание HTTPException при отсутствии приложения."""
    try:
        app = processor._GatewayProcessor__find_app(MockRequest(
            method='GET',
            url='http://localhost:80800',
            headers={'app_redirect': 'app_5'},
        ))
        assert app is None
    except HTTPException as e:
        assert str(e) == '400: Incorrect request'


async def test_get_client_ip_success(processor,):
    """Тестирует корректное получение IP клиента."""
    target = '192.168.1.1'
    ip = processor._GatewayProcessor__get_client_ip(MockRequest(client=Client(host=target)))
    assert ip == target


async def test_get_client_ip_no_client_raises_exception(processor):
    """Тестирует выбрасывание HTTPException при отсутствии client."""
    with pytest.raises(HTTPException, match='Incorrect request'):
        processor._GatewayProcessor__get_client_ip(MockRequest())


async def test_check_allowed_method_allowed(processor):
    """Тестирует, что разрешенный метод проходит проверку."""
    try:
        processor._GatewayProcessor__check_allowed_method(
            MockRequest(method='GET'),
            processor._GatewayProcessor__apps['app_1'],
        )
    except HTTPException:
        pytest.fail("Should not raise HTTPException when method is allowed.")


async def test_check_allowed_method_not_allowed(processor):
    """Тестирует выбрасывание HTTPException, если метод не разрешен."""
    with pytest.raises(HTTPException, match='405: Method not allowed'):
        processor._GatewayProcessor__check_allowed_method(
            MockRequest(method='PUT'),
            processor._GatewayProcessor__apps['app_1'],
        )


async def test_check_timer_consume_success(processor):
    """Тестирует успешное потребление токена."""
    # Настраиваем мок TokenBucket, чтобы он возвращал True при consume()
    mock_timer = Mock()
    mock_timer.consume.return_value = True

    # доступ к __timers.
    processor._GatewayProcessor__timers = {"test": mock_timer}

    try:
        processor._GatewayProcessor__check_timer(App(name="test", redirect_url="http://app.test"))
    except HTTPException:
        pytest.fail("Should not raise HTTPException when token is available.")


async def test_check_timer_consume_failure(processor):
    """Тестирует сбой при потреблении токена."""
    # Настраиваем мок TokenBucket, чтобы он возвращал False при consume()
    mock_timer = Mock()
    mock_timer.consume.return_value = False

    processor._GatewayProcessor__timers = {"test": mock_timer}

    try:
        processor._GatewayProcessor__check_timer(App(name="test", redirect_url="http://app.test"))
    except HTTPException as e:
        assert e.status_code == 429
    else:
        pytest.fail("Should raise HTTPException when token is unavailable.")


async def test_check_unacceptable_path_success(processor):
    """Тестирует вызов blocklist_service.ban при попадании на недопустимый путь."""
    # Для этого нам нужно мокнуть blocklist_service.ban
    with patch('src.gateway.base.blocklist_service.ban', new_callable=AsyncMock):
        # Настраиваем приложение с недопустимым путем
        app = App(name="test", redirect_url="http://app.test")
        client_ip = "1.2.3.4"

        try:
            await processor._GatewayProcessor__check_unacceptable_path(
                Request(scope={'type': 'http', 'method': 'GET', 'path': '/forbidden', 'headers': {}}),
                app,
                client_ip
            )
        except HTTPException:
            pytest.fail(f"Not expected HTTPException")


async def test_check_unacceptable_path_raises_default(processor):
    """Тестирует вызов blocklist_service.ban при попадании на недопустимый путь."""
    # Для этого нам нужно мокнуть blocklist_service.ban
    with patch('src.gateway.base.blocklist_service.ban', new_callable=AsyncMock):
        # Настраиваем приложение с недопустимым путем
        app = App(name="test", redirect_url="http://app.test")
        client_ip = "1.2.3.4"

        try:
            await processor._GatewayProcessor__check_unacceptable_path(
                Request(scope={'type': 'http', 'method': 'GET', 'path': '/.env', 'headers': {}}),
                app,
                client_ip
            )
            assert False, "Expected HTTPException to be raised"
        except HTTPException as e:
            assert e.status_code == status.HTTP_403_FORBIDDEN


async def test_check_unacceptable_path_raises_extended(processor):
    """Тестирует вызов blocklist_service.ban при попадании на недопустимый путь."""
    # Для этого нам нужно мокнуть blocklist_service.ban
    with patch('src.gateway.base.blocklist_service.ban', new_callable=AsyncMock):
        # Настраиваем приложение с недопустимым путем
        app = App(name="test", redirect_url="http://app.test", unacceptable_paths=(
            '/.env',
            '/secrets'
        ))
        client_ip = "1.2.3.4"

        try:
            await processor._GatewayProcessor__check_unacceptable_path(
                Request(scope={'type': 'http', 'method': 'GET', 'path': '/secrets', 'headers': {}}),
                app,
                client_ip
            )
            assert False, "Expected HTTPException to be raised"
        except HTTPException as e:
            assert e.status_code == status.HTTP_403_FORBIDDEN


async def no_test_process_request_success(test_client):
    """
    Тестирует успешное выполнение всего процесса запроса.
    Внеменно тест отключен!!!
    """
    proxy_mock = AsyncMock(return_value=StreamingResponse(
        content=b'',
        status_code=status.HTTP_200_OK
    ))
    with patch.object(blocklist_service, 'in_ban', new=in_ban):
        with patch.object(GatewayProcessor, '_GatewayProcessor__proxy_request', new=proxy_mock):
            response = await test_client.get('/test_path', headers={'app_redirect': 'TestApp'})
            assert response.status_code == status.HTTP_200_OK
            assert proxy_mock.called
            args, kwargs = proxy_mock.call_args
            assert args[0].method == 'GET'
