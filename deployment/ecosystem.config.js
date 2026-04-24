module.exports = {
  apps: [
    {
      name: 'portfolio-backend',
      script: 'uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8000',
      cwd: './backend',
      interpreter: 'python3',
    },
    {
      name: 'rag-backend',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8001',
      cwd: './backend',
      interpreter: 'python3',
    }
  ]
};
