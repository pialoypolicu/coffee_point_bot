from typing import Any, NotRequired, Required, TypedDict
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext

from app.database.requests.user import UserContext
from app.handlers.feedback import NAME_FORM_MSG
from app.keyboards import CALLBACK_COFFEE_POINT_PREFIX, CALLBACK_DRINKS, CALLBACK_ITEM_PREFIX
from app.logic.feedback import ANSWER_MSG, FEEDBACK_STEPS_MSG, FEEDBACK_TYPES
from app.logic.user_logic import UserLogic
from app.services.message_manager import MessageManager
from app.tests.conftest import AsyncMockGenerator


class CallbackHint(TypedDict):
    """Хинт возвращаемых параметров из фиктур."""

    mock: Required[AsyncMock]


class CallbackPointHint(CallbackHint):
    """Хинт возвращаемый значения из фиктсуры."""

    expected_point_id: Required[int]


class CallbackItemHint(CallbackHint):
    """Хинт возвращаемый значения из фиктсуры."""

    expected_item_id: NotRequired[int]


class FeedbackData(TypedDict):
    """Хинт колбека и ожидаемых значений для теста."""

    callback: AsyncMock
    expected_msg: str
    expected_fb_type: str
    expected_answer_msg: str
    expected_feedback_type_rus: str
    expected_msg_id: int


class FeedbackTextData(TypedDict):
    """Хинт сообщения и ожидаемых значений для теста."""

    message: AsyncMock
    expected_text: str


class FeedbackNameForm(FeedbackTextData):
    """Хинт сообщения, состояния памяти и ожидаемых значений для теста."""

    state: AsyncMock


@pytest.fixture(name="coffee_points")
def f_coffee_points() -> list[dict[str, Any]]:
    """Данный для мока. Эмитация возврашаения карточки кофейни."""
    return [{
        "id": 1,
        "name": "Тест ТЦ на зеленом",
        "address": "Москва, Зелёный проспект, 83А",
        "metro_station": "Новогиреево",
        }]


@pytest.fixture()
def test_message_manager(mock_bot: AsyncMock) -> MessageManager:
    """Объект MessageManager.

    Args:
        mock_bot: Мок Bot.
    """
    return MessageManager(mock_bot)

@pytest.fixture(name="test_data", params=[
                                    {"expected": False, "user_id": 1},
                                    {"expected": True, "user_id": 223957535},
                                    ])
def f_test_data(request: pytest.FixtureRequest) -> dict[str, bool | int]:
    """Параметризация теста.

    Args:
        request: параметры теста.
    """
    return request.param

@pytest.fixture(params=["feedback_type:suggestion", "feedback_type:review"])
def feedback_data(request: pytest.FixtureRequest, mock_callback: AsyncMock) -> FeedbackData:
    """Фикстура возвращает callback и ожидаемые занчения для теста.

    Args:
        request: параметры для теста. поступающие значения callback'а клавиатуры inline_feedback
        mock_callback: коллбек.
    """
    param = request.param
    mock_callback.data = param
    mock_callback.message.message_id = 835

    feedback_type = mock_callback.data.split(":")[1]  # Извлекаем 'suggestion' или 'review'
    feedback_type_rus = FEEDBACK_TYPES[feedback_type]
    data: FeedbackData = {"callback": mock_callback,
            "expected_msg": FEEDBACK_STEPS_MSG.format(feedback_type_rus=feedback_type_rus),
            "expected_fb_type": feedback_type,
            "expected_msg_id": 835,
            "expected_answer_msg": ANSWER_MSG.format(feedback_type_rus=feedback_type_rus),
            "expected_feedback_type_rus": feedback_type_rus}
    return data

@pytest.fixture(params=["alex"])
def feedback_name_form_data(request: pytest.FixtureRequest,
                            mock_message: AsyncMock,
                            mock_state: AsyncMock) -> FeedbackNameForm:
    """Фикстура возвращает мок Message, мок состояния памяти с значение для state.get_data и ожидаемое сообщение.

    Args:
        request: параметры для теста.
        mock_message: мок Message.
        mock_state: мок состояния памяти.
    """
    name = request.param
    mock_message.text = name
    msg_id = 12
    mock_message.message_id = msg_id
    mock_message.answer.return_value = mock_message
    msg = NAME_FORM_MSG.format(name=name.capitalize(), feedback_type_rus="предложение")
    mock_state.get_data.return_value = {"feedback_type_rus": "Предложение"}

    return {"message": mock_message,
            "expected_text": msg,
            "state": mock_state}

@pytest.fixture(params=["Тестовое сообщение."])
def feedback_text_form_data(request: pytest.FixtureRequest,
                            mock_message: AsyncMock) -> FeedbackTextData:
    """Фикстура возвращает мок Message, мок состояния памяти с значение для state.get_data и ожидаемое сообщение.

    Args:
        request: параметры для теста.
        mock_message: мок Message.
    """
    text = request.param
    mock_message.text = text
    msg_id = 17
    mock_message.message_id = msg_id
    mock_message.answer.return_value = mock_message

    return {"message": mock_message, "expected_text": text}

@pytest.fixture()
def test_user_logic() -> UserLogic:
    """Объект UserLogic."""
    return UserLogic()

@pytest.fixture(name="mock_fms_context")
def f_mock_fms_context() -> AsyncMock:  # TODO: отказаться от этойфикстуры в пользу mock_state, в tests/conftest.py
    """Мокаем объект FSMContext, чтобы имитировать администратора."""
    return AsyncMock(spec=FSMContext)

@pytest.fixture()
def mock_fms_context_with_get_data(mock_fms_context: AsyncMock) -> AsyncMock:
    """Мокаем get_data объекта FSMContext.

    Args:
        mock_fms_context (AsyncMock): Мок объект FSMContext
    """
    mock_fms_context.get_data.return_value = {}
    return mock_fms_context

@pytest.fixture()
def mock_message_user_configure_for_cmd_start(mock_message: AsyncMock, test_data: dict[str, bool | int]):
    """Конфигурируем параметрами объект User, который принадлежит Message.

    Args:
        mock_message (AsyncMock): Мок Message
        test_data (dict[str, bool  |  int]): параметры для теста.
    """
    mock_message.from_user.configure_mock(
        id=test_data["user_id"],
        username="testuser",
        first_name="Test",
        last_name="User",
        full_name="Test User",
        )
    mock_message.chat.id = 17
    return mock_message

