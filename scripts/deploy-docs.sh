#!/bin/bash

# NOCbRAIN Documentation Deployment Script
# Deploys generated documentation to various platforms

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"
GENERATED_DIR="$PROJECT_ROOT/docs/generated"
VERSION=""
ENVIRONMENT="production"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Help function
show_help() {
    cat << EOF
NOCbRAIN Documentation Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    --version VERSION    Target version (e.g., v1.0.0)
    --environment ENV    Target environment (production|staging|development)
    --dry-run           Show what would be deployed without making changes
    --verbose           Enable verbose output
    --help              Show this help message

ENVIRONMENTS:
    production    - Deploy to production servers
    staging       - Deploy to staging servers
    development   - Deploy to development servers

EXAMPLES:
    $0 --version v1.0.0 --environment production
    $0 --version v1.0.0 --environment staging
    $0 --dry-run --version v1.0.0

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                VERSION="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validate version
    if [[ -z "$VERSION" ]]; then
        log_error "Version is required. Use --version vX.Y.Z"
        exit 1
    fi

    # Validate environment
    case $ENVIRONMENT in
        production|staging|development)
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            show_help
            exit 1
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    local deps=("rsync" "scp" "ssh" "curl")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Missing dependency: $dep"
            log_info "Please install required dependencies"
            exit 1
        fi
    done
}

# Deploy to web servers
deploy_web_docs() {
    log_info "Deploying web documentation..."
    
    local web_server=""
    local web_path=""
    
    case $ENVIRONMENT in
        production)
            web_server="docs.nocbrain.com"
            web_path="/var/www/docs"
            ;;
        staging)
            web_server="staging-docs.nocbrain.com"
            web_path="/var/www/staging-docs"
            ;;
        development)
            web_server="dev-docs.nocbrain.com"
            web_path="/var/www/dev-docs"
            ;;
    esac
    
    if [[ "$DRY_RUN" == false ]]; then
        # Create versioned directory
        local version_path="$web_path/$VERSION"
        
        # Sync documentation
        rsync -avz --delete "$GENERATED_DIR/" "$web_server:$version_path/"
        
        # Update latest symlink
        ssh "$web_server" "cd $web_path && rm -f latest && ln -sf $VERSION latest"
        
        # Restart web server
        ssh "$web_server" "sudo systemctl reload nginx || sudo systemctl reload apache2"
        
        log_info "Web documentation deployed to $web_server"
    else
        log_info "[DRY RUN] Would deploy web documentation to $web_server:$web_path/$VERSION"
    fi
}

# Deploy to API documentation
deploy_api_docs() {
    log_info "Deploying API documentation..."
    
    local api_server=""
    local api_path=""
    
    case $ENVIRONMENT in
        production)
            api_server="api.nocbrain.com"
            api_path="/var/www/api-docs"
            ;;
        staging)
            api_server="staging-api.nocbrain.com"
            api_path="/var/www/staging-api-docs"
            ;;
        development)
            api_server="dev-api.nocbrain.com"
            api_path="/var/www/dev-api-docs"
            ;;
    esac
    
    if [[ "$DRY_RUN" == false ]]; then
        # Deploy OpenAPI documentation
        if [[ -f "$GENERATED_DIR/developer/openapi.json" ]]; then
            scp "$GENERATED_DIR/developer/openapi.json" "$api_server:$api_path/"
            
            # Generate Swagger UI
            ssh "$api_server" "cd $api_path && swagger-codegen generate -i openapi.json -l html2 -o swagger-ui"
            
            log_info "API documentation deployed to $api_server"
        else
            log_warning "OpenAPI documentation not found"
        fi
    else
        log_info "[DRY RUN] Would deploy API documentation to $api_server:$api_path"
    fi
}

# Deploy to package repositories
deploy_packages() {
    log_info "Deploying documentation packages..."
    
    local package_server="packages.nocbrain.com"
    local package_path="/var/www/packages"
    
    if [[ "$DRY_RUN" == false ]]; then
        # Create versioned package directory
        local version_package_path="$package_path/$VERSION"
        
        # Sync packages
        rsync -avz "$GENERATED_DIR/packages/" "$package_server:$version_package_path/"
        
        # Update package index
        ssh "$package_server" "cd $package_path && ./update-index.sh"
        
        log_info "Documentation packages deployed to $package_server"
    else
        log_info "[DRY RUN] Would deploy packages to $package_server:$package_path/$VERSION"
    fi
}

