# Local Development Resources

This folder contains files and tools needed for local development, specifically for setting up Cloudflare tunnels to expose your local development server to the internet.

## Cloudflare Tunnel Files

### Batch Scripts
- `start_tunnel.bat` - Quick start script for Cloudflare tunnel
- `start_named_tunnel.bat` - Start tunnel with a specific name
- `setup_static_tunnel.bat` - Setup script for static tunnel configuration

### Configuration Files
- `config.yml.example` - Example tunnel configuration file
- `config.yml` - Your actual tunnel configuration (create from example)

### Executable
- `cloudflared.exe` - Cloudflare tunnel executable for Windows

## Usage

1. **First Time Setup:**
   - Copy `config.yml.example` to `config.yml`
   - Edit `config.yml` with your tunnel details
   - Run `setup_static_tunnel.bat` to configure

2. **Daily Development:**
   - Run `start_tunnel.bat` to start your tunnel
   - Your local server at `localhost:8000` will be accessible via your configured domain

3. **Named Tunnel:**
   - Use `start_named_tunnel.bat` for persistent tunnel configurations

## Important Notes

- These files are for **local development only**
- Keep your `config.yml` secure and don't commit it to version control
- Make sure your local server is running on port 8000 before starting the tunnel
- The tunnel must be configured in your Cloudflare Dashboard

## Related Documentation

See the `help-files/` folder for detailed setup guides:
- `CLOUDFLARE_DOMAIN_SETUP.md` - Domain setup instructions
- `setup_dev_subdomain.py` - Verification script
- `cloudflare_setup_help.py` - Setup assistance tool
