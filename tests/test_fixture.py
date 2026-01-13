import pytest


@pytest.fixture(scope="module")
def order():
    return []


@pytest.fixture
def append_first(order):
    order.append(1)


@pytest.fixture
def append_second(order, append_first):
    order.extend([2])


@pytest.fixture(autouse=True)
def append_third(order, append_second):
    order += [3]


def test_order(order):
    assert order == [1, 2, 3]

def test_env_exists():
    import os
    assert 'OPENAI_API_KEY' in os.environ