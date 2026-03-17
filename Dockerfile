FROM python:3.11-slim

# Evita que Python genere archivos pyc y usa salida sin buffer
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo
WORKDIR /app

# Copia solo requirements.txt primero para aprovechar la cache de Docker
COPY requirements.txt .

# Instala dependencias en un solo paso optimizado
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .
#COPY . /backend

# Configurar variables de entorno
ENV PORT=8000
EXPOSE $PORT

# Crear usuario sin privilegios y Asegurar que el usuario tiene permisos en el directorio de trabajo
RUN adduser --disabled-password --gecos '' myuser
RUN chown -R myuser:myuser /app
USER myuser

# Ejecutar uvicorn
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]


