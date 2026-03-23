# Docker Walkthrough — Lecture Script

Follow this script top-to-bottom. Every command is shown with its expected output.
Pause at the **discussion** points to let things sink in.

---

## Part 1: Hello Docker (10 min)

### 1.1 — Your first container

```bash
cd 1-hello
docker build -t hello-docker .
```

Expected:
```
=> [1/3] FROM python:3.10-slim
=> [2/3] WORKDIR /app
=> [3/3] COPY hello.py .
=> naming to docker.io/library/hello-docker
```

```bash
docker run hello-docker
```

Expected:
```
==================================================
  Hello from inside a Docker container!
==================================================
  Python version : 3.10.x
  OS             : Linux 6.x.x-...
  Architecture   : aarch64
  User           : root
  Working dir    : /app
  Home dir       : /root
==================================================

This is NOT your laptop's Python.
...
```

**Point out:** It says Linux, even on a Mac! And the user is `root`.

---

### 1.2 — Shell into the container (the "SSH" experience)

```bash
docker run -it hello-docker bash
```

You're now **inside** the container. Try:

```bash
whoami
# → root

pwd
# → /app

ls
# → hello.py

python --version
# → Python 3.10.x

pip list
# → pip, setuptools, wheel — nothing else installed

cat /etc/os-release
# → Debian GNU/Linux 12 (bookworm) — this is the OS inside!
```

**Discussion:** "This is a full Linux machine. Not your Mac, not Windows. A tiny Debian box."

---

### 1.3 — Create a file inside the container

While still inside the container:

```bash
echo "I was here!" > my_note.txt
ls
# → hello.py  my_note.txt

cat my_note.txt
# → I was here!

exit
```

Now start a **new** container:

```bash
docker run -it hello-docker bash
```

```bash
ls
# → hello.py
# WHERE IS my_note.txt?! GONE.

exit
```

**Discussion:** "Every `docker run` creates a brand-new container from the image.
The image is a snapshot — read-only. Your file existed in the old container, which
is now dead. This is the amnesia property. By design."

---

### 1.4 — The image is a class, the container is an object

```bash
# Start two containers from the same image, side by side
docker run -it --name box-a hello-docker bash
```

In **another terminal tab:**

```bash
docker run -it --name box-b hello-docker bash
```

Now in box-a:
```bash
echo "I am box A" > identity.txt
```

In box-b:
```bash
ls
# → hello.py — no identity.txt! box-b is a separate instance.
cat identity.txt
# → cat: identity.txt: No such file or directory
```

Exit both:
```bash
exit   # in both tabs
```

Clean up:
```bash
docker rm box-a box-b
```

**Discussion:** "Same image, two completely independent containers.
Just like `a = list()` and `b = list()` — they don't share state."

---

### 1.5 — Override the default command

The Dockerfile says `CMD ["python", "hello.py"]`, but you can override it:

```bash
# Run Python interactively
docker run -it hello-docker python
>>> 2 + 2
4
>>> import sys; print(sys.version)
3.10.x ...
>>> exit()

# Run a one-liner
docker run hello-docker python -c "print('Hello from a one-liner!')"
# → Hello from a one-liner!

# Run any Linux command
docker run hello-docker cat /etc/os-release
# → PRETTY_NAME="Debian GNU/Linux 12 (bookworm)" ...

# What about something not installed?
docker run hello-docker curl google.com
# → exec: "curl": executable file not found
# curl isn't installed in this slim image!
```

**Discussion:** "The image only has what the Dockerfile put in. No curl, no git,
no vim. If you need something, add `RUN apt-get install ...` to the Dockerfile."

```bash
cd ..
```

---

## Part 2: Dependencies & Reproducibility (5 min)

### 2.1 — Same code, same result, every time

```bash
cd 2-dependencies
docker build -t train-model .
```

```bash
docker run train-model
```

Expected:
```
Python: 3.10.x
sklearn: 1.7.2
Training with random_state=42...
Accuracy: 0.9722
```

Run it again:
```bash
docker run train-model
```

```
Accuracy: 0.9722    # exactly the same!
```

### 2.2 — Compare with your laptop

```bash
python -c "import sklearn; print(sklearn.__version__)"
# → probably a different version!

python 2-dependencies/train.py 2>/dev/null || echo "May not even run without sklearn installed"
# → might get a different accuracy, or crash entirely
```

