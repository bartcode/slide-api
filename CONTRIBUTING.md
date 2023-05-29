# Contributing to Slide-API

Thank you for your interest in contributing to [project name]! We welcome contributions from anyone, regardless of their level of experience or expertise.

## Getting Started

To get started, you'll need to have [Python](https://www.python.org) and [Poetry](https://python-poetry.org/) installed on your system.

Once you have Poetry installed, you can clone the (forked) repository and install the dependencies by running the following commands:

```bash
poetry install
poetry shell
```

Another option is to use the provided Dev Container. More information on using Dev Containers can be
[found here](https://code.visualstudio.com/docs/devcontainers/containers).

## Running Tests

To run the tests, you can use the following command:

```python
poetry run pytest
```

## Making Changes

Before making any changes, please create a new branch for your changes:

```bash
git checkout -b my-feature-branch
```

Once you've made your changes, you can run the tests to make sure everything still works:

```bash
poetry run pytest
```

If the tests pass, you can commit your changes and push them to your fork:

```bash
git add -p
git commit -m "Add my feature"
git push origin my-feature-branch
```

## Creating a Pull Request

To create a pull request, go to the project repository and click on the "New pull request" button. Select your fork and branch, and then click on the "Create pull request" button.

Please make sure to include a clear description of your changes and why they are necessary. Also, please make sure that your changes are consistent with the project's coding style and conventions.

## Code of Conduct

We expect all contributors to abide by our [Code of Conduct](./CODE_OF_CONDUCT.md). Please read it carefully before making any contributions.

## License

By contributing to this project, you agree to license your contributions under the [GNU General Public License v3.0](./LICENSE).

Thank you for your contributions!
