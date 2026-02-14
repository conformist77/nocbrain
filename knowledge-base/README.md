# NOCbRAIN Knowledge Base

This directory contains the knowledge base files that are indexed by the RAG system.

## Structure

```
knowledge-base/
├── README.md                 # This file
├── system/                   # System troubleshooting guides
│   ├── linux-troubleshooting.md
│   ├── windows-troubleshooting.md
│   └── performance-optimization.md
├── network/                  # Network configuration and troubleshooting
│   ├── cisco-configs.md
│   ├── network-security.md
│   └── routing-protocols.md
├── security/                 # Security procedures and incident response
│   ├── incident-response.md
│   ├── threat-intelligence.md
│   └── security-policies.md
├── infrastructure/           # Infrastructure management
│   ├── proxmox-guide.md
│   ├── vmware-guide.md
│   └── cloud-platforms.md
├── applications/             # Application-specific guides
│   ├── web-servers.md
│   ├── databases.md
│   └── monitoring-tools.md
└── incidents/                # Historical incident reports
    ├── incident-001.md
    ├── incident-002.md
    └── incident-003.md
```

## Adding Knowledge

To add new knowledge to the system:

1. Create a new markdown file in the appropriate category
2. Use clear headings and structure
3. Include practical, actionable information
4. The system will automatically index new files

## Knowledge Types

The system automatically classifies content into these types:

- **system**: System administration and troubleshooting
- **network**: Network configuration and management
- **security**: Security procedures and incident response
- **infrastructure**: Infrastructure and virtualization
- **application**: Application-specific knowledge
- **incident_report**: Historical incidents and resolutions

## Best Practices

- Use clear, descriptive filenames
- Include relevant keywords for better search
- Structure content with headings and bullet points
- Include step-by-step procedures
- Add examples and troubleshooting steps
- Update content regularly

## Automatic Indexing

The knowledge base is automatically indexed when:
- New files are added
- The system starts up
- Manual reindexing is triggered via API

The RAG system uses this indexed knowledge to provide context-aware responses to user queries.
