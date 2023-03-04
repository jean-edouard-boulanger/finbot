[Unit]
Description=Finbot application (via Docker)
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=FINBOT_CHECKOUT_DIR
Environment="FINBOT_ENV=production"
ExecStart=DOCKER_COMPOSE_PATH -f docker-compose.prod.yml up --abort-on-container-exit
ExecStop=DOCKER_COMPOSE_PATH -f docker-compose.prod.yml down -v

[Install]
WantedBy=multi-user.target
