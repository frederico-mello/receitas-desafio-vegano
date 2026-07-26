## ADDED Requirements

### Requirement: Automated environment setup
The system MUST provide a single command to configure the complete development environment including virtual environment creation, dependency installation, and database directory preparation.

#### Scenario: Run dev target
- **WHEN** user executes `make dev` in project root
- **THEN** system creates virtual environment, installs all dependencies (production + dev), creates data directory, and runs tests

#### Scenario: Run install target
- **WHEN** user executes `make install` in project root
- **THEN** system creates virtual environment and installs all dependencies (production + dev)

#### Scenario: Run setup-db target
- **WHEN** user executes `make setup-db` in project root
- **THEN** system creates the data directory for SQLite database

### Requirement: Test execution automation
The system MUST provide an automated way to run the test suite through a Makefile target.

#### Scenario: Run test target
- **WHEN** user executes `make test` in project root
- **THEN** system runs pytest with all test configurations from pyproject.toml

### Requirement: Clean operation
The system MUST provide a command to clean generated artifacts.

#### Scenario: Run clean target
- **WHEN** user executes `make clean` in project root
- **THEN** system removes the .venv directory and __pycache__ directories

### Requirement: Help documentation
The system MUST display usage information when no target is specified.

#### Scenario: Run make without target
- **WHEN** user executes `make` without specifying a target
- **THEN** system displays available targets: install, setup-db, test, dev, clean, help
