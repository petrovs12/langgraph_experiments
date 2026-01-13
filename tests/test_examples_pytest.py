from src.examples_pytests import inc


def test_inc():
    assert inc(3) == 4
    print("inc(3) passed")
    assert inc(-1) == 0
    inc2=inc(2)
    print(f"{inc2=}")
    assert inc(0) == 1

