#!/bin/bash
# deploy_nexus_os.sh - Deploys the NexusOS website files to aiseed server.
# Version 2.7.1 - TPC Aligned for NexusOS Rebel Glitch Edition

# --- Configuration - Adjust these to your environment ---
REMOTE_USER="aiseed"  # <<< CRITICAL: REPLACE with your SSH username for 'aiseed'
REMOTE_HOST="192.168.0.95"
REMOTE_WEB_ROOT_PARENT="/var/www/nexus_os_manifest" # As defined in setup script
REMOTE_WEB_ROOT_HTML="${REMOTE_WEB_ROOT_PARENT}/html" # Actual web root for Nginx

# LOCAL_SOURCE_DIR is the directory where this script is located,
# assuming it's in the root of your website project files.
LOCAL_SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Nginx service name and user on remote server (must match setup script)
NGINX_SERVICE_NAME="nginx"
NGINX_FS_USER="www-data" # Typical Nginx user on Debian/Ubuntu systems

# --- Strict Mode & Helper Functions ---
set -eo pipefail 

echo_color() { local color_code="$1"; shift; local message="$*"; echo -e "\033[${color_code}m${message}\033[0m"; }
info() { echo_color "34" "[INFO] $1"; }
warning() { echo_color "33" "[WARN] $1"; }
error() { echo_color "31" "[ERROR] $1"; }
success() { echo_color "32" "[SUCCESS] $1"; }
cmd_echo() { echo_color "36" "CMD: $1"; }

# --- Script Start ---
info "Omnitide NexusOS Website Deployment Protocol v2.7.1 to ${REMOTE_USER}@${REMOTE_HOST}"
info "Target Server Web Root: ${REMOTE_WEB_ROOT_HTML}"
info "Local Source Directory: ${LOCAL_SOURCE_DIR}"
echo ""

# 0. Confirmation
if [ "${REMOTE_USER}" == "aiseed_deploy_user" ]; then
    warning "The REMOTE_USER variable is set to the default 'aiseed_deploy_user'."
    read -r -p "Please confirm this is your correct SSH username for ${REMOTE_HOST} or Ctrl+C to edit script: [Enter to continue]"
fi
read -r -p "Proceed with deployment to ${REMOTE_HOST}? (y/N): " CONFIRM_DEPLOY
if [[ ! "$CONFIRM_DEPLOY" =~ ^[Yy]$ ]]; then
    error "Deployment aborted by Architect."
    exit 1
fi

# 1. Check Local Source Files (Essentials)
info "Verifying essential local source files..."
if [ ! -f "${LOCAL_SOURCE_DIR}/index.html" ]; then
    error "'index.html' not found in local source: ${LOCAL_SOURCE_DIR}."
    exit 1
fi
if [ ! -f "${LOCAL_SOURCE_DIR}/style.css" ]; then
    error "'style.css' not found in local source."
    exit 1
fi
if [ ! -f "${LOCAL_SOURCE_DIR}/script.js" ]; then
    error "'script.js' not found in local source."
    exit 1
fi
if [ ! -d "${LOCAL_SOURCE_DIR}/js/lib" ] || [ ! -f "${LOCAL_SOURCE_DIR}/js/lib/openpgp.min.js" ]; then
    error "'openpgp.min.js' MUST be present in '${LOCAL_SOURCE_DIR}/js/lib/'."
    error "Please download it from https://github.com/openpgpjs/openpgpjs/releases/tag/v5.11.1"
    error "The Secure Channel app WILL NOT FUNCTION without the actual library."
    # If you want to proceed with the STUB for testing (NOT RECOMMENDED FOR SECURE USE):
    # read -r -p "WARN: openpgp.min.js is missing or is a stub. Continue for non-PGP testing? (y/N): " CONTINUE_NO_PGP
    # if [[ ! "$CONTINUE_NO_PGP" =~ ^[Yy]$ ]]; then exit 1; fi
    exit 1 # Hard fail if real library isn't expected to be there.
fi
success "Essential local files verified."
echo ""

# 2. Verify Remote Web Root Parent Directory (created by setup script)
info "Verifying remote parent web root directory '${REMOTE_WEB_ROOT_PARENT}'..."
cmd_echo "ssh \"${REMOTE_USER}@${REMOTE_HOST}\" \"if [ -d ${REMOTE_WEB_ROOT_PARENT} ]; then echo 'exists'; else echo 'not_exists'; fi\""
REMOTE_DIR_CHECK=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "if [ -d ${REMOTE_WEB_ROOT_PARENT} ]; then echo 'exists'; else echo 'not_exists'; fi")

if [ "$REMOTE_DIR_CHECK" != "exists" ]; then
    error "Remote parent web root '${REMOTE_WEB_ROOT_PARENT}' does not exist on ${REMOTE_HOST}."
    error "Please run the 'setup_aiseed_nexusos_server_vX.X.sh' script on '${REMOTE_HOST}' first."
    exit 1
fi
success "Remote parent web root verified."
echo ""

# 3. Sync Files with rsync
info "Syncing website files to server (${REMOTE_WEB_ROOT_HTML}) using rsync..."
# -a: archive (recursive, preserves perms, times, owner, group if possible by user)
# -v: verbose
# -z: compress
# --checksum: smarter diffing
# --delete: remove extraneous files from destination
# --progress: show progress
EXCLUDES=(
    ".git/" ".github/" ".vscode/" "node_modules/" "*.log" "deploy_nexus_os.sh"
    ".DS_Store" "Thumbs.db" "*.swp" "*.swo" "*-bak*" "*~"
)
RSYNC_EXCLUDES_STRING=""
for item in "${EXCLUDES[@]}"; do
    RSYNC_EXCLUDES_STRING+="--exclude='${item}' "
