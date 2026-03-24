# Docker Walkthrough — Lecture Script

Follow this script top-to-bottom. Every command is shown with its expected output.
Pause at the **discussion** points to let things sink in.

---

## Part 1: Hello Docker (15 min)

### 1.1 — Your first container

**First, look at the Dockerfile:**

```bash
cd 1-hello
cat Dockerfile
```

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY hello.py .
CMD ["python", "hello.py"]
```

Line-by-line:

| Line | What it does | Analogy |
|------|-------------|---------|
| `FROM python:3.10-slim` | Start from a pre-built image that already has Python 3.10 + a minimal Debian Linux. Downloaded from Docker Hub (like GitHub but for images). | "I'm starting with a laptop that already has Python installed" |
| `WORKDIR /app` | Create the folder `/app` inside the container and `cd` into it. All future commands run from here. | `mkdir -p /app && cd /app` |
| `COPY hello.py .` | Copy `hello.py` from **your laptop** (the folder with the Dockerfile) into the container's current directory (`/app`). The `.` means "here" = `/app`. | Drag-and-drop a file into the container |
| `CMD ["python", "hello.py"]` | The default command to run when someone types `docker run`. Not executed during build — only at runtime. | "When you turn this machine on, run this" |

**Now build it:**

```bash
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

### 1.2 — What just happened? Inspect images & containers

After that one build + run, let's see what Docker created:

**List all images on your machine:**
```bash
docker images
```

Expected:
```
REPOSITORY     TAG         IMAGE ID       CREATED          SIZE
hello-docker   latest      a1b2c3d4e5f6   30 seconds ago   155MB
python         3.10-slim   f7g8h9i0j1k2   2 weeks ago      155MB
```

**Point out:** Two images! `python:3.10-slim` was downloaded as the base (from Docker Hub). `hello-docker` is our image built on top of it.

**List running containers:**
```bash
docker ps
```

Expected:
```
CONTAINER ID   IMAGE   STATUS   PORTS   NAMES
```

Empty! The container ran `hello.py`, printed output, and **exited**. It's not running anymore.

**List ALL containers (including stopped ones):**
```bash
docker ps -a
```

Expected:
```
CONTAINER ID   IMAGE          STATUS                     NAMES
c3d4e5f6g7h8   hello-docker   Exited (0) 10 seconds ago  bold_tesla
```

The container is still there as a "zombie" — stopped but not deleted.

**How much disk space is Docker using?**
```bash
docker system df
```

Expected:
```
TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
Images          2       1        155.2MB   155.2MB (100%)
Containers      1       0        0B        0B
Build Cache     5       0        0B        0B
```

**Discussion:** "Even one tiny hello-world uses 155 MB because it includes a full Python + Debian installation inside. That's the cost of isolation."

**Dig deeper — which images are the biggest?**
```bash
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

This shows each image and its size. After all 5 demos you'll see:
```
REPOSITORY     TAG         SIZE
env-demo       latest      698MB
spam-app       latest      698MB
train-save     latest      400MB
train-model    latest      400MB
hello-docker   latest      147MB
python         3.10-slim   147MB    ← shared base, not counted twice!
```

**Why are some bigger?** `hello-docker` has only Python (147 MB). `train-model` adds sklearn (+253 MB). `spam-app` adds sklearn + gradio (+551 MB). Each layer adds weight.

**Dig deeper — which containers are eating space?**
```bash
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Size}}"
```

Shows every container (running + stopped) with how much extra data it created:
```
NAMES              IMAGE          STATUS                      SIZE
bold_tesla         hello-docker   Exited (0) 5 min ago        22B (virtual 147MB)
```

The `22B` is data written by the container. The `virtual 147MB` is the image size. Stopped containers are zombies taking up space — `docker container prune -f` cleans them.

**Show Docker Desktop GUI:** Open Docker Desktop and walk through:
- **Images tab** → show `hello-docker` and `python:3.10-slim`, click an image to see its layers
- **Containers tab** → show the stopped container, click it to see Logs, Inspect, Terminal
- Docker Desktop shows the same info as the CLI, just more visual

---

### 1.3 — Shell into the container (the "SSH" experience)

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

### 1.4 — Create a file inside the container

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

### 1.5 — The image is a class, the container is an object

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

### 1.6 — Override the default command

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

### 1.7 — Base images matter: size, packages, and trade-offs

We have three variant Dockerfiles in `1-hello/` that use different base images. Build them all:

```bash
cd 1-hello

