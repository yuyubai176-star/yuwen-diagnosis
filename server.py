# -*- coding: utf-8 -*-
"""
语文学情诊断 · API 服务器（Render 云平台部署版）
零依赖（仅使用 Python 标准库）

端点：
  POST /api/submit   — 学生提交诊断数据
  GET  /api/students — 教师获取全部学生数据
  DELETE /api/student?id=xxx — 删除单个学生
  DELETE /api/clear — 清空全部数据
  GET  /api/health   — 健康检查
"""
import json, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('PORT', 8080))
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), args[0]))

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/')

        if path == '/api/students':
            data = load_data()
            self.send_json(data)

        elif path == '/api/health':
            data = load_data()
            self.send_json({'ok': True, 'total': len(data), 'time': time.strftime('%Y-%m-%d %H:%M:%S')})

        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = self.path.split('?')[0].rstrip('/')

        if path == '/api/submit':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                student = json.loads(body)
                if not student.get('name') or not student.get('ns'):
                    raise ValueError('Invalid data')
                data = load_data()
                # 去重：同一姓名覆盖
                idx = next((i for i, s in enumerate(data) if s.get('name') == student['name']), -1)
                if idx >= 0:
                    data[idx] = student
                else:
                    data.append(student)
                save_data(data)
                self.send_json({'ok': True, 'total': len(data)})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)}, 400)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_DELETE(self):
        path = self.path.split('?')[0].rstrip('/')
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = {}
        for pair in query.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                params[k] = v

        if path == '/api/student':
            sid = params.get('id')
            if sid:
                data = load_data()
                data = [s for s in data if s.get('id') != sid]
                save_data(data)
            self.send_json({'ok': True, 'total': len(data)})

        elif path == '/api/clear':
            save_data([])
            self.send_json({'ok': True, 'total': 0})

        else:
            self.send_json({'error': 'Not found'}, 404)

if __name__ == '__main__':
    import sys
    print('API server starting on port', PORT)
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
        server.server_close()
