# Contributing to Eco-Sorter

Welcome, and thank you for your interest in contributing to **Eco-Sorter**! 🌱

Every contribution — whether it's a bug report, feature request, documentation improvement, or code change — helps make this project better. We appreciate your time and effort.

## Table of Contents

- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Commit Convention](#commit-convention)
- [Thank You](#thank-you)

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](https://github.com/matteoespo/eco-sorter/issues/new?template=bug_report.yml) using the bug report template. Include as much detail as possible:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Docker version, GPU if applicable)
- Screenshots or logs, if relevant

### Suggesting Features

Have an idea for a new feature? [Open a feature request](https://github.com/matteoespo/eco-sorter/issues/new?template=feature_request.yml) and describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Submitting Pull Requests

1. **Fork** the repository and create your branch from `main`.
2. Make your changes in a focused, well-scoped branch.
3. Ensure all existing tests pass and add new tests if applicable.
4. Update documentation to reflect your changes.
5. Submit a pull request using the [PR template](https://github.com/matteoespo/eco-sorter/blob/main/.github/PULL_REQUEST_TEMPLATE.md).

## Development Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/matteoespo/eco-sorter.git
cd eco-sorter

# Start all services
docker compose up
```

### Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your changes and test locally with `docker compose up`.
3. Commit your changes following the [commit convention](#commit-convention).
4. Push your branch and open a pull request.

## Code Style

### Python (Backend)

- **Docstrings**: Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for all public modules, classes, and functions.
- **Type Hints**: Add type annotations to all function signatures.
- **Formatting**: Code is formatted with [Black](https://black.readthedocs.io/). Run it before committing:
  ```bash
  black services/cv-backend/
  ```
- **Linting**: We use [Ruff](https://docs.astral.sh/ruff/) for linting:
  ```bash
  ruff check services/cv-backend/
  ```

### TypeScript (Frontend)

- Follow the project's [ESLint](https://eslint.org/) configuration:
  ```bash
  cd services/frontend
  npm run lint
  ```

## Commit Convention

We follow a simplified [Conventional Commits](https://www.conventionalcommits.org/) format. Prefix your commit messages with one of the following types:

| Prefix       | Description                                      |
| ------------ | ------------------------------------------------ |
| `feat:`      | A new feature                                    |
| `fix:`       | A bug fix                                        |
| `docs:`      | Documentation changes only                       |
| `refactor:`  | Code change that neither fixes a bug nor adds a feature |
| `test:`      | Adding or updating tests                         |
| `chore:`     | Maintenance tasks (dependencies, CI, configs)    |

**Examples:**

```
feat: add glass recycling category to detection model
fix: resolve Ollama container startup timeout
docs: update README with GPU setup instructions
refactor: reorganize YOLO weight loading logic
```

## Thank You

Thank you for taking the time to contribute to Eco-Sorter! Your efforts help build a tool that makes recycling easier and more accessible for everyone. 💚

If you have any questions, feel free to [open a discussion](https://github.com/matteoespo/eco-sorter/discussions) or reach out via an issue.
