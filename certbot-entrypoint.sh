#!/bin/sh
set -euo pipefail

CERT_EMAIL="${CERT_EMAIL:-nevalions@gmail.com}"
DOMAINS="${DOMAINS:-statsboard.ru www.statsboard.ru statsboard.online www.statsboard.online}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

check_certificate() {
  local domain="$1"
  local cert_path="/etc/letsencrypt/live/$domain/fullchain.pem"
  
  if [ -f "$cert_path" ]; then
    local expiry=$(openssl x509 -in "$cert_path" -noout -enddate | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry" +%s)
    local current_epoch=$(date +%s)
    local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    log "Certificate for $domain expires in $days_until_expiry days"
    
    if [ $days_until_expiry -lt 7 ]; then
      log "ERROR: Certificate expires soon!"
      return 1
    fi
  fi
  return 0
}

if [ ! -d /etc/letsencrypt/live ]; then
  log "Obtaining initial certificates..."
  if certbot certonly --webroot -w /var/lib/letsencrypt \
    --agree-tos --no-eff-email --email "$CERT_EMAIL" \
    $DOMAINS; then
    log "Certificates obtained successfully"
    for domain in $DOMAINS; do
      check_certificate "$domain" || exit 1
    done
  else
    log "ERROR: Failed to obtain certificates"
    exit 1
  fi
fi

log "Starting certificate renewal loop..."
while :; do
  sleep 43200  # 12 hours
  log "Checking for certificate renewal..."
  if certbot renew --webroot -w /var/lib/letsencrypt --quiet --agree-tos --post-hook "log 'Certificates renewed successfully'"; then
    log "Renewal check completed"
  else
    log "WARNING: Certificate renewal check failed"
  fi
done
