#!/bin/bash

# Documentation build script for MQTT Event Listener
# Usage: ./scripts/build_docs.sh [format]
# Formats: html, pdf, all (default)

set -e

echo "🔨 Building MQTT Event Listener Documentation"
echo "=============================================="

# Configuration
DOCS_DIR="docs"
ASCIIDOC_DIR="$DOCS_DIR/asciidoc"
HTML_DIR="$DOCS_DIR/html"
PDF_DIR="$DOCS_DIR/pdf"
MAIN_DOC="$ASCIIDOC_DIR/index.adoc"

# Check if format is specified
FORMAT=${1:-all}

# Create output directories
mkdir -p "$HTML_DIR" "$PDF_DIR"

# Check for asciidoctor
if ! command -v asciidoctor &> /dev/null; then
    echo "❌ asciidoctor not found. Installing..."
    gem install asciidoctor
fi

# Check for asciidoctor-pdf for PDF generation
if [[ "$FORMAT" == "pdf" || "$FORMAT" == "all" ]]; then
    if ! command -v asciidoctor-pdf &> /dev/null; then
        echo "📄 Installing asciidoctor-pdf..."
        gem install asciidoctor-pdf
    fi
fi

# Function to build HTML documentation
build_html() {
    echo "🌐 Building HTML documentation..."
    
    asciidoctor \
        --backend html5 \
        --destination-dir "$HTML_DIR" \
        --attribute source-highlighter=highlightjs \
        --attribute highlightjs-theme=github \
        --attribute toc=left \
        --attribute toclevels=4 \
        --attribute sectlinks \
        --attribute sectanchors \
        --attribute icons=font \
        --attribute stylesheet \
        "$MAIN_DOC"
    
    echo "✅ HTML documentation generated: $HTML_DIR/index.html"
}

# Function to build PDF documentation
build_pdf() {
    echo "📄 Building PDF documentation..."
    
    asciidoctor-pdf \
        --destination-dir "$PDF_DIR" \
        --attribute pdf-theme=default \
        --attribute source-highlighter=rouge \
        --attribute rouge-style=github \
        --attribute toc \
        --attribute toclevels=4 \
        --attribute sectlinks \
        --attribute icons=font \
        "$MAIN_DOC"
    
    echo "✅ PDF documentation generated: $PDF_DIR/index.pdf"
}

# Function to copy assets
copy_assets() {
    # Copy any images or other assets
    if [ -d "$ASCIIDOC_DIR/images" ]; then
        cp -r "$ASCIIDOC_DIR/images" "$HTML_DIR/"
        echo "📁 Copied images to HTML output"
    fi
    
    # Copy CSS customizations if they exist
    if [ -f "$ASCIIDOC_DIR/custom.css" ]; then
        cp "$ASCIIDOC_DIR/custom.css" "$HTML_DIR/"
        echo "🎨 Copied custom CSS"
    fi
}

# Function to validate documentation
validate_docs() {
    echo "🔍 Validating documentation..."
    
    # Check if main sections exist
    local sections=(
        "01-installation.adoc"
        "02-configuration.adoc" 
        "03-usage.adoc"
        "04-api-reference.adoc"
        "05-development.adoc"
        "06-testing.adoc"
        "07-architecture.adoc"
        "08-examples.adoc"
        "09-performance.adoc"
        "10-security.adoc"
        "11-troubleshooting.adoc"
        "12-changelog.adoc"
    )
    
    local missing_sections=()
    for section in "${sections[@]}"; do
        if [ ! -f "$ASCIIDOC_DIR/sections/$section" ]; then
            missing_sections+=("$section")
        fi
    done
    
    if [ ${#missing_sections[@]} -eq 0 ]; then
        echo "✅ All required sections found"
    else
        echo "⚠️  Missing sections: ${missing_sections[*]}"
    fi
    
    # Check if index.adoc exists
    if [ ! -f "$MAIN_DOC" ]; then
        echo "❌ Main documentation file not found: $MAIN_DOC"
        exit 1
    fi
    
    echo "✅ Documentation validation complete"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [format]"
    echo ""
    echo "Formats:"
    echo "  html    - Generate HTML documentation only"
    echo "  pdf     - Generate PDF documentation only"
    echo "  all     - Generate both HTML and PDF (default)"
    echo ""
    echo "Examples:"
    echo "  $0 html    # Build HTML only"
    echo "  $0 pdf     # Build PDF only"
    echo "  $0         # Build both formats"
}

# Function to clean output directories
clean_docs() {
    echo "🧹 Cleaning previous builds..."
    rm -rf "$HTML_DIR"/*.html "$HTML_DIR"/*.css "$HTML_DIR"/images
    rm -rf "$PDF_DIR"/*.pdf
    echo "✅ Cleaned output directories"
}

# Main execution
main() {
    # Validate documentation structure
    validate_docs
    
    # Clean previous builds
    clean_docs
    
    case "$FORMAT" in
        "html")
            build_html
            copy_assets
            ;;
        "pdf")
            build_pdf
            ;;
        "all")
            build_html
            copy_assets
            build_pdf
            ;;
        "help"|"-h"|"--help")
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown format: $FORMAT"
            show_usage
            exit 1
            ;;
    esac
    
    echo ""
    echo "🎉 Documentation build complete!"
    echo ""
    echo "📂 Output locations:"
    if [[ "$FORMAT" == "html" || "$FORMAT" == "all" ]]; then
        echo "   HTML: $HTML_DIR/index.html"
    fi
    if [[ "$FORMAT" == "pdf" || "$FORMAT" == "all" ]]; then
        echo "   PDF:  $PDF_DIR/index.pdf"
    fi
    echo ""
    echo "🌐 To view HTML documentation:"
    echo "   python -m http.server -d $HTML_DIR 8080"
    echo "   Then open: http://localhost:8080"
}

# Run main function
main "$@" 