**Discussion:** "The container has sklearn 1.7.2 pinned. Your laptop might have
1.5, 1.6, or nothing at all. That's why we pin versions — and Docker guarantees
the entire environment matches."

```bash
cd ..
```

---

## Part 3: Web App + Ports (15 min)

### 3.1 — Build and run the web app

```bash
cd 3-web-app
docker build -t spam-app .
docker run -p 7861:7860 spam-app
```

Expected:
```
Training spam classifier...
Model accuracy: 0.99
Running on local URL: http://0.0.0.0:7860
```

Open **http://localhost:7861** in your browser. Type "You have won a free prize!"
and classify it.

**Discussion:** "The app runs on port 7860 inside the container. But the container
is isolated — like a room with no windows. `-p 7861:7860` punches a hole: your
laptop's port 7861 connects to the container's port 7860."

---

### 3.2 — What's running? (new terminal tab)

Keep the app running. In a new terminal:

```bash
docker ps
```

Expected:
```
CONTAINER ID   IMAGE      STATUS         PORTS                    NAMES
a1b2c3d4e5f6   spam-app   Up 2 minutes   0.0.0.0:7861->7860/tcp   ...
```

**Point out:** The PORTS column shows the mapping. STATUS shows uptime.

---

### 3.3 — Shell into a running container

```bash
docker exec -it a1b bash       # use first 3 chars of your container ID
```

You're now inside the running container! The app is still serving in the background.

```bash
ls
# → app.py  requirements.txt  spam_model.pkl

python --version
# → Python 3.10.x

pip list | grep gradio
# → gradio  5.x.x

# Can you see the app process?
ps aux
# → python app.py is running!

exit
```

**Discussion:** "`docker exec` is like SSH-ing into a running server. Great for
debugging. The app keeps running while you poke around."

---

### 3.4 — Port conflict

Stop the first container (`Ctrl+C`). Now try running two on the same port:

```bash
docker run -d -p 7861:7860 spam-app
docker run -d -p 7861:7860 spam-app
```

Expected:
```
Error: Bind for 0.0.0.0:7861 failed: port is already allocated
```

Fix: use different laptop ports:
```bash
docker run -d -p 7861:7860 spam-app
docker run -d -p 7862:7860 spam-app
```

Now **both** are running:
- http://localhost:7861 — instance 1
- http://localhost:7862 — instance 2

```bash
docker ps
# → two containers, same image, different ports!
```

**Discussion:** "Each container gets its own port 7860 inside. But your laptop only
has one port 7861. Two apps can't share the same laptop port — use different ones."

Clean up:
```bash
docker stop $(docker ps -q --filter ancestor=spam-app)
```

```bash
cd ..
```

---

## Part 4: Volumes (10 min)

### 4.1 — Without a volume: data vanishes

```bash
cd 4-volumes
docker build -t train-save .
```

```bash
docker run train-save
```

Expected:
```
Training model...
Accuracy: 0.9722
Model saved to outputs/model.pkl
Training log saved to outputs/training_log.txt
Done! Files saved inside the container.
```

Now check your laptop:
```bash
ls outputs/
# → ls: outputs/: No such file or directory
```

**The model is gone.** It was saved inside the container, which has already stopped.

---

### 4.2 — With a volume: data survives

```bash
docker run -v $(pwd)/outputs:/app/outputs train-save
```

```bash
ls outputs/
# → model.pkl  training_log.txt

cat outputs/training_log.txt
# → Timestamp, accuracy, sklearn version, etc.

python -c "import joblib; m = joblib.load('outputs/model.pkl'); print(type(m))"
# → <class 'sklearn.ensemble._forest.RandomForestClassifier'>
```

**The model survived!** `-v` synced the container's `/app/outputs` with your laptop.

---

### 4.3 — Volumes are two-way

```bash
# Create a file on your laptop
echo "config: learning_rate=0.01" > outputs/my_config.txt

# Start a container with the volume
docker run -it -v $(pwd)/outputs:/app/outputs train-save bash
```

Inside the container:
```bash
cat outputs/my_config.txt
# → config: learning_rate=0.01   ← your laptop file is visible!

echo "processed" >> outputs/my_config.txt
exit
```

Back on your laptop:
```bash
cat outputs/my_config.txt
# → config: learning_rate=0.01
# → processed                    ← the container's edit is here!
```

