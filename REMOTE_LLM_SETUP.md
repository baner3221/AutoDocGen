# Remote LLM Server Setup Guide

This guide explains how to use a separate machine (e.g., MacBook Pro) on your local network as the LLM server for AutoDocGen.

## Why Use a Remote Server?

- **GPU Memory Issues**: Your main Windows machine may have limited VRAM
- **Performance**: Intel Macs or machines with more RAM can run LLMs efficiently on CPU
- **Parallel Work**: Keep your development machine responsive while LLM runs elsewhere

---

## MacBook Pro 2019 Server Setup

### Step 1: Install Ollama on MacBook

Open Terminal on your MacBook and run:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (3B is faster for older Macs, 7B for better quality)
ollama pull qwen2.5-coder:3b
# OR for better quality (slower on 2019 MacBook):
ollama pull qwen2.5-coder:7b
```

### Step 2: Configure Ollama to Accept Network Connections

By default, Ollama only listens on localhost. To allow LAN connections:

```bash
# Create/edit Ollama service environment
launchctl setenv OLLAMA_HOST "0.0.0.0"

# Restart Ollama
pkill ollama
ollama serve &
```

**Alternatively**, for persistent configuration:

```bash
# Create a plist for launchd (persistent across reboots)
cat << 'EOF' > ~/Library/LaunchAgents/com.ollama.serve.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.serve</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_HOST</key>
        <string>0.0.0.0</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.ollama.serve.plist
```

### Step 3: Find Your MacBook's IP Address

```bash
# Get the IP address
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example output: inet 192.168.1.105 netmask 0xffffff00 broadcast 192.168.1.255
```

Note down the IP (e.g., `192.168.1.105`).

### Step 4: Test the Server

From your Windows machine, test connectivity:

```powershell
# Replace with your MacBook's IP
curl http://192.168.1.105:11434/api/tags
```

You should see the model list.

---

## Windows Client Configuration

### Step 1: Update AutoDocGen Config

Edit `docs_graphics_lib/autodocgen.config.json`:

```json
{
  "llm": {
    "backend": "ollama",
    "ollama_host": "192.168.1.105",  // Your MacBook's IP
    "ollama_port": 11434,
    "model_name": "qwen2.5-coder:3b",  // Or 7b
    "allow_remote_host": true,  // REQUIRED for non-localhost
    "low_resource_mode": true
  }
}
```

### Step 2: Run AutoDocGen

```powershell
cd C:\Users\Neelanjan\AutoDocGen
.\venv\Scripts\autodocgen init tests\graphics_buffer_lib --output docs_graphics_lib --workers 1
```

---

## Performance Tips for MacBook Pro 2019

| Model | RAM Needed | Speed Estimate |
|-------|-----------|----------------|
| `qwen2.5-coder:3b` | ~4GB | ~10-20 tokens/sec |
| `qwen2.5-coder:7b` | ~8GB | ~5-10 tokens/sec |

### Recommended for 2019 MacBook (Intel, 8-16GB RAM):
- Use the **3B model** for faster generation
- Close other memory-intensive apps
- Run in screen/tmux for persistence:
  ```bash
  tmux new -s ollama
  OLLAMA_HOST=0.0.0.0 ollama serve
  # Ctrl+B, D to detach
  ```

---

## Firewall Notes

If you have a firewall on the MacBook:

```bash
# Allow incoming connections on port 11434
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/ollama
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/bin/ollama
```

---

## Security Considerations

> ⚠️ **Only use on trusted local networks!**

- The Ollama server will be accessible to any device on your network
- Do not expose port 11434 to the internet
- Use a firewall to restrict access if needed