@pytest.fixture()
def mock_wait_typing():
    """Мокаем wait_typing."""
    with patch("app.logic.user_logic.wait_typing", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture()
def mock_set_user_to_db() -> AsyncMockGenerator:
    """Мокаем UserContext.set_user."""
    with patch.object(UserContext, "set_user_to_db", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture()
def mock_get_coffee_points_db(coffee_points: list[dict[str, Any]]) -> AsyncMockGenerator:
    """Мокаем функцию UserContext.get_coffee_points_db.

    Args:
        coffee_points (list[dict[str, Any]]): список кофепойнтов.
    """
    with patch.object(UserContext, "get_coffee_points_db", new_callable=AsyncMock, return_value=coffee_points) as mock:
        yield mock

@pytest.fixture()
def mock_get_coffee_point_info_from_db(coffee_points: list[dict[str, Any]]) -> AsyncMockGenerator:
    """Мокакем функцию UserContext.get_coffee_point_info_db.

    Args:
        coffee_points: список кофеен
    """
    with patch.object(UserContext, "get_coffee_point_info_db", new_callable=AsyncMock) as mock:
        mock.return_value = coffee_points[0]
        yield mock

@pytest.fixture()
def mock_get_user() -> AsyncMockGenerator:
    """Мокаем функцию UserContext.get_user."""
    with patch.object(UserContext, "get_user", new_callable=AsyncMock, return_value=None) as mock:
        yield mock

@pytest.fixture()
def mock_safe_send_message(mock_message: AsyncMock) -> AsyncMockGenerator:
    """Мокаем функцию MessageManager.safe_send_message.

    Args:
        mock_message: Мок Message.
    """
    with patch.object(MessageManager, "safe_send_message", return_value=mock_message) as mock:
        yield mock

@pytest.fixture()
def mock_calback_with_params(mock_callback: AsyncMock) -> CallbackPointHint:
    """Дополняем параметрами мока CallbackQuery.

    Args:
        mock_callback: Мок CallbackQuery
    """
    mock_callback.data = "coffee_point_1"
    mock_callback.message.chat.id = 1
    mock_callback.message.message_id = 12

    point_id = int(mock_callback.data.replace(CALLBACK_COFFEE_POINT_PREFIX, ""))
    return {"mock": mock_callback, "expected_point_id": point_id}

@pytest.fixture()
def mock_calback_with_params_drinks_point(mock_callback: AsyncMock) -> AsyncMock:
    """Конфигурируем параметрами мок CallbackQuery.

    Args:
        mock_callback: Мок CallbackQuery
    """
    mock_callback.data = "drinks_coffee_point_1"
    mock_callback.message.chat.id = 1
    mock_callback.message.message_id = 12

    point_id = int(mock_callback.data.replace(CALLBACK_DRINKS, ""))
    return {"mock": mock_callback, "expected_point_id": point_id}

@pytest.fixture()
def mock_calback_with_params_drink_item(mock_callback: AsyncMock) -> CallbackItemHint:
    """Конфигурируем параметрами мок CallbackQuery.

    Args:
        mock_callback: Мок CallbackQuery
    """
    mock_callback.data = f"{CALLBACK_ITEM_PREFIX}1"
    mock_callback.message.chat.id = 1
    mock_callback.message.message_id = 12

    point_id = int(mock_callback.data.replace(CALLBACK_ITEM_PREFIX, ""))
    return {"mock": mock_callback, "expected_item_id": point_id}

@pytest.fixture()
def mock_calback_with_params_back_to_start(mock_callback: AsyncMock) -> AsyncMock:
    """Конфигурируем параметрами мок CallbackQuery.

    Args:
        mock_callback: Мок CallbackQuery
    """
    mock_callback.from_user.id = 10
    mock_callback.message.message_id = 12

    # point_id = int(mock_callback.data.replace(CALLBACK_ITEM_PREFIX, ""))
    # return {"mock": mock_callback, "expected_item_id": point_id}
    return mock_callback

@pytest.fixture()
def mock_state_with_params(mock_state: AsyncMock) -> AsyncMockGenerator:
    """Конфигурируем параметрами мок FSMContext.

    Args:
        mock_state: Мок FSMContext.
    """
    mock_state.get_data.return_value = {}
    yield mock_state
    mock_state.reset_mock()

@pytest.fixture()
def mock_state_with_params_coffee_item(mock_state: AsyncMock) -> AsyncMockGenerator:
    """Конфигурируем параметрами мок FSMContext.

    Args:
        mock_state: Мок FSMContext.
    """
    mock_state.get_data.return_value = {"point_id": 1}
    yield mock_state
    mock_state.reset_mock()

@pytest.fixture()
def mock_get_names_db() -> AsyncMockGenerator:
    """Мокаем функцию UserContext.get_names_db."""
    with patch.object(UserContext, "get_names_db", new_callable=AsyncMock) as mock:
        mock.return_value = [{"id": 1, "name": "Капучино"}, {"id": 2, "name": "Американо"}]
        yield mock

@pytest.fixture()
def mock_get_drink_detail_db() -> AsyncMockGenerator:
    """Мокаем функцкию UserContext.get_drink_detail_db."""
    data = {"name": "Капучино", "description": "Кофе с молочной пенкой", "photos": [], "ingredients": []}
    with patch.object(UserContext, "get_drink_detail_db", new_callable=AsyncMock) as mock:
        mock.return_value = data
        yield mock
