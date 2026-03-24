FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy app.py to root as server.py to avoid namespace collision with the 'mcp' library package
COPY mcp/app.py ./server.py
EXPOSE 8080
ENV PORT=8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
