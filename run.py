import uvicorn
from config import PORT, BIND, WORKERS, RELOAD, DEBUG
import main

if __name__ == "__main__":
    uvicorn.run("main:app", host=BIND, port=int(PORT), reload=RELOAD, debug=DEBUG, workers=int(WORKERS))
