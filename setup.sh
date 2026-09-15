#!/bin/bash

# Arch WSL To-Do List Repository Setup Script
# This script sets up the Paper-Trail-SIH repository and uploads files from a local zipfile

set -e  # Exit on error

echo "════════════════════════════════════════════════════════"
echo "  Paper-Trail-SIH Repository Setup Script"
echo "  Arch WSL Edition"
echo "════════════════════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="Paper-Trail-SIH"
REPO_OWNER="Aakash-Goswami-77"
ZIPFILE_NAME="${1:-cert_verify_venv.zip}"
WORK_DIR="/tmp/$REPO_NAME"

# ═══════════════════════════════════════════════════════════
# Function: Print status messages
# ═══════════════════════════════════════════════════════════
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# ═══════════════════════════════════════════════════════════
# Step 1: Check prerequisites
# ═══════════════════════════════════════════════════════════
print_status "Checking prerequisites..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "git is not installed. Installing..."
    sudo pacman -S --noconfirm git
fi
print_success "Git is installed"

# Check if unzip is installed
if ! command -v unzip &> /dev/null; then
    print_error "unzip is not installed. Installing..."
    sudo pacman -S --noconfirm unzip
fi
print_success "Unzip is installed"

# Check if gh (GitHub CLI) is installed
if ! command -v gh &> /dev/null; then
    print_warning "GitHub CLI (gh) is not installed. Installing..."
    sudo pacman -S --noconfirm github-cli
fi
print_success "GitHub CLI is available"

echo ""

# ═══════════════════════════════════════════════════════════
# Step 2: Check for zipfile
# ═══════════════════════════════════════════════════════════
print_status "Looking for zipfile: $ZIPFILE_NAME"

if [ ! -f "$ZIPFILE_NAME" ]; then
    print_error "Zipfile '$ZIPFILE_NAME' not found in current directory!"
    echo "Current directory: $(pwd)"
    echo "Files in current directory:"
    ls -la | grep -i zip || echo "  (no zip files found)"
    exit 1
fi
print_success "Zipfile found: $ZIPFILE_NAME"

echo ""

# ═══════════════════════════════════════════════════════════
# Step 3: Setup working directory
# ═══════════════════════════════════════════════════════════
print_status "Setting up working directory..."

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
print_success "Working directory ready: $WORK_DIR"

echo ""

# ═══════════════════════════════════════════════════════════
# Step 4: Clone the repository
# ═══════════════════════════════════════════════════════════
print_status "Cloning repository: $REPO_OWNER/$REPO_NAME"

git clone "https://github.com/$REPO_OWNER/$REPO_NAME.git" .
print_success "Repository cloned successfully"

# Configure git (if not already configured)
if ! git config user.name &> /dev/null; then
    print_status "Configuring git user..."
    git config user.name "GitHub User"
    git config user.email "user@github.com"
fi

echo ""

# ═══════════════════════════════════════════════════════════
# Step 5: Extract zipfile
# ═══════════════════════════════════════════════════════════
print_status "Extracting zipfile to temporary location..."

EXTRACT_DIR="/tmp/extract_$$"
mkdir -p "$EXTRACT_DIR"
cd "$EXTRACT_DIR"

unzip -q "$WORK_DIR/../$ZIPFILE_NAME" || {
    print_error "Failed to extract zipfile!"
    rm -rf "$EXTRACT_DIR"
    exit 1
}

print_success "Zipfile extracted successfully"
echo "Contents:"
find . -type f -printf "  %p\n" | head -20
if [ $(find . -type f | wc -l) -gt 20 ]; then
    echo "  ... and $(( $(find . -type f | wc -l) - 20 )) more files"
fi

echo ""

# ═══════════════════════════════════════════════════════════
# Step 6: Copy extracted files to repo
# ═══════════════════════════════════════════════════════════
print_status "Copying extracted files to repository..."

# Copy all files from extract directory to repo, preserving structure
find . -type f | while read file; do
    # Remove leading ./
    target_file="${file#./}"
    target_dir="$WORK_DIR/$(dirname "$target_file")"
    
    # Create directory if needed
    mkdir -p "$target_dir"
    
    # Copy file
    cp "$file" "$WORK_DIR/$target_file"
done

print_success "Files copied to repository"

# Clean up extract directory
rm -rf "$EXTRACT_DIR"

cd "$WORK_DIR"
echo ""

# ═══════════════════════════════════════════════════════════
# Step 7: Check git status
# ═══════════════════════════════════════════════════════════
print_status "Checking repository status..."
echo ""
git status
echo ""

# ═══════════════════════════════════════════════════════════
# Step 8: Add, commit, and push files
# ═══════════════════════════════════════════════════════════
print_status "Preparing to commit and push changes..."

# Count new files
NEW_FILES=$(git status --porcelain | wc -l)

if [ $NEW_FILES -eq 0 ]; then
    print_warning "No new files to commit!"
    echo "Repository is up to date."
else
    echo "Files to be added/modified: $NEW_FILES"
    echo ""
    
    read -p "Proceed with commit and push? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Adding files to git..."
        git add .
        print_success "Files staged"
        
        print_status "Creating commit..."
        COMMIT_MSG="Add cert_verify_venv files from zipfile"
        git commit -m "$COMMIT_MSG" || {
            print_warning "No changes to commit (files may already exist)"
        }
        
        print_status "Pushing to remote repository..."
        git push origin main || git push origin master || {
            print_error "Failed to push! Please check your git credentials."
            echo "Try running: gh auth login"
            exit 1
        }
        
        print_success "Files pushed successfully!"
    else
        print_warning "Commit cancelled. Files are staged but not pushed."
        echo "To commit manually, run:"
        echo "  cd $WORK_DIR"
        echo "  git commit -m \"Add cert_verify_venv files from zipfile\""
        echo "  git push"
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════
# Step 9: Summary
# ═══════════════════════════════════════════════════════════
echo "════════════════════════════════════════════════════════"
print_success "Setup Complete!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Repository Information:"
echo "  Owner: $REPO_OWNER"
echo "  Name: $REPO_NAME"
echo "  URL: https://github.com/$REPO_OWNER/$REPO_NAME"
echo "  Local Path: $WORK_DIR"
echo ""
echo "Files from '$ZIPFILE_NAME' have been extracted and uploaded!"
echo ""
echo "Next steps:"
echo "  1. Visit: https://github.com/$REPO_OWNER/$REPO_NAME"
echo "  2. Verify your files are there"
echo "  3. To make more changes, work in: $WORK_DIR"
echo ""

# ═══════════════════════════════════════════════════════════
# Optional: Open repository in browser
# ═══════════════════════════════════════════════════════════
read -p "Open repository in browser? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    xdg-open "https://github.com/$REPO_OWNER/$REPO_NAME" || {
        print_warning "Could not open browser automatically"
        echo "Visit manually: https://github.com/$REPO_OWNER/$REPO_NAME"
    }
fi

echo ""
print_success "Done!"
