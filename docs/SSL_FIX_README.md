# SSL Certificate Fix for Corporate Proxy

## Problem
When working behind Netskope corporate SSL inspection, Python applications fail to connect to Azure services with the error:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain
```

## Solution
This project automatically handles SSL certificate issues through the `utils/ssl_fix.py` module.

### How It Works
1. **Automatic Detection**: Detects if you're behind Netskope SSL inspection
2. **Certificate Extraction**: Extracts the Netskope root CA certificate from the SSL chain
3. **Bundle Creation**: Combines it with Python's standard certifi certificate bundle
4. **Environment Setup**: Configures Python to use the combined certificate bundle

### Usage
Simply import the SSL fix at the top of your script:

```python
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()
```

The certificate bundle is stored at: `~/.ssl_certs/combined_certs.pem`

### Features
- **Persistent**: Certificate bundle survives system restarts
- **Auto-Update**: Refreshes certificate every 7 days
- **Automatic**: No manual intervention needed
- **Safe**: Falls back to standard certificates if extraction fails

### Files Using This Fix
- `test_llm.py` - LLM classification testing
- `tools/memory_manager.py` - Vector database operations
- Any script that connects to Azure OpenAI or Azure AI Search

### Troubleshooting

#### If you still get SSL errors:
1. Make sure you're connected to Cato VPN (though Netskope may still intercept)
2. Delete the certificate bundle to force regeneration:
   ```bash
   rm -rf ~/.ssl_certs
   ```
3. Run your script again - it will recreate the bundle

#### If you're not behind Netskope:
The script will automatically use standard certificates without creating a custom bundle.

### Manual Certificate Update
To manually force a certificate update:
```bash
python -c "from utils.ssl_fix import setup_ssl_certificates; setup_ssl_certificates()"
```

## Technical Details
- Uses `openssl s_client` to extract certificate chain
- Combines certifi bundle (137 standard CAs) + Netskope root CA
- Sets environment variables: `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`
