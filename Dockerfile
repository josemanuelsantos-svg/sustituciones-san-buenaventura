FROM python:3.11-slim

WORKDIR /app

# Evitar generación de .pyc y forzar buffer de stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación completa (incluyendo base de datos data/ y plantillas)
COPY . .

# Puerto por defecto para plataformas cloud
ENV PORT=5055
EXPOSE 5055

# Comando de arranque optimizado con Gunicorn
CMD ["sh", "-c", "gunicorn --workers=2 --bind=0.0.0.0:${PORT:-5055} app:app"]