# Our original slim image
docker build -t hello-slim -f Dockerfile .

# The FULL Python image (includes gcc, make, headers, etc.)
docker build -t hello-full -f Dockerfile.full .

# Alpine — the tiny Linux distro
docker build -t hello-alpine -f Dockerfile.alpine .

# Ubuntu — no Python pre-installed, we install it ourselves
docker build -t hello-ubuntu -f Dockerfile.ubuntu .
```

**Compare sizes:**
```bash
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep hello
```

Expected (approximate):
```
REPOSITORY     TAG       SIZE
hello-ubuntu   latest    ~150MB
hello-alpine   latest    ~50MB
hello-slim     latest    ~155MB
hello-full     latest    ~1GB
```

**Discussion:** "Same `hello.py`, four completely different environments. The full image is ~1 GB because it includes a C compiler, development headers, and hundreds of system packages. Alpine is ~50 MB — it's a stripped-down Linux. Slim is the sweet spot for most projects."

**Shell into each and compare what's available:**

```bash
# Full image — has everything
docker run -it hello-full bash
pip list | wc -l
# → ~10+ packages (pip, setuptools, wheel, etc.)
which gcc
# → /usr/bin/gcc  ← C compiler included!
which curl
# → /usr/bin/curl  ← curl is here too!
apt list --installed 2>/dev/null | wc -l
# → ~300+ packages
dpkg -l | grep -c '^ii'
# → 300+ system packages installed
exit
```

```bash
# Slim image — Python + minimal Debian
docker run -it hello-slim bash
which gcc
# → nothing — no compiler!
which curl
# → nothing — no curl!
apt list --installed 2>/dev/null | wc -l
# → ~90 packages — much less
exit
```

```bash
# Alpine — minimal Linux, uses musl instead of glibc
docker run -it hello-alpine sh    # Note: sh, not bash!
which bash
# → nothing — Alpine doesn't have bash by default!
pip list
# → pip, setuptools
cat /etc/os-release
# → Alpine Linux — NOT Debian
exit
```

```bash
# Ubuntu — we had to install Python ourselves
docker run -it hello-ubuntu bash
python3 --version
# → Python 3.10.x
pip3 --version
# → ERROR: pip is not installed!
# We only installed python3, not pip — you have to be explicit
which gcc
# → nothing
exit
```

**Compare WORKDIR across images:**
```bash
docker run hello-slim pwd
# → /app

docker run hello-alpine pwd
# → /code  (we chose a different WORKDIR in Dockerfile.alpine)

docker run hello-ubuntu pwd
# → /home/demo  (different again in Dockerfile.ubuntu)
```

**Point out:** WORKDIR is just a config choice in the Dockerfile — you pick what makes sense for your project.

**Summary table (draw on whiteboard):**

| Image | Base | Size | Has bash? | Has gcc? | Has pip? | Use when... |
|-------|------|------|-----------|----------|----------|-------------|
| `python:3.10` (full) | Debian | ~1 GB | Yes | Yes | Yes | Need to compile C extensions (numpy from source, etc.) |
| `python:3.10-slim` | Debian | ~155 MB | Yes | No | Yes | **Default choice** — most Python projects |
| `python:3.10-alpine` | Alpine | ~50 MB | No | No | Yes | Size matters (edge, IoT), but beware compatibility |
| `ubuntu:22.04` + python3 | Ubuntu | ~150 MB | Yes | No | No | Need Ubuntu-specific packages or tools |

**Discussion:** "For this course, always use `python:3.10-slim`. It's small enough, has pip, and uses Debian so packages install easily. Alpine is tempting but NumPy/sklearn can be painful to install on it because they need glibc."

```bash
# Clean up the variant images
docker rmi hello-full hello-alpine hello-ubuntu hello-slim

cd ..
```

---

## Part 2: Dependencies & Reproducibility (5 min)

### 2.1 — Same code, same result, every time

**First, look at the Dockerfile:**

```bash
cd 2-dependencies
cat Dockerfile
```

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY train.py .
CMD ["python", "train.py"]
```

Two new instructions here:

| Line | What it does | Details |
|------|-------------|---------|
| `COPY requirements.txt .` | Copy `requirements.txt` from your laptop into `/app/requirements.txt` inside the container. | Same as Demo 1's COPY, but now it's the dependency list |
| `RUN pip install --no-cache-dir -r requirements.txt` | **Run this command during the build** (not at runtime!). Installs packages listed in `requirements.txt`. `--no-cache-dir` saves space by not caching downloaded `.whl` files. | This runs ONCE when you `docker build`. The installed packages become part of the image. |
| `COPY train.py .` | Copy the training script after installing deps. | **Why not COPY everything at once?** Docker caches layers. If only `train.py` changes, Docker reuses the cached pip install layer — much faster rebuilds! |

