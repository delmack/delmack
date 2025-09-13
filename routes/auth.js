const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const router = express.Router();

// Usuário admin padrão (em produção, usar banco de dados)
const adminUser = {
  id: 1,
  username: "adm",
  password: "$2a$10$8K1p/a0dRaW0H.6c8KzNoO3YjLd6QcV8JkZ8JkZ8JkZ8JkZ8JkZ8J", // senha: adm
};

// Rota de login
router.post("/login", async (req, res) => {
  try {
    const { username, password } = req.body;

    // Verificar credenciais
    if (
      username === "adm" &&
      bcrypt.compareSync(password, adminUser.password)
    ) {
      // Gerar token JWT
      const token = jwt.sign(
        { userId: adminUser.id, username: adminUser.username },
        process.env.JWT_SECRET || "secret_key",
        { expiresIn: "24h" }
      );

      res.json({
        success: true,
        message: "Login realizado com sucesso!",
        token,
        user: { id: adminUser.id, username: adminUser.username },
      });
    } else {
      res.status(401).json({
        success: false,
        message: "Credenciais inválidas!",
      });
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      message: "Erro no servidor",
    });
  }
});

// Rota para verificar token
router.get("/verify", (req, res) => {
  const token = req.headers.authorization?.split(" ")[1];

  if (!token) {
    return res.status(401).json({ valid: false });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || "secret_key");
    res.json({ valid: true, user: decoded });
  } catch (error) {
    res.status(401).json({ valid: false });
  }
});

module.exports = router;
