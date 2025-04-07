# Myth Metaserver Quick Start Guide

This guide will help you get the Myth metaserver running quickly.

## Prerequisites

1. Python 3.8 or higher
2. pip (Python package manager)
3. Git (for version control)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd myth
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Basic Configuration

1. Create a `.env` file in the root directory:
   ```env
   USERD_HOST=127.0.0.1  # Use your server's IP for production
   METASERVER_ROOT_DIR=/path/to/myth
   ENABLE_MD5_SUPPORT=1
   ALLOW_GUESTS=1        # Set to 0 for production
   ```

2. Verify `rooms.lst` configuration:
   ```
   MYTH 0 0 0 -1 99 0
   MYTH1|MYTH2 1 0 0 -1 99 0
   ```

## Running the Server

1. Start all server components:
   ```bash
   python myth_server.py start
   ```

2. Stop all server components:
   ```bash
   python myth_server.py stop
   ```

## Configuring Myth II Client

1. Open Fear
2. Find "internal metaserver strings"
3. Set 12th string to your server's IP
4. Create plugin if needed (Myth II 1.5+)

## Testing the Connection

1. Launch Myth II
2. Connect to metaserver
3. Log in as "guest" (if guest mode enabled)
4. Join a room

## Basic Administration

1. Create a new user:
   ```python
   from users_new.users import create_user
   create_user("username", "password")
   ```

2. Monitor server:
   ```bash
   tail -f logs/server.log
   ```

## Common Issues

1. **Can't Connect**
   - Check server IP in client config
   - Verify server is running
   - Check firewall settings

2. **Authentication Failed**
   - Verify username/password
   - Check MD5 support settings
   - Review server logs

3. **Room Not Visible**
   - Check rooms.lst configuration
   - Verify room server is running
   - Check client game version

## Next Steps

1. Review full documentation in `Documents/`
2. Configure for production use
3. Set up monitoring
4. Create admin accounts

## Getting Help

1. Check the documentation
2. Review server logs
3. Check issue tracker
4. Contact support

## Security Notes

1. Change default settings
2. Disable guest access
3. Use strong passwords
4. Keep Python updated
5. Monitor access logs
