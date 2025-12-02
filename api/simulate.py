import json
import numpy as np
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # CORS por si lo llamas desde otro dominio algún día
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8") or "{}")

            resultado = self.simular(data)
            self._send_json(resultado, status=200)

        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def simular(self, data):
        precio_actual = float(data.get("current_price", 100.0))
        volatilidad = float(data.get("volatility", 0.20))
        dias = int(data.get("time_steps", 252))
        num_simulaciones = int(data.get("num_simulations", 1000))
        tasa = float(data.get("risk_free_rate", 0.05))

        dt = 1 / dias
        Z = np.random.standard_normal((num_simulaciones, dias))

        rendimientos = (
            (tasa - 0.5 * volatilidad**2) * dt
            + volatilidad * np.sqrt(dt) * Z
        )

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
            "num_simulations": num_simulaciones,
            # Esto es importante: tu front usa datos.current_price
            "current_price": precio_actual,
        }
