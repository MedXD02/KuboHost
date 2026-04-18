import os
import re
import zipfile
import subprocess
import shutil
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================
BASE_DIR = "/var/www/projects"
NGINX_AVAILABLE = "/etc/nginx/sites-available"
NGINX_ENABLED = "/etc/nginx/sites-enabled"
DOMAIN = "medxd.me"

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {
    ".html", ".css", ".js",
    ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".woff", ".woff2", ".ttf"
}

# ==============================
# HELPERS
# ==============================

def is_valid_subdomain(name):
    return re.match(r'^[a-z0-9-]+$', name)


def validate_zip(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for file in z.namelist():

                # Prevent path traversal
                if ".." in file or file.startswith("/"):
                    return False, f"Invalid path: {file}"

                if file.endswith("/"):
                    continue

                _, ext = os.path.splitext(file.lower())

                if ext not in ALLOWED_EXTENSIONS:
                    return False, f"Forbidden file: {file}"

    except zipfile.BadZipFile:
        return False, "Invalid ZIP file"

    return True, "OK"


def extract_and_fix(zip_path, extract_to):
    # Extract safely
    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.infolist():
            extracted_path = os.path.join(extract_to, member.filename)

            if not os.path.realpath(extracted_path).startswith(os.path.realpath(extract_to)):
                raise Exception("Unsafe file detected")

            z.extract(member, extract_to)

    # 🔥 Flatten if single top-level directory
    items = os.listdir(extract_to)

    if len(items) == 1:
        single_item = os.path.join(extract_to, items[0])

        if os.path.isdir(single_item):
            for file in os.listdir(single_item):
                shutil.move(
                    os.path.join(single_item, file),
                    extract_to
                )

            os.rmdir(single_item)


def ensure_index_exists(path):
    if not os.path.exists(os.path.join(path, "index.html")):
        raise Exception("index.html not found in root")


def create_nginx_config(subdomain):
    root_path = f"{BASE_DIR}/{subdomain}"
    conf_path = f"{NGINX_AVAILABLE}/{subdomain}"

    config = f"""
server {{
    listen 80;
    server_name {subdomain}.{DOMAIN};

    root {root_path};
    index index.html;

    location / {{
        try_files $uri $uri/ =404;
    }}
}}
"""

    with open(conf_path, "w") as f:
        f.write(config)

    enabled_path = f"{NGINX_ENABLED}/{subdomain}"

    if not os.path.exists(enabled_path):
        os.symlink(conf_path, enabled_path)


def reload_nginx():
    test = subprocess.run(["nginx", "-t"], capture_output=True)

    if test.returncode != 0:
        return False, test.stderr.decode()

    subprocess.run(["systemctl", "reload", "nginx"])
    return True, "Nginx reloaded"


# ==============================
# ROUTES
# ==============================

@app.route("/deploy", methods=["POST"])
def deploy():
    subdomain = request.form.get("subdomain")
    file = request.files.get("file")

    if not subdomain or not file:
        return jsonify({"error": "Missing subdomain or file"}), 400

    if not is_valid_subdomain(subdomain):
        return jsonify({"error": "Invalid subdomain"}), 400

    project_path = f"{BASE_DIR}/{subdomain}"
    zip_path = f"/tmp/{subdomain}.zip"

    try:
        # Save ZIP
        file.save(zip_path)

        # Validate ZIP
        valid, msg = validate_zip(zip_path)
        if not valid:
            os.remove(zip_path)
            return jsonify({"error": msg}), 400

        # Clean old project
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        os.makedirs(project_path, exist_ok=True)

        # Extract + fix structure
        extract_and_fix(zip_path, project_path)
        os.remove(zip_path)

        # Ensure index.html exists
        ensure_index_exists(project_path)

        # Create nginx config
        create_nginx_config(subdomain)

        # Reload nginx
        ok, msg = reload_nginx()
        if not ok:
            return jsonify({"error": msg}), 500

        return jsonify({
            "message": "Deployed successfully",
            "url": f"http://{subdomain}.{DOMAIN}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete", methods=["POST"])
def delete():
    subdomain = request.form.get("subdomain")

    if not subdomain:
        return jsonify({"error": "Missing subdomain"}), 400

    project_path = f"{BASE_DIR}/{subdomain}"
    conf_path = f"{NGINX_AVAILABLE}/{subdomain}"
    enabled_path = f"{NGINX_ENABLED}/{subdomain}"

    try:
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        if os.path.exists(enabled_path):
            os.remove(enabled_path)

        if os.path.exists(conf_path):
            os.remove(conf_path)

        reload_nginx()

        return jsonify({"message": "Deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
