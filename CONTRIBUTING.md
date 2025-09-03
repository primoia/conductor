# Contributing to Conductor

First off, thank you for considering contributing to Conductor! It's people like you that make open source such a great community. We welcome any type of contribution, not only code.

## How to Contribute

You can contribute in many ways: by reporting bugs, suggesting new features, improving the documentation, or by writing code.

### Reporting Bugs and Suggesting Features

If you find a bug or have an idea for a new feature, please open an issue on our GitHub repository. Please provide as much detail as possible, including steps to reproduce the bug or a clear description of the new feature.

### Your First Code Contribution

Unsure where to begin? You can start by looking through `good first issue` and `help wanted` issues.

### Development Workflow

To contribute code, please follow this general workflow:

1.  **Fork the repository:** Create your own fork of the Conductor repository on GitHub.

2.  **Clone your fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/conductor.git
    cd conductor
    ```

3.  **Create a new branch:** Create a new branch for your changes. Please use a descriptive name.
    ```bash
    # For a new feature
    git checkout -b feature/my-amazing-feature

    # For a bug fix
    git checkout -b fix/a-tricky-bug
    ```

4.  **Make your changes:** Make your changes to the code and documentation.

5.  **Run tests:** Ensure that all tests pass before submitting your changes.
    ```bash
    # Assuming pytest is set up
    pytest
    ```

6.  **Commit your changes:** Write a clear and descriptive commit message. We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
    ```bash
    git add .
    git commit -m "feat: Add my amazing feature"
    ```

7.  **Push to your branch:**
    ```bash
    git push origin feature/my-amazing-feature
    ```

8.  **Open a Pull Request:** Go to the Conductor repository on GitHub and open a new Pull Request from your forked repository's branch. Provide a clear description of the changes you have made.

## Code Style and Review Process

-   We use `black` for code formatting and `ruff` for linting. Please run these tools before committing.
-   All contributions will be reviewed by the core team. We will provide feedback and may request changes before merging.

Thank you again for your contribution!
