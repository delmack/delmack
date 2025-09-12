const express = require("express");
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware para logging de requisições
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Rota principal
app.get("/", (req, res) => {
  res.json({
    message: "Olá! Servidor funcionando no Render!",
    timestamp: new Date().toISOString(),
    status: "OK",
  });
});

// Rota de saúde para verificar se o servidor está online
app.get("/health", (req, res) => {
  res.status(200).json({ status: "Servidor operacional" });
});

// Rota de exemplo com parâmetro
app.get("/user/:name", (req, res) => {
  const { name } = req.params;
  res.json({
    message: `Olá, ${name}! Bem-vindo ao servidor Node.js.`,
    user: name,
  });
});

// Iniciar o servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
  console.log(`Acesse: http://localhost:${PORT}`);
});

// Exportar app para testes (se necessário)
module.exports = app;
