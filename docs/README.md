# NOCbRAIN Documentation System

## 📚 Documentation Categories

NOCbRAIN provides comprehensive documentation for different user groups and purposes:

### 1. 🧑‍💻 **Developer Documentation** (`/docs/developer/`)
For developers and technical teams to understand architecture, code structure, and modules.

### 2. 🔧 **Operations Documentation** (`/docs/operations/`)
For backend operations teams to understand system installation, maintenance, and infrastructure updates.

### 3. 🛡️ **NOC/SOC Documentation** (`/docs/noc-soc/`)
For Level 1 & 2 NOC and SOC personnel to operate and use the final product.

### 4. 📈 **Marketing Documentation** (`/docs/marketing/`)
For marketing teams when system documentation is needed for promotional materials.

### 5. 🤖 **AI/ML Documentation** (`/docs/ai-ml/`)
XML/formatted documentation for AI systems to understand product nature and write tests.

## 🔄 Auto-Update Process

Documentation is automatically updated based on product version changes:

```bash
# Update all documentation for version v1.0.0
./scripts/update-docs.sh --version v1.0.0

# Update specific category
./scripts/update-docs.sh --category developer --version v1.0.0

# Generate downloadable packages
./scripts/generate-docs-packages.sh --version v1.0.0
```

## 📦 Downloadable Documentation Packages

Each category generates downloadable packages:

- `nocbrain-developer-docs-v1.0.0.pdf`
- `nocbrain-operations-docs-v1.0.0.pdf`
- `nocbrain-noc-soc-docs-v1.0.0.pdf`
- `nocbrain-marketing-docs-v1.0.0.pdf`
- `nocbrain-ai-ml-docs-v1.0.0.xml`

## 🚀 Quick Access

- **Live Documentation**: https://docs.nocbrain.com
- **API Reference**: https://api.nocbrain.com/docs
- **Developer Portal**: https://dev.nocbrain.com
- **Operations Guide**: https://ops.nocbrain.com
- **NOC/SOC Portal**: https://portal.nocbrain.com

---

*Last updated: 2024-02-14 | Version: 1.0.0*
