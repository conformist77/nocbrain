#!/bin/bash

# NOCbRAIN Documentation Auto-Update Script
# Automatically updates all documentation categories based on version changes

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"
TEMPLATES_DIR="$PROJECT_ROOT/docs/templates"
OUTPUT_DIR="$PROJECT_ROOT/docs/generated"
VERSION=""
CATEGORY=""
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
NOCbRAIN Documentation Auto-Update Script

Usage: $0 [OPTIONS]

OPTIONS:
    --version VERSION    Target version (e.g., v1.0.0)
    --category CATEGORY  Update specific category only
                        (developer|operations|noc-soc|marketing|ai-ml)
    --dry-run           Show what would be updated without making changes
    --verbose           Enable verbose output
    --help              Show this help message

EXAMPLES:
    $0 --version v1.0.0
    $0 --category developer --version v1.0.0
    $0 --dry-run --version v1.0.0

CATEGORIES:
    developer     - Developer documentation
    operations    - Operations documentation
    noc-soc       - NOC/SOC documentation
    marketing     - Marketing documentation
    ai-ml         - AI/ML documentation (XML format)

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
            --category)
                CATEGORY="$2"
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

    # Validate category if provided
    if [[ -n "$CATEGORY" ]]; then
        case $CATEGORY in
            developer|operations|noc-soc|marketing|ai-ml)
                ;;
            *)
                log_error "Invalid category: $CATEGORY"
                show_help
                exit 1
                ;;
        esac
    fi
}

# Check dependencies
check_dependencies() {
    local deps=("pandoc" "wkhtmltopdf" "xmllint" "jq")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Missing dependency: $dep"
            log_info "Please install required dependencies:"
            log_info "  Ubuntu/Debian: sudo apt-get install pandoc wkhtmltopdf libxml2-utils jq"
            log_info "  CentOS/RHEL: sudo yum install pandoc wkhtmltopdf libxml2 jq"
            log_info "  macOS: brew install pandoc wkhtmltopdf libxml2 jq"
            exit 1
        fi
    done
}

# Create output directory
create_output_dir() {
    if [[ "$DRY_RUN" == false ]]; then
        mkdir -p "$OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR/developer"
        mkdir -p "$OUTPUT_DIR/operations"
        mkdir -p "$OUTPUT_DIR/noc-soc"
        mkdir -p "$OUTPUT_DIR/marketing"
        mkdir -p "$OUTPUT_DIR/ai-ml"
        mkdir -p "$OUTPUT_DIR/packages"
        log_info "Created output directory: $OUTPUT_DIR"
    fi
}

# Extract version information from code
extract_version_info() {
    log_info "Extracting version information..."
    
    # Get version from backend
    local backend_version=$(grep -r "VERSION.*=" "$PROJECT_ROOT/backend/app/core/config.py" | cut -d'"' -f2)
    
    # Get version from frontend
    local frontend_version=$(grep -r '"version"' "$PROJECT_ROOT/frontend/package.json" | cut -d'"' -f4)
    
    # Get last commit info
    local last_commit=$(git -C "$PROJECT_ROOT" log -1 --format="%H")
    local commit_date=$(git -C "$PROJECT_ROOT" log -1 --format="%ci")
    
    # Create version info JSON
    local version_info=$(cat << EOF
{
    "version": "$VERSION",
    "backend_version": "$backend_version",
    "frontend_version": "$frontend_version",
    "git_commit": "$last_commit",
    "commit_date": "$commit_date",
    "build_date": "$(date -Iseconds)",
    "build_environment": "$(uname -s)",
    "python_version": "$(python3 --version)",
    "node_version": "$(node --version)"
}
EOF
    )
    
    if [[ "$DRY_RUN" == false ]]; then
        echo "$version_info" > "$OUTPUT_DIR/version-info.json"
        log_info "Version info saved to $OUTPUT_DIR/version-info.json"
    fi
    
    log_debug "Version info: $version_info"
}

# Update developer documentation
update_developer_docs() {
    log_info "Updating developer documentation..."
    
    # Generate API documentation
    if [[ "$DRY_RUN" == false ]]; then
        # Generate from backend FastAPI
        cd "$PROJECT_ROOT/backend"
        python -c "
import sys
sys.path.append('.')
from app.main import app
import json
openapi_spec = app.openapi()
with open('$OUTPUT_DIR/developer/openapi.json', 'w') as f:
    json.dump(openapi_spec, f, indent=2)
"
        
        # Convert OpenAPI to HTML
        pandoc "$OUTPUT_DIR/developer/openapi.json" -o "$OUTPUT_DIR/developer/api-reference.html"
        
        # Generate architecture documentation
        python "$SCRIPT_DIR/generate-architecture-docs.py" --output "$OUTPUT_DIR/developer/architecture.md"
        
        # Generate module documentation
        python "$SCRIPT_DIR/generate-module-docs.py" --source "$PROJECT_ROOT/backend" --output "$OUTPUT_DIR/developer/modules.md"
        
        # Create developer guide index
        cat > "$OUTPUT_DIR/developer/index.md" << EOF
# NOCbRAIN Developer Documentation

## Version: $VERSION

### 📚 Table of Contents

1. [Architecture Overview](architecture.md)
2. [API Reference](api-reference.html)
3. [Module Documentation](modules.md)
4. [Development Setup](setup.md)
5. [Testing Guide](testing.md)
6. [Deployment Guide](deployment.md)

### 🔗 Quick Links

- **API Base URL**: https://api.nocbrain.com
- **WebSocket URL**: wss://api.nocbrain.com/ws
- **Repository**: https://github.com/conformist77/nocbrain

---
*Generated on: $(date)*
EOF
        
        log_info "Developer documentation updated"
    else
        log_info "[DRY RUN] Would update developer documentation"
    fi
}

