#!/usr/bin/env python3
"""
Generate secure secrets for production deployment.

Usage:
    python scripts/generate_secrets.py

This script generates:
- POSTGRES_PASSWORD: Strong random password for database
- SECRET_KEY: Strong random secret for JWT signing

IMPORTANT: In production, use a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
instead of environment variables in .env files.
"""
import secrets
import sys


def generate_secret(length: int = 32) -> str:
    """Generate a cryptographically secure random secret."""
    return secrets.token_urlsafe(length)


def main():
    print("=" * 70)
    print("SECURITY SECRETS GENERATOR")
    print("=" * 70)
    print()
    print("Generated secrets for your .env file:")
    print()
    print(f"POSTGRES_PASSWORD={generate_secret(32)}")
    print(f"SECRET_KEY={generate_secret(32)}")
    print()
    print("=" * 70)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 70)
    print()
    print("1. NEVER commit these secrets to version control")
    print("2. For production, use a secrets manager:")
    print("   - AWS Secrets Manager")
    print("   - Azure Key Vault")
    print("   - HashiCorp Vault")
    print("   - Google Secret Manager")
    print("   - Kubernetes Secrets")
    print()
    print("3. Rotate secrets regularly (every 90 days recommended)")
    print("4. Use different secrets for different environments")
    print("   (development, staging, production)")
    print()
    print("5. Store these secrets in your .env file (for local development)")
    print("   or in your deployment platform's secret management system")
    print()


if __name__ == "__main__":
    main()
