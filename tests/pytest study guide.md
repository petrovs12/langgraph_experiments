PyTest Study Guide: Imports, Auto-Discovery, Fixtures, Conftest, Environment Variables & Mocking

This guide draws from the official PyTest documentation and recognised testing practices.  It introduces a series of questions to encourage you to think about why PyTest works the way it does, followed by concise answers and links into the documentation.

1. Importing application code in test modules

Questions to consider
	•	How will PyTest locate your application code when tests import modules?  Does the layout of your repository matter?
	•	What happens when you have multiple tests with the same filename or you import test‑utility modules inside tests?
	•	Why does PyTest provide different import modes and what are the trade‑offs?

Key points and references
	•	Test layout matters. PyTest recommends structuring your code as a proper package.  For instance, placing application code under src/mypkg and tests under tests/ or inside mypkg/tests.  This makes it easy to derive a full package name for each test module ￼.  Without packages, PyTest falls back to importing test files as top‑level modules and adds their directory to sys.path ￼.
	•	Import modes: the --import-mode flag controls how PyTest imports test modules and conftest.py files ￼.  The default prepend mode inserts the test directory at the front of sys.path; append inserts it at the end; and importlib uses importlib to load modules without modifying sys.path ￼.  The importlib mode avoids polluting sys.path but prevents tests from importing each other and test‑utility modules inside the tests directory ￼.
	•	Configuration: if you separate your source code and tests (the recommended src layout), configure PyTest to add the src folder to the import path.  You can do this by either setting PYTHONPATH=src pytest when running tests or adding a pythonpath setting in pytest.ini or pyproject.toml ￼.  PyTest will prepend each listed directory to sys.path ￼.

2. Test auto‑discovery

Questions to consider
	•	How does PyTest find tests without explicit registration?  What naming conventions does it use?
	•	How can you customise or limit test collection?

Key points and references
	•	File and function naming conventions: By default, PyTest starts collecting from the current directory (or testpaths if configured), recurses into directories (except those matching norecursedirs), and searches for Python files named test_*.py or *_test.py ￼.  Within those files it collects functions or methods whose names start with test and classes whose names start with Test and have no __init__ method ￼.
	•	Customising discovery: You can customise discovery using configuration options like python_files, python_classes and python_functions or command‑line options such as --ignore, --ignore‑glob, --deselect and --keep‑duplicates.  These options are detailed under Changing standard test discovery in the docs.
	•	Running specific tests: PyTest’s CLI lets you run tests in specific modules, directories or by keyword expressions (e.g., pytest tests/test_mod.py::test_func) ￼.

3. What are fixtures and how do you create them?

Questions to consider
	•	What does the term fixture mean in testing and how does it differ from xUnit’s setup_* functions?
	•	How do you declare a fixture and use it in tests?
	•	How can fixtures depend on other fixtures?

Key points and references
	•	Definition: In testing, a fixture is a reliable context in which tests run.  It may provide environment settings (e.g., a configured database) or test data.  In PyTest, fixtures are functions decorated with @pytest.fixture.  Tests request fixtures by including an argument with the same name as the fixture ￼.  When PyTest runs a test, it looks at the function signature, resolves each argument as a fixture, executes those fixtures (caching the results if needed), and passes their return values into the test ￼.
	•	Example: