#!/bin/bash

# MQTT Integration Test Runner
# This script helps run MQTT integration tests with proper environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if services are healthy
check_services() {
    print_status "Checking if services are running..."
    
    # Check if Mosquitto container is running
    if docker ps --filter "name=mosquitto-broker" --filter "status=running" | grep -q mosquitto-broker; then
        print_success "Mosquitto broker is running"
    else
        print_warning "Mosquitto broker is not running. Starting services..."
        docker-compose up -d
        
        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 5
        
        # Test MQTT connection
        if command -v mosquitto_pub >/dev/null 2>&1; then
            timeout 5 mosquitto_pub -h localhost -p 1883 -t "test/connection" -m "test" || true
        fi
    fi
}

# Function to run specific test categories
run_tests() {
    local test_type="$1"
    
    case "$test_type" in
        "unit")
            print_status "Running unit tests..."
            pytest -m "unit and not mqtt_integration" -v
            ;;
        "integration")
            print_status "Running integration tests (excluding MQTT)..."
            pytest -m "integration and not mqtt_integration" -v
            ;;
        "mqtt")
            print_status "Running MQTT integration tests..."
            check_services
            pytest -m "mqtt_integration" -v --tb=short
            ;;
        "all")
            print_status "Running all tests..."
            check_services
            pytest -v
            ;;
        "mqtt-only")
            print_status "Running only MQTT integration tests..."
            check_services
            pytest tests/test_mqtt_integration.py -v
            ;;
        *)
            print_error "Unknown test type: $test_type"
            echo "Usage: $0 [unit|integration|mqtt|all|mqtt-only]"
            exit 1
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "MQTT Integration Test Runner"
    echo ""
    echo "Usage: $0 [TEST_TYPE]"
    echo ""
    echo "TEST_TYPE options:"
    echo "  unit        - Run unit tests only"
    echo "  integration - Run integration tests (excluding MQTT)"
    echo "  mqtt        - Run MQTT integration tests only"
    echo "  mqtt-only   - Run only the MQTT test file"
    echo "  all         - Run all tests including MQTT integration"
    echo ""
    echo "Environment Variables:"
    echo "  MQTT_HOST     - MQTT broker hostname (default: localhost)"
    echo "  MQTT_PORT     - MQTT broker port (default: 1883)"
    echo "  MQTT_USERNAME - MQTT username (default: user)"
    echo "  MQTT_PASSWORD - MQTT password (default: password)"
    echo ""
    echo "Examples:"
    echo "  $0 mqtt          # Run MQTT integration tests"
    echo "  $0 all           # Run all tests"
    echo "  $0 unit          # Run unit tests only"
}

# Main execution
main() {
    print_status "MQTT Integration Test Runner"
    
    # Check if help is requested
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_usage
        exit 0
    fi
    
    # Check Docker
    check_docker
    
    # Set default test type
    local test_type="${1:-mqtt}"
    
    # Show current environment
    print_status "Environment:"
    echo "  MQTT_HOST: ${MQTT_HOST:-localhost}"
    echo "  MQTT_PORT: ${MQTT_BROKER_PORT:-1883}"
    echo "  MQTT_USERNAME: ${MQTT_USERNAME:-user}"
    echo "  MQTT_PASSWORD: ${MQTT_PASSWORD:-password}"
    echo ""
    
    # Run tests
    run_tests "$test_type"
    
    if [ $? -eq 0 ]; then
        print_success "All tests completed successfully!"
    else
        print_error "Some tests failed. Check the output above."
        exit 1
    fi
}

# Execute main function with all arguments
main "$@" 