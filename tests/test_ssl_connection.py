#!/usr/bin/env python3
"""Quick SSL test - run before and after Cato connection"""

import ssl
import socket

def test_ssl_connection():
    hostname = "ds-main-ai-foundry.cognitiveservices.azure.com"
    port = 443
    
    print(f"Testing SSL connection to {hostname}...")
    
    context = ssl.create_default_context()
    
    try:
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                print(f"\n✅ SSL Connection successful!")
                print(f"Certificate subject: {dict(x[0] for x in cert['subject'])}")
                print(f"Certificate issuer: {dict(x[0] for x in cert['issuer'])}")
                print(f"\nIf issuer contains 'Microsoft' or 'DigiCert' = Good")
                print(f"If issuer contains 'Netskope' or 'Nuvei' = Behind SSL inspection")
                return True
    except ssl.SSLCertVerificationError as e:
        print(f"\n❌ SSL Certificate verification failed!")
        print(f"Error: {e}")
        print(f"\n💡 You are likely behind Netskope SSL inspection")
        print(f"   Connect to Cato VPN and run this test again")
        return False
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_ssl_connection()
