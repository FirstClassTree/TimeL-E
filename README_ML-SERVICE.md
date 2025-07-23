### Update data models in ml-service/src/data/models when they change in db_service/app/db_core/models

### Troubleshooting

Clear Docker caches and restart the environment;  

```bash
docker system prune -a
docker-compose down
```

Completely Restart Docker and WSL2;  

Quit Docker Desktop fully (tray icon → Quit).  

```wsl --shutdown```  

Reboot the host machine.

```docker-compose up --build```

or

```bash
	docker-compose build --no-cache
	docker-compose up
```


note; currently prone to random core dump while building.  
**do not check out this version of ml-service as finished.**  
see requirements.txt, Dockerfile for experiments.  

