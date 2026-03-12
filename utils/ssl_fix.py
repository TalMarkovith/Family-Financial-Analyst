"""
SSL Certificate Fix for Netskope Corporate Proxy
Automatically extracts and configures Netskope root CA certificate
"""
import os
import ssl
import socket
import certifi
from pathlib import Path

# Path to store the combined certificate bundle
CERT_DIR = Path.home() / ".ssl_certs"
COMBINED_CERT_PATH = CERT_DIR / "combined_certs.pem"

def is_netskope_present():
    """Check if we're behind Netskope SSL inspection"""
    try:
        hostname = "ds-main-ai-foundry.cognitiveservices.azure.com"
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get('issuer', []))
                return 'netskope' in str(issuer).lower() or 'nuvei' in str(issuer).lower()
    except (ssl.SSLError, ssl.SSLCertVerificationError):
        return True  # Assume Netskope if SSL fails
    except Exception:
        return False

def extract_netskope_cert():
    """Extract Netskope root certificate from SSL chain"""
    import subprocess
    
    try:
        # Get certificate chain
        cmd = [
            'openssl', 's_client', '-showcerts',
            '-connect', 'ds-main-ai-foundry.cognitiveservices.azure.com:443'
        ]
        result = subprocess.run(
            cmd,
            input=b'',
            capture_output=True,
            timeout=10
        )
        
        output = result.stdout.decode('utf-8', errors='ignore')
        
        # Extract all certificates
        certs = []
        lines = output.split('\n')
        in_cert = False
        current_cert = []
        
        for line in lines:
            if '-----BEGIN CERTIFICATE-----' in line:
                in_cert = True
                current_cert = [line]
            elif '-----END CERTIFICATE-----' in line:
                current_cert.append(line)
                certs.append('\n'.join(current_cert))
                in_cert = False
                current_cert = []
            elif in_cert:
                current_cert.append(line)
        
        # Return the root certificate (last one in chain)
        return certs[-1] if certs else None
        
    except Exception as e:
        print(f"Warning: Could not extract Netskope certificate: {e}")
        return None

def setup_ssl_certificates():
    """
    Set up SSL certificates for Netskope environment
    Creates a combined certificate bundle if needed
    """
    # Create certificate directory if it doesn't exist
    CERT_DIR.mkdir(exist_ok=True)
    
    # Check if we need to create/update the certificate bundle
    needs_update = False
    
    if not COMBINED_CERT_PATH.exists():
        needs_update = True
    elif is_netskope_present():
        # Check if bundle is old (more than 7 days)
        import time
        file_age_days = (time.time() - COMBINED_CERT_PATH.stat().st_mtime) / 86400
        if file_age_days > 7:
            needs_update = True
    
    if needs_update:
        print("🔧 Setting up SSL certificates for Netskope environment...")
        
        # Get certifi bundle
        certifi_bundle = certifi.where()
        
        # Extract Netskope certificate
        netskope_cert = extract_netskope_cert()
        
        if netskope_cert:
            # Combine certifi bundle with Netskope certificate
            with open(certifi_bundle, 'r') as f:
                certifi_content = f.read()
            
            with open(COMBINED_CERT_PATH, 'w') as f:
                f.write(certifi_content)
                f.write('\n\n# Netskope Corporate Root CA\n')
                f.write(netskope_cert)
                f.write('\n')
            
            print(f"✅ Combined certificate bundle created: {COMBINED_CERT_PATH}")
        else:
            # Fallback to certifi bundle only
            import shutil
            shutil.copy(certifi_bundle, COMBINED_CERT_PATH)
            print(f"⚠️  Using standard certifi bundle: {COMBINED_CERT_PATH}")
    
    # Set environment variables to use our certificate bundle
    os.environ['SSL_CERT_FILE'] = str(COMBINED_CERT_PATH)
    os.environ['REQUESTS_CA_BUNDLE'] = str(COMBINED_CERT_PATH)
    os.environ['CURL_CA_BUNDLE'] = str(COMBINED_CERT_PATH)
    
    return str(COMBINED_CERT_PATH)

# Automatically run setup when module is imported
setup_ssl_certificates()