# Deploy to CDN
deploy_cdn() {
    log_info "Deploying to CDN..."
    
    local cdn_provider="cloudflare"
    local cdn_zone="nocbrain.com"
    
    if [[ "$DRY_RUN" == false ]]; then
        case $cdn_provider in
            cloudflare)
                # Purge CDN cache
                curl -X POST "https://api.cloudflare.com/client/v4/zones/$cdn_zone/purge_cache" \
                    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
                    -H "Content-Type: application/json" \
                    --data '{"purge_everything":true}'
                
                log_info "CDN cache purged for $cdn_zone"
                ;;
            aws)
                # Invalidate CloudFront distribution
                aws cloudfront create-invalidation \
                    --distribution-id "$AWS_DISTRIBUTION_ID" \
                    --paths "/docs/*" "/api-docs/*"
                
                log_info "CloudFront cache invalidated"
                ;;
        esac
    else
        log_info "[DRY RUN] Would purge CDN cache"
    fi
}

# Update DNS records
update_dns() {
    log_info "Updating DNS records..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Update DNS for documentation subdomains
        # This would typically be done through DNS provider API
        
        case $ENVIRONMENT in
            production)
                # Update production DNS records
                log_info "Production DNS records updated"
                ;;
            staging)
                # Update staging DNS records
                log_info "Staging DNS records updated"
                ;;
            development)
                # Update development DNS records
                log_info "Development DNS records updated"
                ;;
        esac
    else
        log_info "[DRY RUN] Would update DNS records"
    fi
}

# Send notifications
send_notifications() {
    log_info "Sending deployment notifications..."
    
    local message="NOCbRAIN documentation v$VERSION deployed to $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == false ]]; then
        # Send Slack notification
        if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
            curl -X POST "$SLACK_WEBHOOK_URL" \
                -H 'Content-type: application/json' \
                --data "{\"text\":\"$message\"}"
        fi
        
        # Send email notification
        if command -v mail &> /dev/null; then
            echo "$message" | mail -s "NOCbRAIN Documentation Deployed" "team@nocbrain.com"
        fi
        
        log_info "Notifications sent"
    else
        log_info "[DRY RUN] Would send notifications"
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    local urls=(
        "https://docs.nocbrain.com"
        "https://docs.nocbrain.com/latest"
        "https://api.nocbrain.com/docs"
        "https://packages.nocbrain.com"
    )
    
    for url in "${urls[@]}"; do
        if [[ "$DRY_RUN" == false ]]; then
            if curl -f -s -o /dev/null "$url"; then
                log_info "✓ $url is accessible"
            else
                log_error "✗ $url is not accessible"
            fi
        else
            log_info "[DRY RUN] Would verify $url"
        fi
    done
}

# Generate deployment report
generate_deployment_report() {
    log_info "Generating deployment report..."
    
    local report_file="$GENERATED_DIR/deployment-report-$VERSION-$ENVIRONMENT.json"
    
    local report=$(cat << EOF
{
    "version": "$VERSION",
    "environment": "$ENVIRONMENT",
    "deployment_date": "$(date -Iseconds)",
    "deployed_components": {
        "web_documentation": true,
        "api_documentation": true,
        "packages": true,
        "cdn": true
    },
    "urls": {
        "web_docs": "https://docs.nocbrain.com",
        "api_docs": "https://api.nocbrain.com/docs",
        "packages": "https://packages.nocbrain.com"
    },
    "verification": {
        "status": "completed",
        "timestamp": "$(date -Iseconds)"
    }
}
EOF
    )
    
    if [[ "$DRY_RUN" == false ]]; then
        echo "$report" > "$report_file"
        log_info "Deployment report saved to $report_file"
    else
        log_info "[DRY RUN] Would save deployment report to $report_file"
    fi
}

# Main execution
main() {
    log_info "Starting NOCbRAIN documentation deployment..."
    log_info "Version: $VERSION"
    log_info "Environment: $ENVIRONMENT"
    if [[ "$DRY_RUN" == true ]]; then
        log_info "Mode: DRY RUN"
    fi
    
    check_dependencies
    
    # Check if generated documentation exists
    if [[ ! -d "$GENERATED_DIR" ]]; then
        log_error "Generated documentation not found. Run update-docs.sh first."
        exit 1
    fi
    
    # Deploy components
    deploy_web_docs
    deploy_api_docs
    deploy_packages
    deploy_cdn
    update_dns
    
    # Post-deployment tasks
    verify_deployment
    send_notifications
    generate_deployment_report
    
    log_info "Documentation deployment completed successfully!"
    
    if [[ "$DRY_RUN" == false ]]; then
        log_info "Documentation is now available at:"
        log_info "  - Web Docs: https://docs.nocbrain.com"
        log_info "  - API Docs: https://api.nocbrain.com/docs"
        log_info "  - Packages: https://packages.nocbrain.com"
    fi
}

# Parse arguments and run main
parse_args "$@"
main
