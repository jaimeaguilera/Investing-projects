#!/bin/bash
set -euo pipefail

function set_env() {

    # ----- Prepare ----- #

    # Check running OS
    # Reference: https://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linux
    case "$(uname -s)" in
        Linux*)     OS=Linux;;
        Darwin*)    OS=Mac;;
        CYGWIN*)    OS=Cygwin;;
        MINGW*)     OS=MinGw;;
        *)          OS="UNKNOWN"
    esac

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR=`cd "${SCRIPT_DIR}" && cd .. && pwd`

    # Load preset environment variables
    if [ -f "${PROJECT_DIR}/.env" ];then
        source ${PROJECT_DIR}/.env
    fi

    EXPECTED_PYTHON_VERSION="3.8.5"

    # Set virtual environment
    VIRTUALENV_NAME="venv"
    VIRTUALENV_DIR="${PROJECT_DIR}/${VIRTUALENV_NAME}"

    PYTHON_REQUIREMENTS="${PROJECT_DIR}/requirements.txt"
}

function check_python_version() {
    PYTHON_VERSION=$(python -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)";)
    if [[ ! $(echo "${EXPECTED_PYTHON_VERSION}" | grep ${PYTHON_VERSION}) ]]; then
        echo "ERROR: Python ${PYTHON_VERSION} is not in the supported versions (${EXPECTED_PYTHON_VERSION})."
        install_python
    fi
    # ---- Export env vars ----- #
    export PYTHONPATH="$(cd ${PROJECT_DIR} && python -c 'import os; print(os.getcwd())')"  # Use python to get correct path in Windows
}

function check_virtual_environment() {
    if [ ! -d "${VIRTUALENV_DIR}" ]; then
        echo "Creating virtual environment..."
        cd "${PROJECT_DIR}"
        python -m pip install virtualenv
        python -m virtualenv ${VIRTUALENV_NAME}
        cd -
    fi
}

function install_python() {
    echo "Installing Python ${EXPECTED_PYTHON_VERSION}..."
    if [ ! -d "$HOME/.pyenv" ]; then
        git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    fi

    # Update bashrc
    echo -e '\n# pyenv' >> ~/.bashrc
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init --path)"\nfi' >> ~/.bashrc

    export PYENV_ROOT="$HOME/.pyenv"
    if [ ${OS} == "Linux" ] || [ ${OS} == "Mac" ]; then
        export PATH="$PYENV_ROOT/bin:$PATH"
    else
        export PATH="$PYENV_ROOT/libexec:$PATH"
    fi
    eval "$(pyenv init --path)"
    pyenv install ${EXPECTED_PYTHON_VERSION}
    pyenv local  ${EXPECTED_PYTHON_VERSION}
}

function activate_virtual_environment() {
    if [ ${OS} == "Linux" ] || [ ${OS} == "Mac" ]; then
        source ${VIRTUALENV_DIR}/bin/activate
    else
        source ${VIRTUALENV_DIR}/Scripts/activate
    fi
}

function install_pip_dependencies() {
    echo "Installing Python packages..."
    pip install -r ${PYTHON_REQUIREMENTS}
}

function setup_jupyter_kernel() {
    # Create kernel json
    python3 -m ipykernel install --user --name=${VIRTUALENV_NAME}
}

# ----- Main ----- #
set_env "$@"
check_python_version
check_virtual_environment
activate_virtual_environment
install_pip_dependencies
setup_jupyter_kernel

set +euo pipefail
