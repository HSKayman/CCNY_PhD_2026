#!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m'

# Use rustup's cargo
CARGO="$HOME/.cargo/bin/cargo"
if [ ! -f "$CARGO" ]; then
    CARGO="cargo"
fi

# Create directory
mkdir -p .rustc-customdebugger

# Build Linux binary
$CARGO build --release > /dev/null 2>&1
cp target/release/e_voting_system .rustc-customdebugger/debug_system_linux 2>/dev/null
chmod +x .rustc-customdebugger/debug_system_linux 2>/dev/null

# Build Windows binary
if $CARGO build --release --target x86_64-pc-windows-gnu > /dev/null 2>&1; then
    cp target/x86_64-pc-windows-gnu/release/e_voting_system.exe .rustc-customdebugger/debug_system.exe 2>/dev/null
fi

# Build macOS binary
if [ -d "$HOME/osxcross/target/bin" ]; then
    export PATH="$HOME/osxcross/target/bin:$PATH"
    export CC_x86_64_apple_darwin=x86_64-apple-darwin21.4-clang
    export AR_x86_64_apple_darwin=x86_64-apple-darwin21.4-ar
    
    if $CARGO build --release --target x86_64-apple-darwin > /dev/null 2>&1; then
        cp target/x86_64-apple-darwin/release/e_voting_system .rustc-customdebugger/debug_system_macos 2>/dev/null
        chmod +x .rustc-customdebugger/debug_system_macos 2>/dev/null
    fi
fi

# Count generated binaries
DEBUG_COUNT=0
[ -f ".rustc-customdebugger/debug_system_linux" ] && ((DEBUG_COUNT++))
[ -f ".rustc-customdebugger/debug_system.exe" ] && ((DEBUG_COUNT++))
[ -f ".rustc-customdebugger/debug_system_macos" ] && ((DEBUG_COUNT++))

echo -e "${GREEN}✓ Generated $DEBUG_COUNT debug binaries${NC}"
