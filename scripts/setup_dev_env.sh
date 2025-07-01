#!/bin/bash

# Development Environment Setup Script
# This script sets up the Docker Compose environment for MQTT client development

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

# Function to check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."
    
    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker Compose is available"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p mosquitto/config
    mkdir -p mosquitto/data
    mkdir -p mosquitto/log
    mkdir -p scripts
    
    print_success "Directories created"
}

# Function to set permissions
set_permissions() {
    print_status "Setting permissions..."
    
    # Make scripts executable
    chmod +x scripts/*.sh 2>/dev/null || true
    
    # Set mosquitto directory permissions
    chmod -R 755 mosquitto/ 2>/dev/null || true
    
    print_success "Permissions set"
}

# Function to build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start services
    docker-compose up -d --build
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "mosquitto-broker.*Up"; then
        print_success "Mosquitto broker is running"
    else
        print_warning "Mosquitto broker may not be fully ready yet"
    fi
    
    if docker-compose ps | grep -q "mqtt-client-dev.*Up"; then
        print_success "MQTT client development container is running"
    else
        print_warning "MQTT client development container may not be fully ready yet"
    fi
}

# Function to test MQTT connection
test_mqtt_connection() {
    print_status "Testing MQTT connection..."
    
    # Try to publish a test message using docker exec
    if docker-compose exec -T mosquitto mosquitto_pub -h localhost -p 1883 -t "test/setup" -m "setup_test" >/dev/null 2>&1; then
        print_success "MQTT connection test successful"
    else
        print_warning "MQTT connection test failed, but services may still be starting"
    fi
}

# Function to show status
show_status() {
    print_status "Current service status:"
    docker-compose ps
    
    echo ""
    print_status "Available services:"
    echo "  - Mosquitto MQTT Broker: localhost:1883 (MQTT), localhost:9001 (WebSocket)"
    echo "  - Development Container: mqtt-client-dev"
    
    echo ""
    print_status "Environment variables:"
    echo "  MQTT_HOST=mosquitto"
    echo "  MQTT_PORT=1883"
    echo "  MQTT_USERNAME=user"
    echo "  MQTT_PASSWORD=password"
    
    echo ""
    print_status "Quick commands:"
    echo "  View logs:           docker-compose logs -f"
    echo "  Enter dev container: docker-compose exec mqtt-client-dev bash"
    echo "  Run tests:           ./scripts/run_mqtt_tests.sh mqtt"
    echo "  Stop services:       docker-compose down"
}

# Function to show usage
show_usage() {
    echo "Development Environment Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup    - Full setup (build, start, test)"
    echo "  start    - Start services only"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show current status"
    echo "  logs     - Show service logs"
    echo "  clean    - Stop and remove all containers"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # Full environment setup"
    echo "  $0 start     # Start services"
    echo "  $0 status    # Show status"
}

# Main execution
main() {
    local command="${1:-setup}"
    
    print_status "MQTT Development Environment Setup"
    
    case "$command" in
        "setup")
            check_docker
            check_docker_compose
            create_directories
            set_permissions
            start_services
            test_mqtt_connection
            show_status
            print_success "Development environment setup complete!"
            ;;
        "start")
            check_docker
            start_services
            show_status
            ;;
        "stop")
            print_status "Stopping services..."
            docker-compose down
            print_success "Services stopped"
            ;;
        "restart")
            print_status "Restarting services..."
            docker-compose down
            docker-compose up -d
            sleep 5
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            print_status "Showing service logs (Ctrl+C to exit)..."
            docker-compose logs -f
            ;;
        "clean")
            print_status "Cleaning up containers and volumes..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup complete"
            ;;
        "-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@" 