# Update operations documentation
update_operations_docs() {
    log_info "Updating operations documentation..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Generate installation guides
        python "$SCRIPT_DIR/generate-installation-guide.py" --output "$OUTPUT_DIR/operations/installation.md"
        
        # Generate maintenance procedures
        python "$SCRIPT_DIR/generate-maintenance-guide.py" --output "$OUTPUT_DIR/operations/maintenance.md"
        
        # Generate troubleshooting guide
        python "$SCRIPT_DIR/generate-troubleshooting-guide.py" --output "$OUTPUT_DIR/operations/troubleshooting.md"
        
        # Generate infrastructure documentation
        python "$SCRIPT_DIR/generate-infrastructure-docs.py" --output "$OUTPUT_DIR/operations/infrastructure.md"
        
        # Create operations guide index
        cat > "$OUTPUT_DIR/operations/index.md" << EOF
# NOCbRAIN Operations Documentation

## Version: $VERSION

### 📚 Table of Contents

1. [Installation Guide](installation.md)
2. [Maintenance Procedures](maintenance.md)
3. [Troubleshooting Guide](troubleshooting.md)
4. [Infrastructure Overview](infrastructure.md)
5. [Backup & Recovery](backup-recovery.md)
6. [Security Procedures](security.md)

### 🔧 Quick Commands

\`\`\`bash
# Check service status
systemctl status nocbrain-backend
systemctl status nocbrain-frontend

# View logs
journalctl -u nocbrain-backend -f
journalctl -u nocbrain-frontend -f

# Restart services
systemctl restart nocbrain-backend
systemctl restart nocbrain-frontend
\`\`\`

### 📞 Support Contacts

- **Technical Support**: support@nocbrain.com
- **Emergency Contact**: emergency@nocbrain.com
- **Documentation**: https://ops.nocbrain.com

---
*Generated on: $(date)*
EOF
        
        log_info "Operations documentation updated"
    else
        log_info "[DRY RUN] Would update operations documentation"
    fi
}

# Update NOC/SOC documentation
update_noc_soc_docs() {
    log_info "Updating NOC/SOC documentation..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Generate user guides
        python "$SCRIPT_DIR/generate-user-guide.py" --output "$OUTPUT_DIR/noc-soc/user-guide.md"
        
        # Generate alert management guide
        python "$SCRIPT_DIR/generate-alert-guide.py" --output "$OUTPUT_DIR/noc-soc/alert-management.md"
        
        # Generate incident response procedures
        python "$SCRIPT_DIR/generate-incident-response.py" --output "$OUTPUT_DIR/noc-soc/incident-response.md"
        
        # Generate monitoring procedures
        python "$SCRIPT_DIR/generate-monitoring-guide.py" --output "$OUTPUT_DIR/noc-soc/monitoring.md"
        
        # Create NOC/SOC portal index
        cat > "$OUTPUT_DIR/noc-soc/index.md" << EOF
# NOCbRAIN NOC/SOC Operations Portal

## Version: $VERSION

### 🚀 Quick Start

1. **Login**: https://portal.nocbrain.com
2. **Dashboard**: View real-time network status
3. **Alerts**: Manage and acknowledge alerts
4. **Reports**: Generate and view reports

### 📚 User Guides

1. [User Guide](user-guide.md)
2. [Alert Management](alert-management.md)
3. [Incident Response](incident-response.md)
4. [Monitoring Procedures](monitoring.md)

### 🎯 Daily Procedures

**Morning Checklist:**
- [ ] Review overnight alerts
- [ ] Check system health status
- [ ] Verify backup completion
- [ ] Review performance metrics

**Ongoing Monitoring:**
- [ ] Monitor network performance
- [ ] Respond to critical alerts
- [ ] Document incidents
- [ ] Update knowledge base

### 📞 Emergency Contacts

- **Critical Issues**: emergency@nocbrain.com | +1-555-EMERGENCY
- **Technical Support**: support@nocbrain.com | +1-555-SUPPORT
- **On-call Engineer**: oncall@nocbrain.com

---
*Generated on: $(date)*
EOF
        
        log_info "NOC/SOC documentation updated"
    else
        log_info "[DRY RUN] Would update NOC/SOC documentation"
    fi
}

# Update marketing documentation
update_marketing_docs() {
    log_info "Updating marketing documentation..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Generate product overview
        python "$SCRIPT_DIR/generate-product-overview.py" --output "$OUTPUT_DIR/marketing/product-overview.md"
        
        # Generate feature comparison
        python "$SCRIPT_DIR/generate-feature-comparison.py" --output "$OUTPUT_DIR/marketing/features.md"
        
        # Generate case studies
        python "$SCRIPT_DIR/generate-case-studies.py" --output "$OUTPUT_DIR/marketing/case-studies.md"
        
        # Generate technical specifications
        python "$SCRIPT_DIR/generate-tech-specs.py" --output "$OUTPUT_DIR/marketing/technical-specs.md"
        
        # Create marketing index
        cat > "$OUTPUT_DIR/marketing/index.md" << EOF
# NOCbRAIN Marketing Documentation

## Version: $VERSION

### 🎯 Product Overview

NOCbRAIN is an AI-powered Network Operations Center Assistant designed for modern IT infrastructure monitoring and security analysis.

### 📊 Key Features

- **Real-time Monitoring**: Comprehensive network and infrastructure monitoring
- **AI-Powered Analysis**: Advanced threat detection and anomaly identification
- **Multi-Platform Support**: Windows, Linux, macOS, and cloud platforms
- **Secure Architecture**: End-to-end encryption and zero-trust security model
- **Scalable Design**: Built for enterprise-scale deployments

### 📈 Target Markets

- **Enterprise IT**: Large organizations with complex infrastructure
- **MSSPs**: Managed Security Service Providers
- **Telecommunications**: Network operators and service providers
- **Government**: Public sector organizations with security requirements

### 🚀 Competitive Advantages

1. **AI Integration**: Advanced machine learning for threat detection
2. **Unified Platform**: Single solution for monitoring and security
3. **Open Source**: Transparent and customizable
4. **Global SaaS**: Scalable cloud-native architecture
5. **Community Driven**: Active open-source community

### 📞 Sales & Marketing Contacts

- **Sales Team**: sales@nocbrain.com
- **Partnerships**: partners@nocbrain.com
- **Press Inquiries**: press@nocbrain.com
- **Demo Requests**: demo@nocbrain.com

---
*Generated on: $(date)*
EOF
        
        log_info "Marketing documentation updated"
    else
        log_info "[DRY RUN] Would update marketing documentation"
    fi
}

# Update AI/ML documentation (XML format)
update_ai_ml_docs() {
    log_info "Updating AI/ML documentation (XML format)..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Generate XML documentation for AI systems
        cat > "$OUTPUT_DIR/ai-ml/nocbrain-system.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<system xmlns="http://www.nocbrain.com/schema/system">
    <metadata>
        <name>NOCbRAIN</name>
        <version>$VERSION</version>
        <type>AI Network Operations Center Assistant</type>
        <category>Monitoring, Security, Infrastructure Management</category>
        <description>
            NOCbRAIN is an AI-powered assistant for network operations centers,
            providing comprehensive monitoring, security analysis, and infrastructure management.
        </description>
        <created>2024-02-14</created>
        <last_updated>$(date -Iseconds)</last_updated>
        <license>MIT</license>
        <repository>https://github.com/conformist77/nocbrain</repository>
    </metadata>
    
    <architecture>
        <components>
            <component>
                <name>Backend API</name>
                <technology>Python FastAPI</technology>
                <purpose>RESTful API and business logic</purpose>
                <dependencies>PostgreSQL, Redis, Celery</dependencies>
            </component>
            <component>
                <name>Frontend</name>
                <technology>React TypeScript</technology>
                <purpose>User interface and dashboard</purpose>
                <dependencies>Ant Design, React Query</dependencies>
            </component>
            <component>
                <name>Monitoring Agent</name>
                <technology>Python</technology>
                <purpose>Data collection from systems</purpose>
                <dependencies>psutil, cryptography</dependencies>
            </component>
            <component>
                <name>AI/ML Engine</name>
                <technology>PyTorch, LangChain</technology>
                <purpose>Threat detection and analysis</purpose>
                <dependencies>OpenAI API, scikit-learn</dependencies>
            </component>
        </components>
        
        <data_flow>
            <flow>
                <source>Monitoring Agent</source>
                <destination>Backend API</destination>
                <protocol>HTTPS</protocol>
                <encryption>AES-256</encryption>
            </flow>
            <flow>
                <source>Backend API</source>
                <destination>Frontend</destination>
                <protocol>WebSocket</protocol>
                <encryption>WSS</encryption>
            </flow>
            <flow>
                <source>Backend API</source>
                <destination>AI/ML Engine</destination>
                <protocol>Internal API</protocol>
                <encryption>Internal</encryption>
            </flow>
        </data_flow>
    </architecture>
    
    <capabilities>
        <capability>
            <name>Network Monitoring</name>
            <description>Real-time network device monitoring with SNMP support</description>
            <methods>SNMP, Agent-based, NetFlow</methods>
        </capability>
        <capability>
            <name>Security Analysis</name>
            <description>AI-powered threat detection and security analysis</description>
            <methods>SIEM integration, XDR analysis, ML algorithms</methods>
        </capability>
        <capability>
            <name>Infrastructure Management</name>
            <description>Comprehensive infrastructure monitoring and management</description>
            <methods>VMware ESX, KVM, Cloud APIs</methods>
        </capability>
        <capability>
            <name>Alert Management</name>
            <description>Intelligent alerting and incident response</description>
            <methods>Rule-based, ML-based, correlation</methods>
        </capability>
    </capabilities>
    
    <test_scenarios>
        <scenario>
            <name>System Health Check</name>
            <description>Verify all system components are operational</description>
            <steps>
                <step>Check API health endpoint</step>
                <step>Verify database connectivity</step>
                <step>Test agent communication</step>
                <step>Validate AI/ML engine</step>
            </steps>
            <expected_results>
                <result>All services respond with HTTP 200</result>
                <result>Database queries execute successfully</result>
                <result>Agents send metrics without errors</result>
                <result>AI/ML engine processes requests</result>
            </expected_results>
        </scenario>
        
        <scenario>
            <name>Security Alert Generation</name>
            <description>Test security alert generation and notification</description>
            <steps>
                <step>Simulate security event</step>
                <step>Verify alert rule execution</step>
                <step>Check notification delivery</step>
                <step>Validate alert acknowledgment</step>
            </steps>
            <expected_results>
                <result>Alert generated within 30 seconds</result>
                <result>Notification sent to configured channels</result>
                <result>Alert appears in dashboard</result>
                <result>Alert can be acknowledged</result>
            </expected_results>
        </scenario>
    </test_scenarios>
    
    <integration_points>
        <integration>
            <name>SIEM Systems</name>
            <type>Security Information and Event Management</type>
            <protocols>Syslog, REST API, CEF</protocols>
            <examples>Splunk, ELK Stack, QRadar</examples>
        </integration>
        <integration>
            <name>Cloud Platforms</name>
            <type>Infrastructure as a Service</type>
            <protocols>REST API, SDK</protocols>
            <examples>AWS, Azure, Google Cloud</examples>
        </integration>
        <integration>
            <name>Monitoring Tools</name>
            <type>Network Monitoring</type>
            <protocols>SNMP, NetFlow, sFlow</protocols>
            <examples>Prometheus, Grafana, Zabbix</examples>
        </integration>
    </integration_points>
    
    <security_model>
        <authentication>
            <method>JWT Bearer Tokens</method>
            <refresh_token_rotation>true</refresh_token_rotation>
            <session_timeout>8 hours</session_timeout>
        </authentication>
        <authorization>
            <model>Role-Based Access Control (RBAC)</model>
            <roles>Admin, Operator, Analyst, Viewer</roles>
            <permissions>Granular permission system</permissions>
        </authorization>
        <encryption>
            <in_transit>TLS 1.3</in_transit>
            <at_rest>AES-256</at_rest>
            <key_management>HashiCorp Vault</key_management>
        </encryption>
    </security_model>
</system>
EOF
        
        # Validate XML
        if xmllint --noout "$OUTPUT_DIR/ai-ml/nocbrain-system.xml" 2>/dev/null; then
            log_info "AI/ML XML documentation validated successfully"
        else
            log_error "AI/ML XML documentation validation failed"
        fi
        
        log_info "AI/ML documentation updated"
    else
        log_info "[DRY RUN] Would update AI/ML documentation"
    fi
}

# Generate downloadable packages
generate_packages() {
    log_info "Generating downloadable documentation packages..."
    
    if [[ "$DRY_RUN" == false ]]; then
        local base_name="nocbrain"
        
        # Generate PDF packages
        for category in developer operations noc-soc marketing; do
            local input_file="$OUTPUT_DIR/$category/index.md"
            local output_file="$OUTPUT_DIR/packages/${base_name}-${category}-docs-${VERSION}.pdf"
            
            if [[ -f "$input_file" ]]; then
                pandoc "$input_file" -o "$output_file" --pdf-engine=wkhtmltopdf \
                    --toc --toc-depth=3 --number-sections \
                    --metadata title="NOCbRAIN $category Documentation" \
                    --metadata author="NOCbRAIN Team" \
                    --metadata date="$(date)"
                
                log_info "Generated PDF: $output_file"
            fi
        done
        
        # Generate XML package for AI/ML
        local xml_input="$OUTPUT_DIR/ai-ml/nocbrain-system.xml"
        local xml_output="$OUTPUT_DIR/packages/${base_name}-ai-ml-docs-${VERSION}.xml"
        
        if [[ -f "$xml_input" ]]; then
            cp "$xml_input" "$xml_output"
            log_info "Generated XML: $xml_output"
        fi
        
        # Create package index
        cat > "$OUTPUT_DIR/packages/README.md" << EOF
# NOCbRAIN Documentation Packages

## Version: $VERSION

## Available Downloads

### 📦 PDF Documentation

- [Developer Documentation](${base_name}-developer-docs-${VERSION}.pdf)
- [Operations Documentation](${base_name}-operations-docs-${VERSION}.pdf)
- [NOC/SOC Documentation](${base_name}-noc-soc-docs-${VERSION}.pdf)
- [Marketing Documentation](${base_name}-marketing-docs-${VERSION}.pdf)

### 🤖 XML Documentation

- [AI/ML Documentation](${base_name}-ai-ml-docs-${VERSION}.xml)

## Download Statistics

- **Total Packages**: 5
- **Generated on**: $(date)
- **Version**: $VERSION
- **Size**: $(du -sh "$OUTPUT_DIR/packages" | cut -f1)

## Access Information

- **Online Documentation**: https://docs.nocbrain.com
- **API Reference**: https://api.nocbrain.com/docs
- **Support**: support@nocbrain.com

---
*Generated on: $(date)*
EOF
        
        log_info "Documentation packages generated successfully"
    else
        log_info "[DRY RUN] Would generate documentation packages"
    fi
}

# Update documentation index
update_main_index() {
    log_info "Updating main documentation index..."
    
    if [[ "$DRY_RUN" == false ]]; then
        cat > "$DOCS_DIR/index.md" << EOF
# NOCbRAIN Documentation

## 📚 Documentation Categories

### 1. 🧑‍💻 [Developer Documentation](developer/)
For developers and technical teams to understand architecture, code structure, and modules.

**Contents:**
- Architecture Overview
- API Reference
- Module Documentation
- Development Setup
- Testing Guide
- Deployment Guide

### 2. 🔧 [Operations Documentation](operations/)
For backend operations teams to understand system installation, maintenance, and infrastructure updates.

**Contents:**
- Installation Guide
- Maintenance Procedures
- Troubleshooting Guide
- Infrastructure Overview
- Backup & Recovery
- Security Procedures

### 3. 🛡️ [NOC/SOC Documentation](noc-soc/)
For Level 1 & 2 NOC and SOC personnel to operate and use the final product.

**Contents:**
- User Guide
- Alert Management
- Incident Response
- Monitoring Procedures
- Daily Checklists
- Emergency Contacts

### 4. 📈 [Marketing Documentation](marketing/)
For marketing teams when system documentation is needed for promotional materials.

**Contents:**
- Product Overview
- Feature Comparison
- Case Studies
- Technical Specifications
- Competitive Analysis
- Sales Materials

### 5. 🤖 [AI/ML Documentation](ai-ml/)
XML/formatted documentation for AI systems to understand product nature and write tests.

**Contents:**
- System Architecture (XML)
- Component Specifications
- Test Scenarios
- Integration Points
- Security Model
- API Specifications

## 🔄 Auto-Update Process

Documentation is automatically updated based on product version changes:

\`\`\`bash
# Update all documentation for version v1.0.0
./scripts/update-docs.sh --version v1.0.0

# Update specific category
./scripts/update-docs.sh --category developer --version v1.0.0
\`\`\`

## 📦 Downloadable Documentation Packages

Each category generates downloadable packages:

- \`nocbrain-developer-docs-v1.0.0.pdf\`
- \`nocbrain-operations-docs-v1.0.0.pdf\`
- \`nocbrain-noc-soc-docs-v1.0.0.pdf\`
- \`nocbrain-marketing-docs-v1.0.0.pdf\`
- \`nocbrain-ai-ml-docs-v1.0.0.xml\`

## 🚀 Quick Access

- **Live Documentation**: https://docs.nocbrain.com
- **API Reference**: https://api.nocbrain.com/docs
- **Developer Portal**: https://dev.nocbrain.com
- **Operations Guide**: https://ops.nocbrain.com
- **NOC/SOC Portal**: https://portal.nocbrain.com

## 📞 Support

- **Technical Support**: support@nocbrain.com
- **Documentation Issues**: docs@nocbrain.com
- **Emergency Contact**: emergency@nocbrain.com

---
*Last updated: $(date) | Version: $VERSION*
EOF
        
        log_info "Main documentation index updated"
    else
        log_info "[DRY RUN] Would update main documentation index"
    fi
}

# Main execution
main() {
    log_info "Starting NOCbRAIN documentation update..."
    log_info "Version: $VERSION"
    if [[ -n "$CATEGORY" ]]; then
        log_info "Category: $CATEGORY"
    fi
    if [[ "$DRY_RUN" == true ]]; then
        log_info "Mode: DRY RUN"
    fi
    
    check_dependencies
    create_output_dir
    extract_version_info
    
    # Update documentation based on category or all
    if [[ -n "$CATEGORY" ]]; then
        case $CATEGORY in
            developer)
                update_developer_docs
                ;;
            operations)
                update_operations_docs
                ;;
            noc-soc)
                update_noc_soc_docs
                ;;
            marketing)
                update_marketing_docs
                ;;
            ai-ml)
                update_ai_ml_docs
                ;;
        esac
    else
        update_developer_docs
        update_operations_docs
        update_noc_soc_docs
        update_marketing_docs
        update_ai_ml_docs
    fi
    
    generate_packages
    update_main_index
    
    log_info "Documentation update completed successfully!"
    log_info "Generated files are available in: $OUTPUT_DIR"
    
    if [[ "$DRY_RUN" == false ]]; then
        log_info "To deploy documentation, run:"
        log_info "  ./scripts/deploy-docs.sh --version $VERSION"
    fi
}

# Parse arguments and run main
parse_args "$@"
main
