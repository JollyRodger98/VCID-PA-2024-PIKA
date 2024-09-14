import multiprocessing
from asciistuff import Banner, Lolcat
# import setup_script
import subprocess
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
accesslog = "-"
errorlog = "-"


def on_starting(server):
    print(f"\n{Lolcat(Banner("PIKA App", font="standard"), spread=1)}")

    # Can't import and execute script because somehow the app started by gunicorn then can't find flask routes.
    subprocess.run(["python", "setup_script.py"])

