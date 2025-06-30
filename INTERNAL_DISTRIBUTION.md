# Internal Distribution Guide

This guide explains how to distribute and install the MQTT Event Listener package within your organization.

## For Package Maintainers

### Building a New Release

1. **Update version numbers:**
   - `pyproject.toml` → `version = "x.x.x"`
   - `Listener/__init__.py` → `__version__ = "x.x.x"`

2. **Build the package:**
   ```bash
   ./scripts/build_package.sh
   ```

3. **Tag the release:**
   ```bash
   git tag v1.x.x
   git push origin v1.x.x
   ```

4. **Distribute** the wheel file from `dist/` directory

### Distribution Options

1. **Direct file sharing**: Share the `.whl` file from `dist/` directory
2. **Git-based**: Users install directly from the repository
3. **Internal package server**: Upload to your organization's package index
4. **Shared drive**: Place wheel files in a shared location

## For End Users

### Installation Methods

#### Method 1: From Git Repository (Recommended)
```bash
# Latest version
pip install git+https://github.com/ed-00/Mqtt-client.git

# Specific version
pip install git+https://github.com/ed-00/Mqtt-client.git@v1.0.0
```

#### Method 2: From Wheel File
```bash
# If you received a .whl file
pip install mqtt_event_listener-1.0.0-py3-none-any.whl
```

#### Method 3: Development Installation
```bash
git clone https://github.com/ed-00/Mqtt-client.git
cd Mqtt-client
pip install -e .[dev]  # Includes testing tools
```

### Requirements File Integration

For projects that depend on this package, add to your `requirements.txt`:

```
# For latest version
git+https://github.com/ed-00/Mqtt-client.git

# For specific version
git+https://github.com/ed-00/Mqtt-client.git@v1.0.0

# For development branch
git+https://github.com/ed-00/Mqtt-client.git@develop
```

### Quick Test

After installation, test that the package works:

```python
from Listener import EventListener, EventListenerConfig
print("✅ Package installed successfully!")
```

## Troubleshooting

### Common Issues

1. **Git authentication**: Ensure you have access to the repository
2. **Python version**: Requires Python 3.8+
3. **Dependencies**: The package will automatically install required dependencies

### Getting Help

- Check the main [README.md](README.md) for usage examples
- Review the test files in `tests/` for more examples
- Contact the package maintainer: Abed Hameed (aahameed@kth.se)

## Security Notes

- This package is for internal use only
- Do not share outside the organization
- All installations should be from trusted internal sources 