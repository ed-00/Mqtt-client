# MQTT Event Listener Documentation

This directory contains comprehensive documentation for the MQTT Event Listener project.

## 📚 Documentation Structure

```
docs/
├── asciidoc/           # AsciiDoc source files
│   ├── index.adoc      # Main documentation file
│   ├── attributes/     # Configuration and variables
│   ├── includes/       # Reusable content fragments
│   ├── sections/       # Individual documentation sections
│   └── biblatex/       # Bibliography configuration
├── html/               # Generated HTML documentation
├── pdf/                # Generated PDF documentation
└── README.md           # This file
```

## 🔨 Building Documentation

### Prerequisites

Install AsciiDoctor:

```bash
# Ruby and gems
gem install asciidoctor asciidoctor-pdf
```

### Quick Build

```bash
# Build all formats (HTML + PDF)
./scripts/build_docs.sh

# Build HTML only (faster)
./scripts/build_docs.sh html

# Build PDF only
./scripts/build_docs.sh pdf
```

### Manual Build

```bash
# HTML documentation
asciidoctor \
    --backend html5 \
    --destination-dir docs/html \
    --attribute source-highlighter=highlightjs \
    --attribute toc=left \
    docs/asciidoc/index.adoc

# PDF documentation  
asciidoctor-pdf \
    --destination-dir docs/pdf \
    docs/asciidoc/index.adoc
```

## 📖 Documentation Sections

1. **Installation** - Setup and installation instructions
2. **Configuration** - Complete configuration reference
3. **Usage** - Usage patterns and examples
4. **API Reference** - Complete API documentation
5. **Development** - Development setup and guidelines
6. **Testing** - Testing framework and coverage
7. **Architecture** - System design and architecture
8. **Examples** - Practical code examples
9. **Performance** - Performance optimization guide
10. **Security** - Security considerations
11. **Troubleshooting** - Common issues and solutions
12. **Changelog** - Version history and changes

## 🌐 Viewing Documentation

### HTML (Recommended)

After building, serve the HTML documentation:

```bash
# Using Python's built-in server
python -m http.server -d docs/html 8080

# Then open: http://localhost:8080
```

### PDF

Open the generated PDF file:

```bash
open docs/pdf/index.pdf
```

## ✏️ Editing Documentation

### AsciiDoc Format

Documentation is written in AsciiDoc format for professional output:

- **Syntax highlighting** for code examples
- **Cross-references** between sections
- **Professional PDF** generation
- **Responsive HTML** output

### File Organization

- `index.adoc` - Main document that includes all sections
- `attributes/` - Shared variables and configuration
- `sections/` - Individual documentation chapters
- `includes/` - Reusable content fragments

### Adding New Content

1. **Create new section file** in `sections/`
2. **Include in index.adoc** with `include::`
3. **Update build script** validation if needed
4. **Rebuild documentation**

Example:
```asciidoc
// In sections/13-new-section.adoc
[[new-section]]
== New Section

Content here...

// In index.adoc
include::sections/13-new-section.adoc[]
```

### Variable Usage

Use predefined variables for consistency:

```asciidoc
// Use project variables
{voc-project} - MQTT Event Listener
{voc-version} - 1.0.0
{var-install-cmd} - pip install git+...

// Example in documentation
Install {voc-project} version {voc-version}:
[source,bash,subs="attributes"]
----
{var-install-cmd}
----
```

## 🔧 Configuration

### Document Attributes

Key attributes defined in `attributes/config.adoc`:

- **Source highlighting** - Syntax highlighting for code
- **Table of contents** - Left sidebar navigation
- **Section numbering** - Automatic section numbers
- **Cross-references** - Clickable internal links

### Styling

- **HTML**: Uses default AsciiDoctor CSS with syntax highlighting
- **PDF**: Professional PDF theme with proper typography

## 📝 Style Guide

### Code Examples

Use appropriate language tags:

```asciidoc
[source,python]
----
# Python code example
from Listener import EventListener
----

[source,bash]
----
# Shell commands
pip install package
----

[source,toml]
----
# Configuration files
key = "value"
----
```

### Cross-References

Link between sections:

```asciidoc
See the <<installation>> section for setup instructions.
See <<api-reference,API Reference>> for details.
```

### Admonitions

Use for important information:

```asciidoc
[NOTE]
====
This is a note for additional information.
====

[WARNING]
====
This is a warning about potential issues.
====

[TIP]
====
This is a helpful tip for users.
====
```

## 🚀 Automation

### Build Script Features

The `build_docs.sh` script provides:

- **Format selection** (HTML, PDF, or both)
- **Validation** of documentation structure
- **Clean builds** with automatic cleanup
- **Asset copying** for images and CSS
- **Error handling** with helpful messages

### CI Integration

For automated builds, add to CI pipeline:

```bash
# In GitHub Actions or similar
- name: Build Documentation
  run: |
    gem install asciidoctor asciidoctor-pdf
    ./scripts/build_docs.sh
    
- name: Deploy Documentation
  # Deploy HTML docs to internal server
```

## 📧 Support

For documentation questions or improvements:

- **Repository Issues**: Create issue for documentation bugs
- **Maintainer**: Contact aahameed@kth.se
- **Internal Team**: Review with team for major changes

## 📄 License

Documentation is part of the MQTT Event Listener project and follows the same Apache 2.0 license.


