class DelmackApp {
  constructor() {
    this.token = localStorage.getItem("authToken");
    this.user = null;
    this.init();
  }

  init() {
    this.checkAuth();
    this.bindEvents();
  }

  async checkAuth() {
    if (this.token) {
      try {
        const response = await fetch("/api/auth/verify", {
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        });

        const data = await response.json();

        if (data.valid) {
          this.user = data.user;
          this.showDashboard();
          this.loadDashboardData();
        } else {
          this.showLogin();
        }
      } catch (error) {
        console.error("Erro ao verificar autenticação:", error);
        this.showLogin();
      }
    } else {
      this.showLogin();
    }
  }

  bindEvents() {
    // Login form
    document.getElementById("login-form").addEventListener("submit", (e) => {
      e.preventDefault();
      this.handleLogin();
    });

    // Logout button
    document.getElementById("logout-btn").addEventListener("click", () => {
      this.handleLogout();
    });
  }

  async handleLogin() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const messageEl = document.getElementById("login-message");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success) {
        this.token = data.token;
        this.user = data.user;

        localStorage.setItem("authToken", this.token);

        this.showDashboard();
        this.loadDashboardData();
      } else {
        messageEl.textContent = data.message;
        messageEl.className = "message error";
      }
    } catch (error) {
      console.error("Erro no login:", error);
      messageEl.textContent = "Erro ao conectar com o servidor";
      messageEl.className = "message error";
    }
  }

  handleLogout() {
    localStorage.removeItem("authToken");
    this.token = null;
    this.user = null;
    this.showLogin();
  }

  showLogin() {
    document.getElementById("login-page").classList.add("active");
    document.getElementById("dashboard-page").classList.remove("active");
  }

  showDashboard() {
    document.getElementById("login-page").classList.remove("active");
    document.getElementById("dashboard-page").classList.add("active");

    if (this.user) {
      document.getElementById("user-name").textContent = this.user.username;
    }
  }

  async loadDashboardData() {
    try {
      const response = await fetch("/api/sales/dashboard", {
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
      });

      const data = await response.json();

      if (data.success) {
        this.updateDashboard(data.data);
      } else {
        console.error("Erro ao carregar dados:", data.message);
      }
    } catch (error) {
      console.error("Erro ao carregar dados do dashboard:", error);
    }
  }

  updateDashboard(data) {
    // Atualizar estatísticas
    document.getElementById(
      "total-sales"
    ).textContent = `R$ ${data.totalSales.toLocaleString("pt-BR")}`;
    document.getElementById(
      "monthly-growth"
    ).textContent = `${data.monthlyGrowth}%`;
    document.getElementById("total-customers").textContent = data.customers;
    document.getElementById(
      "weekly-sales"
    ).textContent = `R$ ${data.weeklySales.toLocaleString("pt-BR")}`;

    // Atualizar tabela de vendas recentes
    const salesTableBody = document.getElementById("sales-table-body");
    salesTableBody.innerHTML = "";

    data.recentSales.forEach((sale) => {
      const row = document.createElement("tr");
      row.innerHTML = `
                <td>${sale.client}</td>
                <td>R$ ${sale.value.toLocaleString("pt-BR")}</td>
                <td>${new Date(sale.date).toLocaleDateString("pt-BR")}</td>
                <td><span class="status ${sale.status}">${
        sale.status
      }</span></td>
            `;
      salesTableBody.appendChild(row);
    });

    // Atualizar gráfico de receita
    const chartBars = document.getElementById("chart-bars");
    chartBars.innerHTML = "";

    const maxRevenue = Math.max(
      ...data.monthlyRevenue.map((item) => item.revenue)
    );

    data.monthlyRevenue.forEach((item) => {
      const height = (item.revenue / maxRevenue) * 100;
      const bar = document.createElement("div");
      bar.className = "chart-bar";
      bar.style.height = `${height}%`;
      bar.setAttribute("data-value", `R$ ${(item.revenue / 1000).toFixed(0)}k`);

      const label = document.createElement("span");
      label.textContent = item.month;

      bar.appendChild(label);
      chartBars.appendChild(bar);
    });

    // Atualizar lista de produtos
    const productsList = document.getElementById("products-list");
    productsList.innerHTML = "";

    data.topProducts.forEach((product) => {
      const productEl = document.createElement("div");
      productEl.className = "product-item";
      productEl.innerHTML = `
                <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-stats">${product.sales} vendas</div>
                </div>
                <div class="product-revenue">R$ ${product.revenue.toLocaleString(
                  "pt-BR"
                )}</div>
            `;
      productsList.appendChild(productEl);
    });
  }
}

// Inicializar a aplicação quando o DOM estiver carregado
document.addEventListener("DOMContentLoaded", () => {
  new DelmackApp();
});