**Where does `requirements.txt` get copied to?**

```
Your laptop:                    Inside the container:
  2-dependencies/                 /app/
    Dockerfile                      requirements.txt  ← COPY'd here
    requirements.txt                train.py          ← COPY'd here
    train.py
```

`COPY requirements.txt .` means: copy from the build context (your `2-dependencies/` folder) to `.` (the WORKDIR, which is `/app`). So it ends up at `/app/requirements.txt`.

**Now build and run:**

```bash
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

**First, look at the Dockerfile — this one is the most interesting:**

```bash
cd 3-web-app
cat Dockerfile
```

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV GRADIO_SERVER_NAME="0.0.0.0"
EXPOSE 7860
CMD ["python", "app.py"]
```

Three new instructions:

| Line | What it does | Why it matters |
|------|-------------|----------------|
| `ENV GRADIO_SERVER_NAME="0.0.0.0"` | Sets an **environment variable** inside the container. Like typing `export GRADIO_SERVER_NAME="0.0.0.0"` in a terminal. | Gradio defaults to `127.0.0.1` (localhost only). Inside a container, `127.0.0.1` means "only accept connections from inside this container" — so your browser can't reach it! `0.0.0.0` means "accept connections from anywhere", which lets the port mapping work. |
| `EXPOSE 7860` | Documentation that the app uses port 7860. **Does NOT actually open the port** — that's what `-p` does at runtime. | Think of it as a label on a shipping container: "this side up." Helpful, but doesn't enforce anything. |
| `CMD ["python", "app.py"]` | Run the Gradio app when the container starts. | `app.py` calls `demo.launch()`, which starts a web server on port 7860 by default. |

**How does the app know about the ENV variable?**

Gradio's library internally checks `os.environ.get("GRADIO_SERVER_NAME")`. When we set `ENV GRADIO_SERVER_NAME="0.0.0.0"` in the Dockerfile, it becomes available as an environment variable inside the container — just like if you'd typed `export GRADIO_SERVER_NAME="0.0.0.0"` in your terminal before running the script.

**How does the port plumbing work?**

```
Your laptop                         Docker container
┌─────────────┐     -p 7861:7860    ┌─────────────────┐
│ Browser      │ ──────────────────→│ Gradio server    │
│ localhost:7861│                    │ listening on 7860│
└─────────────┘                     └─────────────────┘
```

1. Gradio calls `demo.launch()` → starts HTTP server on port `7860` inside the container
2. The container is isolated — your laptop can't see port 7860 directly
3. `-p 7861:7860` tells Docker: "forward my laptop's port 7861 to the container's port 7860"
4. You open `localhost:7861` in your browser → Docker forwards it → Gradio responds

**Why 7861 and not 7860?** You could use `-p 7860:7860` too! We use 7861 on the laptop side to make it obvious that these are two different ports. Also, if you already have something running on 7860 on your laptop, this avoids a conflict.

**Now build and run:**

```bash
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

**Point out:** "The app says `http://0.0.0.0:7860` — that's the container's perspective. From YOUR browser, you use `localhost:7861` because that's the laptop-side port you mapped."

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

### 3.4 — Live logs from the container

Go back to the terminal where you ran `docker run -p 7861:7860 spam-app`. Now open http://localhost:7861 in your browser and classify a few messages.

Watch your terminal — you'll see Gradio's HTTP logs streaming live:

```
HTTP Request: POST http://0.0.0.0:7860/api/predict 200 OK
HTTP Request: POST http://0.0.0.0:7860/api/predict 200 OK
```

**Point out:** "Every time you click 'Submit' in the browser, the request travels through the port mapping and hits the Gradio server inside the container. The logs stream straight to your terminal because the container's stdout is attached to your shell."

`Ctrl+C` to stop the container.

**What if you ran it in detached mode (`-d`)?**

```bash
docker run -d -p 7861:7860 spam-app
```

Now your terminal is free — no logs visible. The container runs in the background. To see the logs:

```bash
# Get the container ID
docker ps
# → a1b2c3d4e5f6   spam-app   Up 10 seconds ...

# Tail the logs live (like tail -f)
docker logs -f a1b
```

Now open the browser again, classify a message — you'll see the log lines appear.

