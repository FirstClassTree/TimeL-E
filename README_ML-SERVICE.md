### Update data models in ml-service/src/data/models  
when they change in db_service/app/db_core/models
_________________________________________________________



### `ml-service/training/training.py`

This script designed for training a machine learning model, and it utilizes various optimizations  
i.e memory handling, vectorized feature engineering, and model stacking.  
It should run within the container.  
The script should be executed after the container is fully initialized,  
including when the environment is set up, data is mounted, and the required services are healthy.  

Once the container is up, the script can be executed script interactively    
by attaching to the running container:
```bash
docker exec -it <container_name> bash
python /app/src/training/training.py
```

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


note; this service is currently prone to random core dumps while building.  
**do not checkout this version of ml-service as finished.**  
see requirements.txt, Dockerfile for experiments.  


### next;
* stabilize container build and run
* to train models run `ml-service/training/training.py` (see above)
  * preprocessing;
    * make `data/training-data/processed/prod_features.csv`
    * make `data/training-data/processed/instacart_future.csv`
  * trained models;
    * generate `app/models/stage1_lgbm.pkl`
    * generate `app/models/stage2_lgbm.pkl`

