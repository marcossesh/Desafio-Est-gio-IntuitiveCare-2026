<script setup>
import { ref, onMounted, watch } from 'vue';
import UfChart from './components/UfChart.vue';
import { getOperadoras, getOperadoraDespesas } from './services/api';

const operadoras = ref([]);
const page = ref(1);
const limit = ref(10);
const total = ref(0);
const searchQuery = ref('');
const loading = ref(false);

const modalOpen = ref(false);
const selectedOperadora = ref(null);
const operadoraDespesas = ref([]);
const loadingDespesas = ref(false);

const fetchOperadoras = async () => {
  loading.value = true;
  try {
    const response = await getOperadoras(page.value, limit.value, searchQuery.value);
    operadoras.value = response.data.data || []; 
    total.value = response.data.total || 0;
  } catch (error) {
    console.error('Erro ao buscar operadoras:', error);
    operadoras.value = [];
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  page.value = 1; // Reseta pra primeira página
  fetchOperadoras();
};

const scrollToTable = () => {
  const tableSection = document.querySelector('.table-section');
  if (tableSection) {
    tableSection.scrollIntoView({ behavior: 'smooth' });
  }
};

const nextPage = () => {
  if ((page.value * limit.value) < total.value) {
    page.value++;
    fetchOperadoras().then(() => scrollToTable());
  }
};

const prevPage = () => {
  if (page.value > 1) {
    page.value--;
    fetchOperadoras().then(() => scrollToTable());
  }
};

const openDetails = async (operadora) => {
  selectedOperadora.value = operadora;
  modalOpen.value = true;
  loadingDespesas.value = true;
  operadoraDespesas.value = [];
  
  try {
    const { data } = await getOperadoraDespesas(operadora.cnpj);
    operadoraDespesas.value = data;
  } catch (error) {
    console.error("Erro ao carregar despesas:", error);
  } finally {
    loadingDespesas.value = false;
  }
};

const closeModal = () => {
  modalOpen.value = false;
  selectedOperadora.value = null;
  operadoraDespesas.value = [];
};

let timeout = null;
watch(searchQuery, () => {
  clearTimeout(timeout);
  timeout = setTimeout(() => {
    handleSearch();
  }, 500);
});

onMounted(() => {
  fetchOperadoras();
});
</script>

<template>
  <div class="app-wrapper">
    <!-- Navbar / Header -->
    <header class="navbar">
      <div class="container navbar-content">
        <div class="logo-area">
          <svg class="brand-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h1>IntuitiveCare Analytics</h1>
        </div>
        <div class="user-profile">
          <!-- Placeholder for user profile if needed -->
          <span class="badge">v1.0</span>
        </div>
      </div>
    </header>
    
    <main class="container main-content">
      <!-- Top Section: Chart -->
      <section class="dashboard-card chart-section">
        <div class="card-header">
          <h2>Despesas por Estado (UF)</h2>
          <p class="subtitle">Visão geral dos gastos consolidados</p>
        </div>
        <div class="chart-wrapper">
          <UfChart />
        </div>
      </section>

      <!-- Bottom Section: Table -->
      <section class="dashboard-card table-section">
        <div class="table-header-row">
          <div>
            <h2>Operadoras</h2>
            <p class="subtitle">Gerencie e visualize detalhes das operadoras</p>
          </div>
          <div class="search-wrapper">
            <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Buscar operadora..." 
              class="search-input"
            />
          </div>
        </div>
        
        <div class="table-frame">
          <!-- Loading Overlay -->
          <div v-if="loading && operadoras.length === 0" class="loading-state">
            <div class="spinner"></div>
            <p>Carregando dados...</p>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th>Registro ANS</th>
                <th>CNPJ</th>
                <th>Razão Social</th>
                <th class="text-right">Ações</th>
              </tr>
            </thead>
            <tbody :class="{ 'opacity-50': loading }">
              <tr v-if="operadoras.length === 0 && !loading">
                <td colspan="4" class="empty-state">
                  Nenhuma operadora encontrada.
                </td>
              </tr>
              <tr v-for="op in operadoras" :key="op.cnpj">
                <td><span class="badge-gray">{{ op.registro_ans || 'N/A' }}</span></td>
                <td class="font-mono">{{ op.cnpj }}</td>
                <td class="font-medium">{{ op.razao_social }}</td>
                <td class="text-right">
                  <button class="btn-primary-ghost" @click="openDetails(op)">
                    Ver Detalhes
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination-bar">
          <button 
            class="btn-nav" 
            @click="prevPage" 
            :disabled="page === 1 || loading"
          >
            &larr; Anterior
          </button>
          <span class="page-info">
            Página <strong>{{ page }}</strong> de <strong>{{ Math.ceil(total / limit) || 1 }}</strong>
          </span>
          <button 
            class="btn-nav" 
            @click="nextPage" 
            :disabled="(page * limit) >= total || loading"
          >
            Próximo &rarr;
          </button>
        </div>
      </section>
    </main>

    <!-- Modal de Detalhes -->
    <transition name="fade">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal-panel">
          <div class="modal-header">
            <div>
              <h3>{{ selectedOperadora?.razao_social }}</h3>
              <p class="modal-meta">CNPJ: {{ selectedOperadora?.cnpj }}</p>
            </div>
            <button class="btn-close" @click="closeModal">&times;</button>
          </div>
          
          <div class="modal-body">
            <div v-if="loadingDespesas" class="loading-container">
              <div class="spinner"></div>
            </div>
            
            <div v-else class="modal-table-wrapper">
              <table v-if="operadoraDespesas.length > 0" class="details-table">
                <thead>
                  <tr>
                    <th>Ano</th>
                    <th>Trimestre</th>
                    <th class="text-right">Valor Despesa</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(despesa, index) in operadoraDespesas" :key="index">
                    <td>{{ despesa.ano }}</td>
                    <td>{{ despesa.trimestre }}º Trimestre</td>
                    <td class="text-right font-bold text-green">
                      R$ {{ Number(despesa.valor_despesa).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="empty-state-small">
                Nenhum histórico de despesas disponível.
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="btn-secondary" @click="closeModal">Fechar</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* Scoped Layout */
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  width: 100%;
}

/* Navbar */
.navbar {
  background-color: #1e293b;
  color: white;
  padding: 16px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.navbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 32px;
  height: 32px;
  color: #3b82f6; /* Modern Blue */
}

h1 {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  color: #fff;
}

.badge {
  background: rgba(255,255,255,0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 30px;
  padding-bottom: 40px;
}

/* Cards */
.dashboard-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.card-header {
  padding: 24px 24px 0;
  margin-bottom: 20px;
}

.subtitle {
  color: #64748b;
  font-size: 0.875rem;
  margin-top: 4px;
}

/* Chart */
.chart-wrapper {
  padding: 0 24px 24px;
  height: 400px;
}

/* Table Section */
.table-header-row {
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  border-bottom: 1px solid #f1f5f9;
}

/* Search Input */
.search-wrapper {
  position: relative;
  width: 100%;
  max-width: 300px; /* Constrain max width but allow flexibility */
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #94a3b8;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.2s;
  outline: none;
  box-sizing: border-box; /* Prevent padding from breaking layout */
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Table Styling */
.table-frame {
  position: relative;
  min-height: 600px; /* Fixed height to accommodate ~10 rows + header, preventing jump */
  display: flex;
  flex-direction: column;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed; /* Ensures column widths are stable */
}

.data-table th {
  background-color: #f8fafc;
  color: #475569;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 24px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.data-table th.text-right {
  text-align: right;
}

.data-table td {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.9rem;
  vertical-align: middle;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px; /* Limit width to force ellipsis */
}

.data-table td.text-right {
  text-align: right;
}
.font-mono { font-family: monospace; color: #64748b; }
.font-medium { font-weight: 500; }
.text-green { color: #059669; }
.font-bold { font-weight: 600; }

.badge-gray {
  background-color: #f1f5f9;
  color: #475569;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
}

.btn-primary-ghost {
  background: transparent;
  color: #3b82f6;
  font-weight: 500;
  font-size: 0.85rem;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s;
  border: none;
  cursor: pointer;
}

.btn-primary-ghost:hover {
  background: #eff6ff;
  color: #2563eb;
}

/* Pagination */
.pagination-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #fff;
  border-top: 1px solid #f1f5f9;
}

.page-info {
  color: #64748b;
  font-size: 0.9rem;
}

.btn-nav {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 6px;
  color: #475569;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-nav:hover:not(:disabled) {
  border-color: #cbd5e1;
  background-color: #f8fafc;
  color: #1e293b;
}

.btn-nav:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #f1f5f9;
}

/* Loading States */
.opacity-50 {
  opacity: 0.5;
  pointer-events: none;
  transition: opacity 0.2s;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #94a3b8;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Modal */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 50;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.modal-panel {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-header h3 {
  font-size: 1.1rem;
  color: #1e293b;
  margin-bottom: 4px;
}

.modal-meta {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #94a3b8;
  cursor: pointer;
  line-height: 1;
}

.modal-body {
  padding: 0;
  overflow-y: auto;
  flex: 1;
}

.modal-table-wrapper {
  padding: 0;
}

.details-table {
  width: 100%;
  border-collapse: collapse;
}

.details-table th {
  background: #f8fafc;
  padding: 12px 24px;
  text-align: left;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.details-table td {
  padding: 12px 24px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  text-align: right;
  background-color: #f8fafc;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.btn-secondary {
  background: white;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  border-radius: 6px;
  color: #475569;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #f1f5f9;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