`Ctrl+C` to stop following logs (the container keeps running!).

```bash
# Other useful log commands:
docker logs a1b               # show all logs so far (no live follow)
docker logs --tail 20 a1b     # last 20 lines only
docker logs --since 1m a1b    # logs from the last 1 minute
```

**Discussion:** "In production, `-d` is how you run services — in the background. `docker logs -f` is how you debug them. It's exactly like `tail -f /var/log/app.log` on a traditional server."

```bash
# Stop the background container before moving on
docker stop $(docker ps -q --filter ancestor=spam-app)
```

---

### 3.6 — Who's using my port?

Before starting a web app, check if something is already running on that port:

```bash
lsof -i :7861
```

If nothing is running, you'll get **no output**. If something is using it:
```
COMMAND     PID  USER   FD   TYPE  DEVICE  NODE NAME
com.docke 12345  nipun  17u  IPv6  0x1234  TCP  *:7861 (LISTEN)
```

**Kill it if needed:**
```bash
# Option 1: If it's a Docker container, find and stop it
docker ps --filter "publish=7861"
docker stop <container_id>

# Option 2: Kill whatever process holds the port (works for anything)
lsof -ti :7861 | xargs kill
```

**Verify it's free now:**
```bash
lsof -i :7861
# → no output = port is free!
```

**Tip:** On Mac, `lsof -i :PORT` is your best friend. On Linux, you can also use `ss -tlnp | grep 7861`.

---

### 3.7 — Port conflict

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

**First, look at the Dockerfile:**

```bash
cd 4-volumes
cat Dockerfile
```

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY train_and_save.py .
CMD ["python", "train_and_save.py"]
```

This one looks like Demo 2 — nothing new in the Dockerfile itself. The key lesson is about what happens to files the script *creates at runtime*.

`train_and_save.py` saves files to `outputs/model.pkl` and `outputs/training_log.txt`. Since WORKDIR is `/app`, those files end up at `/app/outputs/` **inside the container**. But when the container stops, those files are trapped inside the dead container — your laptop can't see them.

That's where `-v` (volumes) comes in — covered in 4.2.

**Build and run:**

```bash
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

**How `-v` works:**

```
-v $(pwd)/outputs:/app/outputs
   ───────────────  ────────────
   YOUR LAPTOP       INSIDE CONTAINER

   ~/git/docker-ml-demos/4-volumes/outputs/  ↔  /app/outputs/
```

`-v` creates a two-way link between a folder on your laptop and a folder inside the container. When the script writes to `/app/outputs/model.pkl` inside the container, the file appears at `$(pwd)/outputs/model.pkl` on your laptop — and vice versa. The folder is **shared**, not copied.

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

**First, look at the Dockerfile:**

```bash
cd 5-environment
cat Dockerfile
```

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV MODEL_TYPE="rf"
ENV N_ESTIMATORS="100"
ENV APP_TITLE="Digit Classifier"
ENV GRADIO_SERVER_NAME="0.0.0.0"
EXPOSE 7860
CMD ["python", "app.py"]
```

Multiple ENV variables this time — each sets a **default** that the code reads at runtime:

| ENV variable | Default | How the code reads it | What it controls |
|---|---|---|---|
| `MODEL_TYPE` | `"rf"` | `os.environ.get("MODEL_TYPE", "rf")` | Which sklearn model to train (RandomForest or SVM) |
| `N_ESTIMATORS` | `"100"` | `int(os.environ.get("N_ESTIMATORS", "100"))` | Number of trees for RandomForest |
| `APP_TITLE` | `"Digit Classifier"` | `os.environ.get("APP_TITLE", "Digit Classifier")` | Title shown in the Gradio UI |
| `GRADIO_SERVER_NAME` | `"0.0.0.0"` | Read by Gradio internally | Allow connections from outside the container |

**How does `docker run -e` override these?**

`ENV` in the Dockerfile sets the default. `docker run -e MODEL_TYPE=svm` overrides it at runtime — like passing a command-line argument. The code doesn't know the difference; `os.environ.get(...)` just reads whatever value is set.

```
Dockerfile:    ENV MODEL_TYPE="rf"        ← baked into the image (default)
docker run -e: MODEL_TYPE=svm             ← overrides at runtime
Python code:   os.environ.get("MODEL_TYPE") → "svm"
```

**This is powerful:** one image, many configurations. No rebuild needed.

**Build and run with defaults:**

```bash
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

## Bonus: Inspect Everything (5 min)

