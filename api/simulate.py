import json
import numpy as np
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            resultado = self.simular(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(resultado).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def simular(self, data):
        precio_actual = data.get('current_price', 100.0)
        volatilidad = data.get('volatility', 0.20)
        dias = data.get('time_steps', 252)
        num_simulaciones = data.get('num_simulations', 1000)
        tasa = data.get('risk_free_rate', 0.05)
        
        dt = 1 / dias
        Z = np.random.standard_normal((num_simulaciones, dias))
        
        rendimientos = (tasa - 0.5 * volatilidad**2) * dt + volatilidad * np.sqrt(dt) * Z
        
        caminos = np.zeros((num_simulaciones, dias + 1))
        caminos[:, 0] = precio_actual
        
        for t in range(1, dias + 1):
            caminos[:, t] = caminos[:, t - 1] * np.exp(rendimientos[:, t - 1])
        
        caminos_t = caminos.T
        promedio = np.mean(caminos_t, axis=1)
        p5 = np.percentile(caminos_t, 5, axis=1)
        p95 = np.percentile(caminos_t, 95, axis=1)
        
        precios_finales = caminos[:, -1]
        precio_p5 = np.percentile(precios_finales, 5)
        var = precio_actual - precio_p5
        
        return {
            "simulations": caminos.tolist(),
            "average_path": promedio.tolist(),
            "var_95": float(var),
            "percentile_5": p5.tolist(),
            "percentile_95": p95.tolist(),
            "time_steps": dias,
            "num_simulations": num_simulaciones
        }