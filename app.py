from flask import Flask, request, render_template, jsonify, redirect
import os, urllib.parse, requests
from datetime import datetime

app = Flask(__name__)

# --- CẤU HÌNH QUAN TRỌNG ---
# 1. Nếu chạy Ngrok: Dán link https://xxxx.ngrok-free.app vào đây.
# 2. Nếu chạy Render: Dán link https://xxxx.onrender.com vào đây.
DOMAIN = "https://your-actual-link.onrender.com" 

@app.after_request
def add_header(response):
    # Header này cực kỳ quan trọng để Facebook Crawler không bị chặn bởi Ngrok/Render
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

@app.route('/')
def index():
    return render_template('dashboard.html', domain=DOMAIN)

@app.route('/api/check-token', methods=['POST'])
def check_token():
    token = request.json.get('token')
    try:
        # Kiểm tra token và lấy danh sách Page của anh Mạnh
        res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={token}").json()
        if "data" in res:
            pages = [{"name": p["name"], "id": p["id"]} for p in res["data"]]
            return jsonify({"status": "success", "pages": pages})
        return jsonify({"status": "error", "message": "Token không đúng"}), 401
    except:
        return jsonify({"status": "error", "message": "Lỗi kết nối"}), 500

@app.route('/api/post-fb', methods=['POST'])
def post_fb():
    try:
        data = request.get_json()
        u_token = data.get('token')
        p_id = data.get('page_id')
        
        # Lấy danh sách Page để lấy đúng Page Access Token
        res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={u_token}").json()
        page = next((p for p in res["data"] if p["id"] == p_id), None)
        
        if not page:
            return jsonify({"status": "error", "message": "Không thấy Page"}), 404

        # Tạo link trung gian chuẩn Open Graph
        ts = int(datetime.now().timestamp())
        query = urllib.parse.urlencode({
            'img': data['image_url'],
            'url': data['target_url'],
            'title': data['post_id'],
            't': ts # Chống lưu cache cũ
        })
        bridge_url = f"{DOMAIN}/view-pro?{query}"
        
        # Đăng bài dùng Page Token để ổn định nhất
        post = requests.post(f"https://graph.facebook.com/v19.0/{page['id']}/feed", data={
            'message': data.get('message'),
            'link': bridge_url,
            'access_token': page['access_token']
        }).json()

        if "id" in post:
            return jsonify({"status": "success", "page": page['name']})
        return jsonify({"status": "error", "message": post.get('error', {}).get('message')}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/view-pro')
def view_pro():
    target = request.args.get('url', '#')
    image = request.args.get('img', '')
    title = request.args.get('title', 'Sản phẩm M2V')
    
    # HTML này ép Facebook phải quét được ảnh
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <meta property="og:title" content="{title}" />
        <meta property="og:image" content="{image}" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:type" content="website" />
        <script>
            // Nếu là người dùng thật thì chuyển hướng đến Shopee ngay
            if (!navigator.userAgent.includes("facebookexternalhit")) {{
                window.location.href = "{target}";
            }}
        </script>
    </head>
    <body style="background:#020617; color:#38bdf8; text-align:center; padding-top:20%;">
        <h1>M2V SYSTEM</h1>
        <p>Đang chuyển hướng an toàn...</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)