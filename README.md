# 🧠 Reddit User Persona Project

  

The **Reddit User Persona Project** is a pipeline-based system that builds a comprehensive psychological and behavioral **persona** of any Reddit user. By collecting public Reddit activity (posts and comments), this project analyzes and generates meaningful insights into personality traits, emotions, and behavioral patterns using modern AI techniques.

  

---

  

## 🚀 Overview

  

This project runs in **three major stages**:

  

### 📌 Stage 1: Data Collection

- Fetches user **posts**, **comments**, and **account details** using the Reddit API via the `praw` library.

- All collected data is stored in a structured **JSON** file for later processing.

  

### 📊 Stage 2: Personality & Emotion Analysis

- Uses the collected JSON data to compute psychological and emotional insights, including:

-  **Big Five Personality Traits** (OCEAN model)

-  **MBTI Typing**

-  **Emotion Detection** (Joy, Sadness, Fear, Anger, etc.)

  

### 🤖 Stage 3: RAG-Based Persona Exploration

- A **Retrieval-Augmented Generation (RAG)** system is initialized using **ChromaDB**.

- It enables dynamic, natural language querying of the user’s persona.

- This stage makes the persona interactive and useful for downstream tasks such as:

- Custom targeting

- Recommendation systems

- Behavioral simulation

- AI-assisted moderation

  

---

  

## 🧪 How to Run a Sample Case

  

Follow these steps to set up and run a basic test case:

  

### ✅ Prerequisites

- Python **3.11.3**

- A Reddit developer account with API credentials

  

### 📦 Installation

  

1.  **Clone the repository**:

```bash

git clone https://github.com/your-username/reddit-user-persona.git

cd reddit-user-persona  
```

  

2.  ### 🧰 Create and Activate a Virtual Environment

  

```bash

python -m  venv  venv

source venv/bin/activate  # On Windows: venv\Scripts\activate ```

  ```

3. ### 📦 Install the Package

  

```bash

pip install .
```

### 🔐 Set Up Reddit API Credentials

Update the file `utils/defaultconfig.yaml` with your Reddit app credentials:

```yaml
REDDIT_CLIENT_ID: "your_client_id"
REDDIT_CLIENT_SECRET: "your_client_secret"
REDDIT_USER_AGENT: "your_user_agent"
```

### 🧪 Run the Sample Test

Run a basic test using:

```bash
python unit_tests/test_basic.py
```