[Unit]
Description=Finbot application (via Docker)
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=FINBOT_CHECKOUT_DIR
Environment="FINBOT_ENV=production"
ExecStart=DOCKER_COMPOSE_PATH up --abort-on-container-exit
ExecStop=DOCKER_COMPOSE_PATH down

[Install]
WantedBy=multi-user.target
