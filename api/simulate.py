import json
import numpy as np
from http.server import BaseHTTPRequestHandler
import random

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            result = self.simular_riesgo(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
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
    
    def montecarlo(self, precio_inicial, volatilidad, dias, simulaciones, tasa):
        dt = 1 / dias
        
        Z = np.random.standard_normal((simulaciones, dias))
        rendimientos_diarios = (tasa - 0.5 * volatilidad**2) * dt + volatilidad * np.sqrt(dt) * Z
        
        caminos_precios = np.zeros((simulaciones, dias + 1))
        caminos_precios[:, 0] = precio_inicial
        
        for t in range(1, dias + 1):
            caminos_precios[:, t] = caminos_precios[:, t - 1] * np.exp(rendimientos_diarios[:, t - 1])
            
        return caminos_precios
    
    def simular_riesgo(self, datos):
        precio = datos.get('current_price', 100.0)
        volatilidad = datos.get('volatility', 0.20)
        dias = datos.get('time_steps', 252)
        simulaciones = datos.get('num_simulations', 1000)
        tasa = datos.get('risk_free_rate', 0.05)
        
        if dias <= 0:
            dias = 252
        if simulaciones <= 0:
            simulaciones = 1000
        
        caminos = self.montecarlo(precio, volatilidad, dias, simulaciones, tasa)
        
        caminos_transpuestos = caminos.T
        
        promedio = np.mean(caminos_transpuestos, axis=1)
        percentil_5 = np.percentile(caminos_transpuestos, 5, axis=1)
        percentil_95 = np.percentile(caminos_transpuestos, 95, axis=1)
        
        precios_finales = caminos[:, -1]
        precio_percentil_5 = np.percentile(precios_finales, 5)
        var_95 = precio - precio_percentil_5
        
        return {
            "simulations": caminos.tolist(),
            "average_path": promedio.tolist(),
            "var_95": float(var_95),
            "percentile_5": percentil_5.tolist(),
            "percentile_95": percentil_95.tolist(),
            "time_steps": dias,
            "num_simulations": simulaciones
        }