**Discussion:** "Volumes are a two-way sync. Your laptop and the container see
the same folder in real-time. Like a shared Google Drive folder."

Clean up:
```bash
rm -rf outputs/
cd ..
```

---

## Part 5: Environment Variables (10 min)

### 5.1 — Default config

```bash
cd 5-environment
docker build -t env-demo .
```

```bash
docker run -p 7861:7860 env-demo
```

Expected:
```
Config: MODEL_TYPE=rf, N_ESTIMATORS=100
Title:  Digit Classifier
Model: RandomForest (n=100), Accuracy: 0.97xx
Running on local URL: http://0.0.0.0:7860
```

Open http://localhost:7861 — draw a digit, see the prediction. `Ctrl+C` to stop.

---

### 5.2 — Switch to SVM (no rebuild!)

```bash
docker run -p 7861:7860 -e MODEL_TYPE=svm -e APP_TITLE="SVM Classifier" env-demo
```

Expected:
```
Config: MODEL_TYPE=svm, N_ESTIMATORS=100
Title:  SVM Classifier
Model: SVM, Accuracy: 0.98xx
```

Open http://localhost:7861 — same app, different model! Title changed too.
`Ctrl+C` to stop.

---

### 5.3 — 500 trees (no rebuild!)

```bash
docker run -p 7861:7860 -e N_ESTIMATORS=500 -e APP_TITLE="Big Forest (500 trees)" env-demo
```

Expected:
```
Config: MODEL_TYPE=rf, N_ESTIMATORS=500
Title:  Big Forest (500 trees)
Model: RandomForest (n=500), Accuracy: 0.98xx
```

**Discussion:** "Same image. We never ran `docker build` again. The code reads
`os.environ.get('MODEL_TYPE', 'rf')` — the `-e` flag injects different values.
This is how Netflix configures thousands of services from the same codebase."

---

### 5.4 — See the env vars from inside

```bash
docker run -it -e MODEL_TYPE=svm -e SECRET_KEY=abc123 env-demo bash
```

Inside:
```bash
echo $MODEL_TYPE
# → svm

echo $SECRET_KEY
# → abc123

env | grep -E "MODEL|SECRET|APP"
# → MODEL_TYPE=svm
# → SECRET_KEY=abc123
# → APP_TITLE=Digit Classifier   ← default from Dockerfile

exit
```

**Discussion:** "Environment variables are the standard way to pass config into
containers. Database URLs, API keys, feature flags — never hardcode these in
your code. Read them from the environment."

Clean up:
```bash
docker stop $(docker ps -q --filter ancestor=env-demo) 2>/dev/null
cd ..
```

---

## Bonus: Useful Docker Commands

### See all images on your machine

```bash
docker images
```

Expected:
```
REPOSITORY     TAG       SIZE
hello-docker   latest    155MB
train-model    latest    590MB
spam-app       latest    850MB
train-save     latest    590MB
env-demo       latest    950MB
python         3.10-slim 155MB    ← base image, shared by all!
```

### See stopped containers (zombies)

```bash
docker ps -a
```

Shows containers that ran and stopped. They take up disk space!

### Clean up everything

```bash
# Remove all stopped containers
docker container prune -f

# Remove all demo images
docker rmi hello-docker train-model spam-app train-save env-demo

# Nuclear option: remove everything unused
docker system prune -f
```

### How much disk is Docker using?

```bash
docker system df
```

Expected:
```
TYPE            TOTAL   ACTIVE   SIZE
Images          6       0        2.1GB
Containers      0       0        0B
Build Cache     12      0        450MB
```

---

## Quick Reference Card

| What you want | Command |
|---------------|---------|
| Build an image | `docker build -t name .` |
| Run (one-shot) | `docker run name` |
| Run (interactive shell) | `docker run -it name bash` |
| Run (web app + port) | `docker run -p 7861:7860 name` |
| Run (background) | `docker run -d -p 7861:7860 name` |
| Run (with volume) | `docker run -v $(pwd)/data:/app/data name` |
| Run (with env var) | `docker run -e KEY=value name` |
| List running containers | `docker ps` |
| List all containers | `docker ps -a` |
| Stop a container | `docker stop <id>` |
| Shell into running container | `docker exec -it <id> bash` |
| See images | `docker images` |
| Remove an image | `docker rmi name` |
| Clean up | `docker system prune -f` |
