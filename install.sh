#!/bin/bash

DEBUG_FILE="fly-telegram.log"
REPO="https://github.com/fly-telegram/fly-telegram.git"
BRANCH="v2"
INSTALL_DIR="fly-telegram"
REQUIREMENTS="requirements.txt"

BLACK='\033[0;30m'
GRAY='\033[38;5;245m'
WHITE='\033[0;37m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ARROW_UP=$'\e[A'
ARROW_DOWN=$'\e[B'
ENTER=$'\n'
CHECKMARK="${GREEN}✓${NC}"
CROSSMARK="${RED}✗${NC}"

SPINNER=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
DOTS=(".  " ".. " "..." "   ")

center_text() {
    local text="$1"
    local width=$(tput cols)
    printf "%*s\n" $(( (${#text} + width) / 2 )) "$text"
}

show_banner() {
    clear
    echo -e "${BLUE}"
    center_text "  _______  _____   ___ ___  _______  _______  "
    center_text " |    ___||     |_|   |   ||_     _||     __| "
    center_text " |    ___||       |\\     /   |   |  |    |  | "
    center_text " |___|    |_______| |___|    |___|  |_______| "
    echo -e "${NC}"
    center_text "Fly-Telegram Installer"
}

show_stage() {
    local stage="$1"
    show_banner
    echo -e "${YELLOW}$(center_text "$stage")${NC}\n"
}

animated_spinner() {
    local pid=$!
    local delay=0.1
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        printf "\r${SPINNER[$i]} ${2:-Processing}"
        sleep $delay
    done
    printf "\r${CHECKMARK} ${2:-Done}          \n"
}

progress_dots() {
    local pid=$!
    local delay=0.3
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 4 ))
        printf "\r${3:-Working}${DOTS[$i]}"
        sleep $delay
    done
    printf "\r${CHECKMARK} ${2:-Complete}          \n"
}

show_menu() {
    local options=("$@")
    local current=0

    while true; do
        for i in "${!options[@]}"; do
            if [[ $i -eq $current ]]; then
                echo -e " ${GREEN}»${NC} ${options[i]}"
            else
                echo -e "   ${options[i]}"
            fi
        done

        read -rsn3 key
        case $key in
            $ARROW_UP) ((current--)); [[ $current -lt 0 ]] && current=$((${#options[@]}-1)) ;;
            $ARROW_DOWN) ((current++)); [[ $current -ge ${#options[@]} ]] && current=0 ;;
            "") return $current ;;
        esac
        tput cuu ${#options[@]}
    done
}

error_exit() {
    echo -e "\n${RED}Error: $1${NC}"
    echo -e "Details in: ${YELLOW}$DEBUG_FILE${NC}"
    exit 1
}

run_command() {
    echo "▶ $@" >> "$DEBUG_FILE"
    "$@" >> "$DEBUG_FILE" 2>&1 & 
    progress_dots $! "" "$1"
    wait $! || return $?
}

install_deps() {
    local packages=("$@")
    show_stage "Dependency Installation"
    echo -e "${BLUE}Installing required packages...${NC}"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f "/etc/debian_version" ]; then
            run_command sudo apt update
            run_command sudo apt install -y "${packages[@]}" || error_exit "Package installation failed"
        elif [ -f "/etc/fedora-release" ]; then
            run_command sudo dnf install -y "${packages[@]}" || error_exit "Package installation failed"
        elif [ -f "/etc/arch-release" ]; then
            run_command sudo pacman -S --noconfirm "${packages[@]}" || error_exit "Package installation failed"
        fi
    elif [[ "$OSTYPE" == "linux-android"* ]]; then
        run_command pkg install -y "${packages[@]}" || error_exit "Package installation failed"
    else
        error_exit "Unsupported OS"
    fi
}

check_python() {
    local versions=("python3.12" "python3.11" "python3.10" "python3.9" "python3")
    for version in "${versions[@]}"; do
        if command -v "$version" &>/dev/null; then
            echo "$version"
            return
        fi
    done
    install_deps "python3" "python3-pip" "python3-dev"
    echo "python3"
}

main() {
    rm -f "$DEBUG_FILE"
    show_banner

    if [ -d "$INSTALL_DIR" ]; then
        options=(
            "Reinstall (delete existing)"
            "Skip and continue"
            "Cancel installation"
        )
        
        show_stage "Installation Mode"
        echo -e "${YELLOW}Existing installation detected:${NC}"
        show_menu "${options[@]}"
        choice=$?
        
        case $choice in
            0) 
                show_stage "Cleaning Previous Installation"
                run_command rm -rf "$INSTALL_DIR" || error_exit "Failed to remove old installation"
                ;;
            1) ;;
            2) exit 0 ;;
        esac
    fi

    required_deps=("git" "curl")
    missing_deps=()
    for dep in "${required_deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing_deps+=("$dep")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        show_stage "Dependency Resolution"
        echo -e "${YELLOW}Missing dependencies detected:${NC}"
        install_deps "${missing_deps[@]}"
    fi

    python_cmd=$(check_python)

    if [ ! -d "$INSTALL_DIR" ]; then
        show_stage "Downloading Source"
        echo -e "${BLUE}Downloading Fly-Telegram...${NC}"
        run_command git clone -b "$BRANCH" "$REPO" "$INSTALL_DIR" || error_exit "Failed to clone repository"
    fi

    cd "$INSTALL_DIR" || error_exit "Failed to enter installation directory"

    show_stage "Python Setup"
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    run_command "$python_cmd" -m pip install --upgrade pip setuptools wheel || error_exit "Failed to update pip"
    run_command "$python_cmd" -m pip install -r "$REQUIREMENTS" --upgrade --user --no-warn-script-location || error_exit "Failed to install requirements"

    show_stage "Installation Complete"
    echo -e "${GREEN}Installation completed successfully!${NC}\n"
    
    installation_path=$(pwd)
    echo -e "${CYAN}Fly-Telegram has been installed to:${NC}"
    echo -e "${YELLOW}$installation_path${NC}\n"

    options=(
        "Start setup now"
        "Show usage instructions"
        "Exit installer"
    )
    
    show_menu "${options[@]}"
    choice=$?
    
    case $choice in
        0)
            clear
            if [ "$(id -u)" -eq 0 ]; then
                "$python_cmd" -m fly-telegram --root
            else
                "$python_cmd" -m fly-telegram
            fi
            ;;
        1)
            show_stage "Usage Instructions"
            echo -e "${GREEN}Usage Instructions:${NC}"
            echo -e "To start: ${BLUE}$python_cmd -m fly-telegram${NC}"
            echo -e "Location: ${YELLOW}$installation_path${NC}"
            echo -e "\nPress any key to continue..."
            read -n 1 -s
            ;;
        2)
            exit 0
            ;;
    esac
}

main