After all 5 demos, let's see what Docker accumulated on your machine.

### All images on your machine

```bash
docker images
```

Expected:
```
REPOSITORY     TAG         SIZE
hello-docker   latest      155MB
train-model    latest      590MB
spam-app       latest      850MB
train-save     latest      590MB
env-demo       latest      950MB
python         3.10-slim   155MB    ← base image, shared by all!
```

**Point out:** `python:3.10-slim` appears once even though all 5 demos use it — Docker shares base layers!

### All containers (running + stopped)

```bash
docker ps -a
```

Expected:
```
CONTAINER ID   IMAGE          STATUS                      NAMES
f1g2h3i4j5k6   env-demo       Exited (0) 2 minutes ago    zen_turing
a1b2c3d4e5f6   hello-docker   Exited (0) 30 minutes ago   bold_tesla
...            ...            ...                         ...
```

Every `docker run` creates a container. Stopped ones are "zombies" — they take disk space.

### Total disk usage

```bash
docker system df
```

Expected:
```
TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
Images          6       0        2.1GB     2.1GB (100%)
Containers      8       0        12MB      12MB (100%)
Build Cache     15      0        450MB     450MB (100%)
```

**Discussion:** "All 5 demos used ~2.5 GB of disk. That's the trade-off: isolation costs space. But `docker system prune` cleans it all up."

### Show the same in Docker Desktop GUI

Open Docker Desktop and walk through:

1. **Images tab** — show all 6 images, their sizes, and the "In Use" badge
2. **Containers tab** — show running vs stopped containers, click one to see its logs
3. **Click on `spam-app`** — show the Logs, Inspect, and Terminal tabs
4. **Settings → Resources** — show how much CPU/RAM/Disk is allocated to Docker

**Discussion:** "Everything we just did with CLI commands, you can also see visually in Docker Desktop. Use whichever you prefer — the CLI is faster, the GUI is more discoverable."

### Clean up everything

```bash
# Remove all stopped containers
docker container prune -f

# Remove all demo images
docker rmi hello-docker hello-full hello-alpine hello-ubuntu hello-slim train-model spam-app train-save env-demo 2>/dev/null

# Nuclear option: remove everything unused
docker system prune -f

# Check — should be nearly empty now
docker system df
```

---

## Part 6: Where Docker Shows Up in the Real World (5 min)

### 6.1 — Hugging Face Spaces (Docker-based deployment)

Every Gradio/Streamlit app on Hugging Face Spaces runs inside a Docker container.

**Look at any Space's "Files" tab** — you'll see a `Dockerfile` or the platform generates one from `requirements.txt`.

Our Demo 3 (spam classifier) is *already deployable* to HF Spaces:

```bash
cd 3-web-app
ls
# → Dockerfile  app.py  requirements.txt
```

To deploy to Hugging Face Spaces, you'd:

1. Create a new Space on huggingface.co (select "Docker" as the SDK)
2. Push your files: `Dockerfile`, `app.py`, `requirements.txt`
3. HF builds your Docker image in the cloud and runs it

The `Dockerfile` is nearly identical — the only difference is HF Spaces expects port 7860:

```dockerfile
# Our Dockerfile already uses port 7860 internally!
# HF Spaces maps it automatically — no -p flag needed
EXPOSE 7860
CMD ["python", "app.py"]
```

**Point out:** "The Dockerfile you wrote for your laptop works *almost unchanged* on a cloud platform. That's the whole point — Docker makes your code portable."

```bash
cd ..
```

### 6.2 — GitHub Actions (CI/CD with Docker)

GitHub Actions runs every step inside a container. When you see this in a `.github/workflows/` file:

```yaml
# .github/workflows/test.yml
name: Run Tests
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest    # ← this IS a Docker container!
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m pytest
```

**Discussion:** "That `runs-on: ubuntu-latest` is a Docker container on GitHub's servers. Every push to your repo spins up a fresh container, installs dependencies, runs tests, and destroys it. Sound familiar? It's the same amnesia we saw in Demo 1.4!"

You can also use your *own* Dockerfile in GitHub Actions:

```yaml
# Use a custom Docker image for your CI
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: python:3.10-slim    # ← use any Docker image!
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: python -m pytest
```

**Key insight for students:** "For your course project:
1. **Dockerfile** — packages your app so anyone can run it
2. **HF Spaces** — deploy it publicly with that same Dockerfile
3. **GitHub Actions** — test it automatically on every push

All three use Docker. Learn it once, use it everywhere."

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
