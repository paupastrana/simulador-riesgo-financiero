import json
import numpy as np
from scipy.stats import norm
from http.server import BaseHTTPRequestHandler
import random

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Leer y parsear datos
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Procesar simulación
            result = self.simulate_risk(data)
            
            # Enviar respuesta
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e), "type": type(e).__name__}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    
    def montecarlo(self, S0, sigma, T, M, N):
        """
        S0: Precio actual
        sigma: volatilidad
        T: pasos (días)
        M: simulaciones
        N: drift (tasa libre de riesgo)
        """
        dt = 1 / T  # Cambio de tiempo por paso
        
        # 1. Crear matriz de números aleatorios
        Z = np.random.standard_normal((M, T))
        
        # 2. Calcular variación diaria
        daily_returns = (N - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
        
        # 3. Calcular caminos de precios
        price_paths = np.zeros((M, T + 1))
        price_paths[:, 0] = S0
        
        for t in range(1, T + 1):
            price_paths[:, t] = price_paths[:, t - 1] * np.exp(daily_returns[:, t - 1])
            
        return price_paths
    
    def simulate_risk(self, request_data):
        # Extraer parámetros
        S0 = request_data.get('current_price', 100.0)
        sigma = request_data.get('volatility', 0.20)
        T = request_data.get('time_steps', 252)
        N_sims = request_data.get('num_simulations', 1000)
        r = request_data.get('risk_free_rate', 0.05)
        
        # Validar parámetros
        if T <= 0:
            T = 252  # Default: 1 año de días hábiles
        if N_sims <= 0:
            N_sims = 1000
        if sigma <= 0:
            sigma = 0.20
        
        
        price_paths_array = self.montecarlo(S0, sigma, T, N_sims, r)
        
        transposed_paths = price_paths_array.T
        
        average_path = np.mean(transposed_paths, axis=1)
        percentile_5 = np.percentile(transposed_paths, 5, axis=1)
        percentile_95 = np.percentile(transposed_paths, 95, axis=1)
        
        # 3. Calcular VaR al 95%
        final_day_prices = price_paths_array[:, -1]
        price_at_5th_percentile = np.percentile(final_day_prices, 5)
        VaR_95 = S0 - price_at_5th_percentile
        
        # 4. Preparar respuesta
        return {
            "simulations": price_paths_array.tolist(),
            "average_path": average_path.tolist(),
            "var_95": float(VaR_95),
            "percentile_5": percentile_5.tolist(),
            "percentile_95": percentile_95.tolist(),
            "time_steps": T,
            "num_simulations": N_sims,
            "price_at_5th_percentile": float(price_at_5th_percentile)
        }