done

# Ensure trailing slash on LOCAL_SOURCE_DIR to copy contents *into* REMOTE_WEB_ROOT_HTML
cmd_echo "rsync -avz --checksum --delete --progress ${RSYNC_EXCLUDES_STRING} \"${LOCAL_SOURCE_DIR}/\" \"${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_WEB_ROOT_HTML}/\""
eval "rsync -avz --checksum --delete --progress ${RSYNC_EXCLUDES_STRING} \"${LOCAL_SOURCE_DIR}/\" \"${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_WEB_ROOT_HTML}/\""

if [ $? -eq 0 ]; then
    success "Files synced successfully via rsync."
else
    error "rsync failed. Check SSH connection, permissions for user '${REMOTE_USER}' on remote path '${REMOTE_WEB_ROOT_HTML}', or rsync command output."
    exit 1
fi
echo ""

# 4. Set Final Ownership and Permissions on Remote Server
info "Setting final ownership and permissions on remote server..."
# These commands require REMOTE_USER to have passwordless sudo for chown and chmod.
# If not, these steps must be performed manually on the server by a sudoer.
PERMISSION_COMMANDS_FINAL="
    echo 'Attempting to set ownership to ${NGINX_FS_USER}:${NGINX_FS_USER} for content in ${REMOTE_WEB_ROOT_HTML}...' && \
    sudo chown -R \"${NGINX_FS_USER}\":\"${NGINX_FS_USER}\" \"${REMOTE_WEB_ROOT_HTML}\" && \
    echo 'Setting directory permissions (755: rwxr-xr-x) for Nginx access...' && \
    sudo find \"${REMOTE_WEB_ROOT_HTML}\" -type d -exec chmod 755 {} \; && \
    echo 'Setting file permissions (644: rw-r--r--) for Nginx access...' && \
    sudo find \"${REMOTE_WEB_ROOT_HTML}\" -type f -exec chmod 644 {} \; && \
    echo 'Final permissions and ownership set. Nginx user ${NGINX_FS_USER} should now have read access.'
"
cmd_echo "ssh \"${REMOTE_USER}@${REMOTE_HOST}\" \"${PERMISSION_COMMANDS_FINAL}\""
ssh "${REMOTE_USER}@${REMOTE_HOST}" "${PERMISSION_COMMANDS_FINAL}"
if [ $? -eq 0 ]; then
    success "Ownership and permissions commands sent to remote server."
    warning "Verify output above to ensure commands executed successfully on remote."
else
    error "Failed to execute permission-setting commands on remote server."
    warning "Please manually ensure on ${REMOTE_HOST} that user '${NGINX_FS_USER}' can read all files in '${REMOTE_WEB_ROOT_HTML}' and execute directories."
fi
echo ""

# 5. Test Nginx Configuration and Reload Service on Remote (Optional, as setup script should handle it)
info "The Nginx service on ${REMOTE_HOST} should ideally be reloaded to pick up any subtle changes, though file content changes don't always require it if Nginx caches aggressively."
read -r -p "Attempt to test Nginx config and reload service on ${REMOTE_HOST}? (Requires sudo for '${REMOTE_USER}') (y/N): " RELOAD_NGINX
if [[ "$RELOAD_NGINX" =~ ^[Yy]$ ]]; then
    NGINX_RELOAD_COMMANDS="
        echo 'Testing Nginx configuration on remote...' && \
        sudo nginx -t && \
        echo 'Reloading Nginx service on remote...' && \
        sudo systemctl reload \"${NGINX_SERVICE_NAME}\" && \
        echo 'Nginx reloaded. Checking status briefly...' && \
        sudo systemctl status --no-pager -l \"${NGINX_SERVICE_NAME}\" | head -n 10
    "
    cmd_echo "ssh \"${REMOTE_USER}@${REMOTE_HOST}\" \"${NGINX_RELOAD_COMMANDS}\""
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "${NGINX_RELOAD_COMMANDS}"
    if [ $? -eq 0 ]; then
        success "Nginx configuration tested and service reloaded on ${REMOTE_HOST}."
    else
        error "Nginx test or reload FAILED on ${REMOTE_HOST} during deployment script."
        warning "Check Nginx status and logs manually on ${REMOTE_HOST}:"
        warning "  sudo nginx -t"
        warning "  sudo systemctl status ${NGINX_SERVICE_NAME}"
        warning "  sudo journalctl -xeu ${NGINX_SERVICE_NAME}"
    fi
else
    info "Skipping Nginx reload. If Nginx was already running correctly with the right config, new files should be served."
    info "If you encounter issues, manually run 'sudo nginx -t && sudo systemctl reload nginx' on ${REMOTE_HOST}."
fi
echo ""

success "--- NexusOS Website Content Deployment Finished ---"
info "Website files have been deployed to 'aiseed' at '${REMOTE_WEB_ROOT_HTML}'."
info "Access your NexusOS Website at (remember to accept self-signed SSL cert warning):"
info "  HTTPS: https://${REMOTE_HOST}:8448"
info "  (HTTP http://${REMOTE_HOST}:8488 should redirect to HTTPS)"
info "If using local DNS for 'nexus.local', use https://nexus.local:8448."
echo ""
info "Ensure Nginx is running correctly on ${REMOTE_HOST} and listening on ports 8488/8448."
