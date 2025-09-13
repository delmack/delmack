const express = require("express");
const cors = require("cors");
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
require("dotenv").config();

// Importar rotas
const authRoutes = require("./routes/auth");
const salesRoutes = require("./routes/sales");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static("public"));

// Rotas da API
app.use("/api/auth", authRoutes);
app.use("/api/sales", salesRoutes);

// Rota principal - servir o frontend
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Rota de saúde para o Render
app.get("/health", (req, res) => {
  res.status(200).json({ status: "OK", message: "Servidor está funcionando" });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
