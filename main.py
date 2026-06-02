# Despliegue de un clic en Render (https://render.com)
services:
  - type: web
    name: pf-jump-lab
    runtime: docker
    plan: starter
    healthCheckPath: /
    envVars:
      - key: CATAPULT_WEBHOOK_SECRET
        sync: false
      - key: CATAPULT_API_TOKEN
        sync: false
      - key: CATAPULT_API_BASE
        value: https://connect-eu.catapultsports.com/api/v6
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: ANTHROPIC_MODEL
        value: claude-opus-4-8
      - key: SMTP_HOST
        value: smtp.gmail.com
      - key: SMTP_PORT
        value: "587"
      - key: SMTP_USER
        sync: false
      - key: SMTP_PASS
        sync: false
      - key: MAIL_TO
        sync: false
