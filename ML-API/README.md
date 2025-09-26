# Minecraft ML API #

This is API is used to run any ML related work. 


Author: Jay Mahajan

## How to access ##

To access: *endpoint*/*TASK*





## Commands ##
| **TASK**      	| **REQUEST** 	| **REQUIRED INFO**                        	| **OPTIONAL INFO** 	| **RETURNS**                                                   	|
|---------------	|-------------	|------------------------------------------	|-------------------	|---------------------------------------------------------------	|
| caption-image 	| POST        	| image: bytes<br><br>user-caption: string<br><br> version: int	| user: string      	| feedback: string<br>score: float<br>generated caption: string 	|
|               	|             	|                                          	|                   	|                                                               	|




## File Structure ##

[main.py](main.py): Runs the API server 

[config.py](config.py): Set AI & API configuration settings here.

[install.sh](install.sh): Used to install packages

[model.py](model.py): ML models

[CaptionDataset.py](CaptionDataset.py): Used to load vocab tokens that the model use









