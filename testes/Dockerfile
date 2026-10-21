FROM mcr.microsoft.com/playwright/python:v1.49.1-noble
WORKDIR /testes
RUN pip install --no-cache-dir pytest==8.3.5 playwright==1.49.1 pytest-playwright==0.6.2
COPY . .
CMD ["pytest", "-v"]
