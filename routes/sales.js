const express = require("express");
const auth = require("../middleware/auth");
const router = express.Router();

// Dados de exemplo para o dashboard
const salesData = {
  totalSales: 15420,
  monthlyGrowth: 12.5,
  weeklySales: 3250,
  customers: 124,
  recentSales: [
    {
      id: 1,
      client: "Empresa ABC",
      value: 2500,
      date: "2023-06-15",
      status: "Concluído",
    },
    {
      id: 2,
      client: "Comércio XYZ",
      value: 1800,
      date: "2023-06-14",
      status: "Concluído",
    },
    {
      id: 3,
      client: "Serviços LTDA",
      value: 4200,
      date: "2023-06-13",
      status: "Pendente",
    },
    {
      id: 4,
      client: "Indústria 123",
      value: 3100,
      date: "2023-06-12",
      status: "Concluído",
    },
    {
      id: 5,
      client: "Tech Solutions",
      value: 1950,
      date: "2023-06-11",
      status: "Concluído",
    },
  ],
  topProducts: [
    { name: "Consultoria Estratégica", sales: 28, revenue: 8400 },
    { name: "Plano de Marketing", sales: 19, revenue: 5700 },
    { name: "Análise de Dados", sales: 15, revenue: 6750 },
    { name: "Otimização de Processos", sales: 12, revenue: 4800 },
    { name: "Treinamento Corporativo", sales: 10, revenue: 3000 },
  ],
  monthlyRevenue: [
    { month: "Jan", revenue: 12000 },
    { month: "Fev", revenue: 18000 },
    { month: "Mar", revenue: 15000 },
    { month: "Abr", revenue: 22000 },
    { month: "Mai", revenue: 19000 },
    { month: "Jun", revenue: 25000 },
  ],
};

// Rota protegida para obter dados de vendas
router.get("/dashboard", auth, (req, res) => {
  res.json({
    success: true,
    data: salesData,
  });
});

module.exports = router;
