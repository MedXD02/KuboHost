# 🚀 KuboHost

**KuboHost** is a lightweight self-hosted deployment platform that lets you instantly host static websites using wildcard subdomains.

Upload a ZIP file, and KuboHost will:

* Validate it (static files only)
* Extract it safely
* Configure Nginx automatically
* Deploy it to a live subdomain in seconds

> 💡 Your own mini deployment platform — simple, fast, and resource-friendly.

---

## ✨ Features

* ⚡ One-command deployment via API
* 🌐 Automatic subdomain routing (wildcard DNS)
* 🔒 Secure ZIP validation (static files only)
* 📦 Smart extraction (auto-fixes nested ZIPs)
* 🧠 Nginx config generation + auto reload
* 🗑️ Delete deployed projects via API

---

## 🏗️ How It Works

```text
Client → API → Validate ZIP → Extract → Configure Nginx → Live Subdomain
```

---

## 📦 Requirements

* Python 3.8+
* Nginx installed
* Root or sudo access
* Wildcard DNS configured

Example (DNS):

```
* → YOUR_SERVER_IP
```

---

## ⚙️ Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/kubohost.git
cd kubohost
```

---

### 2. Install dependencies

```bash
pip install flask
```

---

### 3. Create required directories

```bash
sudo mkdir -p /var/www/projects
sudo chown -R www-data:www-data /var/www/projects
```

---

### 4. Run the API

```bash
sudo python3 app.py
```

> ⚠️ Must run with permissions to modify Nginx configs

---

## 🚀 Usage

### 📤 Deploy a project

```bash
curl -X POST http://YOUR_SERVER_IP:5000/deploy \
  -F "subdomain=test1" \
  -F "file=@site.zip"
```

### ✅ Response

```json
{
  "message": "Deployed successfully",
  "url": "http://test1.yourdomain.com"
}
```

---

### 🗑️ Delete a project

```bash
curl -X POST http://YOUR_SERVER_IP:5000/delete \
  -F "subdomain=test1"
```

---

## 📁 ZIP Requirements

Allowed file types:

* `.html`, `.css`, `.js`
* Images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`)
* Fonts (`.woff`, `.woff2`, `.ttf`)

### ✅ Supported structures

**Flat:**

```
index.html
style.css
```

**Nested (auto-fixed):**

```
project/
  index.html
```

---

## 🔒 Security Notes

* Only static files are allowed
* Path traversal protection included
* File size limited (default: 10MB)
* Nginx config is validated before reload

> ⚠️ Do NOT expose this API publicly without authentication

---

## ⚠️ Limitations

* Static sites only (no backend apps yet)
* No authentication (yet)
* No SSL automation (yet)

---

## 🛠️ Roadmap

* 🔐 API authentication (API keys)
* 🌐 Automatic SSL (Let's Encrypt)
* ⚙️ Background job queue
* 📊 Deployment logs
* 🐳 Optional container support

